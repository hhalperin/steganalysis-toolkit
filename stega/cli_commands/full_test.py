"""Full detection test: run all detection modules on a set of images."""

import json
import sys
from pathlib import Path
from datetime import datetime

from ..config import resolve_output_dir, resolve_reports_dir
from ..detection.chunk_analyzer import analyze_png_chunks
from ..detection.steganography import analyze_steganography
from ..detection.visible_watermark_detector import detect_visible_watermarks
from ..advanced_waste_detector import analyze_advanced_waste
from ..cleaning.steganography_sanitizer import SteganographySanitizer


def run_full_detection(image_path: str, quick: bool = False) -> dict:
    results = {
        "file": str(image_path),
        "timestamp": datetime.now().isoformat(),
        "chunk_analysis": None,
        "steganography": None,
        "visible_watermarks": None,
        "text_watermarks": None,
        "advanced_waste": None,
        "sanitizer_patterns": None,
        "summary": {"findings": [], "risk": "low"},
    }

    try:
        r = analyze_png_chunks(image_path)
        results["chunk_analysis"] = r
        if r.get("suspicious_chunks") or r.get("crc_failures"):
            results["summary"]["findings"].append("suspicious_chunks_or_crc")
    except Exception as e:
        results["chunk_analysis"] = {"error": str(e)}

    if not quick:
        try:
            r = analyze_steganography(image_path)
            if isinstance(r, dict) and "error" not in r:
                results["steganography"] = r
                for k, v in r.items():
                    if isinstance(v, dict) and v.get("suspicious"):
                        results["summary"]["findings"].append(f"stego:{k}")
        except Exception as e:
            results["steganography"] = {"error": str(e)}
    else:
        results["steganography"] = {"skipped": "quick mode"}

    if not quick:
        try:
            r = detect_visible_watermarks(image_path)
            results["visible_watermarks"] = {"total_detections": r.get("total_detections", 0), "summary": r.get("summary", {})}
            if r.get("total_detections", 0) > 0:
                results["summary"]["findings"].append(f"visible_watermarks:{r['total_detections']}")
        except Exception as e:
            results["visible_watermarks"] = {"error": str(e)}
    else:
        results["visible_watermarks"] = {"skipped": "quick mode"}

    try:
        from ..detection.text_watermark_detector import detect_text_watermarks
        r = detect_text_watermarks(image_path)
        results["text_watermarks"] = {"total": r.get("total_text_detections", 0), "summary": r.get("summary", {})}
        if r.get("text_detections"):
            results["summary"]["findings"].append(f"text_watermarks:{len(r['text_detections'])}")
    except ImportError:
        results["text_watermarks"] = {"skipped": "pytesseract not available"}
    except Exception as e:
        results["text_watermarks"] = {"error": str(e)}

    try:
        adv = analyze_advanced_waste(image_path)
        results["advanced_waste"] = {}
        for pattern, finding in adv.items():
            if hasattr(finding, "detected") and finding.detected:
                results["advanced_waste"][pattern] = {"confidence": finding.confidence, "removal": getattr(finding, "recommended_removal", "")}
                results["summary"]["findings"].append(f"advanced:{pattern}({finding.confidence:.2f})")
    except Exception as e:
        results["advanced_waste"] = {"error": str(e)}

    try:
        s = SteganographySanitizer()
        pat = s.detect_patterns(image_path, quiet=True)
        results["sanitizer_patterns"] = {k: v for k, v in pat.items() if isinstance(v, dict) and v.get("suspicious")}
        for name in results["sanitizer_patterns"]:
            results["summary"]["findings"].append(f"pattern:{name}")
    except Exception as e:
        results["sanitizer_patterns"] = {"error": str(e)}

    n = len(results["summary"]["findings"])
    results["summary"]["risk"] = "critical" if n >= 5 else "high" if n >= 3 else "medium" if n >= 1 else "low"
    return results
