"""Demo pipeline: full detection, step-by-step cleaning with live overlay state."""

import json
import shutil
import threading
from pathlib import Path
from typing import Any

from .clean import build_cleaning_plan, run_detection
from .agentic import tool_detect, tool_remove, tool_verify
from ..cleaning.steganography_sanitizer import SteganographySanitizer
from ..cleaning.visible_watermark_remover import remove_visible_watermarks
from ..cleaning.image_cleaner import aggressive_lsb_cleaning

PHASE = str  # "scan" | "reveal" | "plan" | "clean" | "verify" | "done"


def _log(quiet: bool, msg: str) -> None:
    if not quiet:
        print(msg)


def _write_frame_and_state(
    image_path: str,
    state: dict[str, Any],
    live_frame_path: Path | None,
    state_path: Path | None,
    export_dir: Path | None,
    step_index: int | None,
) -> None:
    """Write frame (copy of image) and state JSON to live paths and optionally export_dir."""
    if live_frame_path:
        live_frame_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(image_path, live_frame_path)
    if state_path:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(state_path, "w") as f:
            json.dump(state, f, indent=0)
    if export_dir and step_index is not None:
        export_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(image_path, export_dir / f"step_{step_index:02d}.png")
        with open(export_dir / f"step_{step_index:02d}.json", "w") as f:
            json.dump(state, f, indent=0)


def _detection_to_boxes(detection: dict) -> list[dict[str, Any]]:
    """Convert visible_watermarks detections to overlay boxes with labels."""
    boxes = []
    vw = detection.get("visible_watermarks") or {}
    if not isinstance(vw, dict):
        return boxes
    for d in vw.get("detections") or []:
        loc = d.get("location")
        if loc and len(loc) == 4:
            x, y, w, h = loc
            label = d.get("type", "visible") or "visible"
            boxes.append({"x": int(x), "y": int(y), "w": int(w), "h": int(h), "label": label, "type": label})
    return boxes


def _build_findings_summary(detection: dict) -> str:
    """Build short summary of detection styles for overlay."""
    parts = []
    vw = detection.get("visible_watermarks") or {}
    if isinstance(vw, dict) and vw.get("total_detections", 0) > 0:
        types = set(d.get("type", "visible") for d in (vw.get("detections") or []))
        parts.append(f"Visible ({vw['total_detections']}): {', '.join(sorted(types))}")
    for f in detection.get("findings") or []:
        if f.startswith("Steganography:") or f.startswith("Suspicious") or f.startswith("pattern:"):
            parts.append(f)
        elif f.startswith("Visible watermarks"):
            continue
        else:
            parts.append(f)
    return "; ".join(parts) if parts else "No findings"


def _build_detected_styles(detection: dict) -> list[str]:
    """Build list of marking styles for final summary."""
    styles = []
    vw = detection.get("visible_watermarks") or {}
    if isinstance(vw, dict) and vw.get("detections"):
        for d in vw["detections"]:
            t = d.get("type", "visible")
            if t and t not in styles:
                styles.append(t)
    for f in detection.get("findings") or []:
        if f.startswith("Steganography:"):
            styles.append("LSB/stego")
        elif f.startswith("pattern:"):
            styles.append(f.replace("pattern:", "pattern:"))
        elif f.startswith("Suspicious"):
            styles.append("PNG chunks")
        elif f not in styles and not f.startswith("Visible watermarks"):
            styles.append(f)
    return styles


