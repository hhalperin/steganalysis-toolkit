"""
Comprehensive PNG Analyzer - Main script for detecting hidden content and steganography
Combines chunk analysis, Unicode scanning, and steganographic detection
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import hashlib
import binascii

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.tree import Tree
from rich.syntax import Syntax

from detection.chunk_analyzer import PNGChunkAnalyzer, analyze_png_chunks
from detection.unicode_scanner import UnicodeScanner, scan_unicode_in_text
from detection.steganography import SteganographyDetector, analyze_steganography


class PNGForensicsAnalyzer:
    """Comprehensive PNG forensics analysis combining multiple detection methods."""

    def __init__(self, file_path: str, console: Console = None):
        self.file_path = Path(file_path)
        self.console = console or Console()
        self.analysis_results = {}
        self.suspicious_findings = []

    def analyze_file(self, include_visual: bool = False) -> Dict[str, Any]:
        """Perform comprehensive analysis of PNG file."""
        if not self.file_path.exists():
            return {'error': f'File not found: {self.file_path}'}

        if not self.file_path.suffix.lower() in ['.png', '.apng']:
            self.console.print(f"[yellow]Warning: File extension is {self.file_path.suffix}, expected .png[/yellow]")

        start_time = datetime.now()
        self.analysis_results = {
            'file_info': self._get_file_info(),
            'chunk_analysis': {},
            'unicode_analysis': {},
            'steganography_analysis': {},
            'forensics_summary': {},
            'analysis_timestamp': start_time.isoformat(),
            'analysis_version': '1.0'
        }

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:

            # Task 1: Chunk Analysis
            task1 = progress.add_task("[cyan]Analyzing PNG chunks...", total=None)
            try:
                chunk_results = self._analyze_chunks()
                self.analysis_results['chunk_analysis'] = chunk_results
                progress.update(task1, description="[green]✓ Chunk analysis complete")
            except Exception as e:
                self.analysis_results['chunk_analysis'] = {'error': str(e)}
                progress.update(task1, description=f"[red]✗ Chunk analysis failed: {str(e)}")

            # Task 2: Unicode Analysis of text chunks
            task2 = progress.add_task("[cyan]Scanning for Unicode anomalies...", total=None)
            try:
                unicode_results = self._analyze_unicode_content()
                self.analysis_results['unicode_analysis'] = unicode_results
                progress.update(task2, description="[green]✓ Unicode analysis complete")
            except Exception as e:
                self.analysis_results['unicode_analysis'] = {'error': str(e)}
                progress.update(task2, description=f"[red]✗ Unicode analysis failed: {str(e)}")

            # Task 3: Steganographic Analysis
            task3 = progress.add_task("[cyan]Detecting steganographic patterns...", total=None)
            try:
                stego_results = self._analyze_steganography()
                self.analysis_results['steganography_analysis'] = stego_results
                progress.update(task3, description="[green]✓ Steganography analysis complete")
            except Exception as e:
                self.analysis_results['steganography_analysis'] = {'error': str(e)}
                progress.update(task3, description=f"[red]✗ Steganography analysis failed: {str(e)}")

            # Task 4: Generate forensics summary
            task4 = progress.add_task("[cyan]Generating forensics summary...", total=None)
            self._generate_forensics_summary()
            progress.update(task4, description="[green]✓ Forensics summary complete")

        end_time = datetime.now()
        self.analysis_results['analysis_duration'] = str(end_time - start_time)

        return self.analysis_results

    def _get_file_info(self) -> Dict[str, Any]:
        """Get basic file information and hashes."""
        stat = self.file_path.stat()

        # Calculate file hashes
        with open(self.file_path, 'rb') as f:
            file_data = f.read()
            md5_hash = hashlib.md5(file_data).hexdigest()
            sha1_hash = hashlib.sha1(file_data).hexdigest()
            sha256_hash = hashlib.sha256(file_data).hexdigest()

        return {
            'path': str(self.file_path),
            'name': self.file_path.name,
            'size_bytes': stat.st_size,
            'size_human': self._human_readable_size(stat.st_size),
            'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'md5': md5_hash,
            'sha1': sha1_hash,
            'sha256': sha256_hash,
        }

    def _human_readable_size(self, size_bytes: int) -> str:
        """Convert bytes to human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"

    def _analyze_chunks(self) -> Dict[str, Any]:
        """Analyze PNG chunks using the chunk analyzer."""
        return analyze_png_chunks(str(self.file_path))

    def _analyze_unicode_content(self) -> Dict[str, Any]:
        """Analyze text content in chunks for Unicode anomalies."""
        chunk_analyzer = PNGChunkAnalyzer(self.file_path)
        chunk_analyzer.parse_chunks()

        all_text_content = []
        unicode_results = {
            'chunks_with_text': [],
            'suspicious_unicode': [],
            'patterns_detected': [],
            'summary': {}
        }

        # Extract text from all text chunks
        for chunk in chunk_analyzer.chunks:
            text_content = chunk.get_text_content()
            if text_content:
                all_text_content.append(text_content)

                # Analyze this chunk's text for Unicode anomalies
                chunk_unicode_analysis = scan_unicode_in_text(text_content)

                if chunk_unicode_analysis['suspicious_characters']:
                    chunk_info = {
                        'chunk_type': chunk.chunk_type.decode('ascii', errors='replace'),
                        'chunk_offset': f"0x{chunk.offset:x}",
                        'text_content': text_content,
                        'unicode_analysis': chunk_unicode_analysis
                    }
                    unicode_results['chunks_with_text'].append(chunk_info)

                    # Add to suspicious findings
                    for char in chunk_unicode_analysis['suspicious_characters']:
                        unicode_results['suspicious_unicode'].append({
                            'chunk_type': chunk.chunk_type.decode('ascii', errors='replace'),
                            'character': char
                        })

                    for pattern in chunk_unicode_analysis.get('patterns', []):
                        unicode_results['patterns_detected'].append({
                            'chunk_type': chunk.chunk_type.decode('ascii', errors='replace'),
                            'pattern': pattern
                        })

        # Analyze all text content together
        if all_text_content:
            combined_text = '\n'.join(all_text_content)
            combined_analysis = scan_unicode_in_text(combined_text)
            unicode_results['combined_analysis'] = combined_analysis

        # Summary statistics
        unicode_results['summary'] = {
            'total_text_chunks': len([c for c in chunk_analyzer.chunks if c.get_text_content()]),
            'chunks_with_suspicious_unicode': len(unicode_results['chunks_with_text']),
            'total_suspicious_characters': len(unicode_results['suspicious_unicode']),
            'patterns_found': len(unicode_results['patterns_detected'])
        }

        return unicode_results

    def _analyze_steganography(self) -> Dict[str, Any]:
        """Analyze image for steganographic content."""
        return analyze_steganography(str(self.file_path))

    def _generate_forensics_summary(self) -> None:
        """Generate comprehensive forensics summary."""
        summary = {
            'overall_risk_level': 'low',
            'suspicious_indicators': [],
            'confidence_scores': {},
            'recommended_actions': [],
            'technical_findings': [],
            'executive_summary': ''
        }

        risk_score = 0
        max_risk_score = 100

        # Analyze chunk findings
        chunk_analysis = self.analysis_results.get('chunk_analysis', {})
        if 'findings' in chunk_analysis:
            chunk_findings = len(chunk_analysis['findings'])
            if chunk_findings > 0:
                risk_score += min(chunk_findings * 10, 30)
                summary['suspicious_indicators'].append(f"Found {chunk_findings} suspicious PNG chunk patterns")

                for finding in chunk_analysis['findings']:
                    summary['technical_findings'].append({
                        'category': 'PNG Structure',
                        'type': finding['type'],
                        'description': finding['message'],
                        'severity': self._categorize_finding_severity(finding['type'])
                    })

        # Analyze Unicode findings
        unicode_analysis = self.analysis_results.get('unicode_analysis', {})
        if 'suspicious_unicode' in unicode_analysis:
            unicode_findings = len(unicode_analysis['suspicious_unicode'])
            if unicode_findings > 0:
                risk_score += min(unicode_findings * 5, 25)
                summary['suspicious_indicators'].append(f"Found {unicode_findings} suspicious Unicode characters in metadata")

                high_suspicion = sum(1 for char in unicode_analysis['suspicious_unicode']
                                   if char.get('character', {}).get('suspicion_level') == 'high')
                if high_suspicion > 0:
                    risk_score += high_suspicion * 10
                    summary['technical_findings'].append({
                        'category': 'Unicode Anomalies',
                        'type': 'high_suspicion_characters',
                        'description': f'Found {high_suspicion} high-suspicion Unicode characters (likely steganographic)',
                        'severity': 'high'
                    })

        # Analyze steganography findings
        stego_analysis = self.analysis_results.get('steganography_analysis', {})
        if stego_analysis.get('overall_suspicious'):
            risk_score += 30
            suspicious_tests = stego_analysis.get('suspicious_tests_count', 0)
            summary['suspicious_indicators'].append(f"Steganographic analysis flagged {suspicious_tests} tests as suspicious")

            for test in stego_analysis.get('individual_results', []):
                if test['is_suspicious']:
                    summary['technical_findings'].append({
                        'category': 'Steganography',
                        'type': test['test_name'].lower().replace(' ', '_'),
                        'description': f"{test['test_name']} indicates possible hidden content (score: {test['score']:.3f})",
                        'severity': 'high' if test['score'] > 0.7 else 'medium'
                    })

        # Calculate confidence scores
        summary['confidence_scores'] = {
            'chunk_analysis': self._calculate_confidence(chunk_analysis),
            'unicode_analysis': self._calculate_confidence(unicode_analysis),
            'steganography_analysis': self._calculate_confidence(stego_analysis)
        }

        # Determine overall risk level
        if risk_score >= 50:
            summary['overall_risk_level'] = 'high'
        elif risk_score >= 25:
            summary['overall_risk_level'] = 'medium'
        else:
            summary['overall_risk_level'] = 'low'

        # Generate recommendations
        summary['recommended_actions'] = self._generate_recommendations(summary, risk_score)

        # Generate executive summary
        summary['executive_summary'] = self._generate_executive_summary(summary, risk_score)

        self.analysis_results['forensics_summary'] = summary

    def _categorize_finding_severity(self, finding_type: str) -> str:
        """Categorize finding severity based on type."""
        high_severity = {
            'custom_chunk', 'crc_failure', 'high_entropy',
            'non_consecutive_idat', 'invalid_structure'
        }
        medium_severity = {
            'large_chunk', 'duplicate_chunks'
        }

        if finding_type in high_severity:
            return 'high'
        elif finding_type in medium_severity:
            return 'medium'
        else:
            return 'low'

    def _calculate_confidence(self, analysis_result: Dict[str, Any]) -> float:
        """Calculate confidence score for analysis result."""
        if 'error' in analysis_result:
            return 0.0

        # Base confidence on completeness and consistency of results
        confidence = 0.8  # Base confidence

        # Adjust based on findings
        if isinstance(analysis_result, dict):
            if 'findings' in analysis_result and analysis_result['findings']:
                confidence = min(0.95, confidence + 0.1)
            if 'total_matches' in analysis_result and analysis_result['total_matches'] > 0:
                confidence = min(0.95, confidence + 0.1)

        return confidence

    def _generate_recommendations(self, summary: Dict[str, Any], risk_score: int) -> List[str]:
        """Generate actionable recommendations based on findings."""
        recommendations = []

        if summary['overall_risk_level'] == 'high':
            recommendations.extend([
                "IMMEDIATE ACTION: This file shows multiple indicators of hidden content or manipulation",
                "Quarantine file and investigate source/chain of custody",
                "Use specialized steganography tools (steghide, zsteg, binwalk) for extraction attempts",
                "Perform hex dump analysis to examine raw bytes",
                "Consider reverse image search to find potential original"
            ])

        elif summary['overall_risk_level'] == 'medium':
            recommendations.extend([
                "Further investigation recommended",
                "Run additional steganographic analysis tools",
                "Examine file with hex editor for manual review",
                "Verify file source and authenticity"
            ])

        else:
            recommendations.extend([
                "File appears normal but continue monitoring",
                "Verify file integrity if needed for evidence chain"
            ])

        # Specific recommendations based on findings
        for finding in summary['technical_findings']:
            if finding['category'] == 'PNG Structure' and finding['severity'] == 'high':
                recommendations.append("Investigate PNG structure anomalies with PNG debugging tools")

            if finding['category'] == 'Unicode Anomalies':
                recommendations.append("Extract and decode text metadata manually")

            if finding['category'] == 'Steganography':
                if 'lsb' in finding['type']:
                    recommendations.append("Try LSB extraction tools (steghide, outguess)")
                if 'frequency' in finding['type']:
                    recommendations.append("Investigate DCT/frequency domain hiding methods")

        return list(set(recommendations))  # Remove duplicates

    def _generate_executive_summary(self, summary: Dict[str, Any], risk_score: int) -> str:
        """Generate executive summary of analysis."""
        file_name = self.analysis_results['file_info']['name']
        risk_level = summary['overall_risk_level'].upper()

        base_summary = f"Analysis of '{file_name}' completed with {risk_level} risk assessment."

        if summary['overall_risk_level'] == 'high':
            return f"{base_summary} Multiple indicators suggest possible steganographic content or malicious manipulation. Immediate investigation recommended."

        elif summary['overall_risk_level'] == 'medium':
            return f"{base_summary} Some anomalies detected that warrant further investigation. File may contain hidden content."

        else:
            return f"{base_summary} File appears to be a standard PNG with no significant suspicious indicators."

    def print_summary_report(self) -> None:
        """Print a formatted summary report to console."""
        if not self.analysis_results:
            self.console.print("[red]No analysis results available. Run analyze_file() first.[/red]")
            return

        # File Information
        file_info = self.analysis_results['file_info']
        info_text = f"""Path: {file_info['path']}
Size: {file_info['size_human']} ({file_info['size_bytes']:,} bytes)
Modified: {file_info['modified']}
SHA256: {file_info['sha256'][:32]}..."""

        self.console.print(Panel(info_text, title="[bold blue]File Information[/bold blue]"))

        # Forensics Summary
        forensics = self.analysis_results.get('forensics_summary', {})
        risk_level = forensics.get('overall_risk_level', 'unknown').upper()
        risk_color = {'HIGH': 'red', 'MEDIUM': 'yellow', 'LOW': 'green'}.get(risk_level, 'white')

        summary_text = f"Risk Level: [{risk_color}]{risk_level}[/{risk_color}]\n"
        summary_text += forensics.get('executive_summary', 'No summary available')

        self.console.print(Panel(summary_text, title="[bold yellow]Forensics Summary[/bold yellow]"))

        # Suspicious Indicators
        if forensics.get('suspicious_indicators'):
            self.console.print("\n[bold red]Suspicious Indicators:[/bold red]")
            for indicator in forensics['suspicious_indicators']:
                self.console.print(f"  • {indicator}")

        # Technical Findings Table
        if forensics.get('technical_findings'):
            table = Table(title="Technical Findings")
            table.add_column("Category", style="cyan")
            table.add_column("Type", style="yellow")
            table.add_column("Description", style="white")
            table.add_column("Severity", style="magenta")

            for finding in forensics['technical_findings']:
                severity_color = {'high': 'red', 'medium': 'yellow', 'low': 'green'}.get(
                    finding['severity'], 'white')
                table.add_row(
                    finding['category'],
                    finding['type'],
                    finding['description'][:80] + ("..." if len(finding['description']) > 80 else ""),
                    f"[{severity_color}]{finding['severity'].upper()}[/{severity_color}]"
                )

            self.console.print(table)

        # Recommendations
        if forensics.get('recommended_actions'):
            self.console.print("\n[bold green]Recommended Actions:[/bold green]")
            for i, action in enumerate(forensics['recommended_actions'], 1):
                self.console.print(f"  {i}. {action}")

        # Analysis Details
        self.console.print(f"\n[dim]Analysis completed in {self.analysis_results.get('analysis_duration', 'unknown time')}[/dim]")

    def export_report(self, output_path: str, format: str = 'json') -> bool:
        """Export analysis results to file."""
        try:
            output_file = Path(output_path)

            if format.lower() == 'json':
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(self.analysis_results, f, indent=2, ensure_ascii=False)

            elif format.lower() == 'txt':
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(f"PNG Forensics Analysis Report\n")
                    f.write(f"Generated: {self.analysis_results['analysis_timestamp']}\n")
                    f.write("=" * 50 + "\n\n")

                    # File info
                    file_info = self.analysis_results['file_info']
                    f.write("FILE INFORMATION:\n")
                    for key, value in file_info.items():
                        f.write(f"  {key}: {value}\n")
                    f.write("\n")

                    # Forensics summary
                    forensics = self.analysis_results.get('forensics_summary', {})
                    f.write("FORENSICS SUMMARY:\n")
                    f.write(f"  Risk Level: {forensics.get('overall_risk_level', 'unknown').upper()}\n")
                    f.write(f"  Executive Summary: {forensics.get('executive_summary', 'N/A')}\n\n")

                    # Technical findings
                    if forensics.get('technical_findings'):
                        f.write("TECHNICAL FINDINGS:\n")
                        for finding in forensics['technical_findings']:
                            f.write(f"  - {finding['category']} / {finding['type']}: {finding['description']} (Severity: {finding['severity']})\n")
                        f.write("\n")

                    # Recommendations
                    if forensics.get('recommended_actions'):
                        f.write("RECOMMENDATIONS:\n")
                        for i, action in enumerate(forensics['recommended_actions'], 1):
                            f.write(f"  {i}. {action}\n")

            else:
                self.console.print(f"[red]Unsupported export format: {format}[/red]")
                return False

            self.console.print(f"[green]Report exported to: {output_file}[/green]")
            return True

        except Exception as e:
            self.console.print(f"[red]Error exporting report: {e}[/red]")
            return False


