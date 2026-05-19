"""
Ralph Loop for watermark removal: iterate until verifyCompletion.

Ralph Loop pattern:
- State persisted to disk (survives restarts)
- Each iteration: read state, run one step, verify, write state
- Loop until clean or max iterations

Uses texture_synthesis (no blur) as primary; falls back to other methods.
"""

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

# Add project root
_project_root = Path(__file__).resolve().parents[2]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from stega.detection.visible_watermark_detector import detect_visible_watermarks
from stega.cli_commands.remove_region import run_remove_region


def verify_completion(image_path: str, clean_threshold: float = 0.3) -> tuple[bool, dict]:
    """Return (is_clean, verification_result)."""
    try:
        report = detect_visible_watermarks(image_path)
        total = report.get("total_detections", 0)
        max_conf = max((d.get("confidence", 0) for d in report.get("detections", [])), default=0.0)
        clean = total == 0 or max_conf < clean_threshold
        return clean, {
            "clean": clean,
            "score": 1.0 - max_conf if total > 0 else 1.0,
            "total_detections": total,
            "max_confidence": max_conf,
        }
    except Exception as e:
        return False, {"clean": False, "score": 0.0, "error": str(e)}


def load_state(state_path: Path) -> dict:
    if state_path.exists():
        with open(state_path) as f:
            return json.load(f)
    return {}


def save_state(state_path: Path, state: dict) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with open(state_path, "w") as f:
        json.dump(state, f, indent=2)


# Prefer texture_synthesis (no blur); fallback methods if needed
REMOVAL_STRATEGIES = [
    {"method": "texture_synthesis", "frac_w": 0.12, "frac_h": 0.10},
    {"method": "texture_synthesis", "frac_w": 0.15, "frac_h": 0.12},
    {"method": "texture_synthesis", "frac_w": 0.18, "frac_h": 0.15},
    {"method": "gradient_guided", "frac_w": 0.12, "frac_h": 0.10},
    {"method": "lama", "frac_w": 0.12, "frac_h": 0.10},
]


def run_ralph_loop(
    input_path: str,
    output_path: str,
    state_dir: Path | None = None,
    max_iterations: int = 6,
    clean_threshold: float = 0.3,
) -> dict:
    """
    Ralph Loop: iterate until image is clean or max iterations reached.

    State file: state_dir/ralph_state.json
    """
    input_path = Path(input_path).resolve()
    output_path = Path(output_path).resolve()
    state_dir = state_dir or output_path.parent
    state_path = state_dir / "ralph_state.json"

    state = load_state(state_path)
    if not state or state.get("input_path") != str(input_path):
        state = {
            "input_path": str(input_path),
            "output_path": str(output_path),
            "current_path": str(input_path),
            "iteration": 0,
            "strategy_index": 0,
            "history": [],
            "created_at": datetime.now().isoformat(),
        }

    current = Path(state["current_path"])
    strategy_index = state.get("strategy_index", 0)
    iteration = state.get("iteration", 0)

    # Verify first (maybe already clean)
    is_clean, verification = verify_completion(str(current), clean_threshold)
    state["last_verification"] = verification

    if is_clean:
        shutil.copy(current, output_path)
        state["success"] = True
        state["final_path"] = str(output_path)
        save_state(state_path, state)
        return state

    if iteration >= max_iterations:
        state["success"] = False
        state["reason"] = "max_iterations"
        save_state(state_path, state)
        return state

    # Run one iteration: remove-region with current strategy
    strategy = REMOVAL_STRATEGIES[strategy_index % len(REMOVAL_STRATEGIES)]
    step_out = output_path.parent / f"{output_path.stem}_ralph_i{iteration}.png"

    ok, msg = run_remove_region(
        current,
        step_out,
        frac_w=strategy["frac_w"],
        frac_h=strategy["frac_h"],
        method=strategy["method"],
    )

    if not ok:
        state["history"].append({"step": "remove_region", "strategy": strategy, "error": msg})
        state["strategy_index"] = strategy_index + 1
        state["iteration"] = iteration + 1
        save_state(state_path, state)
        return run_ralph_loop(str(input_path), str(output_path), state_dir, max_iterations, clean_threshold)

    is_clean, verification = verify_completion(str(step_out), clean_threshold)
    state["current_path"] = str(step_out)
    state["iteration"] = iteration + 1
    state["last_verification"] = verification
    state["history"].append({"step": "remove_region", "strategy": strategy, "output": str(step_out)})

    if is_clean:
        shutil.copy(step_out, output_path)
        state["success"] = True
        state["final_path"] = str(output_path)
    else:
        state["strategy_index"] = strategy_index + 1

    save_state(state_path, state)

    if is_clean:
        return state
    return run_ralph_loop(str(input_path), str(output_path), state_dir, max_iterations, clean_threshold)


def main():
    import argparse
    p = argparse.ArgumentParser(description="Ralph Loop: iterate until watermark removed")
    p.add_argument("input", help="Input image path")
    p.add_argument("-o", "--output", help="Output path (default: assets/clean/<stem>_ralph.png)")
    p.add_argument("--state-dir", help="Directory for ralph_state.json")
    p.add_argument("--max-iterations", type=int, default=6)
    p.add_argument("--clean-threshold", type=float, default=0.3)
    args = p.parse_args()

    input_path = Path(args.input).resolve()
    if not input_path.exists():
        print(f"Error: {input_path} not found")
        sys.exit(1)

    output_path = args.output
    if not output_path:
        output_path = _project_root / "assets" / "clean" / f"{input_path.stem}_ralph.png"
    output_path = Path(output_path).resolve()

    print(f"Ralph Loop: {input_path} -> {output_path}")
    state = run_ralph_loop(
        str(input_path),
        str(output_path),
        state_dir=Path(args.state_dir) if args.state_dir else None,
        max_iterations=args.max_iterations,
        clean_threshold=args.clean_threshold,
    )

    if state.get("success"):
        print(f"Done: {state.get('final_path', output_path)}")
        sys.exit(0)
    else:
        print(f"Stopped after {state.get('iteration', 0)} iterations (not clean)")
        sys.exit(1)


if __name__ == "__main__":
    main()
