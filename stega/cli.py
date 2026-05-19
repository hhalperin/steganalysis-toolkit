#!/usr/bin/env python3
"""
Unified CLI for steganalysis and watermark-resilience experiments (detect -> modify -> verify).
Run from project root: ``stk …`` or ``python -m stega.cli …``.
"""

import sys
import argparse
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _resolve_path(p: str, base: Path | None = None) -> Path:
    base = base or _PROJECT_ROOT
    path = Path(p)
    if not path.is_absolute():
        path = (base / p).resolve()
    return path


def cmd_detect(args) -> int:
    """Run detection on a single image."""
    from .cli_commands.clean import run_detection
    input_path = _resolve_path(args.input)
    if not input_path.exists():
        print(f"Not found: {input_path}")
        return 1
    detection = run_detection(str(input_path), quick=args.quick)
    print("Findings:", detection["findings"] or ["none"])
    if args.json:
        import json
        print(json.dumps(detection, indent=2, default=str))
    return 0


def cmd_clean(args) -> int:
    """Run detectors, then apply planned disruption/sanitization for lab fixtures."""
    from .config import clean_path, ensure_dirs
    from .cli_commands.clean import run_detection, clean_image
    input_path = _resolve_path(args.input)
    if not input_path.exists():
        print(f"Not found: {input_path}")
        return 1
    ensure_dirs()
    output_path = _resolve_path(args.output) if args.output else clean_path() / f"{input_path.stem}_cleaned.png"
    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    print("Detection:", input_path)
    detection = run_detection(str(input_path), quick=args.quick, invisible_only=args.invisible_only)
    print("Findings:", detection["findings"] or ["none"])
    print("Cleaning ->", output_path)
    clean_image(str(input_path), detection, str(output_path))
    print("Done:", output_path)
    return 0


def cmd_agentic(args) -> int:
    """Iterative pipeline: detect -> modify visible overlays -> verify -> retry."""
    import threading
    from .cli_commands.agentic import run_pipeline
    input_path = _resolve_path(args.input)
    if not input_path.exists():
        print(f"Not found: {input_path}")
        return 1
    output_path = _resolve_path(args.output) if args.output else input_path.parent / f"{input_path.stem}_agentic_cleaned.png"
    output_path = output_path.resolve()
    quiet = getattr(args, "quiet", False)
    use_live = getattr(args, "live", False)

    if use_live:
        from .visualization.agentic_live_viewer import run_live_viewer
        live_frame_path = output_path.parent / ".agentic_live.png"
        done = threading.Event()
        state_holder: list = []
        def run():
            state_holder.append(run_pipeline(
                str(input_path),
                str(output_path),
                max_retries=args.max_retries,
                method=args.method,
                clean_threshold=args.clean_threshold,
                log_path=args.log,
                quiet=quiet,
                live_frame_path=str(live_frame_path),
                done_event=done,
            ))
        t = threading.Thread(target=run)
        t.start()
        run_live_viewer(live_frame_path, done, title="Resilience experiment preview")
        t.join()
        try:
            live_frame_path.unlink(missing_ok=True)
        except OSError:
            pass
        state = state_holder[0] if state_holder else {}
        if not quiet:
            print(f"Output: {output_path}")
        return 0 if state.get("success") else 1
    state = run_pipeline(
        str(input_path),
        str(output_path),
        max_retries=args.max_retries,
        method=args.method,
        clean_threshold=args.clean_threshold,
        log_path=args.log,
        quiet=quiet,
    )
    if not quiet:
        print(f"Output: {output_path}")
    return 0 if state.get("success") else 1


def cmd_remove_region(args) -> int:
    """Inpaint a fixed region (e.g. synthetic corner overlay) for controlled experiments."""
    from .cli_commands.remove_region import run_remove_region
    input_path = _resolve_path(args.input)
    if not input_path.exists():
        print(f"Not found: {input_path}")
        return 1
    output_path = _resolve_path(args.output) if args.output else input_path.parent / f"{input_path.stem}_no_emblem.png"
    output_path = output_path.resolve()
    ok, msg = run_remove_region(
        input_path,
        output_path,
        frac_w=args.frac_w,
        frac_h=args.frac_h,
        box=args.box,
        method=args.method,
    )
    if ok:
        print(msg)
        return 0
    print("Removal failed:", msg)
    return 1


def cmd_ralph(args) -> int:
    """Ralph loop: iterate disruption strategies until verification passes (texture_synthesis path)."""
    from .config import clean_path, ensure_dirs
    from .tools.ralph_clean import run_ralph_loop
    input_path = _resolve_path(args.input)
    if not input_path.exists():
        print(f"Not found: {input_path}")
        return 1
    ensure_dirs()
    output_path = _resolve_path(args.output) if args.output else clean_path() / f"{input_path.stem}_ralph.png"
    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    print("Ralph Loop:", input_path)
    state = run_ralph_loop(
        str(input_path),
        str(output_path),
        state_dir=Path(args.state_dir) if args.state_dir else None,
        max_iterations=args.max_iterations,
        clean_threshold=args.clean_threshold,
    )
    print(f"  Iterations: {state.get('iteration', 0)}")
    print(f"  Verification: clean={state.get('last_verification', {}).get('clean')}, score={state.get('last_verification', {}).get('score', 0):.2f}")
    print(f"  Success: {state.get('success')}")
    print(f"  Output: {output_path}")
    return 0 if state.get("success") else 1


