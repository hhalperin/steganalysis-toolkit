#!/usr/bin/env python3
"""
AI-Enhanced Steganography Detection & Removal CLI
Command-line interface for the complete AI-enhanced forensics toolkit
"""

import sys
import os
from pathlib import Path
import argparse
import logging
from typing import List, Optional

# Add src directory to Python path
sys.path.insert(0, 'src')

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Import our enhanced analyzer
from core.ai_enhanced_analyzer import AIEnhancedAnalyzer

console = Console()


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('ai_stegano.log'),
            logging.StreamHandler(sys.stdout) if verbose else logging.NullHandler()
        ]
    )


def print_banner():
    """Print application banner."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║              🤖 AI-Enhanced Steganography Toolkit           ║
║                                                              ║
║  Advanced AI-powered detection and removal of steganographic ║
║  content in images, with focus on AI-generated patterns     ║
╚══════════════════════════════════════════════════════════════╝
    """
    console.print(banner, style="bold cyan")


def validate_files(file_paths: List[str]) -> List[str]:
    """Validate that input files exist and are images."""
    valid_files = []
    supported_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'}
    
    for file_path in file_paths:
        path = Path(file_path)
        
        if not path.exists():
            console.print(f"[red]❌ File not found: {file_path}[/red]")
            continue
        
        if path.suffix.lower() not in supported_extensions:
            console.print(f"[yellow]⚠️  Unsupported file type: {file_path} (skipping)[/yellow]")
            continue
        
        valid_files.append(str(path.absolute()))
    
    return valid_files


def cmd_analyze(args):
    """Handle analyze command."""
    
    console.print("\n[bold blue]🔍 AI-Enhanced Analysis Mode[/bold blue]")
    
    # Validate files
    valid_files = validate_files(args.files)
    if not valid_files:
        console.print("[red]No valid files to analyze[/red]")
        return 1
    
    # Create analyzer
    analyzer = AIEnhancedAnalyzer(
        models_dir=args.models_dir,
        use_ai=not args.no_ai,
        use_traditional=not args.no_traditional,
        console=console
    )
    
    try:
        if args.batch or len(valid_files) > 1:
            # Batch mode
            console.print(f"[cyan]Processing {len(valid_files)} files in batch mode...[/cyan]")
            results = analyzer.batch_analyze(valid_files, args.output or "assets/ai_analysis_results")
            
            # Summary
            high_risk_count = sum(1 for r in results if r.overall_risk_level in ['high', 'critical'])
            ai_detected_count = sum(1 for r in results if r.ai_detection_result and r.ai_detection_result.is_ai_generated)
            
            console.print(f"\n[bold green]✅ Batch Analysis Complete![/bold green]")
            console.print(f"Files processed: {len(results)}")
            console.print(f"High-risk files: {high_risk_count}")
            console.print(f"AI steganography detected: {ai_detected_count}")
            
        else:
            # Single file mode
            for file_path in valid_files:
                result = analyzer.analyze_image(file_path)
                analyzer.print_analysis_report(result)
                
                # Export individual report if requested
                if args.export:
                    import json
                    from dataclasses import asdict
                    
                    output_dir = Path(args.output or "assets/analysis_results")
                    output_dir.mkdir(parents=True, exist_ok=True)
                    
                    report_file = output_dir / f"{Path(file_path).stem}_report.json"
                    with open(report_file, 'w') as f:
                        json.dump(asdict(result), f, indent=2, default=str)
                    
                    console.print(f"[dim]Report saved: {report_file}[/dim]")
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Analysis interrupted[/yellow]")
        return 1
    except Exception as e:
        console.print(f"[red]Analysis failed: {e}[/red]")
        return 1
    
    return 0


