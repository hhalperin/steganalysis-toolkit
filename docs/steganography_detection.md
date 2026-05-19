# Steganography Detection Rules and Guidelines

## General Principles

### File Format Analysis
1. **Always verify file signatures** - Check magic bytes match the file extension
2. **Analyze chunk/block structure** - Look for non-standard or custom chunks
3. **Check metadata thoroughly** - Hidden data often lurks in metadata fields
4. **Calculate file size ratios** - Compare expected vs actual file sizes

### Visual Inspection Rules
1. **Look for artifacts** - Unusual patterns, noise, or distortions
2. **Check color distribution** - Unnatural color gradients or banding
3. **Examine edges and smooth areas** - Hidden data often affects these regions
4. **Compare with originals** - Use reverse image search to find base images

## PNG-Specific Detection Rules

### Chunk Analysis
```
Critical chunks (must be present):
- IHDR (Image Header) - First chunk, contains image dimensions and color info
- IDAT (Image Data) - Contains compressed image data, can be split across chunks
- IEND (Image End) - Final chunk, marks end of PNG stream

Suspicious chunk patterns:
- Custom chunk types (non-standard 4-byte identifiers)
- IDAT chunks that aren't consecutive
- Unusually large chunks (>1MB for metadata)
- Multiple instances of unique chunks (except IDAT)
- High entropy in non-IDAT chunks
```

### Text Chunk Analysis
```
Standard text chunks:
- tEXt: Uncompressed Latin-1 text
- zTXt: Compressed text using zlib
- iTXt: International text, supports UTF-8

Red flags:
- Private Use Unicode characters (U+E000-U+F8FF)
- Zero-width characters (U+200B, U+200C, U+200D, etc.)
- Non-printable control characters
- Unusual encoding patterns
- Text length disproportionate to visible content
```

### Steganographic Indicators
```
LSB (Least Significant Bit) hiding:
- Check bit frequency distribution (should be ~50/50 for natural images)
- Test for runs of identical bits (too regular = suspicious)
- Analyze autocorrelation (patterns indicate hidden data)
- Look for even/odd pixel value bias

Frequency domain hiding:
- Unusual DCT coefficient distribution
- High entropy in frequency components
- Spectral anomalies in smooth image regions

Statistical tests:
- Chi-square test for uniform distribution
- Histogram analysis for gaps or artificial uniformity
- Noise analysis in smooth regions
```

## Image Types and Common Hiding Methods

### PNG Format
```
Common hiding locations:
- LSB of pixel values (most common)
- Custom chunks with arbitrary data
- Text metadata fields
- Color palette entries (for indexed images)
- Alpha channel data
- IDAT chunk ordering/spacing

Detection methods:
- Chunk-level parsing and analysis
- LSB statistical analysis
- Metadata Unicode scanning
- Visual filtering (view LSB planes)
```

### JPEG Format
```
Common hiding locations:
- DCT coefficients
- EXIF metadata
- Comment fields
- Quantization tables
- Huffman tables

Detection methods:
- DCT coefficient analysis
- EXIF metadata extraction
- Compression artifact analysis
- Block boundary analysis
```

### General Image Formats
```
Universal hiding methods:
- Appended data after EOF marker
- Embedded files within image data
- Palette manipulation
- Modified file headers
- Compression parameter abuse

Detection approach:
- File size analysis (compare to expected)
- Entropy analysis of different regions
- Binary pattern matching
- Structure validation
```

## Unicode Steganography Rules

### Suspicious Character Ranges
```
Zero-width characters (invisible):
U+200B  ZERO WIDTH SPACE
U+200C  ZERO WIDTH NON-JOINER
U+200D  ZERO WIDTH JOINER
U+200E  LEFT-TO-RIGHT MARK
U+200F  RIGHT-TO-LEFT MARK
U+2060  WORD JOINER
U+2061  FUNCTION APPLICATION
U+2062  INVISIBLE TIMES
U+2063  INVISIBLE SEPARATOR

Private Use Areas (common for steganography):
U+E000-U+F8FF   Basic Private Use Area
U+F0000-U+FFFFD Private Use Area-A
U+100000-U+10FFFD Private Use Area-B

Format characters (suspicious in normal text):
U+00AD  SOFT HYPHEN
U+034F  COMBINING GRAPHEME JOINER
U+061C  ARABIC LETTER MARK
```

### Detection Patterns
```
Text-based steganography indicators:
- Multiple zero-width characters in sequence
- Private use characters mixed with normal text
- Variation selectors without corresponding base characters
- Non-characters (should never appear in valid text)
- Script mixing (multiple writing systems unusually combined)
```

## Analysis Workflow

### 1. Initial Triage
```
File integrity checks:
- Verify file opens correctly in standard viewers
- Check file signature matches extension
- Calculate and verify checksums
- Compare file size to expected dimensions

Structure analysis:
- Parse all chunks/segments
- Identify non-standard components
- Check ordering and dependencies
- Look for trailing data
```

### 2. Content Analysis
```
Visual inspection:
- View image normally
- Extract and view LSB planes
- Apply high-pass filters to reveal noise
- Check alpha channel separately

Statistical analysis:
- Calculate pixel value histograms
- Measure entropy across regions
- Test for randomness in LSBs
- Analyze color distribution patterns
```

### 3. Metadata Examination
```
Text analysis:
- Extract all text metadata
- Scan for Unicode anomalies
- Check encoding consistency
- Look for hidden characters

Binary analysis:
- Hex dump suspicious sections
- Search for embedded file signatures
- Check for compression artifacts
- Analyze padding and alignment
```

## Tools and Commands

### Essential Tools
```
Python libraries:
- Pillow (PIL) for image processing
- numpy for numerical analysis
- matplotlib for visualization
- struct for binary parsing

External tools:
- binwalk: Embedded file detection
- steghide: General steganography tool
- zsteg: Ruby-based stego detection
- exiftool: Metadata extraction
- hexdump: Binary inspection
```

### Quick Detection Commands
```bash
# Check for embedded files
binwalk image.png

# Analyze with steghide
steghide info image.png

# Extract metadata
exiftool image.png

# View file structure
xxd image.png | head -20

# Ruby-based analysis (if zsteg installed)
zsteg image.png
```

## Risk Assessment

### Severity Levels
```
HIGH RISK:
- Custom chunks with high entropy
- Private use Unicode characters
- Multiple steganographic indicators
- File size inconsistencies
- CRC failures or structural errors

MEDIUM RISK:
- Minor structural anomalies
- Few suspicious Unicode characters
- Unusual metadata content
- Single steganographic indicator

LOW RISK:
- Standard PNG structure
- Normal metadata content
- Expected statistical properties
- No anomalous indicators
```

### Response Actions
```
High risk files:
- Quarantine immediately
- Full forensic analysis
- Source investigation
- Multiple tool analysis

Medium risk files:
- Detailed investigation
- Additional testing
- Monitor for patterns
- Document findings

Low risk files:
- Standard processing
- Routine documentation
- Periodic re-evaluation
```

## Investigation Documentation

### Required Information
```
File identification:
- Full file path and name
- File size and creation date
- MD5, SHA-1, and SHA-256 hashes
- Source location and custody chain

Technical analysis:
- Tool versions and settings used
- Analysis timestamps
- Specific findings and evidence
- Screenshots of anomalies

Risk assessment:
- Severity rating and justification
- Potential impact assessment
- Recommended actions
- Follow-up requirements
```
