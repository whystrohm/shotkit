#!/usr/bin/env python3
"""
Validate the shared contracts in contracts/: the file formats the WhyStrohm skills use to
hand work to each other through a brand/ folder in the user's project.

This repo holds the canonical copy of every contract schema. Other skill repos keep a
byte-identical copy and check it in their own CI.

Checks:
  - every contracts/*.schema.json is valid JSON Schema, with $id, title and description
  - its $id ends with its own filename, so a copied file cannot claim to be another
  - every schema has at least one example in contracts/examples/, and every example passes
  - with --against DIR, every schema in DIR/contracts/ is byte-identical to the one here

After ./install.sh there is no contracts/ folder next to the tools. The skills do not need
it, so the check reports a skip and passes.

Usage:
    python tools/validate_contracts.py
    python tools/validate_contracts.py --against ~/code/whystrohm-voice-extract
    python tools/validate_contracts.py --selftest
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

CONTRACTS = Path(__file__).resolve().parent.parent / "contracts"


def example_name(schema_path: Path) -> str:
    """voice-profile.v1.schema.json -> voice-profile"""
    stem = schema_path.name[: -len(".schema.json")]
    return stem.rsplit(".v", 1)[0]


def check_contracts(root: Path) -> list[str]:
    """Return a list of errors. Empty list = passes."""
    errors: list[str] = []
    schemas = sorted(root.glob("*.schema.json"))
    if not schemas:
        return [f"no *.schema.json files in {root}"]

    for path in schemas:
        try:
            schema = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            errors.append(f"{path.name}: invalid JSON: {e}")
            continue
        try:
            Draft202012Validator.check_schema(schema)
        except SchemaError as e:
            errors.append(f"{path.name}: invalid schema: {e.message}")
            continue
        for key in ("$id", "title", "description"):
            if key not in schema:
                errors.append(f"{path.name}: missing '{key}'")
        if not str(schema.get("$id", "")).endswith("/" + path.name):
            errors.append(f"{path.name}: $id does not end with /{path.name}")

        examples = sorted((root / "examples").glob(f"{example_name(path)}*.json"))
        if not examples:
            errors.append(f"{path.name}: no example in examples/ named {example_name(path)}*.json")
        validator = Draft202012Validator(schema)
        for ex in examples:
            try:
                data = json.loads(ex.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                errors.append(f"examples/{ex.name}: invalid JSON: {e}")
                continue
            for err in validator.iter_errors(data):
                where = "/".join(str(p) for p in err.absolute_path) or "(root)"
                errors.append(f"examples/{ex.name}: {where}: {err.message}")
    return errors


def compare_copies(root: Path, other_repo: Path) -> list[str]:
    """Every schema in other_repo/contracts/ must be byte-identical to the one in root."""
    errors: list[str] = []
    theirs = sorted((other_repo / "contracts").glob("*.schema.json"))
    if not theirs:
        return [f"no contracts/*.schema.json in {other_repo}"]
    for path in theirs:
        ours = root / path.name
        if not ours.exists():
            errors.append(f"{path.name}: not in the canonical contracts/")
        elif ours.read_bytes() != path.read_bytes():
            errors.append(f"{path.name}: differs from the canonical copy")
    return errors


def selftest() -> int:
    import tempfile

    ok = True

    def expect(label: str, errors: list[str], want: str | None) -> None:
        nonlocal ok
        hit = not errors if want is None else any(want in e for e in errors)
        print(f"  {'ok  ' if hit else 'FAIL'}  selftest: {label}")
        if not hit:
            print(f"        got: {errors}")
            ok = False

    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://example.com/contracts/thing.v1.schema.json",
        "title": "Thing",
        "description": "A test contract.",
        "type": "object",
        "required": ["n"],
        "properties": {"n": {"type": "integer", "maximum": 5}},
    }

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "contracts"
        (root / "examples").mkdir(parents=True)
        (root / "thing.v1.schema.json").write_text(json.dumps(schema))
        (root / "examples" / "thing.example.json").write_text('{"n": 3}')
        expect("a valid schema with a passing example passes", check_contracts(root), None)

        (root / "examples" / "thing.example.json").write_text('{"n": 9}')
        expect("an example that breaks its schema is caught", check_contracts(root), "greater than the maximum")

        (root / "examples" / "thing.example.json").unlink()
        expect("a schema with no example is caught", check_contracts(root), "no example")

        (root / "examples" / "thing.example.json").write_text('{"n": 3}')
        moved = dict(schema, **{"$id": "https://example.com/contracts/other.v1.schema.json"})
        (root / "thing.v1.schema.json").write_text(json.dumps(moved))
        expect("an $id naming another file is caught", check_contracts(root), "$id does not end")

        broken = dict(schema, type="not-a-type")
        (root / "thing.v1.schema.json").write_text(json.dumps(broken))
        expect("an invalid schema is caught", check_contracts(root), "invalid schema")

        (root / "thing.v1.schema.json").write_text(json.dumps(schema))
        other = Path(tmp) / "other-repo"
        (other / "contracts").mkdir(parents=True)
        (other / "contracts" / "thing.v1.schema.json").write_text(json.dumps(schema))
        expect("a byte-identical copy passes", compare_copies(root, other), None)
        (other / "contracts" / "thing.v1.schema.json").write_text(json.dumps(schema, indent=2))
        expect("a reformatted copy is caught", compare_copies(root, other), "differs")

    print()
    print("Selftest passed." if ok else "Selftest FAILED.")
    return 0 if ok else 1


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        return selftest()

    if not CONTRACTS.is_dir():
        print(f"No contracts/ folder next to the tools ({CONTRACTS.parent}).")
        print("That is expected after ./install.sh. Skipped.")
        return 0

    errors = check_contracts(CONTRACTS)
    if "--against" in args:
        i = args.index("--against")
        if i + 1 >= len(args):
            print("ERROR: --against needs a repo folder")
            return 1
        errors += compare_copies(CONTRACTS, Path(args[i + 1]).expanduser())

    for path in sorted(CONTRACTS.glob("*.schema.json")):
        print(f"  {'FAIL' if any(e.startswith(path.name) for e in errors) else 'ok  '}  contracts/{path.name}")
    print()
    if not errors:
        print("All contracts valid.")
        return 0
    for err in errors:
        print(f"  - {err}")
    print()
    print(f"FAILED: {len(errors)} error(s) in contracts.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
