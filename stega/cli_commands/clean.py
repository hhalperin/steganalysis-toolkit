"""Detect and clean a single image (LSB, patterns, visible watermarks)."""

import shutil
from pathlib import Path

from ..config import clean_path, ensure_dirs
from ..detection.chunk_analyzer import analyze_png_chunks
from ..detection.steganography import analyze_steganography
from ..detection.visible_watermark_detector import detect_visible_watermarks
from ..advanced_waste_detector import analyze_advanced_waste
from ..cleaning.steganography_sanitizer import SteganographySanitizer
from ..cleaning.visible_watermark_remover import remove_visible_watermarks
from ..cleaning.image_cleaner import aggressive_lsb_cleaning


def run_detection(image_path: str, quick: bool = False, invisible_only: bool = False) -> dict:
    results = {"file": str(image_path), "findings": [], "advanced_waste": {}, "patterns": {}, "visible_watermarks": None}
    path = Path(image_path)
    is_png = path.suffix.lower() == ".png"

    if is_png and not quick:
        try:
            r = analyze_png_chunks(image_path)
            results["chunk_analysis"] = r
            if r.get("suspicious_chunks") or r.get("crc_failures"):
                results["findings"].append("Suspicious PNG chunks")
        except Exception as e:
            results["chunk_analysis"] = {"error": str(e)}

    if not quick:
        try:
            stego = analyze_steganography(image_path)
            if isinstance(stego, dict):
                for k, v in stego.items():
                    if isinstance(v, dict) and v.get("suspicious"):
                        results["findings"].append(f"Steganography: {k}")
        except Exception:
            pass

    if not quick and not invisible_only:
        try:
            vw = detect_visible_watermarks(image_path)
            results["visible_watermarks"] = vw
            if vw.get("total_detections", 0) > 0:
                results["findings"].append(f"Visible watermarks: {vw['total_detections']}")
        except Exception as e:
            results["visible_watermarks"] = {"error": str(e)}
    else:
        results["visible_watermarks"] = {}

    if not quick:
        try:
            adv = analyze_advanced_waste(image_path)
            for pattern, finding in adv.items():
                if hasattr(finding, "detected") and finding.detected:
                    results["advanced_waste"][pattern] = {
                        "confidence": finding.confidence,
                        "removal": getattr(finding, "recommended_removal", ""),
                    }
                    results["findings"].append(f"{pattern} ({finding.confidence:.2f})")
        except Exception as e:
            results["advanced_waste"] = {"error": str(e)}

    try:
        s = SteganographySanitizer()
        pat = s.detect_patterns(image_path, quiet=True)
        for name, data in pat.items():
            if isinstance(data, dict) and data.get("suspicious"):
                results["patterns"][name] = data
                results["findings"].append(f"pattern:{name}")
    except Exception as e:
        results["patterns"] = {"error": str(e)}

    return results


def build_cleaning_plan(
    detection: dict, visible_method: str = "gradient_guided"
) -> list[tuple[str, str]]:
    """Build ordered list of (step_label, method) for cleaning. Method is 'visible', a sanitizer name, or 'aggressive_lsb'."""
    plan: list[tuple[str, str]] = []
    vw = detection.get("visible_watermarks") or {}
    if isinstance(vw, dict) and vw.get("total_detections", 0) > 0:
        plan.append((f"Visible → {visible_method}", "visible"))

    methods: list[str] = []
    if detection.get("advanced_waste") and "geometric_watermarks" in detection["advanced_waste"]:
        methods.append("geometric_transformation")
    for p, d in (detection.get("advanced_waste") or {}).items():
        r = (d if isinstance(d, dict) else {}).get("removal", "").lower()
        if "lsb" in r or "random" in r:
            methods.extend(["lsb_natural", "selective_clean"])
        elif "noise" in r:
            methods.append("noise_injection")
        elif "channel" in r or "printer" in p:
            methods.append("channel_adjustment")
        elif "compress" in r:
            methods.append("compression_cycle")
    if detection.get("patterns"):
        if "lsb_natural" not in methods and "selective_clean" not in methods:
            methods.extend(["lsb_natural", "selective_clean"])
        if "sequential_encoding" in detection.get("patterns", {}):
            methods.append("compression_cycle")
    if methods and "lsb_natural" not in methods and "geometric_transformation" in methods:
        methods.extend(["lsb_natural", "selective_clean"])
    if not methods:
        methods = ["lsb_natural"]

    seen: set[str] = set()
    ordered = [m for m in methods if m not in seen and not seen.add(m)]
    for m in ordered:
        plan.append((m, m))
    plan.append(("aggressive_lsb", "aggressive_lsb"))
    return plan


def clean_image(image_path: str, detection: dict, output_path: str) -> str:
    plan = build_cleaning_plan(detection)
    sanitizer = SteganographySanitizer()
    out_dir = Path(output_path).parent
    out_dir.mkdir(parents=True, exist_ok=True)
    current = image_path
    vw = detection.get("visible_watermarks") or {}

    for i, (step_label, method) in enumerate(plan):
        if method == "visible":
            if isinstance(vw, dict) and vw.get("detections"):
                try:
                    step = out_dir / f"_step_visible_{Path(image_path).stem}.png"
                    remove_visible_watermarks(current, vw, str(step), method="gradient_guided")
                    current = str(step)
                except Exception:
                    pass
        elif method == "aggressive_lsb":
            try:
                aggressive_lsb_cleaning(current, output_path, quiet=True)
                current = output_path
            except Exception:
                shutil.copy(current, output_path)
        else:
            next_p = out_dir / f"_tmp_{i}_{method}.png"
            try:
                sanitizer.sanitize_image(current, str(next_p), method=method, preserve_quality=0.97, quiet=True)
                current = str(next_p)
            except Exception:
                pass

    for f in out_dir.glob("_tmp_*.png"):
        f.unlink(missing_ok=True)
    for f in out_dir.glob("_step_visible_*.png"):
        f.unlink(missing_ok=True)
    return output_path
