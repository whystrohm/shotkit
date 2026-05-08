#!/usr/bin/env python3
"""
Validate every SKILL.md in the repo has the required frontmatter.

Required fields:
- name (string, matches the directory name)
- description (string, non-empty)

Run from repo root:
    python tools/validate_skills.py
"""

from __future__ import annotations
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not installed. Run: pip install pyyaml")
    sys.exit(1)


REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"


def parse_frontmatter(path: Path) -> dict | None:
    """Extract YAML frontmatter from a Markdown file. Returns None if absent."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    try:
        return yaml.safe_load(parts[1])
    except yaml.YAMLError as e:
        print(f"  YAML parse error: {e}")
        return None


def validate_skill(skill_dir: Path) -> list[str]:
    """Return a list of errors. Empty list = passes."""
    errors: list[str] = []
    skill_md = skill_dir / "SKILL.md"

    if not skill_md.exists():
        errors.append(f"missing SKILL.md")
        return errors

    fm = parse_frontmatter(skill_md)
    if fm is None:
        errors.append("missing or invalid YAML frontmatter")
        return errors

    if "name" not in fm:
        errors.append("frontmatter missing 'name'")
    elif not isinstance(fm["name"], str) or not fm["name"].strip():
        errors.append("frontmatter 'name' must be a non-empty string")
    elif fm["name"] != skill_dir.name:
        errors.append(
            f"frontmatter name '{fm['name']}' does not match directory name '{skill_dir.name}'"
        )

    if "description" not in fm:
        errors.append("frontmatter missing 'description'")
    elif not isinstance(fm["description"], str) or not fm["description"].strip():
        errors.append("frontmatter 'description' must be a non-empty string")
    elif len(fm["description"]) < 50:
        errors.append(
            f"frontmatter description is too short ({len(fm['description'])} chars). "
            "Aim for >= 50 chars to support skill triggering."
        )

    return errors


def main() -> int:
    if not SKILLS_DIR.exists():
        print(f"ERROR: skills directory not found at {SKILLS_DIR}")
        return 1

    skill_dirs = sorted([d for d in SKILLS_DIR.iterdir() if d.is_dir()])
    if not skill_dirs:
        print(f"ERROR: no skill directories found in {SKILLS_DIR}")
        return 1

    print(f"Validating {len(skill_dirs)} skill(s) in {SKILLS_DIR.relative_to(REPO_ROOT)}/")
    print()

    total_errors = 0
    for skill_dir in skill_dirs:
        errors = validate_skill(skill_dir)
        rel = skill_dir.relative_to(REPO_ROOT)
        if not errors:
            print(f"  ok    {rel}")
        else:
            total_errors += len(errors)
            print(f"  FAIL  {rel}")
            for err in errors:
                print(f"        - {err}")

    print()
    if total_errors == 0:
        print("All skills valid.")
        return 0
    print(f"FAILED: {total_errors} error(s) across skills.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
