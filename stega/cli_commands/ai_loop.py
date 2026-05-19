"""
AI Detection Loop: state and next-step logic.
See docs/AI_DETECTION_LOOP.md for the full workflow and prompts.
Loop is capped at max_rounds (default 10). Logs to loop.log (JSONL) and terminal (clean key=value lines for agent context).
"""

import json
import logging
import shutil
from pathlib import Path
from datetime import datetime, timezone

from ..config import processing_path

AI_LOOP_DIR = processing_path("ai-loop")
FINDINGS = "findings.json"
PLAN = "plan.json"
REVIEW = "review.json"
FEEDBACK = "feedback.json"
IMPROVED_PLAN = "improved_plan.json"
CURRENT_IMAGE = "current.png"
EDIT_SPEC = "edit_spec.md"
LOOP_STATE = "loop_state.json"
LOG_FILE = "loop.log"

DEFAULT_MAX_ROUNDS = 10

_LOGGER: logging.Logger | None = None


def _logger() -> logging.Logger:
    """Lazy-init logger: stream only (file is written in log_loop as JSONL)."""
    global _LOGGER
    if _LOGGER is not None:
        return _LOGGER
    log = logging.getLogger("stega.cli_commands.ai_loop")
    log.setLevel(logging.INFO)
    log.propagate = False
    sh = logging.StreamHandler()
    sh.setFormatter(logging.Formatter("%(message)s"))
    log.addHandler(sh)
    _LOGGER = log
    return log


def ensure_ai_loop_dir() -> Path:
    AI_LOOP_DIR.mkdir(parents=True, exist_ok=True)
    return AI_LOOP_DIR


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _short_val(k: str, v: str | int | bool) -> str:
    """Shorten value for terminal (e.g. path -> basename)."""
    if k == "image_path" and isinstance(v, str):
        return Path(v).name
    return str(v)


