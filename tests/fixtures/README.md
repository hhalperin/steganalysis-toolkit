# Test Fixtures

Place sample PNGs and test images here for integration tests.

- Use small images (< 100KB) for fast tests
- `sample_clean.png` – clean PNG for baseline
- `sample_with_lsb.png` – LSB steganography sample
- `sample_with_unicode.png` – metadata with suspicious Unicode

Generate samples via `python -m stega.examples` (option 1 creates samples in project root).
