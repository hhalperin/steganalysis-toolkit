# Report Findings Guide

## Detection Report Structure

Reports are JSON files in `assets/reports/`:

- **sample_emblem_report.json** (example name): Before/after findings for a labeled synthetic dataset under `assets/clean/<dataset>/`
- **full_test_report.json**: Full detection test output (all modules) on a directory

## Finding Types

| Finding | Meaning | Recommended Action |
|---------|---------|--------------------|
| **geometric_watermarks** | SIFT keypoints show regular grid or high rotation persistence | Apply `geometric_transformation`; often false positive on logos |
| **channel_correlation** | RG/RB/GB correlation > 0.99 | Only suspicious if image has meaningful chroma; grayscale logos are normal |
| **lsb_bias** | LSB bits biased away from 0.5 | Apply `lsb_natural`, `selective_clean`, `aggressive_lsb_cleaning` |
| **sequential_encoding** | Near-white pixels use 251,252,253,254,255 in sequence | Apply `compression_cycle` |
| **white_pixel_encoding** | LSB bias in white pixels | Apply `selective_clean` |
| **pattern:channel_correlation** | Same as channel_correlation (sanitizer pattern) | See channel_correlation |

## Interpreting Before/After

- **Removed**: Findings present before cleaning but not after
- **Remaining**: Findings still present after cleaning; may be false positives or require stronger cleaning
- **Risk**: `low` (0 findings), `medium` (1–2), `high` (3–4), `critical` (5+)

## Configurable Parameters

- `GEOMETRIC_PERSISTENCE_THRESHOLD`: SIFT rotation persistence threshold (default 0.7)
- `GEOMETRIC_MIN_CONFIDENCE`: Minimum confidence to report geometric_watermarks (default 0.65)
- `GEOMETRIC_ANGLE_DEG`: Rotation angle for geometric_transformation (degrees)
