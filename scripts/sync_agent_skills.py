#!/usr/bin/env python3
"""Copy project skills from `.agents/skills/` into `.claude/skills/` for Claude Code.

Canonical source: `.agents/skills/<name>/` (Agent Skills layout). Claude Code expects
`.claude/skills/<name>/`. Run from repo root after editing skills under `.agents/skills/`.

Usage:
    python scripts/sync_agent_skills.py
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    src = root / ".agents" / "skills"
    dst = root / ".claude" / "skills"
    if not src.is_dir():
        print(f"Missing {src}", file=sys.stderr)
        return 1
    dst.mkdir(parents=True, exist_ok=True)
    for skill in sorted(src.iterdir()):
        if not skill.is_dir():
            continue
        target = dst / skill.name
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(skill, target)
        print(f"Synced {skill.name} -> {target.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
