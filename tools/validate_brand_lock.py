#!/usr/bin/env python3
"""
Validate a brand-lock Markdown file.

Two modes, because a brand-pack and a snapshot are not the same artifact.

A brand-pack (brand-packs/*.md) is a source document. An unfilled template is a legal
brand-pack: that is what a template is for.

A snapshot (brand-lock.snapshot.md, written into an output tree) is a provenance
record. It has to carry the header storyboard-architect promises to write, and if it
still contains template placeholders then the run it governs was built against nothing.
Pass --snapshot to check those extra rules, and --require-configured to reject
placeholders outright.

Required headings (case-insensitive, in any order):
- Identity, Palette, Typography, Mood adjectives, Never list,
  Aspect ratios, Color grade direction, Motion language, Voice rules

Required identity fields (under ## Identity):
- Brand, One-line description, Archetype, Voice posture

Usage:
    python tools/validate_brand_lock.py path/to/brand-lock.md [...]
    python tools/validate_brand_lock.py --snapshot path/to/brand-lock.snapshot.md
    python tools/validate_brand_lock.py --require-configured brand-packs/whystrohm.md
    python tools/validate_brand_lock.py --snapshots            # every bundled snapshot
    python tools/validate_brand_lock.py --selftest
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from _shotkit import (
    ISO_INSTANT_RE,
    PALETTE_ROLES,
    REPO_ROOT,
    is_unconfigured,
    parse_palette,
    parse_snapshot_header,
    parse_typography,
)

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

ISO_DATE_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")


def parse_headings(text: str) -> list[tuple[int, str]]:
    """Return list of (level, heading_text_lower) for every Markdown heading."""
    out = []
    for line in text.splitlines():
        m = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if m:
            out.append((len(m.group(1)), m.group(2).strip().lower()))
    return out


def extract_section(text: str, heading_lower: str) -> str:
    """Extract the body of a section by its heading. Empty string if not found."""
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


def check_structure(text: str) -> list[str]:
    errors: list[str] = []
    heading_set = {h for _, h in parse_headings(text)}

    for missing in sorted(REQUIRED_SECTIONS - heading_set):
        errors.append(f"missing section: ## {missing.title()}")

    if "identity" in heading_set:
        identity_body = extract_section(text, "identity").lower()
        for field in sorted(REQUIRED_IDENTITY_FIELDS):
            if field not in identity_body:
                errors.append(f"identity section missing field: '{field}'")

    if "palette" in heading_set:
        palette_body = extract_section(text, "palette")
        if not re.search(r"#[0-9A-Fa-f]{6}|#_{6}", palette_body):
            errors.append(
                "palette section has no hex color values (or template placeholders)"
            )

    return errors


def check_roles(text: str) -> list[str]:
    """
    The palette role names the HTML preview maps onto CSS variables.

    A brand-lock is free to add rows, but a missing role means the preview silently
    renders that slot in a generic default, so it is worth saying out loud.
    """
    warnings: list[str] = []
    palette = parse_palette(text)
    for role in PALETTE_ROLES:
        if not any(role in name for name in palette):
            warnings.append(
                f"palette has no '{role}' role; the HTML preview will fall back to a "
                f"generic color for it"
            )
    return warnings


def check_typography(text: str) -> list[str]:
    warnings: list[str] = []
    fonts = parse_typography(text)
    for key, label in (("display_font", "Display"), ("body_font", "Body")):
        if not fonts.get(key):
            warnings.append(
                f"typography declares no {key.replace('_', ' ')} in a readable form; "
                f'expected ``**{label} font:** `Font Name Weight` `` with the name '
                f"backticked immediately after the label"
            )
    return warnings


def check_snapshot(text: str) -> tuple[list[str], list[str]]:
    """The provenance header storyboard-architect writes into every snapshot."""
    errors: list[str] = []
    warnings: list[str] = []
    header = parse_snapshot_header(text)

    taken = header["snapshot_taken"]
    if not taken:
        errors.append(
            "snapshot is missing its '<!-- snapshot taken: ... -->' header, so nothing "
            "records when this brand state was frozen"
        )
    elif ISO_INSTANT_RE.match(taken):
        pass
    elif ISO_DATE_RE.match(taken):
        warnings.append(
            f"snapshot taken '{taken}' is a date with no time; a full UTC instant "
            f"(YYYY-MM-DDThh:mm:ssZ) is what makes two runs on one day distinguishable"
        )
    else:
        errors.append(
            f"snapshot taken '{taken}' is not ISO-8601; expected YYYY-MM-DDThh:mm:ssZ"
        )

    if not header["source"]:
        errors.append(
            "snapshot is missing its '<!-- source: ... -->' header, so nothing records "
            "which brand-pack it was copied from"
        )

    return errors, warnings


def validate_brand_lock(
    path: Path, snapshot: bool = False, require_configured: bool = False
) -> tuple[list[str], list[str]]:
    """Return (errors, warnings). Empty errors means it passes."""
    if not path.exists():
        return ([f"file does not exist: {path}"], [])

    text = path.read_text(encoding="utf-8")
    errors = check_structure(text)
    warnings = check_roles(text) + check_typography(text)

    unconfigured = is_unconfigured(text)
    if unconfigured:
        if require_configured or snapshot:
            errors.append(
                "palette still contains template placeholders (#______), so this is an "
                "unfilled template rather than a real brand-lock"
            )
        else:
            warnings.append(
                "palette contains template placeholders (#______); fine for a template, "
                "not for production work"
            )

    if snapshot:
        snap_errors, snap_warnings = check_snapshot(text)
        errors += snap_errors
        warnings += snap_warnings

    return (errors, warnings)


def selftest() -> int:
    ok = True
    minimal = "\n".join(
        [
            "## Identity",
            "**Brand:** X",
            "**One-line description:** Y",
            "**Archetype:** Operator",
            "**Voice posture:** Calm",
            "## Palette",
            "| Role | Hex | Use |",
            "|---|---|---|",
            "| Background | `#FFFFFF` | canvas |",
            "| Ink | `#000000` | text |",
            "| Accent | `#FF0000` | pop |",
            "| Muted | `#888888` | captions |",
            "| Rule | `#EEEEEE` | borders |",
            "## Typography",
            "**Display font:** `Inter Black 900`, headlines",
            "**Body font:** `Inter Medium 500`, body",
            "## Mood adjectives",
            "## Never list",
            "## Aspect ratios",
            "## Color grade direction",
            "## Motion language",
            "## Voice rules",
        ]
    )

    cases = [
        ("a complete brand-lock passes", minimal, {}, False),
        (
            "a snapshot with no header is rejected",
            minimal,
            {"snapshot": True},
            True,
        ),
        (
            "a snapshot with a full instant header passes",
            "<!-- snapshot taken: 2026-05-07T14:23:00Z -->\n"
            "<!-- source: brand-packs/x.md -->\n" + minimal,
            {"snapshot": True},
            False,
        ),
        (
            "a snapshot with a malformed date is rejected",
            "<!-- snapshot taken: last Tuesday -->\n"
            "<!-- source: brand-packs/x.md -->\n" + minimal,
            {"snapshot": True},
            True,
        ),
        (
            "a snapshot missing its source header is rejected",
            "<!-- snapshot taken: 2026-05-07T14:23:00Z -->\n" + minimal,
            {"snapshot": True},
            True,
        ),
        (
            "placeholders pass as a template",
            minimal.replace("`#FFFFFF`", "`#______`"),
            {},
            False,
        ),
        (
            "placeholders fail under --require-configured",
            minimal.replace("`#FFFFFF`", "`#______`"),
            {"require_configured": True},
            True,
        ),
        (
            "a missing section is caught",
            minimal.replace("## Voice rules", ""),
            {},
            True,
        ),
    ]

    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        for i, (label, text, kwargs, should_fail) in enumerate(cases):
            path = Path(tmp) / f"case-{i}.md"
            path.write_text(text, encoding="utf-8")
            errors, _ = validate_brand_lock(path, **kwargs)
            if bool(errors) == should_fail:
                print(f"  ok    selftest: {label}")
            else:
                print(f"  FAIL  selftest: {label} -> {errors or '(no errors)'}")
                ok = False

        warn_path = Path(tmp) / "warn.md"
        warn_path.write_text(
            minimal.replace("| Muted | `#888888` | captions |", ""), encoding="utf-8"
        )
        _, warnings = validate_brand_lock(warn_path)
        if any("no 'muted' role" in w for w in warnings):
            print("  ok    selftest: a missing palette role warns")
        else:
            print(f"  FAIL  selftest: expected a muted-role warning, got {warnings}")
            ok = False

    print()
    print("Selftest passed." if ok else "Selftest FAILED.")
    return 0 if ok else 1


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print("Usage: python tools/validate_brand_lock.py <path-to-brand-lock.md> [...]")
        print("       python tools/validate_brand_lock.py --snapshot <snapshot.md>")
        print("       python tools/validate_brand_lock.py --require-configured <file>")
        print("       python tools/validate_brand_lock.py --snapshots")
        print("       python tools/validate_brand_lock.py --selftest")
        return 2

    if "--selftest" in args:
        return selftest()

    snapshot = "--snapshot" in args or "--snapshots" in args
    require_configured = "--require-configured" in args

    if "--snapshots" in args:
        paths = sorted(REPO_ROOT.rglob("brand-lock.snapshot.md"))
        if not paths:
            print("ERROR: no brand-lock.snapshot.md files found in the repo")
            return 1
    else:
        paths = [Path(a) for a in args if not a.startswith("--")]
        if not paths:
            print("ERROR: no brand-lock files given")
            return 2

    label = "snapshot" if snapshot else "brand-lock"
    print(f"Validating {len(paths)} {label} file(s)")
    print()

    total_errors = 0
    total_warnings = 0
    for path in paths:
        errors, warnings = validate_brand_lock(path, snapshot, require_configured)
        try:
            shown = path.relative_to(REPO_ROOT)
        except ValueError:
            shown = path
        total_warnings += len(warnings)
        if not errors:
            print(f"  ok    {shown}")
        else:
            total_errors += len(errors)
            print(f"  FAIL  {shown}")
            for err in errors:
                print(f"        - {err}")
        for warn in warnings:
            print(f"  warn  {shown}: {warn}")

    print()
    if total_errors == 0:
        print(f"All {label} files valid ({total_warnings} warning(s)).")
        return 0
    print(f"FAILED: {total_errors} error(s) across {label} files.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
