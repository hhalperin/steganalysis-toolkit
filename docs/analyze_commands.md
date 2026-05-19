# PNG Analysis Commands

## Quick Analysis
```bash
# Basic PNG analysis
python stega/core/png_analyzer.py image.png

# Full analysis with JSON export
python stega/core/png_analyzer.py image.png --export json --output analysis.json

# Text report export
python stega/core/png_analyzer.py image.png --export txt --output report.txt
```

## Individual Component Analysis

### Chunk Analysis
```bash
# Analyze PNG chunks only
python stega/detection/chunk_analyzer.py image.png

# Look for specific chunk types
python -c "
from stega.detection.chunk_analyzer import PNGChunkAnalyzer
from pathlib import Path
analyzer = PNGChunkAnalyzer(Path('image.png'))
result = analyzer.analyze_chunks()
custom_chunks = result.get('custom_chunks', [])
if custom_chunks:
    print('Custom chunks found:')
    for chunk in custom_chunks:
        print(f'  {chunk[\"type\"]}: {chunk[\"length\"]} bytes at {chunk[\"offset\"]}')
else:
    print('No custom chunks found')
"
```

### Unicode Analysis
```bash
# Scan for Unicode anomalies in text
python stega/detection/unicode_scanner.py "suspicious text with hidden chars"

# Scan text file for Unicode anomalies
python stega/detection/unicode_scanner.py text_file.txt

# Extract text from PNG and analyze Unicode
python -c "
from stega.detection.chunk_analyzer import PNGChunkAnalyzer
from stega.detection.unicode_scanner import scan_unicode_in_text
from pathlib import Path

analyzer = PNGChunkAnalyzer(Path('image.png'))
analyzer.parse_chunks()

for chunk in analyzer.chunks:
    text = chunk.get_text_content()
    if text:
        print(f'Chunk {chunk.chunk_type.decode()}: {text[:100]}...')
        result = scan_unicode_in_text(text)
        if result['suspicious_characters']:
            print(f'  Found {len(result[\"suspicious_characters\"])} suspicious Unicode chars')
"
```

### Steganography Detection
```bash
# Run steganography analysis
python stega/detection/steganography.py image.png

# Quick LSB check
python -c "
from stega.detection.steganography import SteganographyDetector
detector = SteganographyDetector('image.png')
result = detector.analyze_lsb_patterns()
print(f'LSB Analysis: Score={result.score:.3f}, Suspicious={result.is_suspicious}')
"
```

## Batch Analysis
```bash
# Analyze multiple PNG files
for file in *.png; do
    echo "Analyzing: $file"
    python src/png_analyzer.py "$file" --export json --output "${file%.png}_analysis.json"
done

# Find suspicious files in directory
python -c "
import os
from pathlib import Path
from stega.core.png_analyzer import PNGForensicsAnalyzer

suspicious_files = []
for png_file in Path('.').glob('*.png'):
    analyzer = PNGForensicsAnalyzer(str(png_file))
    results = analyzer.analyze_file()
    risk_level = results.get('forensics_summary', {}).get('overall_risk_level', 'low')
    if risk_level in ['high', 'medium']:
        suspicious_files.append((str(png_file), risk_level))

if suspicious_files:
    print('Suspicious files found:')
    for file, risk in suspicious_files:
        print(f'  {file}: {risk.upper()} risk')
else:
    print('No suspicious files found')
"
```

## Advanced Analysis

### Hex Dump Inspection
```bash
# View PNG header and chunks
hexdump -C image.png | head -20

# Extract specific chunk by offset (replace OFFSET with actual hex offset)
dd if=image.png bs=1 skip=$((0xOFFSET)) count=100 | hexdump -C

# Look for embedded files or data
binwalk image.png
```

### Manual LSB Extraction
```bash
# Extract LSB bits manually (requires custom script)
python -c "
from PIL import Image
import numpy as np

img = Image.open('image.png').convert('RGB')
data = np.array(img)

# Extract LSBs from red channel
lsb_bits = data[:,:,0] & 1
print('LSB pattern (first 100 pixels):', ''.join(str(b) for b in lsb_bits.flatten()[:100]))

# Try interpreting as ASCII (every 8 bits)
lsb_flat = lsb_bits.flatten()
chars = []
for i in range(0, min(len(lsb_flat), 800), 8):
    byte_val = sum(lsb_flat[i+j] << j for j in range(8))
    if 32 <= byte_val <= 126:  # Printable ASCII
        chars.append(chr(byte_val))
    else:
        chars.append('.')

print('Potential ASCII:', ''.join(chars[:100]))
"
```

### Third-party Tool Integration
```bash
# Use steghide for extraction attempts
steghide extract -sf image.png

# Use zsteg for detection (Ruby tool)
zsteg image.png

# Use binwalk for embedded file detection
binwalk -e image.png

# Use exiftool for metadata analysis
exiftool image.png

# Use ImageMagick for image analysis
identify -verbose image.png
```

## Export and Documentation
```bash
# Generate comprehensive report
python stega/core/png_analyzer.py image.png --export json --output report.json
python -c "
import json
with open('report.json') as f:
    data = json.load(f)

print('=== PNG FORENSICS REPORT ===')
print(f'File: {data[\"file_info\"][\"name\"]}')
print(f'Risk: {data[\"forensics_summary\"][\"overall_risk_level\"].upper()}')
print(f'Summary: {data[\"forensics_summary\"][\"executive_summary\"]}')
print()
print('Technical Findings:')
for finding in data['forensics_summary']['technical_findings']:
    print(f'  - {finding[\"category\"]}: {finding[\"description\"]}')
"

# Create investigation timeline
python -c "
from datetime import datetime
import json

with open('report.json') as f:
    data = json.load(f)

file_info = data['file_info']
print('INVESTIGATION TIMELINE')
print('=' * 50)
print(f'File Creation: {file_info[\"created\"]}')
print(f'File Modified: {file_info[\"modified\"]}')
print(f'Analysis Date: {data[\"analysis_timestamp\"]}')
print(f'File Hash: {file_info[\"sha256\"]}')
"
```
