#!/usr/bin/env python3
"""
Validate a critique.json against the critique schema AND the gating invariant.

Schema validation alone is not enough: JSON Schema cannot express the
cross-field rule that makes the verdict trustworthy. This validator adds it.

Gating invariant (the reason structured output exists):
  - Any 'blocking' issue  => verdict MUST be REJECT.
  - Any 'major' issue     => verdict MUST NOT be ACCEPT (caps at REVISE).
  - Therefore a verdict of ACCEPT requires zero major/blocking issues.

A critique that claims ACCEPT while carrying a blocking issue passes the
schema but FAILS here. That is the whole point.

Usage:
    python tools/validate_critique.py path/to/critique.json [...]
    python tools/validate_critique.py --selftest      # prove the gate fires
"""

from __future__ import annotations
import json
import sys
from pathlib import Path

try:
    from jsonschema import Draft202012Validator
except ImportError:
    print("ERROR: jsonschema not installed. Run: pip install jsonschema")
    sys.exit(1)


REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO_ROOT / "skills" / "visual-asset-critic" / "templates" / "critique.schema.json"


def _load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def check_gating(data: dict) -> list[str]:
    """The cross-field invariant schema can't enforce. Assumes data is schema-valid."""
    errors: list[str] = []
    verdict = data.get("verdict")
    severities = {issue.get("severity") for issue in data.get("issues", [])}

    if "blocking" in severities and verdict != "REJECT":
        errors.append(
            f"gating: a 'blocking' issue requires verdict REJECT, got '{verdict}'"
        )
    if "major" in severities and verdict == "ACCEPT":
        errors.append(
            "gating: a 'major' issue caps the verdict at REVISE; ACCEPT is not allowed"
        )
    return errors


def validate_doc(data: dict, validator: Draft202012Validator) -> list[str]:
    """Return a list of errors. Empty list = passes both schema and gating."""
    errors: list[str] = []
    for err in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
        loc = "/".join(str(p) for p in err.path) or "(root)"
        errors.append(f"schema: {loc}: {err.message}")
    if errors:
        return errors  # gating check assumes a schema-valid shape
    errors.extend(check_gating(data))
    return errors


def validate_path(path: Path, validator: Draft202012Validator) -> list[str]:
    if not path.exists():
        return [f"file does not exist: {path}"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"invalid JSON: {e}"]
    return validate_doc(data, validator)


def selftest() -> int:
    """Prove the gate accepts a clean doc and rejects a contradictory one."""
    validator = Draft202012Validator(_load_schema())
    good = {
        "version": "1.0",
        "verdict": "REVISE",
        "confidence": "HIGH",
        "issues": [
            {"layer": "Series Lock", "severity": "major", "note": "hair mismatch",
             "fix_type": "prompt-level", "fix": "add 'salt-and-pepper hair' to the anchor"}
        ],
    }
    bad = {
        "version": "1.0",
        "verdict": "ACCEPT",  # contradiction: ACCEPT with a blocking issue
        "confidence": "HIGH",
        "issues": [
            {"layer": "Brand Lock", "severity": "blocking", "note": "off-palette",
             "fix_type": "re-roll", "fix": "re-roll with palette anchor"}
        ],
    }
    good_errs = validate_doc(good, validator)
    bad_errs = validate_doc(bad, validator)

    ok = True
    if good_errs:
        print("  FAIL  selftest: clean REVISE doc should pass, got:", good_errs)
        ok = False
    else:
        print("  ok    selftest: clean REVISE doc passes")
    if not bad_errs:
        print("  FAIL  selftest: ACCEPT-with-blocking should be rejected, but it passed")
        ok = False
    else:
        print("  ok    selftest: ACCEPT-with-blocking is rejected by the gate")

    print()
    print("Selftest passed." if ok else "Selftest FAILED.")
    return 0 if ok else 1


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print("Usage: python tools/validate_critique.py <critique.json> [...]")
        print("       python tools/validate_critique.py --selftest")
        return 2
    if "--selftest" in args:
        return selftest()

    if not SCHEMA_PATH.exists():
        print(f"ERROR: schema not found at {SCHEMA_PATH.relative_to(REPO_ROOT)}")
        return 1
    validator = Draft202012Validator(_load_schema())

    paths = [Path(p) for p in args]
    print(f"Validating {len(paths)} critique file(s)")
    print()

    total_errors = 0
    for path in paths:
        errors = validate_path(path, validator)
        if not errors:
            print(f"  ok    {path}")
        else:
            total_errors += len(errors)
            print(f"  FAIL  {path}")
            for err in errors:
                print(f"        - {err}")

    print()
    if total_errors == 0:
        print("All critiques valid.")
        return 0
    print(f"FAILED: {total_errors} error(s) across critiques.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
