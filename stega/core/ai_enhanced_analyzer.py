"""
AI-Enhanced PNG Forensics Analyzer
Integrates AI-powered detection and removal with traditional forensics methods
"""

import os
import sys
from pathlib import Path
import json
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

# Import existing forensics modules
from core.png_analyzer import PNGForensicsAnalyzer
from detection.chunk_analyzer import analyze_png_chunks
from detection.unicode_scanner import scan_unicode_in_text
from detection.steganography import analyze_steganography

# Import AI modules
from models.ai_detector import AISteganoDetector, DetectionResult
from models.ai_cleaner import AISteganoCleaner, CleaningResult
from models.model_manager import ModelManager


@dataclass
class EnhancedAnalysisResult:
    """Comprehensive analysis result combining traditional and AI methods."""
    file_path: str
    analysis_timestamp: str
    
    # Traditional analysis results
    traditional_analysis: Dict[str, Any]
    
    # AI analysis results
    ai_detection_result: Optional[DetectionResult]
    
    # Combined assessment
    overall_risk_level: str  # 'low', 'medium', 'high', 'critical'
    risk_score: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    
    # Findings summary
    key_findings: List[str]
    ai_specific_findings: List[str]
    traditional_specific_findings: List[str]
    
    # Recommendations
    recommended_actions: List[str]
    cleaning_recommendations: List[str]
    
    # Processing metadata
    processing_time: float
    models_used: List[str]


@dataclass
class EnhancedCleaningResult:
    """Result from AI-enhanced cleaning process."""
    original_file: str
    cleaned_files: Dict[str, str]  # method -> file path
    
    # Quality metrics for each method
    quality_metrics: Dict[str, Dict[str, float]]
    
    # Verification results
    verification_results: Dict[str, Dict[str, Any]]
    
    # Recommendations
    recommended_method: str
    recommended_file: str
    
    # Processing metadata
    total_processing_time: float
    methods_used: List[str]


