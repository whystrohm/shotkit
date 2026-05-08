#!/usr/bin/env python3
"""
Validate that every *.schema.json file in the repo is itself valid JSON Schema.

Run from repo root:
    python tools/validate_schemas.py
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


REPO_ROOT = Path(__file__).resolve().parent.parent


def find_schema_files() -> list[Path]:
    """Find every *.schema.json file in the repo."""
    return sorted(REPO_ROOT.rglob("*.schema.json"))


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


def main() -> int:
    schemas = find_schema_files()
    if not schemas:
        print("ERROR: no *.schema.json files found in repo")
        return 1

    print(f"Validating {len(schemas)} schema file(s)")
    print()

    total_errors = 0
    for path in schemas:
        rel = path.relative_to(REPO_ROOT)
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
