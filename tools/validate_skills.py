#!/usr/bin/env python3
"""
Validate that every shotkit SKILL.md has the required frontmatter.

Required fields:
- name (string, matches the directory name)
- description (string, at least 50 characters)

Scope. The check covers the five shotkit skills and nothing else. After ./install.sh
the tools sit in ~/.claude/shotkit-tools/ next to ~/.claude/skills/, which also holds
every other skill the user has installed. Those are not shotkit's to judge.

In a repo clone, a directory under skills/ that is not one of the five is an error:
install.sh would skip it, so it would never reach a user.

Usage:
    python tools/validate_skills.py
    python ~/.claude/shotkit-tools/validate_skills.py
    python tools/validate_skills.py --selftest
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not installed. Run: pip install pyyaml")
    sys.exit(1)

from _shotkit import INSTALLED, SHOTKIT_SKILLS, SKILLS_ROOT, shotkit_skill_dirs


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

    if not skill_dir.is_dir():
        errors.append("skill directory is missing")
        return errors

    if not skill_md.exists():
        errors.append("missing SKILL.md")
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


def check_tree(skills_root: Path, installed: bool) -> dict[str, list[str]]:
    """Errors keyed by skill directory name. Only shotkit's skills are judged."""
    results: dict[str, list[str]] = {}
    for skill_dir in shotkit_skill_dirs(skills_root):
        results[skill_dir.name] = validate_skill(skill_dir)

    if not installed and skills_root.is_dir():
        for extra in sorted(d for d in skills_root.iterdir() if d.is_dir()):
            if extra.name not in SHOTKIT_SKILLS:
                results[extra.name] = [
                    "not one of the five shotkit skills, so install.sh would skip it; "
                    "add it to SHOTKIT_SKILLS in tools/_shotkit.py and to install.sh"
                ]
    return results


def _write_skill(root: Path, name: str, description: str | None = None) -> None:
    d = root / name
    d.mkdir(parents=True)
    desc = description if description is not None else (
        "A skill description long enough to pass the fifty character floor."
    )
    (d / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {desc}\n---\n\n# {name}\n", encoding="utf-8"
    )


def selftest() -> int:
    import tempfile

    ok = True

    def expect(label: str, passed: bool, detail: object = "") -> None:
        nonlocal ok
        if passed:
            print(f"  ok    selftest: {label}")
        else:
            print(f"  FAIL  selftest: {label} {detail}")
            ok = False

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "skills"
        for name in SHOTKIT_SKILLS:
            _write_skill(root, name)
        # Another skill the user has installed, with no frontmatter at all.
        (root / "someone-elses-skill").mkdir()
        (root / "someone-elses-skill" / "SKILL.md").write_text("# no frontmatter\n")

        installed = check_tree(root, installed=True)
        expect(
            "an installed tree ignores skills shotkit does not own",
            not any(installed.values()) and "someone-elses-skill" not in installed,
            installed,
        )

        repo = check_tree(root, installed=False)
        expect(
            "a repo clone flags a skill directory install.sh would skip",
            bool(repo.get("someone-elses-skill")),
            repo,
        )

        broken = Path(tmp) / "broken"
        for name in SHOTKIT_SKILLS:
            _write_skill(broken, name, "short" if name == "visual-prompt-forge" else None)
        result = check_tree(broken, installed=True)
        expect(
            "a shotkit skill with a short description is caught",
            bool(result.get("visual-prompt-forge")),
            result,
        )

        missing = Path(tmp) / "missing"
        for name in SHOTKIT_SKILLS[:-1]:
            _write_skill(missing, name)
        result = check_tree(missing, installed=True)
        expect(
            "a missing shotkit skill is caught",
            bool(result.get(SHOTKIT_SKILLS[-1])),
            result,
        )

    print()
    print("Selftest passed." if ok else "Selftest FAILED.")
    return 0 if ok else 1


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()

    if not SKILLS_ROOT.exists():
        print(f"ERROR: skills directory not found at {SKILLS_ROOT}")
        return 1

    results = check_tree(SKILLS_ROOT, INSTALLED)
    print(f"Validating {len(results)} skill(s) in {SKILLS_ROOT}/")
    print()

    total_errors = 0
    for name, errors in results.items():
        if not errors:
            print(f"  ok    {name}")
        else:
            total_errors += len(errors)
            print(f"  FAIL  {name}")
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
