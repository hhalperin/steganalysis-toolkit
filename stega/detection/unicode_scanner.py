"""
Unicode Scanner - Detects invisible Unicode delimiters and hidden markers
Specialized for finding steganographic Unicode characters in text data
"""

import re
import unicodedata
from typing import List, Dict, Any, Set, Tuple
from dataclasses import dataclass


@dataclass
class UnicodeMatch:
    """Represents a found Unicode character with metadata."""
    char: str
    codepoint: int
    name: str
    category: str
    position: int
    context: str
    suspicious_level: str  # 'low', 'medium', 'high'


class UnicodeScanner:
    """Scans text data for suspicious Unicode characters and patterns."""
    
    # Invisible and suspicious Unicode ranges
    SUSPICIOUS_RANGES = {
        # Zero-width and invisible characters
        'zero_width': {
            0x200B,  # ZERO WIDTH SPACE
            0x200C,  # ZERO WIDTH NON-JOINER
            0x200D,  # ZERO WIDTH JOINER
            0x200E,  # LEFT-TO-RIGHT MARK
            0x200F,  # RIGHT-TO-LEFT MARK
            0x2060,  # WORD JOINER
            0x2061,  # FUNCTION APPLICATION
            0x2062,  # INVISIBLE TIMES
            0x2063,  # INVISIBLE SEPARATOR
            0x2064,  # INVISIBLE PLUS
            0x2065,  # (unassigned)
            0x2066,  # LEFT-TO-RIGHT ISOLATE
            0x2067,  # RIGHT-TO-LEFT ISOLATE
            0x2068,  # FIRST STRONG ISOLATE
            0x2069,  # POP DIRECTIONAL ISOLATE
            0xFEFF,  # ZERO WIDTH NO-BREAK SPACE (BOM)
        },
        
        # Private Use Areas (commonly used for steganography)
        'private_use_basic': set(range(0xE000, 0xF900)),  # Basic Private Use Area
        'private_use_a': set(range(0xF0000, 0x100000)),   # Private Use Area-A
        'private_use_b': set(range(0x100000, 0x110000)),  # Private Use Area-B
        
        # Specific steganographic ranges mentioned by user
        'steganographic_delimiters': {
            0xE200, 0xE201, 0xE202,  # Specific invisible markers
            0xE000, 0xE001, 0xE002, 0xE003, 0xE004, 0xE005,  # Common stego chars
        },
        
        # Variation selectors and format characters
        'format_chars': {
            0x00AD,  # SOFT HYPHEN
            0x034F,  # COMBINING GRAPHEME JOINER
            0x061C,  # ARABIC LETTER MARK
            0x115F,  # HANGUL CHOSEONG FILLER
            0x1160,  # HANGUL JUNGSEONG FILLER
            0x17B4,  # KHMER VOWEL INHERENT AQ
            0x17B5,  # KHMER VOWEL INHERENT AA
            0x180E,  # MONGOLIAN VOWEL SEPARATOR (now whitespace)
            0x3164,  # HANGUL FILLER
            0xFFA0,  # HALFWIDTH HANGUL FILLER
        },
        
        # Variation selectors
        'variation_selectors': set(range(0xFE00, 0xFE10)) | set(range(0xE0100, 0xE01F0)),
        
        # Non-characters (should never appear in normal text)
        'noncharacters': {
            0xFFFE, 0xFFFF,  # BMP non-characters
            0x1FFFE, 0x1FFFF, 0x2FFFE, 0x2FFFF,  # Plane 1-2
            0x3FFFE, 0x3FFFF, 0x4FFFE, 0x4FFFF,  # Plane 3-4
            0x5FFFE, 0x5FFFF, 0x6FFFE, 0x6FFFF,  # Plane 5-6
            0x7FFFE, 0x7FFFF, 0x8FFFE, 0x8FFFF,  # Plane 7-8
            0x9FFFE, 0x9FFFF, 0xAFFFE, 0xAFFFF,  # Plane 9-A
            0xBFFFE, 0xBFFFF, 0xCFFFE, 0xCFFFF,  # Plane B-C
            0xDFFFE, 0xDFFFF, 0xEFFFE, 0xEFFFF,  # Plane D-E
            0xFFFFE, 0xFFFFF, 0x10FFFE, 0x10FFFF,  # Plane F-10
        } | set(range(0xFDD0, 0xFDF0)),  # FDD0-FDEF non-characters
    }
    
    def __init__(self):
        self.matches: List[UnicodeMatch] = []
        self.statistics: Dict[str, Any] = {}
        
    def scan_text(self, text: str, context_chars: int = 20) -> List[UnicodeMatch]:
        """Scan text for suspicious Unicode characters."""
        self.matches = []
        
        if not text:
            return self.matches
        
        for i, char in enumerate(text):
            codepoint = ord(char)
            
            # Skip ASCII printable characters (optimization)
            if 32 <= codepoint <= 126:
                continue
                
            # Check if character is suspicious
            suspicion_info = self._check_suspicion(codepoint, char)
            if suspicion_info:
                # Get context around the character
                start = max(0, i - context_chars)
                end = min(len(text), i + context_chars + 1)
                context = text[start:end]
                
                # Get Unicode name safely
                try:
                    name = unicodedata.name(char)
                except ValueError:
                    name = f"<no name available, U+{codepoint:04X}>"
                
                # Get Unicode category
                category = unicodedata.category(char)
                
                match = UnicodeMatch(
                    char=char,
                    codepoint=codepoint,
                    name=name,
                    category=category,
                    position=i,
                    context=context,
                    suspicious_level=suspicion_info['level']
                )
                
                self.matches.append(match)
        
        self._calculate_statistics()
        return self.matches
    
    def _check_suspicion(self, codepoint: int, char: str) -> Dict[str, Any]:
        """Check if a Unicode codepoint is suspicious."""
        
        # Check each suspicious category
        for category, codepoints in self.SUSPICIOUS_RANGES.items():
            if codepoint in codepoints:
                level = self._get_suspicion_level(category, codepoint)
                return {
                    'category': category,
                    'level': level,
                    'reason': f'Character in {category} range'
                }
        
        # Check for other suspicious patterns
        category = unicodedata.category(char)
        
        # Control characters outside normal range
        if category.startswith('C') and not (0x09 <= codepoint <= 0x0D or codepoint in {0x85, 0xA0}):
            return {
                'category': 'control_character',
                'level': 'medium',
                'reason': f'Control character outside normal range (category: {category})'
            }
        
        # Unassigned characters
        if category == 'Cn':
            return {
                'category': 'unassigned',
                'level': 'high',
                'reason': 'Unassigned Unicode character'
            }
        
        # Characters with no visual representation but not in our explicit lists
        if category in ['Cf', 'Mn', 'Me'] and codepoint not in {0x00AD}:  # Exclude soft hyphen
            # Check if it's a common combining character
            if not self._is_common_combining_char(codepoint):
                return {
                    'category': 'format_or_combining',
                    'level': 'low',
                    'reason': f'Format or combining character (category: {category})'
                }
        
        return None
    
    def _get_suspicion_level(self, category: str, codepoint: int) -> str:
        """Determine suspicion level based on category and specific codepoint."""
        high_suspicion = {
            'noncharacters',
            'steganographic_delimiters',
            'private_use_basic',
            'private_use_a',
            'private_use_b'
        }
        
        medium_suspicion = {
            'zero_width',
            'variation_selectors'
        }
        
        if category in high_suspicion:
            return 'high'
        elif category in medium_suspicion:
            return 'medium'
        else:
            return 'low'
    
    def _is_common_combining_char(self, codepoint: int) -> bool:
        """Check if this is a commonly used combining character."""
        common_combining = {
            # Common diacritics
            0x0300, 0x0301, 0x0302, 0x0303, 0x0304, 0x0305, 0x0306, 0x0307,
            0x0308, 0x0309, 0x030A, 0x030B, 0x030C, 0x030D, 0x030E, 0x030F,
            0x0310, 0x0311, 0x0312, 0x0313, 0x0314, 0x0315, 0x0316, 0x0317,
            # Arabic diacritics
            0x064B, 0x064C, 0x064D, 0x064E, 0x064F, 0x0650, 0x0651, 0x0652,
            # Hebrew points
            0x05B0, 0x05B1, 0x05B2, 0x05B3, 0x05B4, 0x05B5, 0x05B6, 0x05B7,
        }
        return codepoint in common_combining
    
    def _calculate_statistics(self) -> None:
        """Calculate statistics about the found matches."""
        self.statistics = {
            'total_matches': len(self.matches),
            'by_category': {},
            'by_level': {'low': 0, 'medium': 0, 'high': 0},
            'unique_codepoints': set(),
            'position_density': {}
        }
        
        for match in self.matches:
            # Count by category
            category = self._get_match_category(match)
            self.statistics['by_category'][category] = self.statistics['by_category'].get(category, 0) + 1
            
            # Count by suspicion level
            self.statistics['by_level'][match.suspicious_level] += 1
            
            # Track unique codepoints
            self.statistics['unique_codepoints'].add(match.codepoint)
        
        # Convert set to count for JSON serialization
        self.statistics['unique_codepoint_count'] = len(self.statistics['unique_codepoints'])
        del self.statistics['unique_codepoints']
    
    def _get_match_category(self, match: UnicodeMatch) -> str:
        """Get the category of a match based on its codepoint."""
        codepoint = match.codepoint
        
        for category, codepoints in self.SUSPICIOUS_RANGES.items():
            if codepoint in codepoints:
                return category
        
        return 'other'
    
    def detect_patterns(self, text: str) -> List[Dict[str, Any]]:
        """Detect suspicious patterns in Unicode usage."""
        patterns = []
        
        if not text:
            return patterns
        
        # Pattern 1: Repeated invisible characters
        invisible_chars = []
        for i, char in enumerate(text):
            if ord(char) in self.SUSPICIOUS_RANGES['zero_width']:
                invisible_chars.append((i, char))
        
        if len(invisible_chars) > 3:
            patterns.append({
                'type': 'repeated_invisible',
                'description': f'Found {len(invisible_chars)} invisible characters - possible steganographic encoding',
                'positions': [pos for pos, _ in invisible_chars],
                'severity': 'high'
            })
        
        # Pattern 2: Private use area clustering
        private_chars = []
        for i, char in enumerate(text):
            codepoint = ord(char)
            if (codepoint in self.SUSPICIOUS_RANGES['private_use_basic'] or
                codepoint in self.SUSPICIOUS_RANGES['steganographic_delimiters']):
                private_chars.append((i, char))
        
        if len(private_chars) > 0:
            patterns.append({
                'type': 'private_use_characters',
                'description': f'Found {len(private_chars)} private use area characters - likely steganographic',
                'positions': [pos for pos, _ in private_chars],
                'severity': 'high'
            })
        
        # Pattern 3: Variation selector abuse
        vs_count = sum(1 for char in text if ord(char) in self.SUSPICIOUS_RANGES['variation_selectors'])
        if vs_count > 5:  # More than 5 variation selectors is unusual
            patterns.append({
                'type': 'variation_selector_abuse',
                'description': f'Found {vs_count} variation selectors - possible encoding scheme',
                'severity': 'medium'
            })
        
        # Pattern 4: Non-character presence
        nonchar_positions = []
        for i, char in enumerate(text):
            if ord(char) in self.SUSPICIOUS_RANGES['noncharacters']:
                nonchar_positions.append(i)
        
        if nonchar_positions:
            patterns.append({
                'type': 'non_characters',
                'description': f'Found {len(nonchar_positions)} non-characters - should never appear in valid text',
                'positions': nonchar_positions,
                'severity': 'high'
            })
        
        # Pattern 5: Mixed script anomalies (basic check)
        scripts = set()
        for char in text:
            if unicodedata.category(char)[0] == 'L':  # Letters only
                try:
                    script = unicodedata.name(char).split()[0]
                    scripts.add(script)
                except (ValueError, IndexError):
                    pass
        
        if len(scripts) > 3:  # More than 3 different scripts
            patterns.append({
                'type': 'mixed_scripts',
                'description': f'Text contains {len(scripts)} different scripts - possible obfuscation',
                'scripts': list(scripts),
                'severity': 'low'
            })
        
        return patterns
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate a comprehensive report of Unicode analysis."""
        return {
            'suspicious_characters': [
                {
                    'character': match.char,
                    'codepoint': f"U+{match.codepoint:04X}",
                    'name': match.name,
                    'category': match.category,
                    'position': match.position,
                    'context': match.context,
                    'suspicion_level': match.suspicious_level
                }
                for match in self.matches
            ],
            'statistics': self.statistics,
            'recommendations': self._get_recommendations()
        }
    
    def _get_recommendations(self) -> List[str]:
        """Generate recommendations based on findings."""
        recommendations = []
        
        high_count = self.statistics['by_level']['high']
        medium_count = self.statistics['by_level']['medium']
        
        if high_count > 0:
            recommendations.append(
                f"Found {high_count} high-suspicion Unicode characters. "
                "These may indicate steganographic content or malicious encoding."
            )
        
        if medium_count > 5:
            recommendations.append(
                f"Found {medium_count} medium-suspicion characters. "
                "Review for potential invisible text or formatting tricks."
            )
        
        if 'private_use_basic' in self.statistics['by_category']:
            recommendations.append(
                "Private Use Area characters detected. These are commonly used for steganography. "
                "Consider using a hex editor to examine the exact byte sequences."
            )
        
        if 'zero_width' in self.statistics['by_category']:
            recommendations.append(
                "Zero-width characters found. These may encode hidden messages. "
                "Try decoding as binary (0/1) or other encoding schemes."
            )
        
        return recommendations


def scan_unicode_in_text(text: str) -> Dict[str, Any]:
    """Convenience function to scan text for Unicode anomalies."""
    scanner = UnicodeScanner()
    scanner.scan_text(text)
    patterns = scanner.detect_patterns(text)
    report = scanner.generate_report()
    report['patterns'] = patterns
    return report


if __name__ == '__main__':
    import sys
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    
    console = Console()
    
    if len(sys.argv) != 2:
        console.print("[red]Usage: python unicode_scanner.py <text_file_or_string>[/red]")
        console.print("Example: python unicode_scanner.py \"Hello\u200bWorld\"")
        sys.exit(1)
    
    input_arg = sys.argv[1]
    
    # Check if it's a file or direct text
    try:
        with open(input_arg, 'r', encoding='utf-8') as f:
            text = f.read()
        console.print(f"[blue]Analyzing file: {input_arg}[/blue]")
    except FileNotFoundError:
        text = input_arg
        console.print(f"[blue]Analyzing text string (length: {len(text)})[/blue]")
    
    result = scan_unicode_in_text(text)
    
    # Display findings
    if result['suspicious_characters']:
        table = Table(title="Suspicious Unicode Characters")
        table.add_column("Position", style="yellow")
        table.add_column("Character", style="cyan")
        table.add_column("Codepoint", style="magenta")
        table.add_column("Name", style="green")
        table.add_column("Level", style="red")
        table.add_column("Context", style="blue")
        
        for char_info in result['suspicious_characters']:
            # Show invisible characters as their codepoint
            display_char = char_info['character'] if char_info['character'].isprintable() else f"U+{char_info['codepoint'][2:]}"
            
            table.add_row(
                str(char_info['position']),
                display_char,
                char_info['codepoint'],
                char_info['name'][:50] + ("..." if len(char_info['name']) > 50 else ""),
                char_info['suspicion_level'],
                repr(char_info['context'][:30])
            )
        
        console.print(table)
    else:
        console.print("[green]No suspicious Unicode characters found.[/green]")
    
    # Display patterns
    if result['patterns']:
        console.print("\n[bold red]Suspicious Patterns:[/bold red]")
        for pattern in result['patterns']:
            console.print(f"  • [{pattern['type']}] {pattern['description']} (Severity: {pattern['severity']})")
    
    # Display statistics
    if result['statistics']['total_matches'] > 0:
        stats_text = f"""Total matches: {result['statistics']['total_matches']}
High suspicion: {result['statistics']['by_level']['high']}
Medium suspicion: {result['statistics']['by_level']['medium']}
Low suspicion: {result['statistics']['by_level']['low']}
Unique codepoints: {result['statistics']['unique_codepoint_count']}"""
        console.print(Panel(stats_text, title="[yellow]Statistics[/yellow]"))
    
    # Display recommendations
    if result['recommendations']:
        console.print("\n[bold green]Recommendations:[/bold green]")
        for rec in result['recommendations']:
            console.print(f"  • {rec}")
