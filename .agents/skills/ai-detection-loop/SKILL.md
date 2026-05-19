---
name: ai-detection-loop
description: Run the structured ai-loop harness to study synthetic “AI-tell” markers and iterative edits on images you own or generated for research. Use when the user asks for the AI detection loop workflow documented in docs/AI_DETECTION_LOOP.md — not for disguising third-party generated media.
---

# AI Detection Loop

## When to use

Apply this skill when the user:
- Asks to identify what in an image makes it look AI-generated
- Wants to run the "AI detection loop" or "prompt hook" workflow
- Wants to study the experimental loop described in `docs/AI_DETECTION_LOOP.md` on **authorized** images

## Workflow (see docs/AI_DETECTION_LOOP.md)

1. **Identifier (Agent 1):** Look at the image and list every part that makes it look clearly AI-generated (region, what, why). Output structured findings (JSON).
2. **Planner (Agent 2):** From findings, plan what would make each part seem non-AI (change, method, priority).
3. **Reviewer (Agent 3):** From the plan, write questions for the Identifier: "Would [fix] help in [region]?"
4. **Identifier (feedback):** Answer each question (Yes/No/Partially + reason).
5. **Planner (improve):** Revise the plan using feedback.
6. **Implement:** Generate edit_spec.md from improved_plan; user (or tool) edits the image and saves as current.png.
7. **Rerun:** Run Identifier again on the new image. If findings are empty or acceptable, stop; else repeat from step 2.

## What you must do

1. **Resolve the image**
   - Use the image from the user's message or attachment. If they said "this image" with no path, use the most recently referenced or attached image.
   - Prefer paths relative to project root (e.g. `assets/clean/crocs-at-office_demo.png`).

2. **Initialize state (first time)**
   - Run from project root: `python -m stega.cli ai-loop init <image_path>` so the image is copied to `assets/processing/ai-loop/current.png`. Or create the directory and copy the image yourself.

3. **Run Identifier (Agent 1)**
   - Look at the image (current.png or the user-provided image). List every part that makes it look clearly AI-generated: for each give id, region, what, why.
   - Output a JSON object: `{"findings": [ {"id": "1", "region": "...", "what": "...", "why": "..."}, ... ], "image_path": "...", "round": 1}`.
   - Write this to `assets/processing/ai-loop/findings.json` (use the project's config: `processing_path("ai-loop")` or path `assets/processing/ai-loop/findings.json`).

4. **If the user wants the full loop in one session, continue as follows**
   - **Planner:** Read findings.json. For each finding, propose change, method, priority. Write to `assets/processing/ai-loop/plan.json`.
   - **Reviewer:** Read plan.json. For each plan item, write one question for the Identifier. Write to `assets/processing/ai-loop/review.json`.
   - **Identifier (feedback):** Read findings + review. Answer each question (Yes/No/Partially + reason). Write to `assets/processing/ai-loop/feedback.json`.
   - **Planner (improve):** Read plan + feedback. Produce improved plan. Write to `assets/processing/ai-loop/improved_plan.json`.
   - **Implement:** Run `python -m stega.cli ai-loop implement` to generate `edit_spec.md`. Tell the user to edit the image per the spec and save as `assets/processing/ai-loop/current.png`, then say "continue" or "rerun the loop" to run Identifier again.

5. **Rerun until working (max 10 rounds)**
   - The loop is capped at **10 rounds**. After 10 full cycles (Identifier → … → Implement), the loop stops (see `loop_state.json` and `loop.log`).
   - When the user has saved a new current.png and says to continue or rerun: run Identifier again on current.png; write findings.json (use round from `get_loop_state()` or `loop_state.json`). If findings are empty (or negligible), report "Loop complete; image no longer reads as clearly AI-generated." If round has reached max_rounds (10), report "Loop stopped (max rounds reached)." Otherwise run Planner → … → Implement again, then ask the user to edit and rerun.

6. **Logging**
   - After init, next, implement, or when writing findings, the CLI appends to `assets/processing/ai-loop/loop.log` (JSONL: ts, phase, round, message, etc.). Point the user to this file for observability.

## CLI helpers

- `python -m stega.cli ai-loop init <image>` — Copy image to ai-loop/current.png and print next step.
- `python -m stega.cli ai-loop next` — Print which phase is next and where to save output.
- `python -m stega.cli ai-loop implement` — Generate edit_spec.md from improved_plan.json.

All paths and prompts are in **docs/AI_DETECTION_LOOP.md**.
