# Hidden Data Extraction Guidelines

## General Approach to Hidden Data

### Initial Assessment
1. **Identify the container format** - PNG, JPEG, GIF, etc.
2. **Determine likely hiding method** - LSB, metadata, compression, custom chunks
3. **Estimate payload size** - Statistical analysis can hint at hidden data volume
4. **Consider extraction tools** - Match tools to suspected method

### Extraction Strategy
```
Progressive approach:
1. Automated detection tools first (binwalk, steghide, zsteg)
2. Manual analysis of suspicious regions
3. Custom extraction scripts for specific patterns
4. Brute-force approaches if password protected
```

## PNG-Specific Extraction Methods

### Chunk-Based Hidden Data
```python
# Extract data from custom chunks
from stega.detection.chunk_analyzer import PNGChunkAnalyzer
from pathlib import Path

def extract_custom_chunk_data(png_path, chunk_type):
    analyzer = PNGChunkAnalyzer(Path(png_path))
    analyzer.parse_chunks()

    for chunk in analyzer.chunks:
        if chunk.chunk_type == chunk_type.encode():
            return chunk.data
    return None

# Usage: Extract data from chunk named 'pRiv'
hidden_data = extract_custom_chunk_data('image.png', 'pRiv')
```

### LSB Extraction
```python
# Extract LSB data from image pixels
from PIL import Image
import numpy as np

def extract_lsb_data(image_path, channels='RGB', bit_count=1):
    """
    Extract LSB data from image channels.
    channels: Which color channels to use ('R', 'G', 'B', 'RGB', 'ALL')
    bit_count: Number of LSBs to extract per pixel (1-8)
    """
    img = Image.open(image_path).convert('RGB')
    pixels = np.array(img)

    extracted_bits = []

    if 'R' in channels or channels == 'ALL':
        r_lsbs = pixels[:,:,0] & ((1 << bit_count) - 1)
        extracted_bits.extend(r_lsbs.flatten())

    if 'G' in channels or channels == 'ALL':
        g_lsbs = pixels[:,:,1] & ((1 << bit_count) - 1)
        extracted_bits.extend(g_lsbs.flatten())

    if 'B' in channels or channels == 'ALL':
        b_lsbs = pixels[:,:,2] & ((1 << bit_count) - 1)
        extracted_bits.extend(b_lsbs.flatten())

    return extracted_bits

# Convert extracted bits to bytes
def bits_to_bytes(bits, bits_per_byte=8):
    bytes_data = []
    for i in range(0, len(bits), bits_per_byte):
        if i + bits_per_byte <= len(bits):
            byte_val = sum(bits[i+j] << j for j in range(bits_per_byte))
            bytes_data.append(byte_val)
    return bytes(bytes_data)

# Usage example
lsb_bits = extract_lsb_data('image.png', 'R', 1)
hidden_bytes = bits_to_bytes(lsb_bits)

# Try to decode as text
try:
    hidden_text = hidden_bytes.decode('utf-8', errors='ignore')
    print("Hidden text:", hidden_text[:100])
except:
    print("Binary data found, length:", len(hidden_bytes))
```

### Text Metadata Extraction
```python
# Extract and decode text from PNG metadata
from stega.detection.chunk_analyzer import PNGChunkAnalyzer
from stega.detection.unicode_scanner import UnicodeScanner

def extract_all_text_content(png_path):
    analyzer = PNGChunkAnalyzer(Path(png_path))
    analyzer.parse_chunks()

    all_text = []
    for chunk in analyzer.chunks:
        text = chunk.get_text_content()
        if text:
            all_text.append({
                'chunk_type': chunk.chunk_type.decode(),
                'offset': chunk.offset,
                'text': text
            })

    return all_text

def decode_unicode_steganography(text):
    """Decode Unicode-based steganography."""
    scanner = UnicodeScanner()
    scanner.scan_text(text)

    # Extract private use characters
    private_chars = []
    for match in scanner.matches:
        if 0xE000 <= match.codepoint <= 0xF8FF:  # Private Use Area
            private_chars.append(match.codepoint - 0xE000)  # Convert to data

    # Convert to binary
    if private_chars:
        binary_data = bytes(private_chars)
        try:
            decoded = binary_data.decode('utf-8', errors='ignore')
            return decoded
        except:
            return binary_data

    return None
```

