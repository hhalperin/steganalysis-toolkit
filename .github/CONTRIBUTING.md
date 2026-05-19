# Contributing

Contributions are welcome. This document covers how to get started and submit changes.

## Issues and Pull Requests

- **Issues:** [Open an issue](https://github.com/hhalperin/steganalysis-toolkit/issues) for bugs, feature requests, or questions.
- **Pull requests:** Open a PR against the default branch. Link related issues when applicable.

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/hhalperin/steganalysis-toolkit.git
   cd steganalysis-toolkit
   ```

2. Create and activate a virtual environment (`.venv` is the project standard):
   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   # source .venv/bin/activate  # macOS/Linux
   ```

3. Install the package (editable) and runtime deps:

   ```bash
   pip install -e .
   ```

   For optional inpainting support: `pip install -r requirements-lama.txt` (may require a separate env if conflicts occur).

4. Install dev dependencies (tests, formatters):

   ```bash
   pip install -e ".[dev]"
   ```

5. Run tests from the project root:
   ```bash
   pytest
   ```

## Code Style

- **Formatting:** Black (see `[tool.black]` in `pyproject.toml`).
- **Type checking:** mypy (see `[tool.mypy]` in `pyproject.toml`).
- Run from project root; paths like `assets/dirty/photo.png` assume the repo root as the working directory.

## Submitting Changes

1. Create a branch for your work.
2. Make your changes and ensure tests pass.
3. Open a pull request with a clear description of the change.
4. Address any review feedback.
