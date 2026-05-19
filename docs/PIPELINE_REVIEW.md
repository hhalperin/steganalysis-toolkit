# Pipeline run review (example)

Template for reviewing an **agentic** clean run on a complex benchmark image. Replace placeholders with your own asset names and log paths.

## Summary

| Image | Exit | Output | Notes |
|-------|------|--------|--------|
| `benchmark_scene.jpg` | 1 (not clean) | `assets/processing/benchmark_scene_agentic_cleaned.png` | Completed; verification never passed |
| `benchmark_scene_alt.png` | — | — | Long-running or hung; no completion log captured |

## benchmark_scene.jpg

- **Detection:** High region count reported — likely over-detection on a busy scene (many edges, text, and logos).
- **Removal:** LaMa was not installed; pipeline fell back to OpenCV inpainting (`UserWarning: LaMa not available ... Falling back to OpenCV inpainting`).
- **Verification:** After each retry, verification score may stay low. Max retries reached; output file can still be written with `success=False`.
- **Result:** Pipeline ran to completion but did not achieve “clean” (exit code 1). Inspect output under your configured `assets/` paths.

## benchmark_scene_alt.png

- Capture logs with `--log` for audit. If only numpy overflow warnings appear, the run may still be in progress or was stopped early.

## Recommendations

1. **Install LaMa for better inpainting:** `pip install -r requirements-lama.txt` (or use a dedicated env; see AGENTS.md).
2. **Tune detection for complex images:** Very high region counts suggest thresholds or merging may need tuning.
3. **Use `--log` for audit:** e.g. `python -m stega.cli agentic <image> --log pipeline.log` for JSONL records.
4. **Optional quick run:** `--quick` skips slow detectors when you only need visible watermark removal.

## Warnings observed

- **numpy overflow in reduce:** During detection. Often benign; consider float64 or clamping if results are affected.
- **LaMa not available:** Install optional `requirements-lama.txt` for texture-aware inpainting.
