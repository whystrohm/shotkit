#!/usr/bin/env python3
"""
Validate the generator capability matrix and the adapter prose that defers to it.

_capabilities.json is declared the single source of truth for per-generator limits,
and every adapter .md repeats that rule at the top. A rule nothing checks is a
suggestion: the matrix and the prose drifted in three places before this file grew
the parity checks below.

Five checks:
  1. _capabilities.json validates against capabilities.schema.json.
  2. File parity: every generator id has an adapter .md and every adapter .md has a
     generator entry. Non-adapter markdown is skipped by name, not treated as an
     adapter with a missing entry.
  3. Prose parity: the word budget an adapter .md advertises must fit inside that
     generator's max_prompt_words, and the .md must mention the aspect_param the
     matrix says to send. A generator whose documented parameter name disagrees with
     the matrix will be called with the wrong one, because the matrix wins.
  4. Self-consistency: a notes field must not cite a word count above its own
     max_prompt_words.
  5. Staleness: warns when the matrix or an entry is past the freshness window.

Run from repo root:
    python tools/validate_capabilities.py
    python tools/validate_capabilities.py --selftest
"""

from __future__ import annotations

import re
import sys
from datetime import date

try:
    from jsonschema import Draft202012Validator
except ImportError:
    print("ERROR: jsonschema not installed. Run: pip install pyyaml jsonschema")
    sys.exit(1)

from _shotkit import REPO_ROOT, load_json

ADAPTERS_DIR = REPO_ROOT / "skills" / "visual-prompt-forge" / "adapters"
CAPS = ADAPTERS_DIR / "_capabilities.json"
CAPS_SCHEMA = ADAPTERS_DIR / "capabilities.schema.json"

# Re-verify the matrix at least this often. Generator models change monthly.
STALE_AFTER_DAYS = 120

# Markdown in adapters/ that documents the directory rather than a generator.
NON_ADAPTER_STEMS = {"README", "_README"}

# "**80-150 words**", "**40-80 words per prompt**", en dash or hyphen.
WORD_RANGE_RE = re.compile(r"\*\*\s*(\d+)\s*[-–—]\s*(\d+)\s+words[^*]*\*\*")
# "**up to 150 words**" or "**150 words**"
WORD_SINGLE_RE = re.compile(r"\*\*\s*(?:up to\s+)?(\d+)\s+words[^*]*\*\*")
# A bare word count inside a notes string, e.g. "Over 100 words underperforms."
NOTES_WORD_RE = re.compile(r"(\d+)\s+words")


def _parse_date(value: str) -> date | None:
    try:
        y, m, d = (int(p) for p in value.split("-"))
        return date(y, m, d)
    except (ValueError, AttributeError):
        return None


def adapter_word_bound(text: str) -> int | None:
    """Highest word count the adapter prose advertises, or None if it names none."""
    bounds: list[int] = []
    for m in WORD_RANGE_RE.finditer(text):
        bounds.append(max(int(m.group(1)), int(m.group(2))))
    if not bounds:
        for m in WORD_SINGLE_RE.finditer(text):
            bounds.append(int(m.group(1)))
    return max(bounds) if bounds else None


def check_prose_parity(entry: dict, text: str) -> tuple[list[str], list[str]]:
    """Compare one adapter .md against its capability entry."""
    errors: list[str] = []
    warnings: list[str] = []
    gid = entry["id"]

    bound = adapter_word_bound(text)
    if bound is None:
        warnings.append(
            f"prose: '{gid}.md' advertises no word budget, so the matrix value "
            f"({entry['max_prompt_words']}) is the only guidance a reader gets"
        )
    elif bound > entry["max_prompt_words"]:
        errors.append(
            f"prose: '{gid}.md' advertises up to {bound} words but the matrix caps "
            f"max_prompt_words at {entry['max_prompt_words']}"
        )

    aspect = entry["aspect_param"]
    if aspect not in text:
        errors.append(
            f"prose: '{gid}.md' never mentions aspect_param '{aspect}'. The matrix "
            f"wins, so the forge will send a parameter the adapter does not document"
        )

    notes = entry.get("notes") or ""
    for m in NOTES_WORD_RE.finditer(notes):
        cited = int(m.group(1))
        if cited > entry["max_prompt_words"]:
            warnings.append(
                f"self-consistency: '{gid}' notes cite {cited} words but "
                f"max_prompt_words is {entry['max_prompt_words']}"
            )

    return errors, warnings


