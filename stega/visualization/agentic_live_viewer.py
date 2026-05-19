"""
Live viewer for the agentic pipeline: shows the current image as it is cleaned.
Runs in the main thread; pipeline runs in a background thread and writes to the same path.
"""

import threading
from pathlib import Path

# Tk and PIL used only when --live; avoid importing at module level for headless use
def run_live_viewer(live_frame_path: Path, done_event: threading.Event, title: str = "Watermark cleanup") -> None:
    try:
        import tkinter as tk
        from tkinter import ttk
        from PIL import Image, ImageTk
    except ImportError as e:
        raise SystemExit(f"Live viewer requires tkinter and Pillow: {e}") from e

    max_display = (960, 700)
    root = tk.Tk()
    root.title(title)
    root.configure(bg="#1a1a1a")

    label = ttk.Label(root, text="Starting…", font=("Segoe UI", 11))
    label.pack(padx=8, pady=8, fill=tk.BOTH, expand=True)
    current_photo: ImageTk.PhotoImage | None = None

    def load_and_show() -> bool:
        nonlocal current_photo
        if not live_frame_path.exists():
            return False
        try:
            img = Image.open(live_frame_path).convert("RGB")
        except Exception:
            return False
        w, h = img.size
        if w > max_display[0] or h > max_display[1]:
            ratio = min(max_display[0] / w, max_display[1] / h)
            nw, nh = int(w * ratio), int(h * ratio)
            img = img.resize((nw, nh), Image.Resampling.LANCZOS)
        current_photo = ImageTk.PhotoImage(img)
        label.configure(image=current_photo, text="")
        label.image = current_photo
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
