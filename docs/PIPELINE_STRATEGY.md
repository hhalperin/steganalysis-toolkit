# Pipeline Strategy: Why We Use It and What’s Better

## Why the current strategy (agentic) exists

The **agentic** pipeline is:

1. **Visible-only** — Runs only `detect_visible_watermarks` and `remove_visible_watermarks`. No LSB/stego/chunk/advanced-waste detection or cleaning.
2. **Detect → remove → verify → retry** — After each removal it re-runs the visible detector on the output; if not “clean” (max_confidence < clean_threshold), it dilates regions and retries (up to `max_retries`).
3. **Single removal method per run** — One of `lama` | `inpainting` | `opencv_ns` for the whole run.

**Reasons for this design:**

- **Focused on visible marks** — Many resilience experiments start from synthetic overlays (logos, text bands). Visible detector + modifier loop matches that lab setup.
- **Verification loop** — Models how robust a marking is under iterative disruption and re-detection (research framing: red-team informs blue-team).
- **Simplicity** — One detector family, one disruption backend per run. Easier to reproduce and log for papers or tooling benchmarks.
- **No dependency on slow detectors** — Steganography, chunk analysis, and advanced waste are skipped when the experiment only targets visible overlays.

**Why it underperformed on the crocs/office runs:**

- **Over-detection** — The visible detector returned 9020 regions on a complex scene. Thresholds (edge density, texture variance, aspect ratio, etc.) are tuned in code and are not conservative for busy images; many non-watermark regions get boxes.
- **All regions treated equally** — No filtering by confidence, size, or type. So removal runs on thousands of boxes (or on a subset that’s still too large), which is slow and can degrade the image.
- **LaMa not installed** — Fallback to OpenCV inpainting is weaker for texture; verification then often never passes (e.g. score stuck at 0.10).
- **No “quick path” for known watermarks** — If the user knows the mark is in a corner (e.g. sparkle), `remove-region` is a better fit, but the default skill runs agentic.

So the strategy is **visible-centric with verify/retry**, which is good for “remove visible watermarks and make sure we got them,” but it is **not** adapted to: (a) complex images with many false positives, (b) images that also have LSB/stego/patterns, or (c) known corner watermarks.

---

## Other strategies we have (from `stega/`)


| Strategy | What it does | Best for |
|----------|----------------|----------|
| **clean** | Full `run_detection()` (chunks, stego, visible, advanced waste, patterns) → `build_cleaning_plan()` → visible removal (gradient_guided) + sanitizer methods (lsb_natural, selective_clean, etc.) + aggressive_lsb_cleaning | Images that may have **multiple** marking types (visible + LSB + patterns). |
| **ralph** | No region detection; fixed **corner** remove-region with a strategy list (texture_synthesis → gradient_guided → lama), verify with visible detector, advance strategy or frac on failure | **Known corner watermarks** (e.g. bottom-right emblem); avoids over-detection. |
| **remove-region** | One manual region (corner or `--box`) → visible remover | **Known** watermark location (e.g. “always bottom-right”). |
| **detect** | Full detection only; no cleaning | Audit / reporting. |
| **full-test** | Batch full detection on a directory → JSON report | Batch audit. |

The **research-resilience** skill under `.agents/skills/` defaults to **agentic** for iterative detect → modify → verify runs on **synthetic or owned** imagery.

---

## Better strategies (high level)

1. **Route by intent / image type**
   - **“Remove the logo/watermark”** + **known corner** → use **ralph** or **remove-region** (avoid visible detector entirely for region discovery).
   - **“Remove visible watermarks”** + **unknown regions** → use **agentic** but only after making detection less aggressive (see below).
   - **“Clean the image fully”** (visible + LSB + patterns) → use **clean** (full detection + cleaning plan).

2. **Make visible detection less aggressive**
   - Add **confidence/size filters** before removal: e.g. only keep regions with confidence above a threshold and/or area within a range (to drop tiny noise and huge false positives).
   - Add **max_regions** (or similar): cap how many regions we pass to the remover; e.g. take top‑N by confidence or merge/sample.
   - Expose **tunable thresholds** (or presets: “conservative” / “aggressive”) so the pipeline can be strict on complex images.

3. **Combine pipelines instead of one-size-fits-all**
   - **Option A:** Run **detect** first (quick or full); if only visible watermarks and few regions → **agentic**; if corner-only or user says “corner” → **ralph** or **remove-region**; if multiple finding types → **clean**.
   - **Option B:** **clean** as the main path (full detection + cleaning plan), then add an **agentic-style verify/retry** only for visible watermarks at the end (as in DEMO_PLAN).

