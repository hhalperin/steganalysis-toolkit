"""
PNG Chunk Analyzer - Low-level PNG chunk parsing and analysis
Identifies unusual, custom, or suspicious chunks in PNG files
"""

import struct
import zlib
import binascii
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path


class PNGChunk:
    """Represents a single PNG chunk with metadata and analysis capabilities."""
    
    def __init__(self, length: int, chunk_type: bytes, data: bytes, crc: int, offset: int):
        self.length = length
        self.chunk_type = chunk_type
        self.data = data
        self.crc = crc
        self.offset = offset
        self.is_critical = self._is_critical()
        self.is_standard = self._is_standard()
        
    def _is_critical(self) -> bool:
        """Critical chunks have uppercase first letter."""
        return bool(self.chunk_type[0] & 0x20 == 0)
    
    def _is_standard(self) -> bool:
        """Check if this is a standard PNG chunk type."""
        standard_chunks = {
            b'IHDR', b'PLTE', b'IDAT', b'IEND',  # Critical chunks
            b'tRNS', b'cHRM', b'gAMA', b'iCCP', b'sBIT', b'sRGB',  # Ancillary chunks
            b'bKGD', b'hIST', b'tIME', b'tEXt', b'zTXt', b'iTXt',  # Text and metadata
            b'pHYs', b'sPLT', b'eXIf', b'acTL', b'fcTL', b'fdAT'   # Additional standard chunks
        }
        return self.chunk_type in standard_chunks
    
    def verify_crc(self) -> bool:
        """Verify the CRC-32 checksum of the chunk."""
        calculated_crc = zlib.crc32(self.chunk_type + self.data) & 0xffffffff
        return calculated_crc == self.crc
    
    def get_text_content(self) -> Optional[str]:
        """Extract text content from text chunks (tEXt, zTXt, iTXt)."""
        try:
            if self.chunk_type == b'tEXt':
                # Uncompressed text: keyword\0text
                null_pos = self.data.find(b'\0')
                if null_pos != -1:
                    keyword = self.data[:null_pos].decode('latin1')
                    text = self.data[null_pos + 1:].decode('latin1')
                    return f"{keyword}: {text}"
                    
            elif self.chunk_type == b'zTXt':
                # Compressed text: keyword\0compression_method\0compressed_text
                null_pos = self.data.find(b'\0')
                if null_pos != -1:
                    keyword = self.data[:null_pos].decode('latin1')
                    compression_method = self.data[null_pos + 1]
                    if compression_method == 0:  # zlib compression
                        compressed_data = self.data[null_pos + 2:]
                        try:
                            text = zlib.decompress(compressed_data).decode('utf-8')
                            return f"{keyword}: {text}"
                        except zlib.error:
                            return f"{keyword}: <failed to decompress>"
                            
            elif self.chunk_type == b'iTXt':
                # International text: keyword\0compression_flag\0compression_method\0language_tag\0translated_keyword\0text
                parts = self.data.split(b'\0', 4)
                if len(parts) >= 5:
                    keyword = parts[0].decode('utf-8')
                    compression_flag = parts[1][0] if parts[1] else 0
                    text_data = parts[4]
                    
                    if compression_flag == 1:  # Compressed
                        try:
                            text_data = zlib.decompress(text_data)
                        except zlib.error:
                            return f"{keyword}: <failed to decompress>"
                    
                    text = text_data.decode('utf-8', errors='replace')
                    return f"{keyword}: {text}"
                    
        except (UnicodeDecodeError, IndexError):
            pass
        
        return None
    
    def analyze_entropy(self) -> float:
        """Calculate Shannon entropy of chunk data to detect randomness/encryption."""
        if not self.data:
            return 0.0
            
        # Count byte frequencies
        byte_counts = [0] * 256
        for byte in self.data:
            byte_counts[byte] += 1
        
        # Calculate Shannon entropy
        entropy = 0.0
        data_len = len(self.data)
        
        for count in byte_counts:
            if count > 0:
                probability = count / data_len
                entropy -= probability * np.log2(probability)
        
        return entropy
    
    def __str__(self) -> str:
        chunk_type_str = self.chunk_type.decode('ascii', errors='replace')
        return f"Chunk({chunk_type_str}, {self.length} bytes, offset=0x{self.offset:x})"


