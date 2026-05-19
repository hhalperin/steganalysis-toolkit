---
name: research-resilience
description: Run the steganalysis toolkit’s iterative detect→modify→verify harness on synthetic or user-owned images for watermark-resilience research. Use when the user asks to run a resilience experiment, benchmark the agentic pipeline, or study visible-overlay removal with verification — not for stripping third-party attribution.
---

# Research resilience harness

## When to use

Apply when the user wants to:

- Run the **agentic** pipeline (detect → modify → verify → retry) on **their own** images or **synthetic** fixtures
- Study how marking survives iterative disruption and re-detection (“red-team informs blue-team”)
- Log JSONL runs for a paper, portfolio demo, or internal benchmark

Do **not** present this as a way to defeat production content credentials (C2PA, SynthID, vendor watermarks on media the user did not create).

## Critical: you run the commands

Execute the CLI yourself from the **project root** via the Shell tool. Do not ask the user to copy-paste commands unless they prefer to.

## Steps

1. Resolve an image path relative to the repo (for example `tests/fixtures/...` or `assets/dirty/<dataset>/...`).
2. Run:

   **Installed CLI**

   ```powershell
   Set-Location "<workspace_root>"; stk agentic <image_path>
   ```

   **Editable checkout**

   ```powershell
   Set-Location "<workspace_root>"; python -m stega.cli agentic <image_path>
   ```

3. Optional flags: `-o path.png`, `--method lama`, `--log pipeline.log`, `--quiet`.

4. Summarize detector findings, whether verification passed, and where artifacts were written.

## Scope reminder

Use only on media you are authorized to modify. This repository is for **research** on resilience of hidden-information schemes, not for circumventing production provenance.
