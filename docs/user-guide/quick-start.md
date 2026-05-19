# Quick Start Guide

## 🚀 Getting Started

This guide will help you quickly get started with the Watermark Combat System for detecting and removing visible watermarks from images.

## Prerequisites

- Python 3.8+
- OpenCV (`pip install opencv-python`)
- NumPy (`pip install numpy`)
- PIL/Pillow (`pip install Pillow`)

## Quick Installation

1. Clone or download the project
2. Navigate to the project directory
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Basic Usage

### 1. Analyze Images for Watermarks

```python
# Simple text watermark detection and removal
python simple_text_remover.py
```

This will automatically process all images in `assets/dirty-images/visible-dirt/` and save cleaned versions to the current directory.

### 2. Advanced Analysis

```python
# Comprehensive watermark analysis
python stega/core/png_analyzer.py assets/dirty-images/image.png
```

### 3. Text-Specific Analysis

```python
# Detect and analyze text watermarks
python stega/detection/text_watermark_detector.py assets/dirty-images/image.jpg
```

### 4. Expert System Consultation

```python
# Get expert recommendations for your problem
python stega/core/expert_router.py "I need to remove repeated text watermarks from images"
```

## Directory Structure

```
assets/                    # All data files
├── dirty-images/         # Original problematic images
├── cleaned/             # Successfully cleaned images
├── battle-videos/       # Battle visualization videos
└── test-results/        # Test outputs and reports

src/                      # Source code
├── core/                # Core system components
├── detection/           # Detection algorithms
├── cleaning/            # Cleaning/removal tools
├── models/              # AI models and training
├── utils/               # Helper utilities
└── visualization/       # Battle visualization

tests/                   # Test suite
docs/                    # Documentation
.cursor/                 # AI expert system
```

## Common Workflows

### Workflow 1: Quick Text Watermark Removal
1. Run `python simple_text_remover.py`
2. Check `*_simple_cleaned.png` files
3. Verify results visually

### Workflow 2: Comprehensive Analysis
1. Run `python stega/core/png_analyzer.py assets/dirty-images/image.png`
2. Review the detailed analysis report
3. Use specific cleaning tools based on findings

### Workflow 3: Expert-Guided Approach
1. Run `python stega/core/expert_router.py "describe your problem"`
2. Follow the recommended expert's guidance
3. Apply suggested solutions

## Troubleshooting

### Common Issues

**"No module named 'cv2'"**
```bash
pip install opencv-python
```

**"No module named 'pytesseract'"** (for OCR features)
```bash
pip install pytesseract
# Also install Tesseract OCR system library
```

**Images not found**
- Ensure images are in `assets/dirty-images/`
- Check file extensions (.jpg, .png, etc.)

## Next Steps

- Read the [User Guide](user-guide/) for detailed workflows
- Explore the [Developer Guide](developer-guide/) for advanced usage
- Check the [Technical Documentation](technical-docs/) for in-depth specifications

## Getting Help

- Check the troubleshooting guide
- Review the expert system recommendations
- Examine existing test results in `assets/test-results/`
- Consult the detailed documentation in `docs/`

