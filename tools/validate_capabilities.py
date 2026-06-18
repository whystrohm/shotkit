#!/usr/bin/env python3
"""
Validate the generator capability matrix (the single source of truth for
per-generator limits used by visual-prompt-forge).

Three checks:
  1. _capabilities.json validates against capabilities.schema.json.
  2. Parity: every generator id has an adapter .md, and every adapter .md
     has a generator entry. A drifted matrix (id with no adapter, or an
     adapter with no capability data) fails.
  3. Staleness: warns (does not fail) if the matrix or any entry has not
     been re-verified within the freshness window. Image/video models churn.

Run from repo root:
    python tools/validate_capabilities.py
"""

from __future__ import annotations
import json
import sys
from datetime import date
from pathlib import Path

try:
    from jsonschema import Draft202012Validator
except ImportError:
    print("ERROR: jsonschema not installed. Run: pip install jsonschema")
    sys.exit(1)


REPO_ROOT = Path(__file__).resolve().parent.parent
ADAPTERS_DIR = REPO_ROOT / "skills" / "visual-prompt-forge" / "adapters"
CAPS = ADAPTERS_DIR / "_capabilities.json"
CAPS_SCHEMA = ADAPTERS_DIR / "capabilities.schema.json"

# Re-verify the matrix at least this often. Generator models change monthly.
STALE_AFTER_DAYS = 120


def _parse_date(value: str) -> date | None:
    try:
        y, m, d = (int(p) for p in value.split("-"))
        return date(y, m, d)
    except (ValueError, AttributeError):
        return None


def validate() -> tuple[list[str], list[str]]:
    """Return (errors, warnings). Empty errors = passes."""
    errors: list[str] = []
    warnings: list[str] = []

    if not CAPS.exists():
        return ([f"missing {CAPS.relative_to(REPO_ROOT)}"], warnings)
    if not CAPS_SCHEMA.exists():
        return ([f"missing {CAPS_SCHEMA.relative_to(REPO_ROOT)}"], warnings)

    try:
        caps = json.loads(CAPS.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return ([f"_capabilities.json is invalid JSON: {e}"], warnings)
    try:
        schema = json.loads(CAPS_SCHEMA.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return ([f"capabilities.schema.json is invalid JSON: {e}"], warnings)

    # 1. Schema validation
    validator = Draft202012Validator(schema)
    for err in sorted(validator.iter_errors(caps), key=lambda e: list(e.path)):
        loc = "/".join(str(p) for p in err.path) or "(root)"
        errors.append(f"schema: {loc}: {err.message}")
    if errors:
        return (errors, warnings)  # don't trust structure-dependent checks if schema fails

    # 2. Parity between capability ids and adapter .md files
    cap_ids = {g["id"] for g in caps["generators"]}
    md_ids = {p.stem for p in ADAPTERS_DIR.glob("*.md")}
    for missing_md in sorted(cap_ids - md_ids):
        errors.append(f"parity: capability id '{missing_md}' has no adapter file {missing_md}.md")
    for missing_cap in sorted(md_ids - cap_ids):
        errors.append(f"parity: adapter '{missing_cap}.md' has no entry in _capabilities.json")

    # 3. Staleness (warnings only)
    today = date.today()
    reviewed = _parse_date(caps.get("matrix_last_reviewed", ""))
    if reviewed is None:
        warnings.append("matrix_last_reviewed is not a parseable date")
    elif (today - reviewed).days > STALE_AFTER_DAYS:
        warnings.append(
            f"matrix_last_reviewed is {(today - reviewed).days} days old "
            f"(> {STALE_AFTER_DAYS}); re-verify the matrix"
        )
    for g in caps["generators"]:
        lv = _parse_date(g.get("last_verified", ""))
        if lv is not None and (today - lv).days > STALE_AFTER_DAYS:
            warnings.append(
                f"'{g['id']}' last_verified is {(today - lv).days} days old "
                f"(> {STALE_AFTER_DAYS}); re-verify this generator"
            )

    return (errors, warnings)


def main() -> int:
    print(f"Validating capability matrix: {CAPS.relative_to(REPO_ROOT)}")
    print()

    errors, warnings = validate()

    for w in warnings:
        print(f"  warn  {w}")
    if warnings:
        print()

    if not errors:
        n = 0
        try:
            n = len(json.loads(CAPS.read_text())["generators"])
        except Exception:
            pass
        print(f"Capability matrix valid ({n} generators, {len(warnings)} warning(s)).")
        return 0

    for e in errors:
        print(f"  FAIL  {e}")
    print()
    print(f"FAILED: {len(errors)} error(s) in capability matrix.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
