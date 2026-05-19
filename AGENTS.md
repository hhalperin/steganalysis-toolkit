# Agent guide — Steganalysis Toolkit

Unified CLI: **`stk`** (console script) or **`python -m stega.cli`**. Run from the **repository root** so paths like `assets/...` resolve.

## Scope and ethics

Use this project only for **research** on hidden-information schemes on **synthetic fixtures** or **media you own**. It is **not** for defeating C2PA, SynthID, or third-party attribution on others’ content. See the top of [README.md](README.md).

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate      # macOS/Linux
pip install -e .
pip install -e ".[dev]"         # pytest / tooling
pip install -r requirements-lama.txt   # optional inpainting
```

## Commands (summary)

| Command | Purpose |
|--------|---------|
| `stk detect <image>` | Run detectors only |
| `stk clean <image>` | Detect → apply disruption/sanitization plan |
| `stk agentic <image>` | Detect → modify overlays → verify → retry |
| `stk ralph <image>` | Corner-region iteration until verification passes |
| `stk remove-region <image>` | Fixed bbox / corner inpainting for controlled fixtures |
| `stk full-test [dir]` | Batch detection → JSON (default dir: `assets/clean/sample-emblem` if present) |
| `stk ai-loop …` | Structured harness documented in [docs/AI_DETECTION_LOOP.md](docs/AI_DETECTION_LOOP.md) |

Add `-o`, `--quick`, `--json`, `--log`, `--live` as documented in `stk --help`.

## Typical workflows

```bash
stk detect assets/dirty/example.png
stk clean assets/dirty/example.png -o assets/clean/example_cleaned.png
stk agentic assets/dirty/example.png -o assets/clean/example_agentic.png --log pipeline.log
stk remove-region assets/clean/example_cleaned.png -o assets/clean/example_final.png --method lama
stk full-test assets/clean -o assets/reports/verification.json
```

Paths under `assets/` are conventional; large binary datasets remain gitignored — populate locally or use `tests/fixtures/`.

## Agent skills

Canonical definitions live under **`.agents/skills/`**:

| Skill | Path | Intent |
|-------|------|--------|
| research-resilience | `.agents/skills/research-resilience/` | Run the agentic detect→modify→verify harness responsibly |
| ai-detection-loop | `.agents/skills/ai-detection-loop/` | Drive the multi-phase ai-loop workflow |

If you use Claude Code locally, sync skills into a **local** `.claude/skills/` tree (gitignored here):

```bash
python scripts/sync_agent_skills.py
```

## Headless Cursor agent scripts

Optional wrappers in `stega/tools/cursor_agent_clean.ps1` / `.sh` require Cursor Pro and the `agent` CLI; they are **not** required for core library use.

## Further reading

- [docs/PIPELINE_STRATEGY.md](docs/PIPELINE_STRATEGY.md) — When to use agentic vs full clean vs corner loops  
- [docs/AI_DETECTION_LOOP.md](docs/AI_DETECTION_LOOP.md) — ai-loop phases  
- [docs/extraction_guidelines.md](docs/extraction_guidelines.md) — forensic extraction patterns  
