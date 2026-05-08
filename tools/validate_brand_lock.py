#!/usr/bin/env python3
"""
Validate a brand-lock Markdown file has the required sections.

Required headings (case-insensitive, in any order):
- Identity
- Palette
- Typography
- Mood adjectives
- Never list
- Aspect ratios
- Color grade direction
- Motion language
- Voice rules

Required identity fields (under ## Identity):
- Brand
- One-line description
- Archetype
- Voice posture

Usage:
    python tools/validate_brand_lock.py path/to/brand-lock.md
    python tools/validate_brand_lock.py brand-packs/_template.md brand-packs/whystrohm.md
"""

from __future__ import annotations
import re
import sys
from pathlib import Path


REQUIRED_SECTIONS = {
    "identity",
    "palette",
    "typography",
    "mood adjectives",
    "never list",
    "aspect ratios",
    "color grade direction",
    "motion language",
    "voice rules",
}

REQUIRED_IDENTITY_FIELDS = {
    "brand",
    "one-line description",
    "archetype",
    "voice posture",
}


def parse_headings(text: str) -> list[tuple[int, str]]:
    """Return list of (level, heading_text_lower) for every Markdown heading."""
    out = []
    for line in text.splitlines():
        m = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if m:
            level = len(m.group(1))
            heading = m.group(2).strip().lower()
            out.append((level, heading))
    return out


def extract_section(text: str, heading_lower: str) -> str:
    """Extract the body of a section by its heading. Returns empty string if not found."""
    lines = text.splitlines()
    in_section = False
    section_lines: list[str] = []
    section_level: int | None = None
    for line in lines:
        m = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if m:
            level = len(m.group(1))
            heading = m.group(2).strip().lower()
            if not in_section:
                if heading == heading_lower:
                    in_section = True
                    section_level = level
                    continue
            else:
                if section_level is not None and level <= section_level:
                    break
        if in_section:
            section_lines.append(line)
    return "\n".join(section_lines)


def validate_brand_lock(path: Path) -> list[str]:
    """Return a list of errors. Empty list = passes."""
    errors: list[str] = []

    if not path.exists():
        return [f"file does not exist: {path}"]

    text = path.read_text(encoding="utf-8")
    headings = parse_headings(text)
    heading_set = {h for _, h in headings}

    missing = REQUIRED_SECTIONS - heading_set
    for m in sorted(missing):
        errors.append(f"missing section: ## {m.title()}")

    if "identity" in heading_set:
        identity_body = extract_section(text, "identity").lower()
        for field in sorted(REQUIRED_IDENTITY_FIELDS):
            if field not in identity_body:
                errors.append(f"identity section missing field: '{field}'")

    if "palette" in heading_set:
        palette_body = extract_section(text, "palette")
        if not re.search(r"#[0-9A-Fa-f]{6}|#[_]{6}", palette_body):
            errors.append("palette section has no hex color values (or template placeholders)")

    return errors


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python tools/validate_brand_lock.py <path-to-brand-lock.md> [...]")
        return 2

    paths = [Path(p) for p in sys.argv[1:]]
    print(f"Validating {len(paths)} brand-lock file(s)")
    print()

    total_errors = 0
    for path in paths:
        errors = validate_brand_lock(path)
        if not errors:
            print(f"  ok    {path}")
        else:
            total_errors += len(errors)
            print(f"  FAIL  {path}")
            for err in errors:
                print(f"        - {err}")

    print()
    if total_errors == 0:
        print("All brand-locks valid.")
        return 0
    print(f"FAILED: {total_errors} error(s) across brand-locks.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
