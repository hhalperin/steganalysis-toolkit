"""
Demo live viewer: shows image with overlay boxes and step/phase text from state JSON.
Polls frame_path and state_path; draws boxes and labels when state exists.
"""

import json
import threading
from pathlib import Path
from typing import Any


def run_demo_live_viewer(
    frame_path: Path,
    state_path: Path,
    done_event: threading.Event,
    title: str = "Watermark Demo",
) -> None:
    """Run viewer that polls frame + state, draws overlays, updates until done."""
    try:
        import tkinter as tk
        from tkinter import ttk
        from PIL import Image, ImageDraw, ImageFont, ImageTk
    except ImportError as e:
        raise SystemExit(f"Demo viewer requires tkinter and Pillow: {e}") from e

    max_display = (960, 700)
    root = tk.Tk()
    root.title(title)
    root.configure(bg="#1a1a1a")

    label = ttk.Label(root, text="Waiting for first frame…", font=("Segoe UI", 11))
    label.pack(padx=8, pady=8, fill=tk.BOTH, expand=True)
    current_photo: ImageTk.PhotoImage | None = None

    def load_state() -> dict[str, Any] | None:
        if not state_path.exists():
            return None
        try:
            with open(state_path) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

    def draw_overlays(img: Image.Image, state: dict[str, Any]) -> Image.Image:
        """Draw boxes and optional text overlay on image. Returns new image (does not modify original)."""
        img = img.copy().convert("RGB")
        draw = ImageDraw.Draw(img)
        w, h = img.size

        boxes = state.get("boxes") or []
        for b in boxes:
            x, y = int(b.get("x", 0)), int(b.get("y", 0))
            bw, bh = int(b.get("w", 10)), int(b.get("h", 10))
            bw, bh = max(2, bw), max(2, bh)
            draw.rectangle([x, y, x + bw, y + bh], outline=(255, 80, 80), width=max(2, min(bw, bh) // 30))
            lbl = b.get("label", "")
            if lbl:
                try:
                    font = ImageFont.truetype("arial.ttf", 12)
                except OSError:
                    font = ImageFont.load_default()
                draw.text((x, max(0, y - 14)), lbl[:20], fill=(255, 80, 80), font=font)

        step_label = state.get("step_label", "")
        if step_label:
            try:
                font = ImageFont.truetype("arial.ttf", 14)
            except OSError:
                font = ImageFont.load_default()
            draw.rectangle([0, 0, w, 28], fill=(0, 0, 0, 200))
            draw.text((8, 6), step_label, fill=(255, 255, 255), font=font)

        return img

    def load_and_show() -> bool:
        nonlocal current_photo
        if not frame_path.exists():
            return False
        try:
            img = Image.open(frame_path).convert("RGB")
        except Exception:
            return False
        state = load_state()
        if state:
            img = draw_overlays(img, state)
        w, h = img.size
        if w > max_display[0] or h > max_display[1]:
            ratio = min(max_display[0] / w, max_display[1] / h)
            nw, nh = int(w * ratio), int(h * ratio)
            img = img.resize((nw, nh), Image.Resampling.LANCZOS)
        current_photo = ImageTk.PhotoImage(img)
        label.configure(image=current_photo, text="")
        label.image = current_photo
        if state:
            root.title(f"{title} - {state.get('step_label', '')}")
        return True

    shown_once = False
    while not done_event.wait(timeout=0.25):
        if load_and_show():
            shown_once = True
        elif not shown_once:
            label.configure(text="Waiting for first frame…")
        root.update()
    if not shown_once:
        load_and_show()
    root.destroy()
