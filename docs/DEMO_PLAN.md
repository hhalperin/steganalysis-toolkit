# Demo Plan: Showcase Watermark Detection & Cleaning

Goal: One seamless, fun-to-watch demo that shows how the system **identifies combinations and styles** of marking techniques and **cleans** them, so the capability is obvious and engaging.

---

## 1. Narrative Arc (What the Viewer Sees)

| Phase | Name | What happens | What we show |
|-------|------|--------------|--------------|
| **1** | Scan | Run all detectors (visible, stego, chunks, advanced waste, patterns) | Single image; subtle "Scanning…" then **findings list** (no overlay yet). |
| **2** | Reveal | Map findings onto the image | **Overlay**: regions with labels (e.g. "Visible: edge_anomaly", "LSB", "Pattern: sequential"). Optional: small legend "Detection styles: visible (3), stego, pattern". |
| **3** | Plan | Decide cleaning strategy from findings | Short **"Cleaning plan"** line: "Applying: visible → LaMa; stego → lsb_natural, selective_clean; patterns → compression_cycle." |
| **4** | Clean | Run cleaning (visible first, then sanitizer steps, then LSB) | **Live image** updates after each step; optional **step label** ("Visible → LaMa", "LSB natural", "Verifying…"). |
| **5** | Verify | Check clean score; retry if needed (agentic) | "Clean (0.92)" or "Retrying with larger regions…" then next clean frame. |
| **6** | Done | Final state | Final image + one-line summary: "Removed: 3 visible, LSB, 2 patterns. Output: path." |

Seamless = one window + one command; no switching between terminal and viewer.

---

## 2. Single Entry Point: `demo` Command

- **CLI**: `python -m stega.cli demo <image> [-o output] [--live] [--export-dir dir]`
- **Behavior**:
  - **Full pipeline**: same as `clean` (run_detection → clean_image) so we get **all** detection types and **all** cleaning steps (visible, sanitizer methods, aggressive LSB).
  - Optional **agentic-style** verify/retry at the end (e.g. re-detect visible and retry visible removal if not clean) for a "battle" finish.
  - **--live**: one window that shows the narrative phases (scan → reveal → clean → verify) with overlays and step labels.
  - **--export-dir**: write per-step frames (scan_result.png, reveal_overlay.png, step_1_visible.png, step_2_lsb.png, …) for a replay or video.

So the demo **showcases combinations**: which marking styles were found and which techniques were applied.

---

## 3. What to Show (Combinations & Styles)

### 3.1 Detection side (for "Reveal")

- **Visible watermarks**: from `detect_visible_watermarks` — show each region with **type** (e.g. `edge_anomaly`, `texture_anomaly`, `gradient_anomaly`, `geometric_pattern`, `color_transition`, `frequency_anomaly`) and confidence. Already have `location` and `type` / `recommended_removal` in the API.
- **Advanced waste**: from `analyze_advanced_waste` — pattern names (e.g. `multi_layer`, `geometric_watermarks`, `printer_tracking`, `ai_model_fingerprints`) and recommended_removal. These are image-wide; show as **tags** or a **sidebar** ("Also detected: LSB, geometric_watermarks, printer_tracking").
- **Steganography / chunks / patterns**: from `run_detection` — "Steganography: …", "Suspicious PNG chunks", "pattern: sequential_encoding". Show as **badges** (e.g. top or bottom of frame) so "marking styles" are explicit.

### 3.2 Cleaning side (for "Plan" and "Clean")

- **Visible**: method used (LaMa / inpainting / gradient_guided / texture_synthesis, etc.) — one line per attempt if we do agentic verify/retry.
- **Sanitizer**: ordered list of methods actually run (lsb_natural, selective_clean, noise_injection, channel_adjustment, compression_cycle, geometric_transformation, etc.) from `clean_image` logic.
- **Final**: aggressive_lsb_cleaning.

So the "incredible" part is: **we show the exact combination** — "This image had [visible edge + texture, LSB, sequential pattern]. We applied [visible → LaMa, lsb_natural, selective_clean, compression_cycle, LSB clean]."

---

## 4. Visual Layer (One Window)

- **Same window** as current `--live` idea: one image that updates over time.
- **Phases**:
  - **Scan**: image only; title or subtitle "Scanning…".
  - **Reveal**: same image + **overlays**:
    - Colored boxes per visible region with short label (type or "Visible").
    - Optional: strip or panel with "Detection styles: …" (visible types, advanced_waste names, stego/chunk/pattern findings).
  - **Plan**: optional text overlay or console line: "Cleaning plan: …".
  - **Clean**: image updates after each cleaning step; optional short-lived label ("Visible → LaMa", "LSB natural", "Verifying…").
  - **Done**: final image + "Clean" or "Removed: …" summary.