def main():
    """Main entry point for PNG analyzer."""
    console = Console()

    if len(sys.argv) < 2:
        console.print("[red]Usage: python png_analyzer.py <png_file> [--export <format>] [--output <file>][/red]")
        console.print("\nFormats: json, txt")
        console.print("Example: python png_analyzer.py image.png --export json --output report.json")
        sys.exit(1)

    png_file = sys.argv[1]
    export_format = None
    output_file = None

    # Parse arguments
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == '--export' and i + 1 < len(sys.argv):
            export_format = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--output' and i + 1 < len(sys.argv):
            output_file = sys.argv[i + 1]
            i += 2
        else:
            i += 1

    # Create analyzer and run analysis
    analyzer = PNGForensicsAnalyzer(png_file, console)

    console.print(f"[bold blue]🔍 PNG Forensics Analyzer v1.0[/bold blue]")
    console.print(f"[dim]Analyzing: {png_file}[/dim]\n")

    results = analyzer.analyze_file()

    if 'error' in results:
        console.print(Panel(results['error'], title="[red]Error[/red]", border_style="red"))
        sys.exit(1)

    # Display results
    analyzer.print_summary_report()

    # Export if requested
    if export_format and output_file:
        analyzer.export_report(output_file, export_format)
    elif export_format:
        # Auto-generate output filename
        base_name = Path(png_file).stem
        output_file = f"{base_name}_analysis.{export_format}"
        analyzer.export_report(output_file, export_format)


if __name__ == '__main__':
    main()
