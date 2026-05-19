"""
Battle Engine - Orchestrates the steganography battle simulation
Manages rounds, confidence tracking, and self-healing detection
"""

import time
import random
import sys
import os
import numpy as np

try:
    import cv2
except ImportError:
    cv2 = None
from typing import Dict, List, Any, Tuple
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.ai_enhanced_analyzer import AIEnhancedAnalyzer

from advanced_waste_detector import AdvancedWasteDetector
from .metaphors import create_heat_map, add_ripple_effect, create_particle_effect, create_battle_overlay
from .battle_state_machine import (
    BattleStateMachine,
    BattleState,
    detect_self_healing as detect_self_healing_fn,
)
from cleaning.image_cleaner import aggressive_lsb_cleaning, minimal_cleaning
from cleaning.steganography_sanitizer import SteganographySanitizer

class BattleEngine:
    """Manages the battle between cleaning algorithms and watermarks."""

    def __init__(self, confidence_threshold: float = 0.95, demo_mode: bool = False, verbose: bool = False, max_rounds: int = 50):
        self.demo_mode = demo_mode
        self.confidence_threshold = confidence_threshold
        self.verbose = verbose
        self.max_rounds = max_rounds
        self.no_improvement_rounds = 0

        self.state_machine = BattleStateMachine(
            confidence_threshold=confidence_threshold,
            max_rounds=max_rounds,
            self_healing_threshold=0.8,
            no_improvement_rounds_limit=5,
        )

        if demo_mode:
            if verbose:
                print("[BATTLE] Running in DEMO MODE - Enhanced visualization, simplified detection")
            self.analyzer = None  # Skip AI analyzer in demo mode
        self.sanitizer = SteganographySanitizer()
        if not demo_mode:
            self.analyzer = AIEnhancedAnalyzer()

        self.battle_state = {
            'round': 0,
            'max_rounds': max_rounds,
            'confidence': 0.0,
            'waste_detected': {},
            'battle_log': [],
            'active_cleaning': [],
            'particles': [],
            'self_healing_detected': False,
            'last_confidence': 0.0,
            '_confidence_history': [],
        }

    def run_battle(self, image_path: str, images_dir: str = "assets/battle_output") -> Dict[str, Any]:
        """Run the full battle simulation against watermarks."""
        images_path = Path(images_dir)
        images_path.mkdir(exist_ok=True)

        if self.verbose:
            self._log("Battle initiated against watermarks in: " + image_path)
        self.battle_state['image_path'] = image_path

        while not self._should_stop_battle():
            self.battle_state['round'] += 1
            round_num = self.battle_state['round']

            if self.verbose:
                self._log(f"Round {round_num}: Analyzing and cleaning...")

            waste_detected = self._detect_waste(image_path)
            self.battle_state['waste_detected'] = waste_detected

            # Step 2: Generate visualization
            self._generate_visualization_frame(image_path, round_num, images_path)

            # Step 3: Apply cleaning if waste detected
            if waste_detected:
                self._apply_cleaning(image_path, waste_detected, images_path)

            # Step 4: Update confidence before self-healing check
            self._update_confidence()

            # Step 5: Check for self-healing (watermarks regenerating)
            self_healing = self._detect_self_healing()
            if self_healing:
                self.battle_state['self_healing_detected'] = True
                if self.verbose:
                    self._log("Self-healing watermarks detected! Deploying counter-measures...")
                self._apply_counter_measures(image_path, images_path)

            # Step 6: State machine transition and termination check
            self.state_machine.transition(
                round_num,
                self.battle_state['confidence'],
                waste_detected,
                self_healing,
            )
            if self.verbose:
                self._log(f"Confidence: {self.battle_state['confidence']:.1%}")

            if self.state_machine.is_terminal():
                if self.state_machine.state == BattleState.VICTORY and self.verbose:
                    self._log("Victory! Image appears normalized.")
                elif self.state_machine.state == BattleState.MAX_ROUNDS_REACHED and self.verbose:
                    self._log(f"Max rounds ({self.max_rounds}) reached.")
                break

            if self.battle_state['confidence'] >= self.confidence_threshold:
                if self.verbose:
                    self._log("Victory! Image appears normalized.")
                break

        # Final cleanup and summary
        self._finalize_battle(images_path)
        return self.battle_state

    def _detect_waste(self, image_path: str) -> Dict[str, float]:
        """Detect various types of waste in the image."""
        waste_detected = {}

        try:
            # In demo mode, create fake waste detection for visualization
            if self.demo_mode:
                import random
                demo_waste_types = [
                    'lsb_steganography', 'ai_fingerprint', 'unicode_markers',
                    'blockchain_watermark', 'printer_tracking'
                ]

                # Randomly detect 1-3 waste types with varying confidence
                num_waste = random.randint(1, 3)
                for i in range(num_waste):
                    waste_type = random.choice(demo_waste_types)
                    confidence = random.uniform(0.3, 0.9)
                    waste_detected[waste_type] = confidence

                # Add some particles for visual effects
                self.battle_state['particles'] = [
                    (random.randint(50, 300), random.randint(50, 300), random.uniform(0.5, 1.0))
                    for _ in range(random.randint(3, 8))
                ]

            else:
                # Use advanced waste detector (created per image)
                detector = AdvancedWasteDetector(image_path)
                analysis = detector.analyze()
                for pattern, finding in analysis.items():
                    if hasattr(finding, 'detected') and finding.detected:
                        waste_detected[pattern] = finding.confidence

                # Also check traditional methods if AI analyzer is available
                if self.analyzer:
                    stego_result = self.analyzer.analyze_image(image_path)
                    if stego_result.overall_risk_level in ['medium', 'high', 'critical']:
                        waste_detected['traditional_steganography'] = min(0.9, stego_result.risk_score)

        except Exception as e:
            self._log(f"Detection error: {e}")
            if self.demo_mode:
                # In demo mode, still create some fake waste for visualization
                waste_detected['demo_error'] = 0.5
            else:
                waste_detected['error'] = 0.1

        return waste_detected

    def _apply_cleaning(self, image_path: str, waste_detected: Dict[str, float], output_dir: Path):
        """Apply appropriate cleaning methods based on detected waste."""
        cleaning_methods = []

        # Determine cleaning strategy based on waste types
        if 'lsb_steganography' in waste_detected or 'traditional_steganography' in waste_detected:
            cleaning_methods.extend(['lsb_natural', 'selective_clean'])

        if 'ai_fingerprint' in waste_detected:
            cleaning_methods.append('noise_injection')  # Disrupt AI patterns

        if 'printer_tracking' in waste_detected:
            cleaning_methods.append('channel_adjustment')  # Target yellow channel

        # Apply cleaning methods
        for method in cleaning_methods:
            try:
                output_file = output_dir / f"cleaned_round_{self.battle_state['round']}_{method}.png"
                self.sanitizer.sanitize_image(image_path, str(output_file), method=method, preserve_quality=0.98)

                # Add to active cleaning for visualization
                self.battle_state['active_cleaning'].append({
                    'method': method,
                    'center': (random.randint(50, 200), random.randint(50, 200)),  # Random center for demo
                    'progress': 0.5
                })

                self._log(f"Applied {method} cleaning")

            except Exception as e:
                self._log(f"Cleaning failed for {method}: {e}")

    def _detect_self_healing(self) -> bool:
        """Check if watermarks are regenerating (confidence dropping)."""
        current_confidence = self.battle_state['confidence']
        last_confidence = self.battle_state.get('last_confidence', 1.0)
        history = self.battle_state.get('_confidence_history', [])

        result = detect_self_healing_fn(
            current_confidence,
            last_confidence,
            history,
            min_drop_ratio=0.8,
            min_history_len=3,
        )
        if result:
            self.no_improvement_rounds += 1
        return result

    def _apply_counter_measures(self, image_path: str, output_dir: Path):
        """Apply stronger cleaning when self-healing is detected."""
        counter_methods = ['compression_cycle', 'channel_adjustment', 'noise_injection']

        for method in counter_methods:
            try:
                output_file = output_dir / f"counter_{self.battle_state['round']}_{method}.png"
                self.sanitizer.sanitize_image(image_path, str(output_file), method=method, preserve_quality=0.97)

                # Add counter-ripple for visualization
                self.battle_state['active_cleaning'].append({
                    'method': f'counter_{method}',
                    'center': (random.randint(100, 300), random.randint(100, 300)),
                    'progress': 0.8,
                    'counter_measure': True
                })

                self._log(f"Applied counter-measure: {method}")

            except Exception as e:
                self._log(f"Counter-measure failed: {e}")

    def _generate_visualization_frame(self, image_path: str, round_num: int, output_dir: Path):
        """Generate a comprehensive visualization frame for this round."""
        try:
            # Load current image
            from PIL import Image
            img = Image.open(image_path)
            image_array = np.array(img)

            # Create comprehensive battle visualization
            battle_frame = self._create_comprehensive_battle_frame(image_array, round_num)

            # Save frame
            frame_path = output_dir / f"battle_frame_{round_num:03d}.png"

            # Try with OpenCV first, fallback to PIL if not available
            try:
                import cv2
                cv2.imwrite(str(frame_path), cv2.cvtColor(battle_frame, cv2.COLOR_RGB2BGR))
            except ImportError:
                # Fallback to PIL if OpenCV not available
                battle_img = Image.fromarray(battle_frame)
                battle_img.save(frame_path)

            if self.verbose:
                self._log(f"Generated visualization frame: {frame_path}")

        except Exception as e:
            if self.verbose:
                self._log(f"Visualization frame generation failed: {e}")
            # Create a simple fallback frame
            self._create_fallback_frame(image_path, round_num, output_dir)

    def _create_comprehensive_battle_frame(self, image_array, round_num):
        """Create a comprehensive battle visualization frame."""
        try:
            # Start with the original image
            frame = image_array.copy()

            # Apply battle effects based on current state
            frame = self._apply_battle_effects(frame, round_num)

            # Add informational overlays
            frame = self._add_battle_info_overlay(frame, round_num)

            return frame

        except Exception as e:
            if self.verbose:
                self._log(f"Comprehensive frame creation failed: {e}")
            # Return original image as fallback
            return image_array

    def _apply_battle_effects(self, frame, round_num):
        """Apply visual battle effects to the frame."""
        try:
            # Apply the existing battle overlay for waste visualization
            frame = create_battle_overlay(frame, self.battle_state)

            # Add dramatic effects based on confidence level
            confidence = self.battle_state.get('confidence', 0)

            if confidence < 0.3:
                # Low confidence - red tint, chaotic effects
                frame = self._apply_red_tint(frame, 0.3)
            elif confidence < 0.7:
                # Medium confidence - yellow/orange tint, warning effects
                frame = self._apply_yellow_tint(frame, 0.2)
            else:
                # High confidence - green tint, victory effects
                frame = self._apply_green_tint(frame, 0.2)

            # Add particle effects if we have them
            if self.battle_state.get('particles'):
                frame = self._add_particle_effects(frame)

            return frame

        except Exception as e:
            if self.verbose:
                self._log(f"Battle effects application failed: {e}")
            return frame

    def _add_battle_info_overlay(self, frame, round_num):
        """Add comprehensive battle information overlay."""
        try:
            import cv2

            # Battle status info
            confidence = self.battle_state.get('confidence', 0)
            waste_count = len(self.battle_state.get('waste_detected', {}))
            round_info = f"ROUND {round_num}"
            confidence_info = f"Confidence: {confidence:.1%}"
            waste_info = f"Waste Detected: {waste_count}"

            # Position information
            height, width = frame.shape[:2]

            # Background for text
            cv2.rectangle(frame, (5, 5), (width-5, 120), (0, 0, 0), -1)
            cv2.rectangle(frame, (5, 5), (width-5, 120), (0, 0, 0), 2)

            # Text styling
            font = cv2.FONT_HERSHEY_SIMPLEX
            white = (255, 255, 255)
            green = (0, 255, 0)
            yellow = (0, 255, 255)
            red = (0, 0, 255)

            # Status color based on confidence
            if confidence > 0.8:
                status_color = green
                status_text = "STATUS: VICTORIOUS"
            elif confidence > 0.5:
                status_color = yellow
                status_text = "STATUS: BATTLING"
            else:
                status_color = red
                status_text = "STATUS: INTENSE"

            # Add text overlays
            cv2.putText(frame, round_info, (15, 30), font, 0.8, white, 2, cv2.LINE_AA)
            cv2.putText(frame, confidence_info, (15, 55), font, 0.7, status_color, 2, cv2.LINE_AA)
            cv2.putText(frame, waste_info, (15, 80), font, 0.6, white, 2, cv2.LINE_AA)
            cv2.putText(frame, status_text, (15, 105), font, 0.6, status_color, 2, cv2.LINE_AA)

            # Progress bar
            bar_width = int((width - 30) * (confidence / 1.0))
            cv2.rectangle(frame, (15, height-40), (width-15, height-20), (50, 50, 50), -1)
            cv2.rectangle(frame, (15, height-40), (15 + bar_width, height-20), status_color, -1)
            cv2.putText(frame, "Battle Progress", (15, height-45), font, 0.5, white, 1, cv2.LINE_AA)

            return frame

        except ImportError:
            # Skip OpenCV overlays if not available
            return frame
        except Exception as e:
            if self.verbose:
                self._log(f"Info overlay creation failed: {e}")
            return frame

    def _apply_red_tint(self, frame, intensity):
        """Apply red tint for low confidence situations."""
        red_overlay = np.zeros_like(frame)
        red_overlay[:, :, 0] = int(255 * intensity)  # Red channel
        return cv2.addWeighted(frame, 1.0, red_overlay, intensity, 0) if cv2 is not None else frame

    def _apply_yellow_tint(self, frame, intensity):
        """Apply yellow tint for medium confidence situations."""
        yellow_overlay = np.zeros_like(frame)
        yellow_overlay[:, :, 0] = int(255 * intensity)  # Red channel
        yellow_overlay[:, :, 1] = int(255 * intensity)  # Green channel
        return cv2.addWeighted(frame, 1.0, yellow_overlay, intensity, 0) if cv2 is not None else frame

    def _apply_green_tint(self, frame, intensity):
        """Apply green tint for high confidence situations."""
        green_overlay = np.zeros_like(frame)
        green_overlay[:, :, 1] = int(255 * intensity)  # Green channel
        return cv2.addWeighted(frame, 1.0, green_overlay, intensity, 0) if cv2 is not None else frame

    def _add_particle_effects(self, frame):
        """Add particle effects from battle state."""
        try:
            import cv2
            particles = self.battle_state.get('particles', [])

            for x, y, intensity in particles:
                # Draw particle as glowing dot
                center = (int(x), int(y))
                radius = max(2, int(intensity * 8))
                color = (255, 255, 0)  # Yellow particles

                cv2.circle(frame, center, radius, color, -1)
                # Add glow effect
                cv2.circle(frame, center, radius + 2, (255, 255, 0), 2)

            return frame

        except Exception:
            return frame

    def _create_fallback_frame(self, image_path: str, round_num: int, output_dir: Path):
        """Create a simple fallback frame when main generation fails."""
        try:
            from PIL import Image, ImageDraw

            # Load original image
            img = Image.open(image_path)
            draw = ImageDraw.Draw(img)

            # Add simple text overlay
            try:
                # Try to use a nice font if available
                from PIL import ImageFont
                font = ImageFont.load_default()
            except:
                font = None

            # Draw battle info
            draw.text((10, 10), f"BATTLE FRAME {round_num}", fill=(255, 255, 255))
            draw.text((10, 40), f"Confidence: {self.battle_state.get('confidence', 0):.1%}", fill=(0, 255, 0))

            # Save fallback frame
            frame_path = output_dir / f"battle_frame_{round_num:03d}.png"
            img.save(frame_path)
            self._log(f"Created fallback frame: {frame_path}")

        except Exception as e:
            self._log(f"Fallback frame creation also failed: {e}")

    def _update_confidence(self):
        """Update overall confidence based on current state."""
        if self.demo_mode:
            # In demo mode, create gradual confidence increase for better visualization
            current_round = self.battle_state['round']
            max_rounds = self.battle_state['max_rounds']

            # Gradual confidence increase: starts low, builds up over rounds
            base_confidence = min(0.9, current_round / max_rounds * 0.8)

            # Add some randomness for more interesting progression
            import random
            random_factor = random.uniform(-0.1, 0.1)
            confidence = max(0.1, min(0.95, base_confidence + random_factor))

            # Reduce waste count as battle progresses (simulate cleaning)
            initial_waste = 3  # Start with 3 waste types
            remaining_waste = max(0, initial_waste - (current_round // 5))

            self.battle_state['last_confidence'] = self.battle_state.get('confidence', 0.0)
            self.battle_state['confidence'] = confidence
            hist = self.battle_state.setdefault('_confidence_history', [])
            hist.append(confidence)
            if len(hist) > 20:
                hist.pop(0)

            # Update waste count for display
            if remaining_waste == 0:
                self.battle_state['waste_detected'] = {}
            else:
                # Keep some waste types for visual feedback
                demo_waste = {k: v for k, v in list(self.battle_state['waste_detected'].items())[:remaining_waste]}
                self.battle_state['waste_detected'] = demo_waste

        else:
            # Original confidence calculation for non-demo mode
            waste_count = len(self.battle_state['waste_detected'])
            waste_confidence = sum(self.battle_state['waste_detected'].values()) / max(waste_count, 1)
            self.battle_state['last_confidence'] = self.battle_state.get('confidence', 0.0)
            self.battle_state['confidence'] = 1.0 - waste_confidence
            hist = self.battle_state.setdefault('_confidence_history', [])
            hist.append(self.battle_state['confidence'])
            if len(hist) > 20:
                hist.pop(0)

    def _should_stop_battle(self) -> bool:
        """Determine if battle should stop."""
        # Stop if confidence threshold reached
        if self.battle_state['confidence'] >= self.confidence_threshold:
            return True

        # Stop if no improvement for several rounds
        if self.no_improvement_rounds >= 5:
            if self.verbose:
                self._log("No improvement detected for 5 rounds - terminating battle")
            return True

        # Stop if no waste detected for several rounds (battle won)
        if self.battle_state['round'] > 10 and not self.battle_state['waste_detected']:
            if self.verbose:
                self._log("No waste detected for multiple rounds - battle won!")
            return True

        # Stop if max rounds reached
        if self.battle_state['round'] >= self.max_rounds:
            if self.verbose:
                self._log(f"Max rounds ({self.max_rounds}) reached - terminating battle")
            return True

        return False

    def _log(self, message: str):
        """Add message to battle log."""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.battle_state['battle_log'].append(log_entry)

        # Keep only last 20 entries
        if len(self.battle_state['battle_log']) > 20:
            self.battle_state['battle_log'] = self.battle_state['battle_log'][-20:]

    def _finalize_battle(self, output_dir: Path):
        """Perform final battle cleanup and generate summary."""
        self._log("Battle completed!")

        # Generate final summary
        total_rounds = self.battle_state['round']
        final_confidence = self.battle_state['confidence']
        waste_removed = len(self.battle_state['waste_detected']) == 0

        self._log(f"Summary: {total_rounds} rounds, {final_confidence:.1%} confidence")
        if waste_removed:
            self._log("All detected waste successfully removed!")
        else:
            self._log(f"Remaining waste: {list(self.battle_state['waste_detected'].keys())}")

        # Generate final battle report
        report_path = output_dir / "battle_report.txt"
        with open(report_path, 'w') as f:
            f.write("STEGANOGRAPHY BATTLE REPORT\n")
            f.write("=" * 40 + "\n\n")
            f.write(f"Total Rounds: {total_rounds}\n")
            f.write(f"Final Confidence: {final_confidence:.1%}\n")
            f.write(f"Self-Healing Detected: {self.battle_state['self_healing_detected']}\n")
            f.write(f"Waste Types Detected: {len(self.battle_state['waste_detected'])}\n\n")
            f.write("Battle Log:\n")
            for entry in self.battle_state['battle_log']:
                f.write(f"  {entry}\n")

        self._log(f"Final report saved: {report_path}")
