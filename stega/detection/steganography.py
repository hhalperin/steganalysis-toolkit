"""
Steganography Detection Module - Advanced analysis for hidden data in images
Includes LSB analysis, statistical tests, and pattern detection
"""

import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import io
import base64


@dataclass
class StegoAnalysisResult:
    """Results from steganography analysis."""
    test_name: str
    score: float
    threshold: float
    is_suspicious: bool
    details: Dict[str, Any]
    recommendations: List[str]


class SteganographyDetector:
    """Advanced steganography detection using multiple statistical methods."""
    
    def __init__(self, image_path: str):
        self.image_path = Path(image_path)
        self.image = None
        self.image_array = None
        self.results: List[StegoAnalysisResult] = []
        self.load_image()
    
    def load_image(self) -> bool:
        """Load and prepare the image for analysis."""
        try:
            self.image = Image.open(self.image_path)
            
            # Convert to RGB if necessary
            if self.image.mode not in ['RGB', 'RGBA', 'L']:
                self.image = self.image.convert('RGB')
            
            self.image_array = np.array(self.image)
            return True
            
        except Exception as e:
            print(f"Error loading image: {e}")
            return False
    
    def analyze_lsb_patterns(self) -> StegoAnalysisResult:
        """Analyze Least Significant Bit patterns for steganographic content."""
        if self.image_array is None:
            return StegoAnalysisResult("LSB Pattern Analysis", 0.0, 0.5, False, {}, [])
        
        # Extract LSBs from each channel
        if len(self.image_array.shape) == 3:  # Color image
            channels = ['R', 'G', 'B'] if self.image_array.shape[2] >= 3 else ['Gray']
            lsb_data = {}
            
            for i, channel in enumerate(channels[:self.image_array.shape[2]]):
                channel_data = self.image_array[:, :, i]
                lsb_bits = channel_data & 1
                lsb_data[channel] = lsb_bits
        else:  # Grayscale
            lsb_bits = self.image_array & 1
            lsb_data = {'Gray': lsb_bits}
        
        # Statistical analysis of LSB patterns
        analysis = {}
        total_suspicion_score = 0.0
        
        for channel, bits in lsb_data.items():
            # Calculate bit frequency (should be close to 50% for natural images)
            ones_ratio = np.mean(bits)
            frequency_score = abs(0.5 - ones_ratio) * 2  # 0 = perfect balance, 1 = all 0s or 1s
            
            # Calculate randomness using runs test
            runs_score = self._calculate_runs_test(bits.flatten())
            
            # Calculate chi-square test for uniformity
            chi_square_score = self._chi_square_uniformity_test(bits.flatten())
            
            # Autocorrelation test (hidden data often has patterns)
            autocorr_score = self._calculate_autocorrelation(bits.flatten())
            
            channel_scores = {
                'ones_ratio': ones_ratio,
                'frequency_score': frequency_score,
                'runs_score': runs_score,
                'chi_square_score': chi_square_score,
                'autocorrelation_score': autocorr_score,
                'combined_score': (frequency_score + runs_score + chi_square_score + autocorr_score) / 4
            }
            
            analysis[channel] = channel_scores
            total_suspicion_score += channel_scores['combined_score']
        
        # Average across all channels
        avg_suspicion = total_suspicion_score / len(lsb_data)
        threshold = 0.3  # Empirically determined threshold
        is_suspicious = avg_suspicion > threshold
        
        recommendations = []
        if is_suspicious:
            recommendations.extend([
                "LSB patterns suggest possible steganographic content",
                "Try extracting LSB data using tools like steghide or zsteg",
                "Examine specific channels that show highest suspicion scores"
            ])
        
        return StegoAnalysisResult(
            test_name="LSB Pattern Analysis",
            score=avg_suspicion,
            threshold=threshold,
            is_suspicious=is_suspicious,
            details=analysis,
            recommendations=recommendations
        )
    
    def _calculate_runs_test(self, bits: np.ndarray) -> float:
        """Calculate runs test score for randomness (0 = random, 1 = patterns)."""
        if len(bits) == 0:
            return 0.0
        
        # Count runs (consecutive identical bits)
        runs = 1
        for i in range(1, len(bits)):
            if bits[i] != bits[i-1]:
                runs += 1
        
        # Expected runs for random sequence
        ones = np.sum(bits)
        zeros = len(bits) - ones
        
        if ones == 0 or zeros == 0:
            return 1.0  # All same bits = highly suspicious
        
        expected_runs = (2 * ones * zeros) / len(bits) + 1
        
        # Normalize score (deviation from expected)
        if expected_runs == 0:
            return 1.0
        
        deviation = abs(runs - expected_runs) / expected_runs
        return min(deviation, 1.0)
    
    def _chi_square_uniformity_test(self, bits: np.ndarray) -> float:
        """Chi-square test for uniform distribution of bits."""
        if len(bits) == 0:
            return 0.0
        
        ones = np.sum(bits)
        zeros = len(bits) - ones
        expected = len(bits) / 2
        
        if expected == 0:
            return 0.0
        
        chi_square = ((ones - expected) ** 2 + (zeros - expected) ** 2) / expected
        
        # Normalize to 0-1 scale (empirically based on typical values)
        normalized_score = min(chi_square / 50.0, 1.0)
        return normalized_score
    
    def _calculate_autocorrelation(self, bits: np.ndarray, max_lag: int = 100) -> float:
        """Calculate autocorrelation to detect periodic patterns."""
        if len(bits) < max_lag * 2:
            max_lag = len(bits) // 4
        
        if max_lag <= 1:
            return 0.0
        
        # Calculate autocorrelation for various lags
        autocorrs = []
        mean_val = np.mean(bits)
        
        for lag in range(1, max_lag):
            if lag >= len(bits):
                break
            
            # Calculate correlation coefficient for this lag
            x1 = bits[:-lag] - mean_val
            x2 = bits[lag:] - mean_val
            
            if np.std(x1) == 0 or np.std(x2) == 0:
                corr = 0
            else:
                corr = np.corrcoef(x1, x2)[0, 1]
                if np.isnan(corr):
                    corr = 0
            
            autocorrs.append(abs(corr))
        
        # Return maximum absolute autocorrelation (higher = more patterns)
        return max(autocorrs) if autocorrs else 0.0
    
    def analyze_pixel_value_distribution(self) -> StegoAnalysisResult:
        """Analyze pixel value distributions for anomalies."""
        if self.image_array is None:
            return StegoAnalysisResult("Pixel Distribution Analysis", 0.0, 0.5, False, {}, [])
        
        analysis = {}
        
        # Flatten image to analyze all pixels
        if len(self.image_array.shape) == 3:
            channels = []
            for i in range(self.image_array.shape[2]):
                channels.append(self.image_array[:, :, i].flatten())
        else:
            channels = [self.image_array.flatten()]
        
        suspicion_scores = []
        
        for i, channel_data in enumerate(channels):
            # Calculate histogram
            hist, bins = np.histogram(channel_data, bins=256, range=(0, 255))
            
            # Analyze histogram for anomalies
            # 1. Even/odd pixel value bias (common in LSB steganography)
            even_sum = np.sum(hist[::2])
            odd_sum = np.sum(hist[1::2])
            total_pixels = len(channel_data)
            
            even_odd_bias = abs(even_sum - odd_sum) / total_pixels
            
            # 2. Histogram uniformity (too uniform suggests modification)
            hist_variance = np.var(hist)
            expected_variance = total_pixels / 256  # Expected for uniform distribution
            uniformity_score = 1.0 - min(hist_variance / expected_variance, 1.0) if expected_variance > 0 else 0.0
            
            # 3. Histogram gaps (missing values might indicate manipulation)
            zero_bins = np.sum(hist == 0)
            gap_score = zero_bins / 256
            
            # 4. Check for suspicious peaks or valleys
            hist_smooth = np.convolve(hist, np.ones(5)/5, mode='same')
            peaks_valleys_score = np.std(hist - hist_smooth) / np.mean(hist) if np.mean(hist) > 0 else 0.0
            
            channel_suspicion = (even_odd_bias + uniformity_score + gap_score + peaks_valleys_score) / 4
            suspicion_scores.append(channel_suspicion)
            
            analysis[f'channel_{i}'] = {
                'even_odd_bias': even_odd_bias,
                'uniformity_score': uniformity_score,
                'gap_score': gap_score,
                'peaks_valleys_score': peaks_valleys_score,
                'combined_score': channel_suspicion
            }
        
        avg_suspicion = np.mean(suspicion_scores)
        threshold = 0.25
        is_suspicious = avg_suspicion > threshold
        
        recommendations = []
        if is_suspicious:
            recommendations.extend([
                "Pixel value distribution shows anomalies",
                "Check for even/odd pixel value biases (common in LSB hiding)",
                "Analyze histogram for artificial uniformity or gaps"
            ])
        
        return StegoAnalysisResult(
            test_name="Pixel Distribution Analysis",
            score=avg_suspicion,
            threshold=threshold,
            is_suspicious=is_suspicious,
            details=analysis,
            recommendations=recommendations
        )
    
    def analyze_noise_patterns(self) -> StegoAnalysisResult:
        """Analyze noise patterns that might indicate steganographic content."""
        if self.image_array is None:
            return StegoAnalysisResult("Noise Pattern Analysis", 0.0, 0.5, False, {}, [])
        
        # Convert to grayscale for noise analysis
        if len(self.image_array.shape) == 3:
            gray = np.dot(self.image_array[...,:3], [0.2989, 0.5870, 0.1140])
        else:
            gray = self.image_array
        
        # Calculate noise using high-pass filtering
        # Sobel edge detection
        from scipy import ndimage
        
        sobel_x = ndimage.sobel(gray, axis=0, mode='constant')
        sobel_y = ndimage.sobel(gray, axis=1, mode='constant')
        edge_magnitude = np.hypot(sobel_x, sobel_y)
        
        # Analyze noise in smooth regions (where edges are minimal)
        smooth_mask = edge_magnitude < np.percentile(edge_magnitude, 20)
        smooth_regions = gray[smooth_mask]
        
        if len(smooth_regions) == 0:
            return StegoAnalysisResult("Noise Pattern Analysis", 0.0, 0.5, False, {}, [])
        
        # Calculate local variance in smooth regions
        variance_score = np.var(smooth_regions) / 255**2  # Normalize
        
        # Calculate noise entropy
        hist, _ = np.histogram(smooth_regions, bins=256, range=(0, 255))
        hist = hist[hist > 0]  # Remove zero entries
        entropy = -np.sum(hist * np.log2(hist / np.sum(hist))) / 8  # Normalize to 0-1
        
        # High entropy in smooth regions might indicate hidden data
        combined_score = (variance_score + entropy) / 2
        
        threshold = 0.4
        is_suspicious = combined_score > threshold
        
        recommendations = []
        if is_suspicious:
            recommendations.extend([
                "Unusual noise patterns detected in smooth image regions",
                "High entropy in supposedly smooth areas may indicate hidden data",
                "Consider advanced steganalysis tools like StegExpose or ImageJ"
            ])
        
        return StegoAnalysisResult(
            test_name="Noise Pattern Analysis",
            score=combined_score,
            threshold=threshold,
            is_suspicious=is_suspicious,
            details={
                'variance_score': variance_score,
                'entropy_score': entropy,
                'smooth_regions_count': len(smooth_regions)
            },
            recommendations=recommendations
        )
    
    def analyze_compression_artifacts(self) -> StegoAnalysisResult:
        """Analyze compression artifacts that might reveal steganographic modifications."""
        if self.image_array is None:
            return StegoAnalysisResult("Compression Artifact Analysis", 0.0, 0.5, False, {}, [])
        
        # This analysis is most relevant for JPEG images, but we can still detect some patterns in PNG
        
        # Look for block-like artifacts (8x8 patterns common in JPEG)
        height, width = self.image_array.shape[:2]
        
        # Sample 8x8 blocks and analyze variance within blocks vs between blocks
        block_variances = []
        inter_block_differences = []
        
        for y in range(0, height - 8, 8):
            for x in range(0, width - 8, 8):
                if len(self.image_array.shape) == 3:
                    block = np.mean(self.image_array[y:y+8, x:x+8], axis=2)
                else:
                    block = self.image_array[y:y+8, x:x+8]
                
                block_var = np.var(block)
                block_variances.append(block_var)
                
                # Compare with adjacent blocks
                if x + 16 < width:
                    if len(self.image_array.shape) == 3:
                        adj_block = np.mean(self.image_array[y:y+8, x+8:x+16], axis=2)
                    else:
                        adj_block = self.image_array[y:y+8, x+8:x+16]
                    
                    diff = np.mean(np.abs(block - adj_block))
                    inter_block_differences.append(diff)
        
        if not block_variances or not inter_block_differences:
            return StegoAnalysisResult("Compression Artifact Analysis", 0.0, 0.5, False, {}, [])
        
        # Calculate metrics
        avg_block_variance = np.mean(block_variances)
        avg_inter_block_diff = np.mean(inter_block_differences)
        
        # Ratio of inter-block differences to intra-block variance
        # High ratio might indicate artificial block boundaries
        if avg_block_variance > 0:
            artifact_score = min(avg_inter_block_diff / avg_block_variance, 1.0)
        else:
            artifact_score = 0.0
        
        threshold = 0.3
        is_suspicious = artifact_score > threshold
        
        recommendations = []
        if is_suspicious:
            recommendations.extend([
                "Compression artifacts suggest possible image manipulation",
                "Block-like patterns may indicate steganographic insertion",
                "Check image history and processing chain"
            ])
        
        return StegoAnalysisResult(
            test_name="Compression Artifact Analysis",
            score=artifact_score,
            threshold=threshold,
            is_suspicious=is_suspicious,
            details={
                'avg_block_variance': avg_block_variance,
                'avg_inter_block_diff': avg_inter_block_diff,
                'blocks_analyzed': len(block_variances)
            },
            recommendations=recommendations
        )
    
    def detect_frequency_domain_anomalies(self) -> StegoAnalysisResult:
        """Detect anomalies in frequency domain that might indicate steganographic content."""
        if self.image_array is None:
            return StegoAnalysisResult("Frequency Domain Analysis", 0.0, 0.5, False, {}, [])
        
        try:
            # Convert to grayscale for frequency analysis
            if len(self.image_array.shape) == 3:
                gray = np.dot(self.image_array[...,:3], [0.2989, 0.5870, 0.1140])
            else:
                gray = self.image_array.copy()
            
            # Apply 2D FFT
            f_transform = np.fft.fft2(gray)
            f_shift = np.fft.fftshift(f_transform)
            magnitude_spectrum = np.abs(f_shift)
            
            # Analyze frequency distribution
            # Natural images typically have energy concentrated in low frequencies
            
            height, width = magnitude_spectrum.shape
            center_y, center_x = height // 2, width // 2
            
            # Create frequency masks for different regions
            y, x = np.ogrid[:height, :width]
            
            # Low frequency region (center)
            low_freq_mask = ((x - center_x)**2 + (y - center_y)**2) <= (min(height, width) * 0.1)**2
            
            # High frequency region (edges)
            high_freq_mask = ((x - center_x)**2 + (y - center_y)**2) >= (min(height, width) * 0.3)**2
            
            # Calculate energy distribution
            total_energy = np.sum(magnitude_spectrum**2)
            low_freq_energy = np.sum(magnitude_spectrum[low_freq_mask]**2)
            high_freq_energy = np.sum(magnitude_spectrum[high_freq_mask]**2)
            
            if total_energy == 0:
                return StegoAnalysisResult("Frequency Domain Analysis", 0.0, 0.5, False, {}, [])
            
            low_freq_ratio = low_freq_energy / total_energy
            high_freq_ratio = high_freq_energy / total_energy
            
            # Natural images should have most energy in low frequencies
            # Steganographic content might alter this distribution
            
            # Calculate spectral entropy
            magnitude_flat = magnitude_spectrum.flatten()
            magnitude_flat = magnitude_flat[magnitude_flat > 0]
            
            if len(magnitude_flat) > 0:
                # Normalize
                magnitude_normalized = magnitude_flat / np.sum(magnitude_flat)
                spectral_entropy = -np.sum(magnitude_normalized * np.log2(magnitude_normalized + 1e-10))
                spectral_entropy /= np.log2(len(magnitude_normalized))  # Normalize to 0-1
            else:
                spectral_entropy = 0.0
            
            # Anomaly score based on unusual frequency distribution
            # Expected low frequency ratio for natural images: 0.6-0.8
            freq_anomaly = abs(0.7 - low_freq_ratio) * 2
            
            # High spectral entropy might indicate added noise/data
            entropy_anomaly = max(0, spectral_entropy - 0.8)
            
            combined_score = (freq_anomaly + entropy_anomaly) / 2
            
            threshold = 0.3
            is_suspicious = combined_score > threshold
            
            recommendations = []
            if is_suspicious:
                recommendations.extend([
                    "Frequency domain analysis shows anomalies",
                    "Unusual energy distribution may indicate spectral steganography",
                    "Consider DCT-based analysis for JPEG-like hiding methods"
                ])
            
            return StegoAnalysisResult(
                test_name="Frequency Domain Analysis",
                score=combined_score,
                threshold=threshold,
                is_suspicious=is_suspicious,
                details={
                    'low_freq_ratio': low_freq_ratio,
                    'high_freq_ratio': high_freq_ratio,
                    'spectral_entropy': spectral_entropy,
                    'freq_anomaly': freq_anomaly,
                    'entropy_anomaly': entropy_anomaly
                },
                recommendations=recommendations
            )
            
        except Exception as e:
            return StegoAnalysisResult(
                test_name="Frequency Domain Analysis",
                score=0.0,
                threshold=0.5,
                is_suspicious=False,
                details={'error': str(e)},
                recommendations=["Error in frequency domain analysis"]
            )
    
    def run_full_analysis(self) -> Dict[str, Any]:
        """Run all steganographic analysis methods."""
        if not self.image:
            return {'error': 'Failed to load image'}
        
        # Clear previous results
        self.results = []
        
        # Run all analysis methods
        analyses = [
            self.analyze_lsb_patterns,
            self.analyze_pixel_value_distribution,
            self.analyze_noise_patterns,
            self.analyze_compression_artifacts,
            self.detect_frequency_domain_anomalies
        ]
        
        for analysis_func in analyses:
            try:
                result = analysis_func()
                self.results.append(result)
            except Exception as e:
                error_result = StegoAnalysisResult(
                    test_name=analysis_func.__name__,
                    score=0.0,
                    threshold=0.5,
                    is_suspicious=False,
                    details={'error': str(e)},
                    recommendations=[f"Error in {analysis_func.__name__}: {str(e)}"]
                )
                self.results.append(error_result)
        
        # Calculate overall suspicion score
        suspicious_count = sum(1 for r in self.results if r.is_suspicious)
        total_score = sum(r.score for r in self.results) / len(self.results) if self.results else 0.0
        
        overall_suspicious = suspicious_count >= 2 or total_score > 0.4
        
        # Collect all recommendations
        all_recommendations = []
        for result in self.results:
            all_recommendations.extend(result.recommendations)
        
        return {
            'image_path': str(self.image_path),
            'image_info': {
                'size': self.image.size,
                'mode': self.image.mode,
                'format': self.image.format
            },
            'overall_suspicious': overall_suspicious,
            'suspicious_tests_count': suspicious_count,
            'average_suspicion_score': total_score,
            'individual_results': [
                {
                    'test_name': r.test_name,
                    'score': r.score,
                    'threshold': r.threshold,
                    'is_suspicious': r.is_suspicious,
                    'details': r.details,
                    'recommendations': r.recommendations
                }
                for r in self.results
            ],
            'summary_recommendations': list(set(all_recommendations))  # Remove duplicates
        }
    
    def generate_visual_report(self) -> Optional[str]:
        """Generate visual plots for steganography analysis."""
        if not self.image_array is not None:
            return None
        
        try:
            fig, axes = plt.subplots(2, 3, figsize=(15, 10))
            fig.suptitle(f'Steganography Analysis: {self.image_path.name}', fontsize=16)
            
            # Original image
            axes[0, 0].imshow(self.image)
            axes[0, 0].set_title('Original Image')
            axes[0, 0].axis('off')
            
            # LSB visualization
            if len(self.image_array.shape) == 3:
                lsb_image = (self.image_array & 1) * 255
                axes[0, 1].imshow(lsb_image)
            else:
                lsb_image = (self.image_array & 1) * 255
                axes[0, 1].imshow(lsb_image, cmap='gray')
            axes[0, 1].set_title('LSB Plane')
            axes[0, 1].axis('off')
            
            # Histogram
            if len(self.image_array.shape) == 3:
                colors = ['red', 'green', 'blue']
                for i in range(3):
                    hist, bins = np.histogram(self.image_array[:, :, i], bins=256, range=(0, 255))
                    axes[0, 2].plot(bins[:-1], hist, color=colors[i], alpha=0.7)
            else:
                hist, bins = np.histogram(self.image_array, bins=256, range=(0, 255))
                axes[0, 2].plot(bins[:-1], hist, color='black')
            axes[0, 2].set_title('Pixel Value Histogram')
            axes[0, 2].set_xlabel('Pixel Value')
            axes[0, 2].set_ylabel('Frequency')
            
            # Noise visualization (high-pass filter)
            if len(self.image_array.shape) == 3:
                gray = np.dot(self.image_array[...,:3], [0.2989, 0.5870, 0.1140])
            else:
                gray = self.image_array
            
            # Simple high-pass filter
            kernel = np.array([[-1, -1, -1], [-1, 8, -1], [-1, -1, -1]])
            from scipy import ndimage
            noise_map = ndimage.convolve(gray, kernel)
            axes[1, 0].imshow(noise_map, cmap='gray')
            axes[1, 0].set_title('Noise/Edge Map')
            axes[1, 0].axis('off')
            
            # Frequency domain
            f_transform = np.fft.fft2(gray)
            f_shift = np.fft.fftshift(f_transform)
            magnitude_spectrum = np.log(np.abs(f_shift) + 1)
            axes[1, 1].imshow(magnitude_spectrum, cmap='hot')
            axes[1, 1].set_title('Frequency Domain (Log)')
            axes[1, 1].axis('off')
            
            # Results summary
            axes[1, 2].axis('off')
            summary_text = "Analysis Results:\n\n"
            for result in self.results:
                status = "SUSPICIOUS" if result.is_suspicious else "NORMAL"
                summary_text += f"{result.test_name}:\n"
                summary_text += f"  Score: {result.score:.3f}\n"
                summary_text += f"  Status: {status}\n\n"
            
            axes[1, 2].text(0.1, 0.9, summary_text, transform=axes[1, 2].transAxes,
                          fontsize=10, verticalalignment='top', fontfamily='monospace')
            
            plt.tight_layout()
            
            # Save to memory buffer
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            
            # Encode as base64 for easy transport/display
            plot_data = base64.b64encode(buffer.getvalue()).decode()
            plt.close(fig)
            
            return plot_data
            
        except Exception as e:
            print(f"Error generating visual report: {e}")
            return None