def cmd_clean(args):
    """Handle clean command."""
    
    console.print("\n[bold green]🧼 AI-Enhanced Cleaning Mode[/bold green]")
    
    # Validate files
    valid_files = validate_files(args.files)
    if not valid_files:
        console.print("[red]No valid files to clean[/red]")
        return 1
    
    # Create analyzer
    analyzer = AIEnhancedAnalyzer(
        models_dir=args.models_dir,
        console=console
    )
    
    try:
        for file_path in valid_files:
            console.print(f"\n[cyan]Cleaning: {Path(file_path).name}[/cyan]")
            
            # Determine cleaning methods
            if args.method:
                methods = [args.method]
            else:
                methods = ["intelligent_adaptive", "content_preserving", "style_preserving"]
            
            # Perform cleaning
            result = analyzer.clean_image(
                file_path,
                args.output or "assets/cleaned_ai",
                methods=methods
            )
            
            # Display results
            console.print(f"[green]✅ Cleaning complete![/green]")
            console.print(f"Methods applied: {len(result.methods_used)}")
            console.print(f"Recommended method: [bold]{result.recommended_method}[/bold]")
            console.print(f"Best cleaned file: {result.recommended_file}")
            
            # Show quality metrics for recommended method
            if result.recommended_method in result.quality_metrics:
                metrics = result.quality_metrics[result.recommended_method]
                
                quality_table = Table(title=f"Quality Metrics: {result.recommended_method}")
                quality_table.add_column("Metric", style="cyan")
                quality_table.add_column("Value", style="green")
                
                for metric, value in metrics.items():
                    if isinstance(value, float):
                        quality_table.add_row(metric.replace('_', ' ').title(), f"{value:.3f}")
                    else:
                        quality_table.add_row(metric.replace('_', ' ').title(), str(value))
                
                console.print(quality_table)
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Cleaning interrupted[/yellow]")
        return 1
    except Exception as e:
        console.print(f"[red]Cleaning failed: {e}[/red]")
        return 1
    
    return 0


def cmd_models(args):
    """Handle models command."""
    
    console.print("\n[bold magenta]🤖 AI Model Management[/bold magenta]")
    
    from models.model_manager import ModelManager
    
    manager = ModelManager(args.models_dir)
    
    if args.action == 'list':
        # List available models
        available = manager.list_available_models()
        installed = manager.list_installed_models()
        
        console.print("\n[bold cyan]Available Models:[/bold cyan]")
        for model in available:
            status = "✅ INSTALLED" if model.name in installed else "⬇️  Available"
            size_mb = model.file_size / 1e6
            console.print(f"  • {model.name} v{model.version} ({size_mb:.1f} MB) - {status}")
            console.print(f"    {model.description}")
        
        if installed:
            console.print(f"\n[bold green]Installed Models: {len(installed)}[/bold green]")
        else:
            console.print("\n[yellow]No models installed[/yellow]")
    
    elif args.action == 'install':
        if not args.model:
            console.print("[red]Model name required for installation[/red]")
            return 1
        
        def progress_callback(progress, downloaded, total):
            console.print(f"Download: {progress:.1%} ({downloaded/1e6:.1f}/{total/1e6:.1f} MB)", end='\r')
        
        try:
            path = manager.install_model(args.model, progress_callback)
            console.print(f"\n[green]✅ Model installed: {path}[/green]")
        except Exception as e:
            console.print(f"\n[red]Installation failed: {e}[/red]")
            return 1
    
    elif args.action == 'uninstall':
        if not args.model:
            console.print("[red]Model name required for uninstallation[/red]")
            return 1
        
        try:
            manager.uninstall_model(args.model)
            console.print(f"[green]✅ Model uninstalled: {args.model}[/green]")
        except Exception as e:
            console.print(f"[red]Uninstallation failed: {e}[/red]")
            return 1
    
    elif args.action == 'status':
        status = manager.get_model_status()
        
        status_text = f"""Installed Models: {status['installed_models']}
Available Models: {status['available_models']}
Cache Size: {status['cache_size_mb']:.1f} MB
Total Storage: {status['storage_usage']['total_size_mb']:.1f} MB"""
        
        console.print(Panel(status_text, title="[magenta]Model Status[/magenta]"))
        
        if status['models']:
            model_table = Table(title="Model Details")
            model_table.add_column("Name", style="cyan")
            model_table.add_column("Version", style="yellow")
            model_table.add_column("Size (MB)", style="green")
            model_table.add_column("Status", style="magenta")
            
            for name, info in status['models'].items():
                status_icon = "✅" if info['valid'] and info['loadable'] else "❌"
                model_table.add_row(
                    name,
                    info['version'],
                    f"{info['file_size_mb']:.1f}",
                    f"{status_icon} {'Valid' if info['valid'] else 'Invalid'}"
                )
            
            console.print(model_table)
    
    return 0


