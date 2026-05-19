"""
Example Usage of PNG Forensics Tools
Demonstrates comprehensive PNG analysis, steganography detection, and extraction
"""

import os
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import json

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from stega.core.png_analyzer import PNGForensicsAnalyzer
from stega.detection.chunk_analyzer import PNGChunkAnalyzer, analyze_png_chunks
from stega.detection.unicode_scanner import scan_unicode_in_text
from stega.detection.steganography import analyze_steganography

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import track

console = Console()


def create_sample_images():
    """Create sample PNG images for testing (clean and with hidden data)."""

    console.print("[bold blue]Creating sample PNG images...[/bold blue]")

    # Create clean sample image
    img_clean = Image.new('RGB', (200, 150), color='lightblue')
    draw = ImageDraw.Draw(img_clean)
    draw.rectangle([50, 50, 150, 100], fill='white', outline='black', width=2)
    draw.text((75, 70), "Clean PNG", fill='black')
    img_clean.save('sample_clean.png')

    # Create sample with LSB steganography (simple example)
    img_stego = img_clean.copy()
    pixels = np.array(img_stego)

    # Hide simple message "HIDDEN" in LSBs of red channel
    message = "HIDDEN"
    message_bits = ''.join(format(ord(c), '08b') for c in message) + '0' * 8  # Add terminator

    # Modify LSBs of red channel
    flat_pixels = pixels[:,:,0].flatten()
    for i, bit in enumerate(message_bits[:len(flat_pixels)]):
        if i < len(flat_pixels):
            flat_pixels[i] = (flat_pixels[i] & 0xFE) | int(bit)

    pixels[:,:,0] = flat_pixels.reshape(pixels[:,:,0].shape)
    img_stego_final = Image.fromarray(pixels)
    img_stego_final.save('sample_with_lsb.png')

    # Create sample with suspicious Unicode in metadata
    img_unicode = img_clean.copy()

    # Add metadata with hidden Unicode characters
    from PIL.PngImagePlugin import PngInfo
    metadata = PngInfo()

    # Normal metadata
    metadata.add_text("Title", "Sample Image")
    metadata.add_text("Author", "research-sample")

    # Suspicious metadata with invisible Unicode
    suspicious_text = "Normal text\u200BHidden\u200CContent\u200DHere\uE200Secret"
    metadata.add_text("Description", suspicious_text)

    # Private use area characters
    private_chars = "Data: " + ''.join(chr(0xE000 + i) for i in range(10))
    metadata.add_text("Keywords", private_chars)

    img_unicode.save('sample_with_unicode.png', pnginfo=metadata)

    console.print("[green]✓ Created sample_clean.png[/green]")
    console.print("[green]✓ Created sample_with_lsb.png[/green]")
    console.print("[green]✓ Created sample_with_unicode.png[/green]")


def example_basic_analysis():
    """Example: Basic PNG analysis."""

    console.print("\n[bold yellow]Example 1: Basic PNG Analysis[/bold yellow]")
    console.print("=" * 50)

    test_files = ['sample_clean.png', 'sample_with_lsb.png', 'sample_with_unicode.png']

    for file_name in test_files:
        if not Path(file_name).exists():
            console.print(f"[red]File not found: {file_name}. Run create_sample_images() first.[/red]")
            continue

        console.print(f"\n[cyan]Analyzing: {file_name}[/cyan]")

        # Quick analysis using convenience function
        chunk_results = analyze_png_chunks(file_name)

        # Display summary
        console.print(f"Total chunks: {chunk_results['total_chunks']}")
        console.print(f"Custom chunks: {len(chunk_results['custom_chunks'])}")
        console.print(f"Suspicious findings: {len(chunk_results['findings'])}")

        if chunk_results['findings']:
            for finding in chunk_results['findings'][:3]:  # Show first 3 findings
                console.print(f"  • {finding['message']}")

        if chunk_results['text_content']:
            console.print("Text content found:")
            for text in chunk_results['text_content'][:2]:  # Show first 2 text items
                console.print(f"  • {text['chunk_type']}: {text['content'][:50]}...")