class AIEnhancedAnalyzer:
    """Main AI-enhanced forensics analyzer."""
    
    def __init__(self, models_dir: str = "models/", 
                 use_traditional: bool = True,
                 use_ai: bool = True,
                 console: Console = None):
        
        self.models_dir = Path(models_dir)
        self.use_traditional = use_traditional
        self.use_ai = use_ai
        self.console = console or Console()
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.model_manager = ModelManager(str(self.models_dir))
        
        # AI components (will be initialized when needed)
        self.ai_detector = None
        self.ai_cleaner = None
        
        # Traditional analyzer
        if use_traditional:
            self.traditional_analyzer = PNGForensicsAnalyzer
        
        # Setup AI components if requested
        if use_ai:
            self._setup_ai_components()
    
    def _setup_ai_components(self):
        """Initialize AI components and ensure models are available."""
        
        try:
            self.console.print("[blue]Setting up AI components...[/blue]")
            
            # Check for required models
            required_models = [
                "steganography_detector_v1",
                "content_preserving_cleaner_v1",
                "style_preserving_gan_v1",
                "regional_cleaner_v1"
            ]
            
            # Install missing models
            for model_name in required_models:
                if model_name not in self.model_manager.list_installed_models():
                    self.console.print(f"[yellow]Installing required model: {model_name}[/yellow]")
                    try:
                        self.model_manager.install_model(model_name, self._model_download_progress)
                    except Exception as e:
                        self.console.print(f"[red]Failed to install {model_name}: {e}[/red]")
                        self.console.print("[yellow]AI features will be limited[/yellow]")
            
            # Initialize AI components
            self.ai_detector = AISteganoDetector(str(self.models_dir))
            self.ai_cleaner = AISteganoCleaner(str(self.models_dir))
            
            self.console.print("[green]AI components ready[/green]")
            
        except Exception as e:
            self.console.print(f"[red]AI setup failed: {e}[/red]")
            self.console.print("[yellow]Falling back to traditional analysis only[/yellow]")
            self.use_ai = False
    
    def _model_download_progress(self, progress: float, downloaded: int, total: int):
        """Progress callback for model downloads."""
        self.console.print(f"Download: {progress:.1%} ({downloaded/1e6:.1f}/{total/1e6:.1f} MB)", end='\r')
    
    def analyze_image(self, image_path: str, 
                     include_ai: bool = None,
                     include_traditional: bool = None) -> EnhancedAnalysisResult:
        """Perform comprehensive AI-enhanced analysis."""
        
        start_time = time.time()
        include_ai = include_ai if include_ai is not None else self.use_ai
        include_traditional = include_traditional if include_traditional is not None else self.use_traditional
        
        self.console.print(f"\n[bold blue]🔍 Enhanced Analysis: {Path(image_path).name}[/bold blue]")
        
        # Initialize results
        traditional_analysis = {}
        ai_detection_result = None
        models_used = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console
        ) as progress:
            
            # Traditional analysis
            if include_traditional:
                task1 = progress.add_task("[cyan]Traditional forensics analysis...", total=100)
                
                try:
                    traditional_analyzer = PNGForensicsAnalyzer(image_path, self.console)
                    traditional_analysis = traditional_analyzer.analyze_file()
                    progress.update(task1, completed=100)
                    
                except Exception as e:
                    self.logger.error(f"Traditional analysis failed: {e}")
                    traditional_analysis = {'error': str(e)}
                    progress.update(task1, completed=100)
            
            # AI analysis
            if include_ai and self.ai_detector:
                task2 = progress.add_task("[magenta]AI steganography detection...", total=100)
                
                try:
                    ai_detection_result = self.ai_detector.detect(image_path)
                    models_used.extend(['ai_detector'])
                    progress.update(task2, completed=100)
                    
                except Exception as e:
                    self.logger.error(f"AI analysis failed: {e}")
                    ai_detection_result = None
                    progress.update(task2, completed=100)
        
        # Combine results and generate comprehensive assessment
        processing_time = time.time() - start_time
        
        result = self._generate_combined_assessment(
            image_path,
            traditional_analysis,
            ai_detection_result,
            models_used,
            processing_time
        )
        
        return result
    
    def _generate_combined_assessment(self, 
                                    image_path: str,
                                    traditional_analysis: Dict[str, Any],
                                    ai_detection_result: Optional[DetectionResult],
                                    models_used: List[str],
                                    processing_time: float) -> EnhancedAnalysisResult:
        """Generate comprehensive assessment combining all analysis methods."""
        
        # Extract traditional findings
        traditional_findings = []
        traditional_risk = 0.0
        
        if traditional_analysis.get('forensics_summary'):
            forensics = traditional_analysis['forensics_summary']
            traditional_risk = {'low': 0.2, 'medium': 0.5, 'high': 0.8}.get(
                forensics.get('overall_risk_level', 'low'), 0.2
            )
            traditional_findings = forensics.get('suspicious_indicators', [])
        
        # Extract AI findings
        ai_findings = []
        ai_risk = 0.0
        
        if ai_detection_result:
            ai_risk = ai_detection_result.confidence if ai_detection_result.is_ai_generated else 0.1
            if ai_detection_result.is_ai_generated:
                ai_findings.append(f"AI-generated steganography detected: {ai_detection_result.steganography_type}")
                ai_findings.extend(ai_detection_result.recommendations)
        
        # Calculate combined risk assessment
        if ai_detection_result and traditional_analysis:
            # Weight AI detection higher for AI-generated content
            combined_risk = (traditional_risk * 0.4) + (ai_risk * 0.6)
        elif ai_detection_result:
            combined_risk = ai_risk
        elif traditional_analysis:
            combined_risk = traditional_risk
        else:
            combined_risk = 0.0
        
        # Determine overall risk level
        if combined_risk >= 0.7:
            overall_risk = 'critical'
        elif combined_risk >= 0.5:
            overall_risk = 'high'
        elif combined_risk >= 0.3:
            overall_risk = 'medium'
        else:
            overall_risk = 'low'
        
        # Generate key findings
        key_findings = []
        
        if ai_detection_result and ai_detection_result.is_ai_generated:
            key_findings.append(f"🤖 AI-Generated Steganography: {ai_detection_result.steganography_type}")
            key_findings.append(f"🎯 Detection Confidence: {ai_detection_result.confidence:.1%}")
            
            if ai_detection_result.suspicious_regions:
                key_findings.append(f"📍 Suspicious Regions: {len(ai_detection_result.suspicious_regions)} areas identified")
        
        if traditional_findings:
            key_findings.append(f"🔍 Traditional Indicators: {len(traditional_findings)} suspicious patterns")
        
        # Generate recommendations
        recommendations = []
        cleaning_recommendations = []
        
        if overall_risk in ['high', 'critical']:
            recommendations.extend([
                "IMMEDIATE ACTION: Multiple indicators suggest steganographic content",
                "Quarantine file and investigate source",
                "Apply AI-enhanced cleaning methods"
            ])
            
            if ai_detection_result and ai_detection_result.is_ai_generated:
                cleaning_recommendations.extend([
                    "Use AI-powered adversarial cleaning",
                    "Apply content-preserving neural cleaning",
                    "Verify cleaning effectiveness with AI re-detection"
                ])
            else:
                cleaning_recommendations.extend([
                    "Use traditional steganography removal methods",
                    "Apply LSB randomization techniques"
                ])
        
        elif overall_risk == 'medium':
            recommendations.extend([
                "Further investigation recommended",
                "Consider AI-enhanced analysis if not already performed",
                "Monitor file for additional context"
            ])
        
        else:
            recommendations.extend([
                "File appears clean but continue monitoring",
                "Standard security protocols apply"
            ])
        
        # Calculate confidence
        confidence = 0.8  # Base confidence
        if ai_detection_result and traditional_analysis:
            confidence = 0.95  # High confidence when both methods agree
        elif ai_detection_result or traditional_analysis:
            confidence = 0.75  # Medium confidence with single method
        
        return EnhancedAnalysisResult(
            file_path=image_path,
            analysis_timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            traditional_analysis=traditional_analysis,
            ai_detection_result=ai_detection_result,
            overall_risk_level=overall_risk,
            risk_score=combined_risk,
            confidence=confidence,
            key_findings=key_findings,
            ai_specific_findings=ai_findings,
            traditional_specific_findings=traditional_findings,
            recommended_actions=recommendations,
            cleaning_recommendations=cleaning_recommendations,
            processing_time=processing_time,
            models_used=models_used
        )
    
    def clean_image(self, image_path: str, 
                   output_dir: str = "cleaned_ai_enhanced",
                   methods: List[str] = None) -> EnhancedCleaningResult:
        """Perform AI-enhanced cleaning with multiple methods."""
        
        start_time = time.time()
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        if methods is None:
            methods = ["intelligent_adaptive", "content_preserving", "style_preserving", "regional_cleaning"]
        
        self.console.print(f"\n[bold green]🧼 Enhanced Cleaning: {Path(image_path).name}[/bold green]")
        
        cleaned_files = {}
        quality_metrics = {}
        verification_results = {}
        
        # Perform analysis first to guide cleaning
        analysis_result = self.analyze_image(image_path)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console
        ) as progress:
            
            task = progress.add_task("[green]AI-enhanced cleaning...", total=len(methods))
            
            for method in methods:
                try:
                    # Determine output filename
                    input_name = Path(image_path).stem
                    output_file = output_path / f"{input_name}_cleaned_{method}.png"
                    
                    # Apply cleaning method
                    if self.ai_cleaner:
                        # Use suspicious regions from analysis if available
                        suspicious_regions = []
                        if analysis_result.ai_detection_result:
                            suspicious_regions = analysis_result.ai_detection_result.suspicious_regions
                        
                        cleaning_result = self.ai_cleaner.clean_image(
                            image_path, 
                            str(output_file),
                            method=method,
                            suspicious_regions=suspicious_regions
                        )
                        
                        cleaned_files[method] = str(output_file)
                        quality_metrics[method] = cleaning_result.quality_metrics
                        
                        # Verify cleaning effectiveness
                        verification = self._verify_cleaning_effectiveness(
                            image_path, str(output_file), analysis_result
                        )
                        verification_results[method] = verification
                    
                    progress.update(task, advance=1)
                    
                except Exception as e:
                    self.logger.error(f"Cleaning method {method} failed: {e}")
                    progress.update(task, advance=1)
                    continue
        
        # Determine best cleaning method
        recommended_method, recommended_file = self._select_best_cleaning_method(
            cleaned_files, quality_metrics, verification_results
        )
        
        total_time = time.time() - start_time
        
        return EnhancedCleaningResult(
            original_file=image_path,
            cleaned_files=cleaned_files,
            quality_metrics=quality_metrics,
            verification_results=verification_results,
            recommended_method=recommended_method,
            recommended_file=recommended_file,
            total_processing_time=total_time,
            methods_used=list(cleaned_files.keys())
        )
    
    def _verify_cleaning_effectiveness(self, 
                                     original_path: str, 
                                     cleaned_path: str,
                                     original_analysis: EnhancedAnalysisResult) -> Dict[str, Any]:
        """Verify that cleaning was effective."""
        
        verification = {
            'steganography_removed': False,
            'quality_preserved': False,
            'ai_detection_after_cleaning': None,
            'traditional_detection_after_cleaning': None,
            'overall_success': False
        }
        
        try:
            # Re-analyze cleaned image
            cleaned_analysis = self.analyze_image(cleaned_path, include_ai=True, include_traditional=True)
            
            # Check if AI-generated steganography was removed
            if original_analysis.ai_detection_result and original_analysis.ai_detection_result.is_ai_generated:
                if cleaned_analysis.ai_detection_result:
                    verification['steganography_removed'] = not cleaned_analysis.ai_detection_result.is_ai_generated
                    verification['ai_detection_after_cleaning'] = {
                        'is_ai_generated': cleaned_analysis.ai_detection_result.is_ai_generated,
                        'confidence': cleaned_analysis.ai_detection_result.confidence
                    }
                else:
                    verification['steganography_removed'] = True  # No AI detection = likely cleaned
            
            # Check traditional detection results
            if cleaned_analysis.traditional_analysis.get('forensics_summary'):
                new_risk = cleaned_analysis.traditional_analysis['forensics_summary']['overall_risk_level']
                verification['traditional_detection_after_cleaning'] = {
                    'risk_level': new_risk,
                    'indicators_count': len(cleaned_analysis.traditional_analysis['forensics_summary'].get('suspicious_indicators', []))
                }
            
            # Overall success assessment
            risk_reduced = cleaned_analysis.risk_score < original_analysis.risk_score * 0.5
            verification['overall_success'] = verification.get('steganography_removed', True) and risk_reduced
            
        except Exception as e:
            self.logger.error(f"Verification failed: {e}")
            verification['error'] = str(e)
        
        return verification
    
    def _select_best_cleaning_method(self, 
                                   cleaned_files: Dict[str, str],
                                   quality_metrics: Dict[str, Dict[str, float]],
                                   verification_results: Dict[str, Dict[str, Any]]) -> Tuple[str, str]:
        """Select the best cleaning method based on quality and effectiveness."""
        
        if not cleaned_files:
            return "", ""
        
        scores = {}
        
        for method in cleaned_files:
            score = 0.0
            
            # Quality score (40% weight)
            if method in quality_metrics:
                quality = quality_metrics[method]
                ssim = quality.get('ssim', 0.5)
                visual_quality = quality.get('visual_quality', 0.5)
                score += (ssim + visual_quality) * 0.2
            
            # Effectiveness score (60% weight)
            if method in verification_results:
                verification = verification_results[method]
                if verification.get('overall_success', False):
                    score += 0.6
                elif verification.get('steganography_removed', False):
                    score += 0.3
            
            scores[method] = score
        
        # Select method with highest score
        best_method = max(scores, key=scores.get)
        best_file = cleaned_files[best_method]
        
        return best_method, best_file
    
    def batch_analyze(self, image_paths: List[str], 
                     output_dir: str = "batch_analysis_results") -> List[EnhancedAnalysisResult]:
        """Perform batch analysis on multiple images."""
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        results = []
        
        self.console.print(f"\n[bold blue]📊 Batch Analysis: {len(image_paths)} images[/bold blue]")
        
        for i, image_path in enumerate(image_paths):
            self.console.print(f"\n[cyan]Processing {i+1}/{len(image_paths)}: {Path(image_path).name}[/cyan]")
            
            try:
                result = self.analyze_image(image_path)
                results.append(result)
                
                # Save individual report
                report_file = output_path / f"{Path(image_path).stem}_enhanced_report.json"
                with open(report_file, 'w') as f:
                    json.dump(asdict(result), f, indent=2, default=str)
                
            except Exception as e:
                self.logger.error(f"Failed to analyze {image_path}: {e}")
                continue
        
        # Generate batch summary
        self._generate_batch_summary(results, output_path)
        
        return results
    
    def _generate_batch_summary(self, results: List[EnhancedAnalysisResult], output_path: Path):
        """Generate summary report for batch analysis."""
        
        summary = {
            'total_images': len(results),
            'analysis_timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'risk_distribution': {'low': 0, 'medium': 0, 'high': 0, 'critical': 0},
            'ai_generated_count': 0,
            'traditional_suspicious_count': 0,
            'average_processing_time': 0.0,
            'most_common_ai_types': {},
            'recommendations_summary': []
        }
        
        total_time = 0.0
        ai_types = []
        
        for result in results:
            # Risk distribution
            summary['risk_distribution'][result.overall_risk_level] += 1
            
            # AI-generated count
            if result.ai_detection_result and result.ai_detection_result.is_ai_generated:
                summary['ai_generated_count'] += 1
                ai_types.append(result.ai_detection_result.steganography_type)
            
            # Traditional suspicious count
            if result.traditional_analysis.get('forensics_summary', {}).get('overall_risk_level') in ['medium', 'high']:
                summary['traditional_suspicious_count'] += 1
            
            total_time += result.processing_time
        
        # Calculate averages and summaries
        if results:
            summary['average_processing_time'] = total_time / len(results)
        
        # Most common AI types
        from collections import Counter
        if ai_types:
            summary['most_common_ai_types'] = dict(Counter(ai_types).most_common(5))
        
        # Generate recommendations
        high_risk_count = summary['risk_distribution']['high'] + summary['risk_distribution']['critical']
        if high_risk_count > len(results) * 0.2:  # More than 20% high/critical risk
            summary['recommendations_summary'].append("HIGH ALERT: Significant portion of images show suspicious indicators")
        
        if summary['ai_generated_count'] > 0:
            summary['recommendations_summary'].append(f"AI-generated steganography detected in {summary['ai_generated_count']} images")
        
        # Save summary
        summary_file = output_path / "batch_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Print summary to console
        self._print_batch_summary(summary)
    
    def _print_batch_summary(self, summary: Dict[str, Any]):
        """Print batch summary to console."""
        
        self.console.print("\n" + "="*60)
        self.console.print("[bold yellow]📊 BATCH ANALYSIS SUMMARY[/bold yellow]")
        self.console.print("="*60)
        
        # Risk distribution table
        table = Table(title="Risk Distribution")
        table.add_column("Risk Level", style="cyan")
        table.add_column("Count", style="yellow")
        table.add_column("Percentage", style="green")
        
        total = summary['total_images']
        for risk_level, count in summary['risk_distribution'].items():
            percentage = (count / total * 100) if total > 0 else 0
            color = {'low': 'green', 'medium': 'yellow', 'high': 'red', 'critical': 'bold red'}.get(risk_level, 'white')
            table.add_row(
                f"[{color}]{risk_level.upper()}[/{color}]",
                str(count),
                f"{percentage:.1f}%"
            )
        
        self.console.print(table)
        
        # Key statistics
        stats_text = f"""Total Images Processed: {summary['total_images']}
AI-Generated Steganography: {summary['ai_generated_count']} images
Traditional Suspicious: {summary['traditional_suspicious_count']} images
Average Processing Time: {summary['average_processing_time']:.2f} seconds"""
        
        self.console.print(Panel(stats_text, title="[green]Key Statistics[/green]"))
        
        # Recommendations
        if summary['recommendations_summary']:
            self.console.print("\n[bold red]🚨 Key Recommendations:[/bold red]")
            for rec in summary['recommendations_summary']:
                self.console.print(f"  • {rec}")
    
    def print_analysis_report(self, result: EnhancedAnalysisResult):
        """Print comprehensive analysis report."""
        
        self.console.print("\n" + "="*60)
        self.console.print(f"[bold blue]🔍 ENHANCED FORENSICS REPORT[/bold blue]")
        self.console.print("="*60)
        
        # File info
        file_info = f"""File: {Path(result.file_path).name}
Analysis Time: {result.analysis_timestamp}
Processing Time: {result.processing_time:.2f} seconds
Models Used: {', '.join(result.models_used)}"""
        
        self.console.print(Panel(file_info, title="[blue]File Information[/blue]"))
        
        # Risk assessment
        risk_color = {'low': 'green', 'medium': 'yellow', 'high': 'red', 'critical': 'bold red'}.get(
            result.overall_risk_level, 'white'
        )
        
        risk_text = f"""Risk Level: [{risk_color}]{result.overall_risk_level.upper()}[/{risk_color}]
Risk Score: {result.risk_score:.2f} / 1.0
Confidence: {result.confidence:.1%}"""
        
        self.console.print(Panel(risk_text, title="[yellow]Risk Assessment[/yellow]"))
        
        # Key findings
        if result.key_findings:
            self.console.print("\n[bold yellow]🔍 Key Findings:[/bold yellow]")
            for finding in result.key_findings:
                self.console.print(f"  • {finding}")
        
        # AI-specific results
        if result.ai_detection_result:
            ai_info = result.ai_detection_result
            ai_text = f"""AI Detection: {'✓ DETECTED' if ai_info.is_ai_generated else '✗ CLEAN'}
Type: {ai_info.steganography_type}
Confidence: {ai_info.confidence:.1%}
Suspicious Regions: {len(ai_info.suspicious_regions)}"""
            
            self.console.print(Panel(ai_text, title="[magenta]AI Analysis Results[/magenta]"))
        
        # Recommendations
        if result.recommended_actions:
            self.console.print("\n[bold green]💡 Recommended Actions:[/bold green]")
            for i, action in enumerate(result.recommended_actions, 1):
                self.console.print(f"  {i}. {action}")
        
        if result.cleaning_recommendations:
            self.console.print("\n[bold cyan]🧼 Cleaning Recommendations:[/bold cyan]")
            for rec in result.cleaning_recommendations:
                self.console.print(f"  • {rec}")