class PNGChunkAnalyzer:
    """Analyzes PNG files at the chunk level for forensics and steganography detection."""
    
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.chunks: List[PNGChunk] = []
        self.suspicious_findings: List[Dict[str, Any]] = []
        
    def parse_chunks(self) -> bool:
        """Parse all chunks from the PNG file."""
        try:
            with open(self.file_path, 'rb') as f:
                # Verify PNG signature
                signature = f.read(8)
                if signature != b'\x89PNG\r\n\x1a\n':
                    self.suspicious_findings.append({
                        'type': 'invalid_signature',
                        'message': 'File does not have valid PNG signature',
                        'data': binascii.hexlify(signature).decode()
                    })
                    return False
                
                offset = 8
                while True:
                    # Read chunk header
                    header = f.read(8)
                    if len(header) < 8:
                        break
                    
                    length, chunk_type = struct.unpack('>I4s', header)
                    
                    # Read chunk data and CRC
                    if length > 0:
                        data = f.read(length)
                        if len(data) != length:
                            break
                    else:
                        data = b''
                    
                    crc_bytes = f.read(4)
                    if len(crc_bytes) != 4:
                        break
                    
                    crc = struct.unpack('>I', crc_bytes)[0]
                    
                    # Create chunk object
                    chunk = PNGChunk(length, chunk_type, data, crc, offset)
                    self.chunks.append(chunk)
                    
                    offset += 8 + length + 4
                    
                    # Stop at IEND chunk
                    if chunk_type == b'IEND':
                        break
                        
            return True
            
        except Exception as e:
            self.suspicious_findings.append({
                'type': 'parse_error',
                'message': f'Error parsing PNG chunks: {str(e)}'
            })
            return False
    
    def analyze_chunks(self) -> Dict[str, Any]:
        """Perform comprehensive analysis of all chunks."""
        if not self.parse_chunks():
            return {'error': 'Failed to parse PNG chunks', 'findings': self.suspicious_findings}
        
        analysis = {
            'total_chunks': len(self.chunks),
            'chunk_summary': [],
            'suspicious_chunks': [],
            'text_content': [],
            'custom_chunks': [],
            'crc_failures': [],
            'high_entropy_chunks': [],
            'findings': self.suspicious_findings
        }
        
        for chunk in self.chunks:
            # Basic chunk info
            chunk_info = {
                'type': chunk.chunk_type.decode('ascii', errors='replace'),
                'length': chunk.length,
                'offset': f"0x{chunk.offset:x}",
                'critical': chunk.is_critical,
                'standard': chunk.is_standard
            }
            analysis['chunk_summary'].append(chunk_info)
            
            # Check for non-standard chunks
            if not chunk.is_standard:
                analysis['custom_chunks'].append({
                    **chunk_info,
                    'data_sample': binascii.hexlify(chunk.data[:32]).decode() if chunk.data else '',
                    'entropy': chunk.analyze_entropy()
                })
                
                self.suspicious_findings.append({
                    'type': 'custom_chunk',
                    'message': f'Non-standard chunk type: {chunk_info["type"]}',
                    'chunk': chunk_info
                })
            
            # Verify CRC
            if not chunk.verify_crc():
                analysis['crc_failures'].append(chunk_info)
                self.suspicious_findings.append({
                    'type': 'crc_failure',
                    'message': f'CRC verification failed for chunk {chunk_info["type"]}',
                    'chunk': chunk_info
                })
            
            # Check entropy for possible encryption/compression
            entropy = chunk.analyze_entropy()
            if entropy > 7.5:  # High entropy threshold
                analysis['high_entropy_chunks'].append({
                    **chunk_info,
                    'entropy': entropy
                })
                
                if not chunk.is_standard or chunk.chunk_type not in [b'IDAT']:  # IDAT is expected to be compressed
                    self.suspicious_findings.append({
                        'type': 'high_entropy',
                        'message': f'Chunk {chunk_info["type"]} has high entropy ({entropy:.2f}), possible encryption or random data',
                        'chunk': chunk_info,
                        'entropy': entropy
                    })
            
            # Extract text content
            text_content = chunk.get_text_content()
            if text_content:
                analysis['text_content'].append({
                    'chunk_type': chunk_info['type'],
                    'content': text_content
                })
            
            # Check for unusual chunk sizes
            if chunk.length > 1024 * 1024:  # > 1MB
                self.suspicious_findings.append({
                    'type': 'large_chunk',
                    'message': f'Unusually large chunk: {chunk_info["type"]} ({chunk.length} bytes)',
                    'chunk': chunk_info
                })
        
        # Check chunk order and structure
        self._analyze_chunk_structure(analysis)
        
        return analysis
    
    def _analyze_chunk_structure(self, analysis: Dict[str, Any]) -> None:
        """Analyze the overall structure and ordering of chunks."""
        if not self.chunks:
            return
        
        # Check if IHDR is first
        if self.chunks[0].chunk_type != b'IHDR':
            self.suspicious_findings.append({
                'type': 'invalid_structure',
                'message': 'PNG file does not start with IHDR chunk'
            })
        
        # Check if IEND is last
        if self.chunks[-1].chunk_type != b'IEND':
            self.suspicious_findings.append({
                'type': 'invalid_structure',
                'message': 'PNG file does not end with IEND chunk'
            })
        
        # Count IDAT chunks and check for gaps
        idat_positions = []
        for i, chunk in enumerate(self.chunks):
            if chunk.chunk_type == b'IDAT':
                idat_positions.append(i)
        
        # IDAT chunks should be consecutive
        if len(idat_positions) > 1:
            consecutive = all(idat_positions[i] + 1 == idat_positions[i + 1] 
                            for i in range(len(idat_positions) - 1))
            if not consecutive:
                self.suspicious_findings.append({
                    'type': 'non_consecutive_idat',
                    'message': 'IDAT chunks are not consecutive - possible data hiding between chunks',
                    'idat_positions': idat_positions
                })
        
        # Look for duplicate chunk types (except IDAT)
        chunk_types = {}
        for chunk in self.chunks:
            chunk_type_str = chunk.chunk_type.decode('ascii', errors='replace')
            if chunk_type_str != 'IDAT':
                if chunk_type_str in chunk_types:
                    chunk_types[chunk_type_str] += 1
                else:
                    chunk_types[chunk_type_str] = 1
        
        duplicates = {k: v for k, v in chunk_types.items() if v > 1}
        if duplicates:
            self.suspicious_findings.append({
                'type': 'duplicate_chunks',
                'message': 'Multiple instances of chunk types (unusual for most PNG chunks)',
                'duplicates': duplicates
            })


