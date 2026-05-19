# Prompt-Build Orchestration: Multi-Agent Architecture

Goal: build the best possible image-generation prompt by using **specialist agents** (each focused on one detail), **review agents** (track how descriptions change), and an **orchestrator** that knows when and how to ask specialists to deepen their analysis. No single agent holds the whole image in mind—each contributes a layer; the orchestrator composes and refines.

---

## 1. Roles

| Role | Responsibility | Input | Output |
|------|----------------|--------|--------|
| **Specialist agents** | One focus each: background, ears, neck, realism, eyes, teeth, smile, posture, lighting, hands, fabric, style (e.g. stencil/realism/cartoon), etc. | Current image (or iteration), optional prior analysis, optional orchestrator question | Full written analysis of their dimension only; can use sub-agents for sub-topics |
| **Review agents** | Read specialist outputs; compare across iterations; summarize what changed and whether the description improved or regressed | Set of specialist analyses (current vs previous), iteration index | Change summary, gaps, conflicts, suggestions for orchestrator |
| **Orchestrator** | Decide when/how/why to ask specialists to go deeper; trigger reviews; compose final prompt; respect project vs generic agent set | Registry (which agents exist), iteration state, review summaries | Questions to specialists, final composed prompt, decision to iterate or ship |
| **Image-creator agent** | Consume the final prompt and call the image generator | Final prompt | Image (and optionally re-run loop if quality check fails) |

---

## 2. Specialist agents (focused on one detail)

Each specialist has:

- **Focus** — e.g. `background`, `ears`, `neck`, `realism`, `eyes`, `teeth`, `smile`, `posture`, `lighting`, `hands`, `fabric`, `style`.
- **Instruction** — Analyze the reference image (or current generated image) **only** for that dimension. Output a full, detailed breakdown: shapes, colors, relationships, mood, technical terms (e.g. rim light, occlusal plane). If the task is “build a prompt to recreate this,” write the slice of the prompt that would describe their dimension so an image model could reproduce it.
- **Optional sub-agents** — A specialist can internally break its topic into sub-topics (e.g. “eyes” → lids, iris, catchlights, gaze direction) and delegate to sub-agents, then synthesize. The orchestrator doesn’t need to know; the specialist’s output is the contract.

**Per iteration:** Each specialist receives (1) the current image, (2) their own prior analysis for that dimension (if any), (3) an optional **orchestrator question** (e.g. “Focus on how the teeth interact with the smile and lips; be explicit about occlusion and shadows”). They output an updated analysis. That output is **appended or versioned** so review agents can see how the description changed.

---

## 3. Review agents

- **Input:** All specialists’ analyses for iteration N and (optionally) N−1.
- **Job:** (a) Summarize what changed per dimension. (b) Identify gaps (e.g. “lighting mentioned but no shadow direction”). (c) Identify conflicts (e.g. “posture says relaxed, smile says tense”). (d) Suggest what the orchestrator should ask next (e.g. “Ask eyes and smile to align on gaze and mouth symmetry”).
- **Output:** Structured: `changes`, `gaps`, `conflicts`, `suggestions`. Optional: simple “improved / regressed / neutral” per dimension so the orchestrator can decide to re-ask or ship.

---

## 4. Orchestrator

- **Registry-aware:** Reads a **project agent registry** (or plan file) that lists which specialists and reviewers exist for this project vs generic (see below).
- **Loop:** For each iteration:
  1. Invoke all specialists (with current image + prior analysis + optional question).
  2. Invoke review agents with current and previous analyses.
  3. Read review output (changes, gaps, conflicts, suggestions).
  4. Decide: (a) **Ship** — compose final prompt from specialist outputs and send to image-creator; or (b) **Iterate** — choose which specialists to re-ask and with what question (e.g. “Critically walk through how you broke down the lighting into key, fill, and rim; then add one sentence for shadow falloff”).
- **Composition:** Final prompt = ordered merge of each specialist’s prompt slice (e.g. background first, then figure, then face, then micro-details), with light editing only to fix grammar or remove redundancy.
- **Orchestrator prompt design:** The orchestrator’s system prompt should say: “You know when, how, and why to ask questions that require each specialist to critically think through their reasoning and how they broke down their topic (including any sub-agents they used) so that their slice is comprehensive and prompt-ready.”

---

## 5. Agent registry / plan file (project vs generic)

A single **registry** (e.g. YAML or JSON) defines which agents exist and whether they are **project-specific** or **generic**.

