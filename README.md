# Steganalysis Toolkit

**Steganalysis Toolkit** is a research codebase for studying how fragile or resilient hidden-information schemes are across **text and images** — which disruption or sanitization attempts still leave detectable traces, and which wash out under verification. The goal is defensive: **red-team informs blue-team** so watermark and steganography designers can harden realistic threat models.

**This project is not intended for defeating C2PA, SynthID, or any production content-provenance attribution.** Experiments here are meant to run against **synthetic test inputs** or **media you own and may modify**. Use this code to study attack/defense dynamics and detector behavior — not to strip provenance from media you did not create.

## Engineering contribution

The most reusable artifact is the **agentic loop**: **detect → modify → verify → retry**, with structured logging and optional live previews. The steganalysis substrate (PNG chunks, LSB statistics, frequency-domain cues, Unicode anomalies, visible-overlay detectors, etc.) is the domain the loop was developed against; you can reuse the orchestration pattern for other forensic pipelines.

## Features (high level)

- **Multi-medium signals** — Text and image paths share a CLI and reporting mindset; image stack emphasizes PNG structure, metadata, and statistical detectors.
- **Detection** — Chunk analysis, Unicode scanning, LSB / steganography statistics, visible-overlay heuristics, pattern / “advanced waste” style cues.
- **Resilience experiments** — Cleaning and inpainting backends to stress-test whether markers survive iterative disruption (always in an authorized research context).
- **Visualization** — Optional dashboards and visualization helpers for comparing rounds of detection.

Primary CLI (after install): **`stk`**. From a checkout you can also run `python -m stega.cli`.

## Quick start

```bash
git clone https://github.com/hhalperin/steganalysis-toolkit.git
cd steganalysis-toolkit
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate      # macOS / Linux
pip install -e .
pip install -e ".[dev]"          # optional: pytest, black, mypy
pytest
```

Run examples (creates sample PNGs in the cwd):

```bash
python -m stega.examples
```

Analyze a PNG:

```bash
python stega/core/png_analyzer.py path/to/image.png
stk detect path/to/image.png
stk full-test path/to/image_dir   # batch JSON report
```

Optional stronger inpainting (LaMa): see `requirements-lama.txt`.

## What this is useful for

- **Defensive watermark design** — Empirically seeing which perturbations remove or preserve detector-visible signals.
- **Academic / lab steganalysis** — Reproducible scripts for coursework or publications (cite this repo; follow your institution’s ethics policies).
- **Learning the protect-vs-clean arms race** — Hands-on loops that show why naive marking fails and why verification matters.

## Repository layout

```
steganalysis-toolkit/
├── stega/                 # Python package (detection, cleaning, CLI, visualization)
├── tests/                 # pytest suite
├── docs/                  # Guides, ADRs, pipeline notes
├── assets/                # README only in git; local datasets stay ignored
├── .agents/skills/        # Agent skill stubs for research workflows
├── .github/               # Contributing, security, issue templates
├── pyproject.toml         # Package metadata + stk entry point
├── requirements.txt       # Mirror of runtime pins (optional alongside pip install -e .)
└── README.md
```

## Legal / ethics

MIT License — see [LICENSE](LICENSE). You are responsible for lawful, authorized use. Authors assume no liability for misuse.

## References

- PNG: [https://www.w3.org/TR/PNG/](https://www.w3.org/TR/PNG/)
- Unicode: [https://unicode.org/standard/standard.html](https://unicode.org/standard/standard.html)