Implementation options:

- **A) Enriched live viewer**: extend `agentic_live_viewer` to accept not only a frame path but also **overlay metadata** (boxes + labels) and **phase/step text**. The pipeline writes a frame plus a small JSON (or shared struct) with overlay and step text; viewer reads both and draws.
- **B) Browser UI**: pipeline writes frames + a tiny JSON "state" (phase, step, findings, plan). A local HTML page (or single HTML file opened in browser) polls or uses a simple WS/server to refresh image and overlays. Easier to make pretty and to record (browser record or export frames).
- **C) Tkinter with overlays**: same as A but implemented in the current Tk viewer (draw boxes and text on top of the image). No new stack; keeps one process.

Recommendation: **C** for minimal dependencies and one-command demo; **B** if you want a shareable "demo reel" page later.

---

## 5. Technique Combination Summary (Explicit)

At the end of the run (and optionally on screen in "Done" phase), print or show:

- **Detected**: list of "marking styles" (e.g. "Visible (3): edge_anomaly, texture_anomaly; LSB; Pattern: sequential_encoding; Advanced: geometric_watermarks").
- **Applied**: ordered list of cleaning steps (e.g. "visible→gradient_guided, lsb_natural, selective_clean, compression_cycle, aggressive_lsb").
- **Result**: clean score (if we did verify) and output path.

This is the "showcase": one block that tells the story of **what we found** and **how we cleaned it**.

---

## 6. Optional: Demo Reel Export

- **--export-dir <dir>**: for each phase/step, write a frame (and optional overlay data). Then:
  - A small script or HTML can play them in order (slideshow or video).
  - Or use ffmpeg to turn frames into a short video (e.g. "demo_reel.mp4") for sharing.

Makes the demo **replayable** without re-running the pipeline.

---

## 7. Implementation Outline (Order of Work)

1. **Unified demo pipeline**
   - New `run_demo_pipeline(image_path, output_path, …)` that:
     - Runs `run_detection` (full, not quick).
     - Builds "cleaning plan" from findings (mirror `clean_image` logic into a list of (step_name, method) or similar).
     - Runs cleaning step-by-step, writing to a **live frame path** and optional **overlay/step state** after each step.
     - Optionally runs verify + retry (agentic-style) at the end.
   - No UI yet; just flow + state.

2. **Overlay + step state**
   - Define a small structure: e.g. `{ "phase": "reveal"|"clean"|"verify"|"done", "step_label": "...", "boxes": [{ "xywh", "label", "type" }], "findings_summary": "...", "plan_summary": "..." }`.
   - Pipeline writes this (e.g. next to the live frame as `.agentic_live.json` or similar) whenever it updates the frame.

3. **Viewer that reads frame + state**
   - Extend the live viewer (or add a "demo viewer"):
     - Load image from path.
     - If state file exists, draw boxes + labels and step/phase text.
     - Refresh at same poll rate.
   - Pipeline drives everything by writing frame + state; viewer is dumb.

4. **CLI `demo`**
   - `python -m stega.cli demo <image> [-o output] [--live] [--export-dir dir]`.
   - Calls `run_demo_pipeline` with live_frame_path and export_dir; if `--live`, starts the enriched viewer in the main thread and pipeline in a background thread (same pattern as agentic --live).

5. **Final summary**
   - In pipeline and in CLI: print (and optionally show in "Done" overlay) the **Detected / Applied / Result** block.

6. **(Later)** **Export reel**
   - If `--export-dir` is set, write numbered frames + state; add a small HTML or script to replay, or an ffmpeg step to produce a video.

---

## 8. What Makes It "Highly Incredible" and Seamless

- **One command**: `demo image.png --live` → one window, full story.
- **Combinations visible**: overlays and summary show **which marking styles** were found and **which techniques** were used to clean them.
- **No redundancy**: one narrative (scan → reveal → plan → clean → verify → done), no duplicate logs; optional `--quiet` for terminal.
- **Replayable**: `--export-dir` gives a set of frames (and optional reel) so you can showcase without re-running.
- **Fun to watch**: live image updates, boxes appearing, then disappearing as regions are cleaned, and a clear "Clean" or "Retrying…" moment.

This plan keeps the existing detection and cleaning code as-is and adds a **demo orchestration layer** (run_demo_pipeline + enriched viewer + demo CLI) that surfaces the combinations and styles seamlessly.