def cmd_full_test(args) -> int:
    """Run full detection on a directory of images."""
    from .config import resolve_output_dir, resolve_reports_dir
    from .cli_commands.full_test import run_full_detection
    image_dir = _resolve_path(args.dir) if args.dir else resolve_output_dir("sample-emblem")
    if not image_dir.is_dir():
        print(f"Not a directory: {image_dir}")
        return 1
    files = sorted(image_dir.glob("*.png")) + sorted(image_dir.glob("*.jpg"))
    if not files:
        print(f"No PNG/JPG files in {image_dir}")
        return 1
    report_dir = resolve_reports_dir()
    report_dir.mkdir(parents=True, exist_ok=True)
    out_path = _resolve_path(args.output) if args.output else report_dir / "full_test_report.json"
    print("=" * 60)
    print("FULL DETECTION TEST")
    print(f"Directory: {image_dir}")
    print(f"Images: {len(files)}")
    print("=" * 60)
    if args.quick:
        print("(Quick mode: skipping steganography + visible_watermarks)")
    all_results = {}
    for i, f in enumerate(files, 1):
        print(f"\n[{i}/{len(files)}] {f.name}")
        r = run_full_detection(str(f), quick=args.quick)
        all_results[f.stem] = r
        print(f"  Risk: {r['summary']['risk']}  Findings: {len(r['summary']['findings'])}")
        for x in r["summary"]["findings"][:15]:
            print(f"    - {x}")
    import json
    with open(out_path, "w") as out:
        json.dump(all_results, out, indent=2, default=str)
    print(f"\nReport saved: {out_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="stk",
        description="Steganalysis toolkit - detection, resilience experiments, and verification. Use only on media you own or synthetic fixtures.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    p = subparsers.add_parser("detect", help="Run detection on a single image")
    p.add_argument("input", help="Input image path")
    p.add_argument("--quick", action="store_true", help="Skip slow detectors")
    p.add_argument("--json", action="store_true", help="Output full JSON")
    p.set_defaults(func=cmd_detect)

    p = subparsers.add_parser("clean", help="Detect then apply disruption/sanitization plan")
    p.add_argument("input", help="Input image path")
    p.add_argument("-o", "--output", help="Output path")
    p.add_argument("--quick", action="store_true", help="Skip slow detectors")
    p.add_argument("--invisible-only", action="store_true", help="Skip visible-overlay branch; LSB/steganography/patterns only")
    p.set_defaults(func=cmd_clean)

    p = subparsers.add_parser("agentic", help="Detect -> modify overlays -> verify -> retry (logged)")
    p.add_argument("input", help="Input image path")
    p.add_argument("-o", "--output", help="Output path")
    p.add_argument("--live", action="store_true", help="Live preview window during run")
    p.add_argument("--quiet", "-q", action="store_true", help="Suppress pipeline logs")
    p.add_argument("--max-retries", type=int, default=3)
    p.add_argument("--method", choices=["lama", "inpainting", "opencv_ns"], default="lama")
    p.add_argument("--clean-threshold", type=float, default=0.3)
    p.add_argument("--log", help="JSONL log file")
    p.set_defaults(func=cmd_agentic)

    p = subparsers.add_parser("ralph", help="Corner-region iteration until verification passes")
    p.add_argument("input", help="Input image path")
    p.add_argument("-o", "--output", help="Output path")
    p.add_argument("--state-dir", help="Directory for ralph_state.json")
    p.add_argument("--max-iterations", type=int, default=6)
    p.add_argument("--clean-threshold", type=float, default=0.3)
    p.set_defaults(func=cmd_ralph)

    p = subparsers.add_parser("remove-region", help="Inpaint a bbox/corner region (controlled fixture)")
    p.add_argument("input", help="Input image path")
    p.add_argument("-o", "--output", help="Output path")
    p.add_argument("--frac-w", type=float, default=0.12, help="Width of corner region as fraction")
    p.add_argument("--frac-h", type=float, default=0.10, help="Height of corner region as fraction")
    p.add_argument("--box", help="Explicit bbox: x,y,w,h (pixels)")
    p.add_argument("--method", choices=["lama", "inpainting", "opencv_ns", "gradient_guided", "multi_scale_blending", "texture_synthesis"], default="lama")
    p.set_defaults(func=cmd_remove_region)

    p = subparsers.add_parser("full-test", help="Run full detection on a directory")
    p.add_argument("dir", nargs="?", help="Directory (default: assets/clean/sample-emblem)")
    p.add_argument("-o", "--output", help="Output JSON report path")
    p.add_argument("--quick", action="store_true", help="Skip slow detectors")
    p.set_defaults(func=cmd_full_test)

    p = subparsers.add_parser("ai-loop", help='Structured loop to study synthetic "AI-tell" markers (research harness)')
    p_sub = p.add_subparsers(dest="ai_phase", required=True)
    p_init = p_sub.add_parser("init", help="Initialize: copy image to assets/processing/ai-loop/current.png")
    p_init.add_argument("image", help="Input image path")
    p_init.set_defaults(ai_loop_func="init")
    p_next = p_sub.add_parser("next", help="Print which phase is next and where to save output")
    p_next.set_defaults(ai_loop_func="next")
    p_impl = p_sub.add_parser("implement", help="Generate edit_spec.md from improved_plan.json")
    p_impl.set_defaults(ai_loop_func="implement")

    args = parser.parse_args()
    if args.command == "ai-loop":
        from .cli_commands.ai_loop import (
            cmd_ai_loop_init,
            cmd_ai_loop_next,
            cmd_ai_loop_implement,
        )
        if args.ai_phase == "init":
            return cmd_ai_loop_init(_resolve_path(args.image))
        if args.ai_phase == "next":
            return cmd_ai_loop_next()
        if args.ai_phase == "implement":
            return cmd_ai_loop_implement()
        return 1
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
