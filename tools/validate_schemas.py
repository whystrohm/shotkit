#!/usr/bin/env python3
"""
Validate that every *.schema.json file shotkit ships is itself valid JSON Schema.

Scope. Only the five shotkit skill directories are searched. After ./install.sh the
tools sit in ~/.claude/shotkit-tools/, and searching everything under ~/.claude would
judge files that belong to other tools.

Usage:
    python tools/validate_schemas.py
    python ~/.claude/shotkit-tools/validate_schemas.py
    python tools/validate_schemas.py --selftest
"""

from __future__ import annotations
import json
import sys
from pathlib import Path

try:
    from jsonschema import Draft202012Validator
    from jsonschema.exceptions import SchemaError
except ImportError:
    print("ERROR: jsonschema not installed. Run: pip install jsonschema")
    sys.exit(1)


from _shotkit import SKILLS_ROOT, shotkit_skill_dirs, shown_path


def find_schema_files(skills_root: Path | None = None) -> list[Path]:
    """Every *.schema.json under the five shotkit skill directories."""
    found: list[Path] = []
    for skill_dir in shotkit_skill_dirs(skills_root):
        if skill_dir.is_dir():
            found.extend(skill_dir.rglob("*.schema.json"))
    return sorted(found)


def validate_schema_file(path: Path) -> list[str]:
    """Return a list of errors. Empty list = passes."""
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        errors.append(f"invalid JSON: {e}")
        return errors

    try:
        Draft202012Validator.check_schema(data)
    except SchemaError as e:
        errors.append(f"invalid schema: {e.message}")

    if "$id" not in data:
        errors.append("missing '$id' field")
    if "title" not in data:
        errors.append("missing 'title' field")
    if "description" not in data:
        errors.append("missing 'description' field")

    return errors


def selftest() -> int:
    import tempfile

    ok = True
    good = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://example.com/x.schema.json",
        "title": "X",
        "description": "A valid schema.",
        "type": "object",
    }
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "skills"
        own = root / "storyboard-architect" / "templates"
        own.mkdir(parents=True)
        (own / "good.schema.json").write_text(json.dumps(good))
        foreign = root / "someone-elses-skill"
        foreign.mkdir(parents=True)
        (foreign / "broken.schema.json").write_text("{ not json")

        found = find_schema_files(root)
        names = [p.name for p in found]
        if names == ["good.schema.json"]:
            print("  ok    selftest: schemas outside the shotkit skills are not searched")
        else:
            print(f"  FAIL  selftest: expected only good.schema.json, found {names}")
            ok = False

        bad = dict(good)
        del bad["$id"]
        bad["type"] = "not-a-type"
        (own / "bad.schema.json").write_text(json.dumps(bad))
        errors = validate_schema_file(own / "bad.schema.json")
        if any("invalid schema" in e for e in errors) and any("$id" in e for e in errors):
            print("  ok    selftest: an invalid shotkit schema is caught")
        else:
            print(f"  FAIL  selftest: invalid schema not caught -> {errors}")
            ok = False

    print()
    print("Selftest passed." if ok else "Selftest FAILED.")
    return 0 if ok else 1


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()

    schemas = find_schema_files()
    if not schemas:
        print(f"ERROR: no *.schema.json files found under {SKILLS_ROOT}")
        return 1

    print(f"Validating {len(schemas)} schema file(s)")
    print()

    total_errors = 0
    for path in schemas:
        rel = shown_path(path)
        errors = validate_schema_file(path)
        if not errors:
            print(f"  ok    {rel}")
        else:
            total_errors += len(errors)
            print(f"  FAIL  {rel}")
            for err in errors:
                print(f"        - {err}")

    print()
    if total_errors == 0:
        print("All schemas valid.")
        return 0
    print(f"FAILED: {total_errors} error(s) across schemas.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
