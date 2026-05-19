"""
Entry point for python -m stega
Delegates to the stk CLI (``stega.cli:main``).
"""

import sys
from pathlib import Path

# Ensure project root is on path
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

if __name__ == "__main__":
    from stega.cli import main
    sys.exit(main())