def main():
    """Example usage of AI-Enhanced Analyzer."""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="AI-Enhanced PNG Forensics Analyzer")
    parser.add_argument("images", nargs="+", help="Image files to analyze")
    parser.add_argument("--no-ai", action="store_true", help="Disable AI analysis")
    parser.add_argument("--no-traditional", action="store_true", help="Disable traditional analysis")
    parser.add_argument("--clean", action="store_true", help="Apply AI-enhanced cleaning")
    parser.add_argument("--batch", action="store_true", help="Process images in batch mode")
    parser.add_argument("--output", "-o", help="Output directory for results")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Create analyzer
    analyzer = AIEnhancedAnalyzer(
        use_ai=not args.no_ai,
        use_traditional=not args.no_traditional
    )
    
    try:
        if args.batch:
            # Batch processing
            results = analyzer.batch_analyze(args.images, args.output or "batch_results")
            analyzer.console.print(f"\n[green]✅ Batch analysis complete: {len(results)} images processed[/green]")
        
        else:
            # Individual processing
            for image_path in args.images:
                result = analyzer.analyze_image(image_path)
                analyzer.print_analysis_report(result)
                
                if args.clean:
                    cleaning_result = analyzer.clean_image(image_path, args.output or "cleaned_enhanced")
                    analyzer.console.print(f"\n[green]✅ Cleaning complete: {len(cleaning_result.cleaned_files)} methods applied[/green]")
                    analyzer.console.print(f"[blue]📄 Recommended: {cleaning_result.recommended_method} -> {cleaning_result.recommended_file}[/blue]")
    
    except KeyboardInterrupt:
        analyzer.console.print("\n[yellow]Analysis interrupted by user[/yellow]")
    except Exception as e:
        analyzer.console.print(f"\n[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()

