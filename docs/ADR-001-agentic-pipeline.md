# ADR-001: Agentic Watermark Removal Pipeline

## Status
Accepted

## Context
We need a pipeline that: (1) detects watermarks, (2) removes them with tools (LaMa or OpenCV inpainting), (3) verifies the image is "clean", (4) retries with different params if not clean, and (5) logs outcomes for threshold tuning.

## Decision
Implement a **custom loop** (Option B from the plan) rather than LangGraph or AutoGen. Rationale:
- Easiest to integrate with existing Python scripts (detector, remover, verifier)
- No new framework dependencies
- Explicit control flow; easy to add logging and later extend to LangGraph if needed

## Tool Interfaces

| Tool | Input | Output |
|------|-------|--------|
| **detect** | `image_path: str` | `{ total_detections: int, detections: [{ type, confidence, location: (x,y,w,h), ... }] }` |
| **remove** | `image_path: str`, `detection_results: dict`, `output_path: str`, `method: str` | `success: bool`, `cleaned_path: str` |
| **verify** | `image_path: str`, `clean_threshold: float` | `{ clean: bool, score: float, total_detections: int }` |

Verifier: re-run visible watermark detector on cleaned image. `clean` = total_detections == 0 or max confidence < threshold.

## Retry Strategy
- If verify returns not clean and retries < N: re-run remove with dilated mask (expand each bbox by 10%) or alternate method (lama -> inpainting).
- Max retries default: 3.

## Logging Format
JSONL, one record per image processed:
```json
{"timestamp": "ISO8601", "input_path": "...", "output_path": "...", "detection_count": N, "verification": {"clean": bool, "score": float}, "retries": N, "success": bool}
```

## Implementation
`python -m stega.cli agentic` - see `stega/cli_commands/agentic.py` for implementation.