def cmd_train(args):
    """Handle train command (for custom model training)."""
    
    console.print("\n[bold red]🎯 AI Model Training[/bold red]")
    console.print("[yellow]⚠️  Training requires significant computational resources[/yellow]")
    
    if not args.confirm:
        console.print("[red]Use --confirm flag to start training[/red]")
        return 1
    
    from models.training import TrainingPipeline, TrainingConfig
    
    config = TrainingConfig(
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        num_epochs=args.epochs,
        device="auto"
    )
    
    try:
        pipeline = TrainingPipeline(config, args.models_dir)
        console.print("[cyan]Starting training pipeline...[/cyan]")
        pipeline.full_training_pipeline(args.synthetic_samples)
        console.print("[green]✅ Training completed successfully![/green]")
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Training interrupted[/yellow]")
        return 1
    except Exception as e:
        console.print(f"[red]Training failed: {e}[/red]")
        return 1
    
    return 0


def main():
    """Main CLI entry point."""
    
    parser = argparse.ArgumentParser(
        description="AI-Enhanced Steganography Detection & Removal",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s analyze image.png --export
  %(prog)s analyze *.png --batch --output results/
  %(prog)s clean suspicious.png --method intelligent_adaptive
  %(prog)s models list
  %(prog)s models install steganography_detector_v1
        """
    )
    
    # Global options
    parser.add_argument("--models-dir", default="models/", help="Directory for AI models")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    parser.add_argument("--no-banner", action="store_true", help="Skip banner display")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze images for steganographic content")
    analyze_parser.add_argument("files", nargs="+", help="Image files to analyze")
    analyze_parser.add_argument("--output", "-o", help="Output directory for reports")
    analyze_parser.add_argument("--batch", action="store_true", help="Enable batch processing mode")
    analyze_parser.add_argument("--export", action="store_true", help="Export detailed JSON reports")
    analyze_parser.add_argument("--no-ai", action="store_true", help="Disable AI analysis")
    analyze_parser.add_argument("--no-traditional", action="store_true", help="Disable traditional analysis")
    
    # Clean command
    clean_parser = subparsers.add_parser("clean", help="Remove steganographic content from images")
    clean_parser.add_argument("files", nargs="+", help="Image files to clean")
    clean_parser.add_argument("--output", "-o", help="Output directory for cleaned images")
    clean_parser.add_argument("--method", choices=[
        "intelligent_adaptive", "content_preserving", "style_preserving", 
        "regional_cleaning", "adversarial_cleaning"
    ], help="Specific cleaning method to use")
    
    # Models command
    models_parser = subparsers.add_parser("models", help="Manage AI models")
    models_parser.add_argument("action", choices=["list", "install", "uninstall", "status"], 
                              help="Model management action")
    models_parser.add_argument("--model", help="Model name (for install/uninstall)")
    
    # Train command (advanced)
    train_parser = subparsers.add_parser("train", help="Train custom AI models")
    train_parser.add_argument("--confirm", action="store_true", help="Confirm training start")
    train_parser.add_argument("--epochs", type=int, default=50, help="Number of training epochs")
    train_parser.add_argument("--batch-size", type=int, default=8, help="Training batch size")
    train_parser.add_argument("--learning-rate", type=float, default=0.0001, help="Learning rate")
    train_parser.add_argument("--synthetic-samples", type=int, default=10000, help="Number of synthetic samples")
    
    args = parser.parse_args()
    
    # Setup
    setup_logging(args.verbose)
    
    if not args.no_banner:
        print_banner()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Route to command handlers
    try:
        if args.command == "analyze":
            return cmd_analyze(args)
        elif args.command == "clean":
            return cmd_clean(args)
        elif args.command == "models":
            return cmd_models(args)
        elif args.command == "train":
            return cmd_train(args)
        else:
            console.print(f"[red]Unknown command: {args.command}[/red]")
            return 1
    
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