def run_demo_pipeline(
    image_path: str,
    output_path: str,
    *,
    live_frame_path: Path | str | None = None,
    state_path: Path | str | None = None,
    export_dir: Path | str | None = None,
    quiet: bool = False,
    do_verify: bool = True,
    max_retries: int = 3,
    clean_threshold: float = 0.3,
    visible_method: str = "gradient_guided",
    done_event: threading.Event | None = None,
) -> dict[str, Any]:
    """Run full detection, reveal, plan, clean step-by-step, optional verify/retry."""
    frame_p = Path(live_frame_path) if live_frame_path else None
    state_p = Path(state_path) if state_path else None
    export_p = Path(export_dir) if export_dir else None
    out_dir = Path(output_path).parent
    out_dir.mkdir(parents=True, exist_ok=True)

    step_idx = 0
    applied_steps: list[str] = []

    try:
        # Scan
        _log(quiet, "Scanning…")
        detection = run_detection(image_path, quick=False)
        state = {"phase": "scan", "step_label": "Scanning…", "boxes": [], "findings_summary": "", "plan_summary": ""}
        _write_frame_and_state(image_path, state, frame_p, state_p, export_p, step_idx)
        step_idx += 1

        # Reveal
        state = {
            "phase": "reveal",
            "step_label": "Reveal",
            "boxes": _detection_to_boxes(detection),
            "findings_summary": _build_findings_summary(detection),
            "plan_summary": "",
        }
        _write_frame_and_state(image_path, state, frame_p, state_p, export_p, step_idx)
        step_idx += 1

        plan = build_cleaning_plan(detection, visible_method=visible_method)
        plan_str = " → ".join(label for label, _ in plan)
        state = {
            "phase": "plan",
            "step_label": "Plan",
            "boxes": _detection_to_boxes(detection),
            "findings_summary": _build_findings_summary(detection),
            "plan_summary": f"Applying: {plan_str}",
        }
        _write_frame_and_state(image_path, state, frame_p, state_p, export_p, step_idx)
        step_idx += 1

        vw = detection.get("visible_watermarks") or {}
        sanitizer = SteganographySanitizer()
        current = image_path

        for step_label, method in plan:
            if method == "visible":
                if isinstance(vw, dict) and vw.get("detections"):
                    _log(quiet, f"Removing visible ({visible_method})…")
                    state = {"phase": "clean", "step_label": step_label, "boxes": [], "findings_summary": "", "plan_summary": plan_str}
                    _write_frame_and_state(current, state, frame_p, state_p, export_p, step_idx)
                    step_idx += 1
                    try:
                        step_file = out_dir / f"_demo_visible_{Path(image_path).stem}.png"
                        result = remove_visible_watermarks(current, vw, str(step_file), method=visible_method)
                        if result.success:
                            current = result.cleaned_path
                            applied_steps.append(f"visible→{visible_method}")
                    except Exception:
                        pass
            elif method == "aggressive_lsb":
                _log(quiet, "Aggressive LSB cleaning…")
                state = {"phase": "clean", "step_label": step_label, "boxes": [], "findings_summary": "", "plan_summary": plan_str}
                _write_frame_and_state(current, state, frame_p, state_p, export_p, step_idx)
                step_idx += 1
                try:
                    aggressive_lsb_cleaning(current, output_path, quiet=True)
                    current = output_path
                    applied_steps.append("aggressive_lsb")
                except Exception:
                    shutil.copy(current, output_path)
                    current = output_path
                    applied_steps.append("aggressive_lsb")
            else:
                _log(quiet, f"{step_label}…")
                state = {"phase": "clean", "step_label": step_label, "boxes": [], "findings_summary": "", "plan_summary": plan_str}
                _write_frame_and_state(current, state, frame_p, state_p, export_p, step_idx)
                step_idx += 1
                next_p = out_dir / f"_demo_tmp_{method}.png"
                try:
                    sanitizer.sanitize_image(current, str(next_p), method=method, preserve_quality=0.97, quiet=True)
                    current = str(next_p)
                    applied_steps.append(method)
                except Exception:
                    pass

        verification: dict[str, Any] = {}
        if do_verify:
            _log(quiet, "Verifying…")
            state = {"phase": "verify", "step_label": "Verifying…", "boxes": [], "findings_summary": "", "plan_summary": plan_str}
            _write_frame_and_state(output_path, state, frame_p, state_p, export_p, step_idx)
            step_idx += 1
            verification = tool_verify(output_path, clean_threshold)
            if not verification.get("clean") and max_retries > 0:
                vw_detect = tool_detect(output_path)
                for attempt in range(max_retries):
                    _log(quiet, f"Retrying ({attempt + 1}/{max_retries})…")
                    state = {"phase": "verify", "step_label": f"Retrying… ({attempt + 1})", "boxes": [], "findings_summary": "", "plan_summary": plan_str}
                    _write_frame_and_state(output_path, state, frame_p, state_p, export_p, step_idx)
                    step_idx += 1
                    ok, cleaned = tool_remove(output_path, vw_detect, output_path, method=visible_method)
                    if ok:
                        _write_frame_and_state(cleaned, state, frame_p, state_p, export_p, step_idx)
                        verification = tool_verify(cleaned, clean_threshold)
                        if verification.get("clean"):
                            break
                        vw_detect = tool_detect(cleaned)

        detected_styles = _build_detected_styles(detection)
        final_state = {
            "phase": "done",
            "step_label": "Done",
            "boxes": [],
            "findings_summary": _build_findings_summary(detection),
            "plan_summary": plan_str,
            "detected_styles": detected_styles,
            "applied_steps": applied_steps,
            "verification": verification,
            "output_path": output_path,
        }
        _write_frame_and_state(output_path, final_state, frame_p, state_p, export_p, step_idx)

        for f in out_dir.glob("_demo_tmp_*.png"):
            f.unlink(missing_ok=True)
        for f in out_dir.glob("_demo_visible_*.png"):
            f.unlink(missing_ok=True)

        return {
            "detected_styles": detected_styles,
            "applied_steps": applied_steps,
            "verification": verification,
            "output_path": output_path,
            "success": verification.get("clean", True) if do_verify else True,
        }
    finally:
        if done_event:
            done_event.set()