## Common extraction patterns

### Password-Protected Steganography
```bash
# Try common passwords with steghide
passwords=("password" "123456" "secret" "hidden" "stego" "")

for pwd in "${passwords[@]}"; do
    echo "Trying password: '$pwd'"
    steghide extract -sf image.png -p "$pwd" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "Success with password: '$pwd'"
        break
    fi
done
```

### Multi-stage recovery
```python
# Example: LSB extraction followed by decompression
import zlib
import base64

def multi_stage_extraction(image_path):
    # Stage 1: Extract LSB data
    lsb_bits = extract_lsb_data(image_path, 'RGB', 1)
    lsb_bytes = bits_to_bytes(lsb_bits)

    # Stage 2: Try decompression
    try:
        decompressed = zlib.decompress(lsb_bytes)
        print("Decompression successful")

        # Stage 3: Try base64 decoding
        try:
            decoded = base64.b64decode(decompressed)
            print("Base64 decoding successful")
            return decoded
        except:
            return decompressed

    except zlib.error:
        print("Not compressed data")

        # Alternative: Try base64 directly
        try:
            decoded = base64.b64decode(lsb_bytes)
            return decoded
        except:
            return lsb_bytes
```

### File Signature Detection
```python
# Detect embedded files by signature
def detect_embedded_files(data):
    signatures = {
        b'\x89PNG\r\n\x1a\n': 'PNG Image',
        b'\xff\xd8\xff': 'JPEG Image',
        b'GIF8': 'GIF Image',
        b'PK\x03\x04': 'ZIP Archive',
        b'PDF': 'PDF Document',
        b'\x7fELF': 'ELF Executable',
        b'MZ': 'PE Executable',
        b'\xca\xfe\xba\xbe': 'Java Class',
    }

    found_files = []
    for i in range(len(data) - 8):
        for sig, file_type in signatures.items():
            if data[i:i+len(sig)] == sig:
                found_files.append({
                    'offset': i,
                    'type': file_type,
                    'signature': sig.hex()
                })

    return found_files
```

## Advanced Extraction Techniques

### Frequency Domain Analysis
```python
# Extract data hidden in frequency domain
import numpy as np
from scipy import fftpack

def extract_frequency_domain_data(image_path):
    from PIL import Image

    img = Image.open(image_path).convert('L')  # Grayscale
    img_array = np.array(img, dtype=float)

    # Apply 2D DCT
    dct_coeffs = fftpack.dctn(img_array)

    # Extract LSBs from DCT coefficients
    # Focus on medium-frequency components (not DC or high-freq noise)
    h, w = dct_coeffs.shape
    mid_freq_region = dct_coeffs[h//4:3*h//4, w//4:3*w//4]

    # Quantize and extract LSBs
    quantized = np.round(mid_freq_region)
    lsb_data = (quantized.astype(int) & 1).flatten()

    return bits_to_bytes(lsb_data)
```

### Pattern-Based Extraction
```python
# Extract data based on specific patterns
def extract_pattern_data(data, pattern_start, pattern_end=None):
    """Extract data between specific byte patterns."""
    results = []

    start_pos = 0
    while True:
        # Find start pattern
        start_idx = data.find(pattern_start, start_pos)
        if start_idx == -1:
            break

        start_idx += len(pattern_start)

        if pattern_end:
            # Find end pattern
            end_idx = data.find(pattern_end, start_idx)
            if end_idx == -1:
                break

            extracted = data[start_idx:end_idx]
            results.append(extracted)
            start_pos = end_idx + len(pattern_end)
        else:
            # Extract rest of data
            results.append(data[start_idx:])
            break

    return results

# Usage examples
png_data = open('image.png', 'rb').read()

# Extract data between custom markers
hidden_chunks = extract_pattern_data(png_data, b'HIDE', b'ENDD')

# Extract data after EOF marker
trailing_data = extract_pattern_data(png_data, b'IEND\x00\x00\x00\x00')
```

