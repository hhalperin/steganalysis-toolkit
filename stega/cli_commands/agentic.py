"""Agentic watermark removal: detect -> remove -> verify -> retry."""

import json
import shutil
import threading
from pathlib import Path
from datetime import datetime

from ..detection.visible_watermark_detector import detect_visible_watermarks
from ..cleaning.visible_watermark_remover import remove_visible_watermarks


def _log(quiet: bool, msg: str) -> None:
    if not quiet:
        print(msg)


def _write_live_frame(path: str | Path | None, image_path: str) -> None:
    if not path:
        return
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(image_path, p)


def _write_live_frame_with_boxes(path: str | Path | None, image_path: str, detections: list) -> None:
    if not path or not detections:
        _write_live_frame(path, image_path)
        return
    try:
        from PIL import Image, ImageDraw
        img = Image.open(image_path).convert("RGB")
        draw = ImageDraw.Draw(img)
        for d in detections:
            loc = d.get("location")
            if loc and len(loc) == 4:
                x, y, w, h = loc
                draw.rectangle([x, y, x + w, y + h], outline=(255, 80, 80), width=max(2, min(w, h) // 30))
        img.save(path)
    except Exception:
        _write_live_frame(path, image_path)


def tool_detect(image_path: str) -> dict:
    try:
        return detect_visible_watermarks(image_path)
    except Exception as e:
        return {"total_detections": 0, "detections": [], "error": str(e)}


def tool_remove(image_path: str, detection_results: dict, output_path: str, method: str = "lama") -> tuple[bool, str]:
    detections = detection_results.get("detections", [])
    if not detections:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(image_path, output_path)
        return True, output_path
    try:
        result = remove_visible_watermarks(image_path, detection_results, output_path, method=method)
        return result.success, result.cleaned_path if result.success else ""
    except Exception as e:
        return False, str(e)


def tool_verify(image_path: str, clean_threshold: float = 0.3) -> dict:
    try:
        report = detect_visible_watermarks(image_path)
        total = report.get("total_detections", 0)
        max_conf = max((d.get("confidence", 0) for d in report.get("detections", [])), default=0.0)
        clean = total == 0 or max_conf < clean_threshold
        score = 1.0 - max_conf if total > 0 else 1.0
        return {"clean": clean, "score": score, "total_detections": total, "max_confidence": max_conf}
    except Exception as e:
        return {"clean": False, "score": 0.0, "total_detections": -1, "error": str(e)}


def dilate_detections(detections: list, factor: float = 1.1, img_w: int | None = None, img_h: int | None = None) -> list:
    dilated = []
    for d in detections:
        loc = list(d.get("location", (0, 0, 10, 10)))
        if len(loc) != 4:
            continue
        x, y, w, h = loc
        dw = max(0, int((w * factor - w) / 2))
        dh = max(0, int((h * factor - h) / 2))
        x2, y2 = max(0, x - dw), max(0, y - dh)
        w2, h2 = int(w * factor), int(h * factor)
        if img_w is not None:
            w2 = min(w2, img_w - x2)
        if img_h is not None:
            h2 = min(h2, img_h - y2)
        d2 = dict(d)
        d2["location"] = (x2, y2, max(2, w2), max(2, h2))
        dilated.append(d2)
    return dilated


def run_pipeline(
    input_path: str,
    output_path: str,
    max_retries: int = 3,
    method: str = "lama",
    clean_threshold: float = 0.3,
    log_path: str | None = None,
    quiet: bool = False,
    live_frame_path: str | Path | None = None,
    done_event: threading.Event | None = None,
) -> dict:
    state = {"input_path": input_path, "output_path": output_path, "detection": None, "verification": None, "retries": 0, "success": False}
    try:
        _write_live_frame(live_frame_path, input_path)
        _log(quiet, "Detecting watermarks…")
        current_input = input_path
        detection = tool_detect(current_input)
        n = detection.get("total_detections", 0)
        state["detection"] = {"total_detections": n}
        _write_live_frame_with_boxes(live_frame_path, current_input, detection.get("detections", []))

        if n == 0:
            _log(quiet, "No watermarks found.")
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(input_path, output_path)
            state["verification"] = tool_verify(output_path, clean_threshold)
            state["success"] = state["verification"].get("clean", True)
            if log_path:
                _append_log(log_path, state)
            return state

        _log(quiet, f"Found {n} region(s).")

        for attempt in range(max_retries + 1):
            out = output_path if attempt == 0 else str(Path(output_path).with_stem(f"{Path(output_path).stem}_retry{attempt}"))
            Path(out).parent.mkdir(parents=True, exist_ok=True)

            if attempt > 0:
                _log(quiet, f"Retry {attempt}/{max_retries}: dilating regions and re-removing…")
                try:
                    from PIL import Image
                    with Image.open(current_input) as im:
                        img_w, img_h = im.size
                except OSError:
                    img_w, img_h = None, None
                dilated = dilate_detections(detection.get("detections", []), factor=1.0 + 0.1 * attempt, img_w=img_w, img_h=img_h)
                detection = {"detections": dilated, "total_detections": len(dilated)}

            _log(quiet, f"Removing (attempt {attempt + 1}, method={method})…")
            ok, cleaned = tool_remove(current_input, detection, out, method=method)
            if not ok:
                _log(quiet, f"Removal failed: {cleaned}")
                state["error"] = cleaned
                if log_path:
                    _append_log(log_path, state)
                return state

            _write_live_frame(live_frame_path, cleaned)
            _log(quiet, "Verifying…")
            verification = tool_verify(cleaned, clean_threshold)
            state["verification"] = verification
            state["retries"] = attempt
            score = verification.get("score", 0.0)

            if verification.get("clean", False):
                _log(quiet, f"Clean (score {score:.2f}).")
                state["success"] = True
                if attempt > 0:
                    shutil.copy(cleaned, output_path)
                if log_path:
                    _append_log(log_path, state)
                return state

            _log(quiet, f"Still traces (score {score:.2f}). Retrying with larger regions…")
            current_input = cleaned
            detection = tool_detect(cleaned)

        _log(quiet, "Max retries reached; some traces may remain.")
        state["success"] = False
    finally:
        if done_event is not None:
            done_event.set()
    if log_path:
        _append_log(log_path, state)
    return state


def _append_log(log_path: str, state: dict) -> None:
    record = {
        "timestamp": datetime.now().isoformat(),
        "input_path": state.get("input_path"),
        "output_path": state.get("output_path"),
        "detection_count": state.get("detection", {}).get("total_detections", 0),
        "verification": state.get("verification"),
        "retries": state.get("retries", 0),
        "success": state.get("success", False),
    }
    with open(log_path, "a") as f:
        f.write(json.dumps(record) + "\n")
