# Pipeline Run Review (crocs-at-office / office_crocs)

## Summary

| Image | Exit | Output | Notes |
|-------|------|--------|--------|
| `office_crocs.jpg` | 1 (not clean) | `assets/dirty/office_crocs_agentic_cleaned.png` | Completed; verification never passed |
| `crocs-at-office.png` | — | — | Long-running or hung; no completion log captured |

## office_crocs.jpg

- **Detection:** 9020 regions reported — likely over-detection on a complex scene (Oval Office, flags, seals, laptop, Crocs).
- **Removal:** LaMa was not installed; pipeline fell back to OpenCV inpainting (`UserWarning: LaMa not available ... Falling back to OpenCV inpainting`).
- **Verification:** After each of 4 attempts, verification score stayed at 0.10 (“Still traces”). Max retries reached; output file was still written.
- **Result:** Pipeline ran to completion but did not achieve “clean” (success=False, exit code 1). Output exists at `assets/dirty/office_crocs_agentic_cleaned.png`.

## crocs-at-office.png

- Only logs captured: numpy overflow warnings and LaMa fallback warning. No “Detecting watermarks” or later steps in the captured terminal output.
- Either still running (e.g. large image / many regions) or process was stopped/hung. No output file path in logs.

## Recommendations

1. **Install LaMa for better inpainting:** `pip install -r requirements-lama.txt` (or use a dedicated env; see AGENTS.md).
2. **Tune detection for complex images:** 9020 regions suggests detector thresholds or merging may need tuning to avoid treating normal scene elements as watermarks.
3. **Use `--log` for audit:** e.g. `python -m stega.cli agentic <image> --log pipeline.log` to get JSONL records of each run.
4. **Optional quick run:** `--quick` skips slow detectors; use when you only need visible watermark removal.

## Warnings observed

- **numpy overflow in reduce:** During detection (e.g. in mean/sum). Benign for current use; consider casting to float64 or clamping if it affects results.
- **LaMa not available:** Install optional `requirements-lama.txt` for better texture-aware inpainting.