def analyze_steganography(image_path: str) -> Dict[str, Any]:
    """Convenience function to run steganographic analysis on an image."""
    detector = SteganographyDetector(image_path)
    return detector.run_full_analysis()


if __name__ == '__main__':
    import sys
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    
    console = Console()
    
    if len(sys.argv) != 2:
        console.print("[red]Usage: python steganography.py <image_file>[/red]")
        sys.exit(1)
    
    image_path = sys.argv[1]
    if not Path(image_path).exists():
        console.print(f"[red]File not found: {image_path}[/red]")
        sys.exit(1)
    
    console.print(f"[bold blue]Analyzing steganographic content: {image_path}[/bold blue]")
    
    result = analyze_steganography(image_path)
    
    if 'error' in result:
        console.print(Panel(result['error'], title="[red]Error[/red]", border_style="red"))
        sys.exit(1)
    
    # Display overall results
    status_color = "red" if result['overall_suspicious'] else "green"
    status_text = "SUSPICIOUS" if result['overall_suspicious'] else "NORMAL"
    
    console.print(Panel(
        f"Overall Status: [{status_color}]{status_text}[/{status_color}]\n"
        f"Suspicious Tests: {result['suspicious_tests_count']}/{len(result['individual_results'])}\n"
        f"Average Score: {result['average_suspicion_score']:.3f}",
        title="[yellow]Analysis Summary[/yellow]"
    ))
    
    # Display detailed results
    table = Table(title="Detailed Analysis Results")
    table.add_column("Test", style="cyan")
    table.add_column("Score", style="yellow")
    table.add_column("Threshold", style="blue")
    table.add_column("Status", style="magenta")
    
    for test in result['individual_results']:
        status = "[red]SUSPICIOUS[/red]" if test['is_suspicious'] else "[green]NORMAL[/green]"
        table.add_row(
            test['test_name'],
            f"{test['score']:.3f}",
            f"{test['threshold']:.3f}",
            status
        )
    
    console.print(table)
    
    # Display recommendations
    if result['summary_recommendations']:
        console.print("\n[bold green]Recommendations:[/bold green]")
        for rec in result['summary_recommendations']:
            console.print(f"  • {rec}")
    
    console.print(f"\n[dim]Image Info: {result['image_info']['size']} pixels, {result['image_info']['mode']} mode[/dim]")