## Automated Extraction Pipeline

### Comprehensive Extraction Function
```python
def comprehensive_extraction(image_path):
    """
    Run multiple extraction methods and return all findings.
    """
    results = {}

    # 1. Chunk-based extraction
    try:
        analyzer = PNGChunkAnalyzer(Path(image_path))
        chunk_analysis = analyzer.analyze_chunks()

        custom_chunks = chunk_analysis.get('custom_chunks', [])
        if custom_chunks:
            results['custom_chunks'] = custom_chunks
    except Exception as e:
        results['chunk_error'] = str(e)

    # 2. LSB extraction (multiple methods)
    try:
        # Single bit LSB
        lsb1_data = extract_lsb_data(image_path, 'RGB', 1)
        lsb1_bytes = bits_to_bytes(lsb1_data)
        if len(lsb1_bytes) > 10:  # Only if substantial data
            results['lsb_1bit'] = lsb1_bytes[:1000]  # Truncate for analysis

        # Two bit LSB
        lsb2_data = extract_lsb_data(image_path, 'RGB', 2)
        lsb2_bytes = bits_to_bytes(lsb2_data, 2)
        if len(lsb2_bytes) > 10:
            results['lsb_2bit'] = lsb2_bytes[:1000]

    except Exception as e:
        results['lsb_error'] = str(e)

    # 3. Text metadata extraction
    try:
        text_content = extract_all_text_content(image_path)
        if text_content:
            results['text_metadata'] = text_content

            # Check for Unicode steganography
            for text_item in text_content:
                decoded = decode_unicode_steganography(text_item['text'])
                if decoded:
                    results['unicode_decoded'] = decoded

    except Exception as e:
        results['text_error'] = str(e)

    # 4. File signature scanning
    try:
        with open(image_path, 'rb') as f:
            file_data = f.read()

        embedded_files = detect_embedded_files(file_data)
        if embedded_files:
            results['embedded_files'] = embedded_files

    except Exception as e:
        results['signature_error'] = str(e)

    return results
```

### Batch Processing
```python
# Process multiple files
def batch_extract(file_pattern='*.png'):
    from glob import glob

    findings = {}

    for file_path in glob(file_pattern):
        print(f"Processing: {file_path}")

        try:
            extraction_results = comprehensive_extraction(file_path)

            # Only store files with findings
            if any(key not in ['chunk_error', 'lsb_error', 'text_error', 'signature_error']
                   for key in extraction_results.keys()):
                findings[file_path] = extraction_results

        except Exception as e:
            print(f"Error processing {file_path}: {e}")

    return findings
```

## Validation and Verification

### Data Integrity Checks
```python
def validate_extracted_data(data):
    """Validate and analyze extracted data."""
    if not data:
        return {'valid': False, 'reason': 'No data'}

    analysis = {
        'valid': True,
        'length': len(data),
        'entropy': calculate_entropy(data),
        'printable_ratio': sum(32 <= b <= 126 for b in data) / len(data),
        'null_bytes': data.count(0),
        'file_signatures': detect_embedded_files(data)
    }

    # Heuristics for data validity
    if analysis['entropy'] < 1.0:  # Very low entropy
        analysis['likely_padding'] = True

    if analysis['printable_ratio'] > 0.8:  # Mostly printable
        analysis['likely_text'] = True
        try:
            analysis['decoded_text'] = data.decode('utf-8', errors='ignore')[:200]
        except:
            pass

    if analysis['file_signatures']:
        analysis['likely_embedded_file'] = True

    return analysis

def calculate_entropy(data):
    """Calculate Shannon entropy of data."""
    if not data:
        return 0

    byte_counts = [0] * 256
    for byte in data:
        byte_counts[byte] += 1

    entropy = 0
    length = len(data)

    for count in byte_counts:
        if count > 0:
            p = count / length
            entropy -= p * np.log2(p)

    return entropy
```