def validate(today: date | None = None) -> tuple[list[str], list[str]]:
    """Return (errors, warnings). Empty errors means it passes."""
    errors: list[str] = []
    warnings: list[str] = []
    today = today or date.today()

    if not CAPS.exists():
        return ([f"missing {CAPS.relative_to(REPO_ROOT)}"], warnings)
    if not CAPS_SCHEMA.exists():
        return ([f"missing {CAPS_SCHEMA.relative_to(REPO_ROOT)}"], warnings)

    caps, caps_err = load_json(CAPS)
    if caps_err:
        return ([f"_capabilities.json: {caps_err}"], warnings)
    schema, schema_err = load_json(CAPS_SCHEMA)
    if schema_err:
        return ([f"capabilities.schema.json: {schema_err}"], warnings)

    # 1. Schema validation
    validator = Draft202012Validator(schema)
    for err in sorted(validator.iter_errors(caps), key=lambda e: list(e.path)):
        loc = "/".join(str(p) for p in err.path) or "(root)"
        errors.append(f"schema: {loc}: {err.message}")
    if errors:
        return (errors, warnings)  # structure-dependent checks need a valid shape

    entries = {g["id"]: g for g in caps["generators"]}
    cap_ids = set(entries)
    md_ids = {
        p.stem
        for p in ADAPTERS_DIR.glob("*.md")
        if p.stem not in NON_ADAPTER_STEMS
    }

    # 2. File parity
    for missing_md in sorted(cap_ids - md_ids):
        errors.append(
            f"parity: capability id '{missing_md}' has no adapter file {missing_md}.md"
        )
    for missing_cap in sorted(md_ids - cap_ids):
        errors.append(
            f"parity: adapter '{missing_cap}.md' has no entry in _capabilities.json"
        )

    # 3 and 4. Prose parity and self-consistency
    for gid in sorted(cap_ids & md_ids):
        text = (ADAPTERS_DIR / f"{gid}.md").read_text(encoding="utf-8")
        prose_errors, prose_warnings = check_prose_parity(entries[gid], text)
        errors.extend(prose_errors)
        warnings.extend(prose_warnings)

    # 5. Staleness
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


def selftest() -> int:
    ok = True

    cases = [
        (
            "prose advertising more words than the cap is caught",
            {"id": "x", "max_prompt_words": 250, "aspect_param": "size", "notes": ""},
            "Handles **150-300 words** comfortably. Pass `size` alongside.",
            True,
        ),
        (
            "prose inside the cap passes",
            {"id": "x", "max_prompt_words": 250, "aspect_param": "size", "notes": ""},
            "Handles **150-250 words** comfortably. Pass `size` alongside.",
            False,
        ),
        (
            "an undocumented aspect_param is caught",
            {
                "id": "x",
                "max_prompt_words": 120,
                "aspect_param": "aspect_ratio",
                "notes": "",
            },
            "Handles **60-120 words**. Pass `aspectRatio` as a parameter.",
            True,
        ),
        (
            "en dash ranges parse",
            {"id": "x", "max_prompt_words": 80, "aspect_param": "--ar", "notes": ""},
            "Aim for **40–80 words per prompt** including `--ar`.",
            False,
        ),
    ]
    for label, entry, text, should_error in cases:
        errors, _ = check_prose_parity(entry, text)
        if bool(errors) == should_error:
            print(f"  ok    selftest: {label}")
        else:
            print(f"  FAIL  selftest: {label} -> {errors or '(no errors)'}")
            ok = False

    entry = {"id": "x", "max_prompt_words": 80, "aspect_param": "--ar", "notes": "Over 100 words underperforms."}
    _, warnings = check_prose_parity(entry, "Aim for **40-80 words** with `--ar`.")
    if any("self-consistency" in w for w in warnings):
        print("  ok    selftest: notes citing more words than the cap are flagged")
    else:
        print(f"  FAIL  selftest: expected a self-consistency warning, got {warnings}")
        ok = False

    if adapter_word_bound("no budget stated here") is None:
        print("  ok    selftest: prose with no word budget reports none")
    else:
        print("  FAIL  selftest: found a word budget where there is none")
        ok = False

    print()
    print("Selftest passed." if ok else "Selftest FAILED.")
    return 0 if ok else 1


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()

    print(f"Validating capability matrix: {CAPS.relative_to(REPO_ROOT)}")
    print()

    errors, warnings = validate()

    for w in warnings:
        print(f"  warn  {w}")
    if warnings:
        print()

    if not errors:
        caps, _ = load_json(CAPS)
        count = len((caps or {}).get("generators", []))
        print(f"Capability matrix valid ({count} generators, {len(warnings)} warning(s)).")
        return 0

    for e in errors:
        print(f"  FAIL  {e}")
    print()
    print(f"FAILED: {len(errors)} error(s) in capability matrix.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