4. **Use the right removal method**
   - Install **LaMa** (`requirements-lama.txt`) when texture quality matters.
   - For corner watermarks, **ralph** already prefers **texture_synthesis** then **gradient_guided** then **lama**; agentic could similarly try **texture_synthesis** or **gradient_guided** before falling back to OpenCV when LaMa isn’t available.

5. **Audit and tuning**
   - Use **--log** (agentic) or equivalent so each run is auditable.
   - Use **--quick** when only visible removal is needed (skip stego/chunk/advanced waste in `clean`/detect).

---

## More effective pipeline (orchestrator plan)

Goal: **one orchestrated pipeline** that chooses strategy and parameters from context, reusing existing tools under `stega/` and the agent skill entry points.

### Phase 1: Lightweight classification (no new detectors)

- **Input:** image path, optional hints (e.g. “corner”, “full clean”, “visible only”).
- **Steps:**
  1. If user hint is “corner” or “remove emblem” → go to **Corner path**.
  2. Else run **visible-only** detect once; get `total_detections` and, if available, max confidence and maybe region count above a high-confidence threshold.
  3. **Branch:**
     - **Corner path:** Run **ralph** (or **remove-region** with default frac) → verify with visible detector; if not clean, advance strategy or frac (already in ralph). **No** full visible region detection for removal.
     - **Few visible regions** (e.g. total_detections in 1–50 and max_confidence > 0.5): Run **agentic** with current logic but **filter regions** (e.g. confidence ≥ 0.4, cap at 30 regions) before first removal. Optionally **--method lama** if available.
     - **Many visible regions** (e.g. >100 or 9020): **Do not** run agentic on all; either (i) run **remove-region** for a default corner only (assume “sparkle in corner”), or (ii) run **agentic** only after **filtering** (e.g. top 20 by confidence, or regions with area in [100, 50000] pixels). Log “filtered N regions to M” for audit.
     - **“Full clean”** or user asked for “everything”: Run **clean** (full detection + cleaning plan); optionally add a final **agentic-style** visible verify/retry with filtered regions only.

### Phase 2: Add filtering in code (minimal change)

- In **agentic** (or in a shared “prepare visible detections” helper): after `tool_detect()`, apply:
  - **confidence threshold** (e.g. keep only detections with confidence ≥ 0.4 or 0.5).
  - **area filter** (e.g. discard regions with area &lt; 100 or &gt; 10% of image).
  - **cap** (e.g. keep at most 30 or 50 regions, by confidence).
- Pass the filtered list to `tool_remove()` instead of the raw list. Log original vs filtered counts when quiet=False or when --log is set.

### Phase 3: Optional “demo” / unified entry (from DEMO_PLAN)

- Add **`python -m stega.cli demo <image> [-o output] [--live]`** that runs the **full** pipeline (same as **clean**: run_detection → build_cleaning_plan → clean_image) with optional agentic-style verify/retry at the end, and optional live overlay (Scan → Reveal → Plan → Clean → Verify → Done). This gives a single entry point that showcases all detection types and cleaning steps; the orchestrator can call **demo** when the goal is “show everything” or “full clean.”

### Phase 4: Skill/command behavior

- **research-resilience** skill can be updated so that:
  - By default it runs the **orchestrator** (Phase 1) instead of raw agentic.
  - Or it accepts a **mode** (e.g. “agentic” | “ralph” | “clean” | “auto”): “auto” = orchestrator; others = current behavior.
- **Agent-facing docs** under `.agents/skills/` describe how assistants invoke the CLI; keep them aligned with `stk` / `python -m stega.cli`.

### What we reuse (no new tools)

- All detectors and cleaners in **stega/** (visible, LSB, sanitizer, remove_region, etc.).
- Existing CLI: **agentic**, **ralph**, **remove-region**, **clean**, **detect**.
- Config and paths from **stega.config**.
- **--log**, **--quick**, **--method**, **clean_threshold** as they are; add **--max-regions** and/or **--confidence-min** on agentic or on the orchestrator.

### Summary

- **Current strategy:** Visible-only agentic (detect → remove → verify → retry) by default; simple but over-detects on complex images and has no path for “corner only” or “full clean.”
- **Better strategies:** Route by hint or by a quick visible-only check (corner → ralph/remove-region; few regions → agentic with filtering; many regions → filter or corner-only; full clean → clean + optional verify). Add region filtering (confidence, size, cap) before removal so we never pass 9020 regions to the remover.
- **More effective pipeline:** Orchestrator (Phase 1) + filtering in agentic (Phase 2) + optional demo (Phase 3) + skill/command (Phase 4), reusing existing `stega/` modules only.