- **Generic agents** — Reusable across projects: e.g. `background`, `lighting`, `realism`, `eyes`, `posture`, `hands`, `fabric`. These are “always available” for any image-prompt project.
- **Project-specific agents** — Tied to a project’s goal: e.g. `stencil_style`, `cartoon_linework`, `teeth` (for a portrait project), `neck_and_collar` (for a formal photo project). The plan file for **this** project lists which of these to include; removing an agent is “remove from project list,” not delete from registry.

**Concrete layout (this repo):**

- **Registry:** `assets/processing/prompt-build/agent_registry.json` — `generic` and `project_specific` arrays; each agent has `id`, `focus`, `description`, `prompt_hint`.
- **Project plan:** `assets/processing/prompt-build/projects/<project_id>/plan.json` — `project_id`, `description`, `generic_agents`, `project_agents`, `max_iterations`, `image_ref_path`.

**Loader:** `stega.prompt_build.registry` — `load_registry()`, `load_project_plan(project_id)`, `resolve_agents_for_project(project_id)` returns the ordered list of agent configs for that project.

Adding/removing an agent for a project = edit the project’s `plan.json` (`generic_agents` / `project_agents`). Adding a new agent type = add to `agent_registry.json` (generic or project_specific).

---

## 6. Iteration and change tracking

- **State per iteration:** For iteration N, store: (1) image path (reference or generated), (2) each specialist’s output (e.g. `analyses/round_N/specialist_<focus>.md`), (3) review output (`reviews/round_N/review.json`), (4) orchestrator decision (e.g. `questions_round_N.json` or “compose”).
- **Review agents need diff:** Either (a) pass previous and current analysis text to the review agent, or (b) produce a short `changelog` per specialist (e.g. “Added shadow direction; removed vague ‘nice lighting’”) so the review agent can summarize “how the description has changed” without re-reading huge blobs.
- **Cap iterations:** e.g. `max_iterations: 5` in the project plan so the loop doesn’t run forever.

---

## 7. Optional: image-creator in the loop

- After the orchestrator composes the final prompt, an **image-creator agent** calls the image generator (e.g. GenerateImage or external API).
- Optionally, a **quality-check** step: run the same specialist/review stack on the **generated** image and compare to the reference (or to “realism” / “style” criteria). If something regressed, the orchestrator can run another round with a targeted question (e.g. “Eyes specialist: the generated image has X wrong; refine your slice to fix X”) and re-compose, then re-generate. That gives a closed loop: prompt → image → analyze → refine prompt → image again.

---

## 8. Summary

- **Specialists** = one detail each; full analysis per iteration; optional sub-agents; output = prompt slice for their dimension.
- **Reviewers** = compare iterations, report changes/gaps/conflicts, suggest next questions.
- **Orchestrator** = registry + project plan; invokes specialists and reviewers; asks targeted questions to deepen reasoning; composes final prompt; optionally drives image-creator and quality-check.
- **Registry** = generic agents (reusable) + project plan (which agents for this project; add/remove without touching generic set).
- **State** = analyses and reviews per round; changelog or diff for reviewers; iteration cap.

This keeps “remember every important detail” off a single agent and puts it in the combined output of specialists, with the orchestrator and reviewers ensuring consistency and depth.

---

## 9. More suggestions

- **Changelog per specialist:** Each specialist outputs a short "what I changed this round" (2-3 lines) in addition to the full analysis; review agents consume changelogs to report "how the description has changed" without re-reading long text.
- **Confidence or completeness:** Specialists can tag their slice with e.g. confidence: low | medium | high or "completeness" so the orchestrator prioritizes re-asking low-confidence dimensions.
- **Conflict resolution agent:** A dedicated agent that only looks at review "conflicts" and proposes one sentence that reconciles them (e.g. "Relaxed posture with an intent gaze"); orchestrator can inject that into the final prompt.
- **Prompt schema:** Final prompt has a fixed structure (e.g. [setting] [figure] [face] [style] [lighting]) so composition is deterministic and specialists know where their slice goes.
- **Round-robin deepening:** Orchestrator doesn't ask everyone every time; it asks the "weakest" N specialists (by review score or confidence) to go deeper, so the loop focuses compute where it matters.
- **Export for image model:** Final prompt is written to a file (e.g. prompts/round_N_final.txt) and optionally passed to the image-creator agent/script so the same pipeline can run headless or from a CLI.