def example_steganography_detection():
    """Example: Steganography detection."""

    console.print("\n[bold yellow]Example 2: Steganography Detection[/bold yellow]")
    console.print("=" * 50)

    test_files = ['sample_clean.png', 'sample_with_lsb.png']

    for file_name in test_files:
        if not Path(file_name).exists():
            console.print(f"[red]File not found: {file_name}[/red]")
            continue

        console.print(f"\n[cyan]Steganography analysis: {file_name}[/cyan]")

        results = analyze_steganography(file_name)

        if 'error' in results:
            console.print(f"[red]Error: {results['error']}[/red]")
            continue

        # Create summary table
        table = Table(title=f"Steganography Results: {file_name}")
        table.add_column("Test", style="cyan")
        table.add_column("Score", style="yellow")
        table.add_column("Status", style="magenta")

        for test in results['individual_results']:
            status = "[red]SUSPICIOUS[/red]" if test['is_suspicious'] else "[green]NORMAL[/green]"
            table.add_row(
                test['test_name'],
                f"{test['score']:.3f}",
                status
            )

        console.print(table)

        overall_status = "[red]SUSPICIOUS[/red]" if results['overall_suspicious'] else "[green]CLEAN[/green]"
        console.print(f"Overall assessment: {overall_status}")


def example_unicode_analysis():
    """Example: Unicode analysis of text metadata."""

    console.print("\n[bold yellow]Example 3: Unicode Analysis[/bold yellow]")
    console.print("=" * 50)

    if not Path('sample_with_unicode.png').exists():
        console.print("[red]File not found: sample_with_unicode.png[/red]")
        return

    # Extract text content from PNG
    analyzer = PNGChunkAnalyzer(Path('sample_with_unicode.png'))
    analyzer.parse_chunks()

    console.print("Text chunks found:")

    for chunk in analyzer.chunks:
        text_content = chunk.get_text_content()
        if text_content:
            console.print(f"\n[cyan]Chunk: {chunk.chunk_type.decode()}[/cyan]")
            console.print(f"Content: {repr(text_content)}")

            # Analyze Unicode
            unicode_results = scan_unicode_in_text(text_content)

            if unicode_results['suspicious_characters']:
                console.print(f"[red]Suspicious Unicode characters found: {len(unicode_results['suspicious_characters'])}[/red]")

                # Display first few suspicious characters
                for char_info in unicode_results['suspicious_characters'][:3]:
                    console.print(f"  • U+{char_info['codepoint'][2:]} ({char_info['name']}) at position {char_info['position']}")

            if unicode_results['patterns']:
                console.print(f"[yellow]Suspicious patterns detected: {len(unicode_results['patterns'])}[/yellow]")
                for pattern in unicode_results['patterns']:
                    console.print(f"  • {pattern['type']}: {pattern['description']}")


def example_comprehensive_analysis():
    """Example: Comprehensive analysis using the main analyzer."""

    console.print("\n[bold yellow]Example 4: Comprehensive Forensics Analysis[/bold yellow]")
    console.print("=" * 50)

    test_files = ['sample_with_unicode.png', 'sample_with_lsb.png']

    for file_name in test_files:
        if not Path(file_name).exists():
            console.print(f"[red]File not found: {file_name}[/red]")
            continue

        console.print(f"\n[bold blue]🔍 Comprehensive Analysis: {file_name}[/bold blue]")

        # Create analyzer instance
        analyzer = PNGForensicsAnalyzer(file_name, console)

        # Run full analysis
        results = analyzer.analyze_file()

        if 'error' in results:
            console.print(f"[red]Analysis failed: {results['error']}[/red]")
            continue

        # Print summary report
        analyzer.print_summary_report()

        # Export detailed report
        report_file = f"{Path(file_name).stem}_analysis.json"
        analyzer.export_report(report_file, 'json')
        console.print(f"[dim]Detailed report saved to: {report_file}[/dim]")


def example_manual_extraction():
    """Example: Manual LSB data extraction."""

    console.print("\n[bold yellow]Example 5: Manual LSB Extraction[/bold yellow]")
    console.print("=" * 50)

    if not Path('sample_with_lsb.png').exists():
        console.print("[red]File not found: sample_with_lsb.png[/red]")
        return

    # Manual LSB extraction
    img = Image.open('sample_with_lsb.png')
    pixels = np.array(img)

    # Extract LSBs from red channel
    red_channel = pixels[:, :, 0]
    lsb_bits = red_channel & 1  # Extract LSBs

    console.print(f"Image size: {img.size}")
    console.print(f"Total pixels: {red_channel.size}")
    console.print(f"LSB pattern (first 64 bits): {''.join(map(str, lsb_bits.flatten()[:64]))}")

    # Convert LSBs to bytes
    lsb_flat = lsb_bits.flatten()
    extracted_bytes = []

    for i in range(0, len(lsb_flat), 8):
        if i + 8 <= len(lsb_flat):
            byte_val = sum(lsb_flat[i+j] << j for j in range(8))
            extracted_bytes.append(byte_val)

    extracted_data = bytes(extracted_bytes)

    # Try to find the hidden message
    try:
        # Look for printable ASCII sequences
        text_parts = []
        current_text = []

        for byte in extracted_data[:100]:  # Check first 100 bytes
            if 32 <= byte <= 126:  # Printable ASCII
                current_text.append(chr(byte))
            else:
                if current_text and len(current_text) >= 3:  # At least 3 chars
                    text_parts.append(''.join(current_text))
                current_text = []

        if current_text and len(current_text) >= 3:
            text_parts.append(''.join(current_text))

        if text_parts:
            console.print(f"[green]Extracted text: {text_parts}[/green]")
        else:
            console.print("[yellow]No readable text found in LSB data[/yellow]")

    except Exception as e:
        console.print(f"[red]Extraction error: {e}[/red]")

    # Show raw bytes (first 20)
    console.print(f"Raw extracted bytes (first 20): {extracted_data[:20].hex()}")


