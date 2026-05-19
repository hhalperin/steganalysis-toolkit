#!/usr/bin/env python3
"""
Battle Visualization CLI - Run steganography battle simulation with visual feedback
Run from project root: python -m stega.tools.battle_visualization <image_path> [options]
"""

import sys
import argparse
from pathlib import Path

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from stega.config import BATTLE_VIDEOS_DIR
from stega.visualization.battle_engine import BattleEngine
from stega.visualization.dashboard import BattleDashboard


def main():
    parser = argparse.ArgumentParser(
        description="Steganography Battle Visualization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m stega.tools.battle_visualization image.png
  python -m stega.tools.battle_visualization image.png --verbose
  python -m stega.tools.battle_visualization image.png --demo-mode --verbose
        """
    )

    parser.add_argument("image", help="Image file to analyze and clean")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Show detailed battle progress (default: quiet mode)")
    parser.add_argument("--demo-mode", action="store_true",
                       help="Demo mode with enhanced visualization")
    parser.add_argument("--confidence-threshold", type=float, default=0.95,
                       help="Confidence threshold to stop battle (0.0-1.0)")
    parser.add_argument("--output-dir", "-o", default=None,
                       help="Base output directory (default: assets/battle-videos)")
    parser.add_argument("--generate-video", action="store_true", default=True,
                       help="Generate video from battle frames (default: True)")
    parser.add_argument("--max-rounds", type=int, default=50,
                       help="Maximum number of cleaning rounds (default: 50)")

    args = parser.parse_args()

    # Validate and resolve image file path
    image_path = Path(args.image)
    if not image_path.exists():
        for candidate in [project_root / args.image, project_root / "assets" / "dirty" / args.image]:
            if candidate.exists():
                image_path = candidate
                break
        else:
            print(f"[ERROR] Image file not found: {args.image}")
            return 1

    # Create structured output directories
    image_name = image_path.stem
    base_output_dir = Path(args.output_dir) if args.output_dir else BATTLE_VIDEOS_DIR
    battle_dir = base_output_dir / image_name
    images_dir = battle_dir / "images"
    video_dir = battle_dir / "video"
    images_dir.mkdir(parents=True, exist_ok=True)

    if args.verbose:
        print("[BATTLE] Initializing steganography battle visualization...")
        print(f"[BATTLE] Target: {image_path.name}")
        print(f"[BATTLE] Output: {battle_dir}")
        print(f"[BATTLE] Confidence threshold: {args.confidence_threshold:.1%}")
        print(f"[BATTLE] Demo mode: {args.demo_mode}")

    try:
        battle_engine = BattleEngine(
            confidence_threshold=args.confidence_threshold,
            demo_mode=args.demo_mode,
            verbose=args.verbose,
            max_rounds=args.max_rounds
        )

        final_state = battle_engine.run_battle(
            str(image_path),
            images_dir=str(images_dir)
        )

        if args.generate_video:
            video_path = _generate_battle_video(images_dir, final_state, args.verbose)
            if video_path and args.verbose:
                print(f"[VIDEO] Generated: {video_path}")

        _generate_battle_summary(battle_dir, final_state, args.verbose)

        print(f"\n[SUCCESS] Battle completed! Check {battle_dir} for results.")

        return 0

    except KeyboardInterrupt:
        if args.verbose:
            print("\n[BATTLE] Interrupted by user")
        return 1
    except Exception as e:
        if args.verbose:
            print(f"\n[ERROR] Battle failed: {e}")
            import traceback
            traceback.print_exc()
        return 1


def _generate_battle_video(images_dir: str, battle_state: dict, verbose: bool = False) -> str:
    """Generate video from battle frames if available."""
    try:
        import cv2

        images_path = Path(images_dir)

        frame_files = sorted(images_path.glob("battle_frame_*.png"))
        if not frame_files:
            if verbose:
                print("[VIDEO] No battle frames found for video generation")
            return ""

        if verbose:
            print(f"[VIDEO] Found {len(frame_files)} battle frames, generating video...")

        first_frame = cv2.imread(str(frame_files[0]))
        if first_frame is None:
            if verbose:
                print("[VIDEO] Could not read first frame")
            return ""

        height, width = first_frame.shape[:2]

        battle_dir = images_path.parent
        video_dir = battle_dir / "video"
        video_dir.mkdir(exist_ok=True)

        video_path = video_dir / "battle_video.mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        fps = 3

        video = cv2.VideoWriter(str(video_path), fourcc, fps, (width, height))

        for frame_file in frame_files:
            frame = cv2.imread(str(frame_file))
            if frame is not None:
                video.write(frame)

        video.release()

        if verbose:
            print(f"[VIDEO] Generated battle video: {video_path}")

        return str(video_path)

    except Exception as e:
        if verbose:
            print(f"[VIDEO] Video generation failed: {e}")
            import traceback
            traceback.print_exc()
        return ""


def _generate_battle_summary(battle_dir: Path, battle_state: dict, verbose: bool = False):
    """Write a markdown summary for a visualization run."""
    try:
        summary_file = battle_dir / "battle_analysis.md"

        total_rounds = battle_state['round']
        final_confidence = battle_state['confidence']
        waste_detected = battle_state['waste_detected']
        self_healing = battle_state['self_healing_detected']
        battle_log = battle_state['battle_log']

        story = _create_battle_story(total_rounds, final_confidence, waste_detected, self_healing)
        technical_analysis = _create_technical_analysis(battle_state)

        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("# Resilience visualization report\n\n")
            f.write("## Narrative summary\n\n")
            f.write(story)
            f.write("\n## Metrics\n\n")
            f.write(technical_analysis)
            f.write("\n## Statistics\n\n")
            f.write(f"- **Total rounds**: {total_rounds}\n")
            f.write(f"- **Final confidence**: {final_confidence:.1%}\n")
            f.write(f"- **Signal buckets flagged**: {len(waste_detected)}\n")
            f.write(f"- **Adaptive recovery observed**: {'Yes' if self_healing else 'No'}\n")
            f.write(f"- **Outcome**: {'Threshold met' if final_confidence >= 0.95 else 'Partial progress' if final_confidence >= 0.7 else 'Needs review'}\n\n")

            if battle_log:
                f.write("## Run log\n\n")
                for entry in battle_log[-10:]:
                    f.write(f"- {entry}\n")

        if verbose:
            print(f"[SUMMARY] Generated detailed analysis: {summary_file}")

    except Exception as e:
        if verbose:
            print(f"[SUMMARY] Failed to generate battle summary: {e}")


def _create_battle_story(total_rounds, final_confidence, waste_detected, self_healing):
    """Neutral narrative for markdown exports (research / demo runs)."""
    story_lines = []
    story_lines.append(
        "This run recorded how detectors and modifiers interacted over multiple rounds on a controlled fixture."
    )
    story_lines.append(
        "Treat the summary as a lab notebook excerpt — not an endorsement of bypassing real-world attribution systems."
    )

    story_lines.append(f"Completed rounds: {total_rounds}. Final detector confidence: {final_confidence:.1%}.")

    waste_count = len(waste_detected)
    if waste_count == 0:
        story_lines.append("No additional signal categories were flagged beyond baseline noise.")
    else:
        keys_preview = ", ".join(list(waste_detected.keys())[:5])
        story_lines.append(f"Flagged signal categories ({waste_count}): {keys_preview}.")

    if self_healing:
        story_lines.append("Adaptive recovery behaviors were observed during the run — review logs for details.")

    if final_confidence >= 0.95:
        story_lines.append("Verification threshold met under the configured detector settings.")
    else:
        story_lines.append("Verification did not reach the high-confidence threshold — iterate parameters or review false positives.")

    return "\n\n".join(story_lines)


def _create_technical_analysis(battle_state):
    """Structured metrics for markdown exports."""
    analysis = []

    analysis.append("### Run metrics")
    analysis.append(f"- **Rounds observed**: {battle_state['round']}")
    analysis.append(f"- **Final detector confidence**: {battle_state['confidence']:.1%}")
    analysis.append(f"- **Distinct signal buckets**: {len(battle_state['waste_detected'])}")

    if battle_state['self_healing_detected']:
        analysis.append("- **Adaptive recovery**: Detected during the run")

    confidence = battle_state['confidence']
    if confidence >= 0.95:
        analysis.append("- **Interpretation**: High-confidence clearance under this harness configuration")
    elif confidence >= 0.8:
        analysis.append("- **Interpretation**: Strong reduction; residual alerts may remain")
    elif confidence >= 0.6:
        analysis.append("- **Interpretation**: Partial progress; tune thresholds or fixtures")
    else:
        analysis.append("- **Interpretation**: Low confidence clearance — inspect detector outputs")

    return "\n".join(analysis)


if __name__ == "__main__":
    sys.exit(main())
