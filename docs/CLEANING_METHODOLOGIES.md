# Additional Cleaning Methodologies & Review Tools

Summary of methods and tools beyond our current pipeline, for reviewing and improving watermark/artifact removal.

---

## Current Pipeline (This Project)

- **Detection:** Visible watermark detector (gradient/edge/texture/frequency), advanced waste (SIFT geometric, AI fingerprints, LSB patterns), sanitizer patterns (LSB bias, sequential encoding, channel correlation).
- **Removal:** LaMa (learning-based, texture-aware; optional, `pip install simple-lama-inpainting`), OpenCV inpainting (TELEA/NS), gradient-guided, texture synthesis, multi-scale blending; LSB cleaning; manual region removal via `python -m stega.cli remove-region` with `--method lama` for best texture reconstruction.

---

## Deep Learning & 2024 Methods

| Approach | Description | Use case |
|----------|-------------|----------|
| **Diffusion-based** | Image-to-image diffusion with semantic guidance (e.g. captions); NeurIPS 2024 invisible watermark challenge winner ~95.7% removal. | Invisible watermarks, high fidelity |
| **VAE evasion** | Test-time optimization + color-contrast restoration (CIELAB). | Invisible watermarks, quality preservation |
| **Micro-geometric (MarkCleaner)** | Mask-guided encoder + 2D Gaussian Splatting decoder; separates content from strict alignment. | Visible/invisible, avoids semantic drift |
| **View synthesis (RAVEN)** | Reformulates removal as novel-view synthesis; diffusion + geometric transforms; zero-shot, no detector. | Black-box invisible watermarks |
| **Clustering** | Cluster by spatial/frequency artifacts; per-cluster removal parameters. | Black-box, batch processing |

---

## Open-Source Tools to Review / Integrate

| Project | Focus | Notes |
|---------|--------|------|
| [deep-blind-watermark-removal](https://github.com/vinthony/deep-blind-watermark-removal) | Visible, blind removal | AAAI 2021; Stacked Attention ResUNets |
| [SLBR-Visible-Watermark-Removal](https://github.com/bcmi/SLBR-Visible-Watermark-Removal) | Visible removal | ACM MM 2021; localization + background refinement |
| [remove-watermarks](https://github.com/X-CCS/remove-watermarks) | Visible | “On the Effectiveness of Visible Watermarks” (MIT) |
| [watermark-removal](https://github.com/olivermen/watermark-removal) | General | Minimal docs |
| **untext** (Jurph) | Text + known watermarks | EAST/DocTR/EasyOCR + ORB for watermarks; LaMa/TELEA inpainting; CLI + web UI; Python 3.10+, GPU recommended |

---

## Review & Verification

1. **Re-run detection on cleaned output**
   `python scripts/full_detection_test.py assets/cleaned` (or single file) to check remaining findings.

2. **Manual region removal**
   For known emblem/logo in a corner:
   `python -m stega.cli remove-region <image> -o <output> [--method lama] [--frac-w 0.12] [--frac-h 0.10]`
   Use `--method lama` for texture-aware inpainting (requires `pip install simple-lama-inpainting`); falls back to OpenCV if unavailable. Or exact bbox: `--box x,y,w,h`.

3. **Quality metrics**
   PSNR/SSIM in `VisibleWatermarkRemover._calculate_removal_quality` (when SSIM available). Compare original vs cleaned in a region of interest.

4. **Visual inspection**
   Compare `office_crocs_cleaned.png` (LSB/pattern cleaning) vs `office_crocs_final.png` (after bottom-right emblem inpainting).

---

## Suggested Next Steps

- Run **full** detection (no `--quick`) on key assets periodically to catch visible + advanced waste.
- Add **SLBR** or **deep-blind-watermark-removal** as an optional path for visible watermarks when PyTorch/GPU is available.
- **LaMa** is now integrated: use `--method lama` in `remove_region.py` for texture-aware inpainting; install via `pip install -r requirements-lama.txt` (may have dependency conflicts; falls back to OpenCV if unavailable).
- **Agentic pipeline** (`python -m stega.cli agentic`): detect → remove → verify → retry if not clean. Use `--log` for JSONL logging. See [ADR-001-agentic-pipeline.md](ADR-001-agentic-pipeline.md).
- Suppress or fix **numpy overflow** warnings in detection (e.g. steganography or advanced waste analyzers) for cleaner logs.
