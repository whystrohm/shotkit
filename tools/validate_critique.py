#!/usr/bin/env python3
"""
Validate critique.json files against the critique schema AND the gating invariant.

Schema validation alone is not enough: JSON Schema cannot express the cross-field
rules that make a verdict trustworthy. This validator adds them.

Gating invariant (the reason structured output exists):
  - Any 'blocking' issue      => verdict MUST be REJECT.
  - Three or more 'major'     => verdict MUST be REJECT.
  - One or two 'major'        => verdict MUST NOT be ACCEPT (caps at REVISE).
  - Therefore ACCEPT requires zero major/blocking issues.

Provenance invariant (version 1.1 and later):
  - A hash without its path, or a path without its hash, is not a reference.
  - image_ref must be present and non-null: a verdict about no image is not a verdict.
  - HIGH confidence requires the shot spec, the brand-lock, and the prompt to all be
    identified. The critic's own rubric says HIGH means all three were available.
  - generator, when named, must be an id in the capability matrix.

A critique that claims ACCEPT while carrying a blocking issue passes the schema but
FAILS here. So does a 1.1 critique that records an image hash and no image path.

Usage:
    python tools/validate_critique.py path/to/critique.json [...]
    python tools/validate_critique.py path/to/output-dir      # every critique in the tree
    python tools/validate_critique.py --examples              # bundled fixtures
    python tools/validate_critique.py --selftest              # prove the gates fire
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from jsonschema import Draft202012Validator
except ImportError:
    print("ERROR: jsonschema not installed. Run: pip install pyyaml jsonschema")
    sys.exit(1)

from _shotkit import REPO_ROOT, capability_ids, critique_paths, load_json

SCHEMA_PATH = (
    REPO_ROOT / "skills" / "visual-asset-critic" / "templates" / "critique.schema.json"
)
EXAMPLES_DIR = REPO_ROOT / "skills" / "visual-asset-critic" / "examples"

MAJOR_REJECT_THRESHOLD = 3

# Pairs that must be present or absent together.
REF_HASH_PAIRS = (
    ("image_ref", "image_sha256"),
    ("brand_lock_ref", "brand_lock_sha256"),
    ("prompt_ref", "prompt_sha256"),
)


def _load_schema() -> dict:
    data, err = load_json(SCHEMA_PATH)
    if err:
        raise RuntimeError(err)
    return data


def check_gating(data: dict) -> list[str]:
    """The severity-to-verdict invariant. Assumes data is schema-valid."""
    errors: list[str] = []
    verdict = data.get("verdict")
    severities = [issue.get("severity") for issue in data.get("issues", [])]
    majors = severities.count("major")

    if "blocking" in severities and verdict != "REJECT":
        errors.append(
            f"gating: a 'blocking' issue requires verdict REJECT, got '{verdict}'"
        )
    if majors >= MAJOR_REJECT_THRESHOLD and verdict != "REJECT":
        errors.append(
            f"gating: {majors} 'major' issues require verdict REJECT "
            f"(threshold {MAJOR_REJECT_THRESHOLD}), got '{verdict}'"
        )
    if majors and verdict == "ACCEPT":
        errors.append(
            "gating: a 'major' issue caps the verdict at REVISE; ACCEPT is not allowed"
        )
    return errors


def check_provenance(data: dict, known_generators: set[str]) -> list[str]:
    """The provenance invariant. Only applies from version 1.1."""
    errors: list[str] = []
    if data.get("version") == "1.0":
        return errors

    for ref_key, hash_key in REF_HASH_PAIRS:
        ref, digest = data.get(ref_key), data.get(hash_key)
        if ref and not digest:
            errors.append(f"provenance: {ref_key} is set but {hash_key} is null")
        if digest and not ref:
            errors.append(f"provenance: {hash_key} is set but {ref_key} is null")

    if not data.get("image_ref"):
        errors.append(
            "provenance: image_ref is null; a verdict that names no image cannot be audited"
        )

    if data.get("confidence") == "HIGH":
        missing = [
            key
            for key in ("shot_id", "brand_lock_ref", "prompt_ref")
            if not data.get(key)
        ]
        if missing:
            errors.append(
                "provenance: confidence HIGH requires "
                + ", ".join(missing)
                + " to be identified"
            )

    generator = data.get("generator")
    if generator and known_generators and generator not in known_generators:
        errors.append(
            f"provenance: generator '{generator}' is not an id in the capability matrix"
        )

    return errors


def validate_doc(
    data: dict,
    validator: Draft202012Validator,
    known_generators: set[str] | None = None,
) -> tuple[list[str], list[str]]:
    """Return (errors, warnings). Empty errors means it passes every gate."""
    errors: list[str] = []
    warnings: list[str] = []

    for err in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
        loc = "/".join(str(p) for p in err.path) or "(root)"
        errors.append(f"schema: {loc}: {err.message}")
    if errors:
        return (errors, warnings)  # the gates assume a schema-valid shape

    errors += check_gating(data)
    errors += check_provenance(data, known_generators or set())

    if data.get("version") == "1.0":
        warnings.append(
            "version 1.0 carries no run id, no round, and no content hashes, so the "
            "verdict cannot be tied to the bytes it reviewed; re-emit as 1.1"
        )

    return (errors, warnings)


def validate_path(
    path: Path,
    validator: Draft202012Validator,
    known_generators: set[str] | None = None,
) -> tuple[list[str], list[str]]:
    data, err = load_json(path)
    if err:
        return ([err], [])
    if not isinstance(data, dict):
        return ([f"top level is not an object: {path}"], [])
    return validate_doc(data, validator, known_generators)


def _selftest_cases() -> list[tuple[str, dict, bool]]:
    """(label, document, should_pass)."""
    base_provenance = {
        "run_id": "20260730T142300Z-9f2c1ab4",
        "round": 1,
        "created_at": "2026-07-30T14:31:00Z",
        "shot_id": "shot_03",
        "brand_lock_ref": "brand-lock.snapshot.md",
        "brand_lock_sha256": "a" * 64,
        "image_ref": "frames/round-1/shot_03.png",
        "image_sha256": "b" * 64,
        "prompt_ref": "prompts/round-1/flux.txt",
        "prompt_sha256": "c" * 64,
        "generator": "flux",
        "model_version": "2 Pro",
        "seed": 12345,
    }
    major_issue = {
        "layer": "Series Lock",
        "severity": "major",
        "note": "hair mismatch",
        "fix_type": "prompt-level",
        "fix": "add 'salt-and-pepper hair' to the anchor",
    }
    blocking_issue = {
        "layer": "Brand Lock",
        "severity": "blocking",
        "note": "off-palette",
        "fix_type": "re-roll",
        "fix": "re-roll with palette anchor",
    }

    def doc(**overrides) -> dict:
        out = {
            "version": "1.1",
            **base_provenance,
            "verdict": "REVISE",
            "confidence": "HIGH",
            "issues": [dict(major_issue)],
        }
        out.update(overrides)
        return out

    return [
        ("clean REVISE with full provenance passes", doc(), True),
        (
            "legacy 1.0 document still validates",
            {
                "version": "1.0",
                "verdict": "REVISE",
                "confidence": "HIGH",
                "issues": [dict(major_issue)],
            },
            True,
        ),
        (
            "ACCEPT with a blocking issue is rejected",
            doc(verdict="ACCEPT", issues=[dict(blocking_issue)]),
            False,
        ),
        (
            "REVISE with a blocking issue is rejected",
            doc(verdict="REVISE", issues=[dict(blocking_issue)]),
            False,
        ),
        (
            "ACCEPT with a major issue is rejected",
            doc(verdict="ACCEPT"),
            False,
        ),
        (
            "three major issues cannot stay at REVISE",
            doc(verdict="REVISE", issues=[dict(major_issue) for _ in range(3)]),
            False,
        ),
        (
            "three major issues at REJECT pass",
            doc(verdict="REJECT", issues=[dict(major_issue) for _ in range(3)]),
            True,
        ),
        (
            "1.1 with a hash and no path is rejected",
            doc(prompt_ref=None),
            False,
        ),
        (
            "1.1 with a path and no hash is rejected",
            doc(prompt_sha256=None),
            False,
        ),
        (
            "1.1 with no image_ref is rejected",
            doc(image_ref=None, image_sha256=None),
            False,
        ),
        (
            "HIGH confidence with no prompt identified is rejected",
            doc(prompt_ref=None, prompt_sha256=None),
            False,
        ),
        (
            "MEDIUM confidence with no prompt identified passes",
            doc(confidence="MEDIUM", prompt_ref=None, prompt_sha256=None),
            True,
        ),
        (
            "unknown generator id is rejected",
            doc(generator="runway-sora"),
            False,
        ),
        (
            "1.1 missing a required provenance field is rejected",
            {
                "version": "1.1",
                "verdict": "ACCEPT",
                "confidence": "LOW",
                "issues": [],
            },
            False,
        ),
    ]


def selftest() -> int:
    validator = Draft202012Validator(_load_schema())
    known = capability_ids() or {"flux"}
    ok = True

    for label, document, should_pass in _selftest_cases():
        errors, _ = validate_doc(document, validator, known)
        passed = not errors
        if passed == should_pass:
            print(f"  ok    selftest: {label}")
        else:
            detail = errors if errors else ["(no errors raised)"]
            print(f"  FAIL  selftest: {label} -> {detail}")
            ok = False

    print()
    print("Selftest passed." if ok else "Selftest FAILED.")
    return 0 if ok else 1


def _collect(args: list[str]) -> list[Path] | None:
    if "--examples" in args:
        found = sorted(EXAMPLES_DIR.glob("*.json"))
        found += critique_paths(EXAMPLES_DIR / "worked-run")
        return found or None

    paths: list[Path] = []
    for raw in args:
        path = Path(raw)
        if path.is_dir():
            found = critique_paths(path)
            if not found:
                print(f"  FAIL  {raw}")
                print("        - no critique files found in this output tree")
                return None
            paths.extend(found)
        else:
            paths.append(path)
    return paths


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print("Usage: python tools/validate_critique.py <critique.json|output-dir> [...]")
        print("       python tools/validate_critique.py --examples")
        print("       python tools/validate_critique.py --selftest")
        return 2
    if "--selftest" in args:
        return selftest()

    if not SCHEMA_PATH.exists():
        print(f"ERROR: schema not found at {SCHEMA_PATH}")
        return 1

    paths = _collect(args)
    if paths is None:
        return 1

    validator = Draft202012Validator(_load_schema())
    known = capability_ids()

    print(f"Validating {len(paths)} critique file(s)")
    print()

    total_errors = 0
    total_warnings = 0
    for path in paths:
        errors, warnings = validate_path(path, validator, known)
        try:
            label = path.relative_to(REPO_ROOT)
        except ValueError:
            label = path
        total_warnings += len(warnings)
        if not errors:
            print(f"  ok    {label}")
        else:
            total_errors += len(errors)
            print(f"  FAIL  {label}")
            for err in errors:
                print(f"        - {err}")
        for warn in warnings:
            print(f"  warn  {label}: {warn}")

    print()
    if total_errors == 0:
        print(f"All critiques valid ({total_warnings} warning(s)).")
        return 0
    print(f"FAILED: {total_errors} error(s) across critiques.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