def log_loop(
    phase: str,
    message: str,
    round_num: int | None = None,
    **extra: str | int | bool,
) -> None:
    """Write JSONL to loop.log and a clean key=value line to terminal (cohesive system record for agents)."""
    ensure_ai_loop_dir()
    entry = {
        "ts": _now_iso(),
        "phase": phase,
        "message": message,
        **extra,
    }
    if round_num is not None:
        entry["round"] = round_num
    with open(AI_LOOP_DIR / LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
    out = {k: v for k, v in entry.items() if k not in ("ts", "message") and v is not None}
    first = [f"{k}={_short_val(k, out[k])}" for k in ("round", "phase") if k in out]
    rest = [f"{k}={_short_val(k, v)}" for k, v in sorted(out.items()) if k not in ("round", "phase")]
    line = "ai-loop " + " ".join(first + rest)
    _logger().info(line)


def _read_loop_state() -> dict:
    s = _read_json(LOOP_STATE)
    if not s:
        return {"round": 1, "max_rounds": DEFAULT_MAX_ROUNDS, "completed": False, "updated_at": _now_iso()}
    return s


def _write_loop_state(state: dict) -> None:
    state["updated_at"] = _now_iso()
    with open(AI_LOOP_DIR / LOOP_STATE, "w") as f:
        json.dump(state, f, indent=2)


def get_loop_state() -> dict:
    """Return current loop state (round, max_rounds, completed). Use when writing findings to get current round."""
    ensure_ai_loop_dir()
    return _read_loop_state()


def _read_json(name: str) -> dict | None:
    p = AI_LOOP_DIR / name
    if not p.exists():
        return None
    try:
        with open(p) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def cmd_ai_loop_init(image_path: Path) -> int:
    """Initialize the AI-loop state: copy image to current.png and print Identifier prompt."""
    if not image_path.exists():
        print(f"Not found: {image_path}")
        return 1
    ensure_ai_loop_dir()
    dest = AI_LOOP_DIR / CURRENT_IMAGE
    shutil.copy(image_path, dest)
    state = {"round": 1, "max_rounds": DEFAULT_MAX_ROUNDS, "completed": False}
    _write_loop_state(state)
    log_loop("init", "image copied to current.png", round_num=1, image_path=str(image_path), max_rounds=DEFAULT_MAX_ROUNDS)
    print(f"Image copied to {dest}")
    print("\n--- Run the Identifier (Agent 1) with this image. ---")
    print("Prompt: See docs/AI_DETECTION_LOOP.md section '1. Identifier (Agent 1)'.")
    print(f"Save the JSON output to: {AI_LOOP_DIR / FINDINGS}")
    return 0


def cmd_ai_loop_next() -> int:
    """Print which phase is next and what to do (or generate the next prompt content)."""
    ensure_ai_loop_dir()
    state = _read_loop_state()
    round_num = state.get("round", 1)
    max_rounds = state.get("max_rounds", DEFAULT_MAX_ROUNDS)
    completed = state.get("completed", False)

    if completed:
        log_loop("next", "loop already completed (max rounds reached)", round_num=round_num)
        print(f"Loop finished (max rounds={max_rounds} reached). No further rounds.")
        return 0

    findings = _read_json(FINDINGS)
    plan = _read_json(PLAN)
    review = _read_json(REVIEW)
    feedback = _read_json(FEEDBACK)
    improved = _read_json(IMPROVED_PLAN)

    if not findings and not plan:
        log_loop("next", "no state yet; init required")
        print("No findings.json yet. Run: python -m stega.cli ai-loop init <image>")
        return 1
    if not findings:
        log_loop("next", "missing findings.json", round_num=round_num)
        print("Missing findings.json. Run the Identifier first (see docs/AI_DETECTION_LOOP.md).")
        return 1

    n = len(findings.get("findings", []))
    if n == 0:
        log_loop("next", "findings empty; loop can stop", round_num=round_num, findings_count=0)
        print(f"No AI tells found (findings empty). Loop can stop. Round {round_num}/{max_rounds}.")
        return 0

    if not plan:
        log_loop("next", "phase=planner", round_num=round_num, next_phase="planner", findings_count=n)
        print(f"Round {round_num}/{max_rounds}. Next: Planner (Agent 2). Input: findings.json.")
        print(f"  Paste contents of {AI_LOOP_DIR / FINDINGS} into the Planner prompt.")
        print(f"  Save output to: {AI_LOOP_DIR / PLAN}")
        return 0
    if not review:
        log_loop("next", "phase=reviewer", round_num=round_num, next_phase="reviewer")
        print(f"Round {round_num}/{max_rounds}. Next: Reviewer (Agent 3). Input: plan.json.")
        print(f"  Paste contents of {AI_LOOP_DIR / PLAN} into the Reviewer prompt.")
        print(f"  Save output to: {AI_LOOP_DIR / REVIEW}")
        return 0
    if not feedback:
        log_loop("next", "phase=identifier_feedback", round_num=round_num, next_phase="identifier_feedback")
        print(f"Round {round_num}/{max_rounds}. Next: Identifier feedback (Agent 1). Input: findings.json + review.json questions.")
        print(f"  Paste findings and questions into the Identifier feedback prompt.")
        print(f"  Save output to: {AI_LOOP_DIR / FEEDBACK}")
        return 0
    if not improved:
        log_loop("next", "phase=planner_improve", round_num=round_num, next_phase="planner_improve")
        print(f"Round {round_num}/{max_rounds}. Next: Planner improve (Agent 2). Input: plan.json + feedback.json.")
        print(f"  Paste plan and feedback into the Planner improve prompt.")
        print(f"  Save output to: {AI_LOOP_DIR / IMPROVED_PLAN}")
        return 0

    next_round = round_num + 1
    log_loop("next", "phase=implement", round_num=round_num, next_phase="implement", next_round=next_round)
    print(f"Round {round_num}/{max_rounds}. Next: Implement. Use improved_plan.json to edit the image.")
    print("  Run: python -m stega.cli ai-loop implement")
    if next_round > max_rounds:
        print(f"  After this implement, max rounds ({max_rounds}) will be reached; loop will stop.")
    else:
        print(f"  Then save the edited image as current.png and run Identifier again (round {next_round}).")
    return 0


def cmd_ai_loop_implement() -> int:
    """Generate edit_spec.md from improved_plan.json; increment round and enforce max_rounds."""
    ensure_ai_loop_dir()
    state = _read_loop_state()
    round_num = state.get("round", 1)
    max_rounds = state.get("max_rounds", DEFAULT_MAX_ROUNDS)

    improved = _read_json(IMPROVED_PLAN)
    if not improved:
        log_loop("implement", "skipped: no improved_plan.json", round_num=round_num)
        print("No improved_plan.json. Run Planner improve step first.")
        return 1
    plan_list = improved.get("plan", [])
    if not plan_list:
        log_loop("implement", "skipped: empty plan", round_num=round_num)
        print("improved_plan.json has empty plan.")
        return 1

    lines = [
        "# Edit spec (from improved_plan.json)",
        "",
        f"Round {round_num} of {max_rounds}. Apply these changes to the current image, then save as current.png for the next round.",
        "",
    ]
    for i, item in enumerate(plan_list, 1):
        fid = item.get("finding_id", "")
        change = item.get("change", "")
        method = item.get("method", "")
        priority = item.get("priority", "")
        note = item.get("note", "")
        lines.append(f"## {i}. Finding {fid} (priority: {priority})")
        lines.append(f"- **Change:** {change}")
        lines.append(f"- **Method:** {method}")
        if note:
            lines.append(f"- **Note:** {note}")
        lines.append("")

    spec_path = AI_LOOP_DIR / EDIT_SPEC
    spec_path.write_text("\n".join(lines), encoding="utf-8")

    next_round = round_num + 1
    state["round"] = next_round
    if next_round > max_rounds:
        state["completed"] = True
        _write_loop_state(state)
        log_loop(
            "implement",
            "edit_spec written; max_rounds reached, loop stopping",
            round_num=round_num,
            next_round=next_round,
            max_rounds=max_rounds,
            plan_items=len(plan_list),
        )
        log_loop("stopped", "loop completed (max_rounds reached)", round_num=round_num, max_rounds=max_rounds)
        print(f"Round {round_num} complete. Max rounds ({max_rounds}) reached. Loop will not continue.")
        print("Edit the image per the spec and save as current.png if you want to keep the last edits.")
        return 0

    _write_loop_state(state)
    log_loop(
        "implement",
        "edit_spec written; next round will be " + str(next_round),
        round_num=round_num,
        next_round=next_round,
        plan_items=len(plan_list),
    )
    print(f"Round {round_num} complete. Next round: {next_round} / {max_rounds}.")
    print("Edit the image per the spec, save as current.png, then run Identifier again.")
    return 0


def write_findings(findings_obj: dict, round_num: int | None = None) -> None:
    """Write findings JSON (e.g. from the Identifier agent). Uses current round from loop_state if round_num omitted."""
    ensure_ai_loop_dir()
    if round_num is None:
        state = get_loop_state()
        round_num = state.get("round", 1)
    path = AI_LOOP_DIR / FINDINGS
    findings_obj["round"] = findings_obj.get("round", round_num)
    findings_obj.setdefault("image_path", str(AI_LOOP_DIR / CURRENT_IMAGE))
    with open(path, "w") as f:
        json.dump(findings_obj, f, indent=2)
    n = len(findings_obj.get("findings", []))
    log_loop("identifier", "findings written", round_num=round_num, findings_count=n)