def analyze_png_chunks(file_path: str) -> Dict[str, Any]:
    """Convenience function to analyze PNG chunks from a file path."""
    analyzer = PNGChunkAnalyzer(Path(file_path))
    return analyzer.analyze_chunks()


if __name__ == '__main__':
    import sys
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    
    console = Console()
    
    if len(sys.argv) != 2:
        console.print("[red]Usage: python chunk_analyzer.py <png_file>[/red]")
        sys.exit(1)
    
    file_path = sys.argv[1]
    if not Path(file_path).exists():
        console.print(f"[red]File not found: {file_path}[/red]")
        sys.exit(1)
    
    console.print(f"[bold blue]Analyzing PNG chunks: {file_path}[/bold blue]")
    
    result = analyze_png_chunks(file_path)
    
    if 'error' in result:
        console.print(Panel(result['error'], title="[red]Error[/red]", border_style="red"))
        sys.exit(1)
    
    # Display chunk summary
    table = Table(title="PNG Chunks Summary")
    table.add_column("Type", style="cyan")
    table.add_column("Length", style="green")
    table.add_column("Offset", style="yellow")
    table.add_column("Critical", style="magenta")
    table.add_column("Standard", style="blue")
    
    for chunk in result['chunk_summary']:
        table.add_row(
            chunk['type'],
            str(chunk['length']),
            chunk['offset'],
            "Yes" if chunk['critical'] else "No",
            "Yes" if chunk['standard'] else "No"
        )
    
    console.print(table)
    
    # Display findings
    if result['findings']:
        console.print("\n[bold red]Suspicious Findings:[/bold red]")
        for finding in result['findings']:
            console.print(f"  • [{finding['type']}] {finding['message']}")
    
    # Display text content
    if result['text_content']:
        console.print("\n[bold green]Text Content Found:[/bold green]")
        for text in result['text_content']:
            console.print(f"  • {text['chunk_type']}: {text['content']}")