def example_batch_processing():
    """Example: Batch processing multiple files."""

    console.print("\n[bold yellow]Example 6: Batch Processing[/bold yellow]")
    console.print("=" * 50)

    png_files = list(Path('.').glob('*.png'))

    if not png_files:
        console.print("[yellow]No PNG files found in current directory[/yellow]")
        return

    console.print(f"Found {len(png_files)} PNG files")

    # Batch analysis results
    batch_results = {}

    for png_file in track(png_files, description="Processing files..."):
        try:
            # Quick steganography check
            stego_results = analyze_steganography(str(png_file))

            if not stego_results.get('error'):
                risk_level = 'HIGH' if stego_results['overall_suspicious'] else 'LOW'
                suspicious_count = stego_results['suspicious_tests_count']

                batch_results[str(png_file)] = {
                    'risk_level': risk_level,
                    'suspicious_tests': suspicious_count,
                    'average_score': stego_results['average_suspicion_score']
                }

        except Exception as e:
            batch_results[str(png_file)] = {'error': str(e)}

    # Display batch results
    table = Table(title="Batch Analysis Results")
    table.add_column("File", style="cyan")
    table.add_column("Risk Level", style="magenta")
    table.add_column("Suspicious Tests", style="yellow")
    table.add_column("Avg Score", style="blue")

    for file_path, results in batch_results.items():
        if 'error' in results:
            table.add_row(Path(file_path).name, "[red]ERROR[/red]", "-", "-")
        else:
            risk_color = "red" if results['risk_level'] == 'HIGH' else "green"
            table.add_row(
                Path(file_path).name,
                f"[{risk_color}]{results['risk_level']}[/{risk_color}]",
                str(results['suspicious_tests']),
                f"{results['average_score']:.3f}"
            )

    console.print(table)


def main():
    """Run all examples."""

    console.print("[bold green]🔍 PNG Forensics Tools - Example Demonstrations[/bold green]")
    console.print("=" * 60)

    # Check if sample files exist, create if needed
    sample_files = ['sample_clean.png', 'sample_with_lsb.png', 'sample_with_unicode.png']
    missing_samples = [f for f in sample_files if not Path(f).exists()]

    if missing_samples:
        console.print(f"[yellow]Missing sample files: {', '.join(missing_samples)}[/yellow]")
        create_sample_images()

    console.print("\n[bold blue]Available Examples:[/bold blue]")
    console.print("1. Basic PNG Analysis")
    console.print("2. Steganography Detection")
    console.print("3. Unicode Analysis")
    console.print("4. Comprehensive Forensics Analysis")
    console.print("5. Manual LSB Extraction")
    console.print("6. Batch Processing")
    console.print("0. Run All Examples")

    try:
        choice = input("\nEnter example number (0-6): ")

        if choice == '0':
            example_basic_analysis()
            example_steganography_detection()
            example_unicode_analysis()
            example_comprehensive_analysis()
            example_manual_extraction()
            example_batch_processing()
        elif choice == '1':
            example_basic_analysis()
        elif choice == '2':
            example_steganography_detection()
        elif choice == '3':
            example_unicode_analysis()
        elif choice == '4':
            example_comprehensive_analysis()
        elif choice == '5':
            example_manual_extraction()
        elif choice == '6':
            example_batch_processing()
        else:
            console.print("[red]Invalid choice[/red]")
            return

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        return
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    console.print("\n[bold green]✓ Example demonstrations completed![/bold green]")
    console.print("\n[dim]Next steps:[/dim]")
    console.print("• Try analyzing your own PNG files")
    console.print("• Check the .cursor/commands/ directory for more analysis commands")
    console.print("• Read the .cursor/rules/ directory for advanced techniques")
    console.print("• Export detailed analysis reports in JSON format for further investigation")


if __name__ == '__main__':
    main()
