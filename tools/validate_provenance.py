#!/usr/bin/env python3
"""
Validate the provenance chain of a shotkit output tree.

This is the tool that answers "does this verdict still describe the file it reviewed."
Paths lie: a filename says nothing about the bytes behind it, so a frame regenerated
after its critique leaves every path reference intact and every claim about it wrong.
Content hashes are what make that detectable, and this walks them.

Checks:
  1. run.json validates against run.schema.json, and its run_id agrees with created_at.
  2. Rounds are numbered from 1 with no gaps and no duplicates.
  3. Every input hash in run.json still matches the file on disk. A brand-lock edited
     mid-project fails here instead of silently repointing the project's history.
  4. Every prompt hash recorded in run.json still matches the file on disk.
  5. Every critique validates against the schema and the gating invariant.
  6. Every critique's run_id matches run.json.
  7. Every critique's image, prompt, and brand-lock hashes match the files on disk.
  8. No two critiques cover the same shot in the same round. Two operators writing the
     same verdict path is a real conflict, not a silent overwrite.
  9. Every frame on disk has a critique for its round. An unreviewed frame is the
     failure mode where a re-roll slips past the gate on a stale ACCEPT.
 10. Every shot has at least one critique, and the latest verdict per shot is reported.
 11. Shots recorded as post_only still owe compositing work.

Exit status is 0 when the chain is intact. Add --require-accept to also demand that
every shot's latest verdict is ACCEPT, which is the pipeline stop condition made
executable rather than described.

Usage:
    python tools/validate_provenance.py <output-dir> [...]
    python tools/validate_provenance.py <output-dir> --require-accept
    python tools/validate_provenance.py <output-dir> --json
    python tools/validate_provenance.py --examples
    python tools/validate_provenance.py --selftest
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    from jsonschema import Draft202012Validator
except ImportError:
    print("ERROR: jsonschema not installed. Run: pip install pyyaml jsonschema")
    sys.exit(1)

from _shotkit import (
    IMAGE_EXTS,
    REPO_ROOT,
    critique_paths,
    load_json,
    round_dirs,
    run_id_timestamp,
    sha256_file,
)
from validate_critique import _load_schema as _load_critique_schema
from validate_critique import validate_doc as validate_critique_doc

RUN_SCHEMA = (
    REPO_ROOT / "skills" / "storyboard-architect" / "templates" / "run.schema.json"
)
WORKED_RUN = REPO_ROOT / "skills" / "visual-asset-critic" / "examples" / "worked-run"


class Report:
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.shots: dict[str, dict] = {}
        self.rounds_seen: list[int] = []
        # (path, recorded, actual) -> the labels that referenced it. One edited file is
        # one problem, even when twenty critiques all hash it.
        self.hash_failures: dict[tuple[str, str, str], list[str]] = {}

    def as_dict(self) -> dict:
        return {
            "output_dir": str(self.output_dir),
            "ok": not self.errors,
            "errors": self.errors,
            "warnings": self.warnings,
            "rounds": self.rounds_seen,
            "shots": self.shots,
        }


def _check_hash(
    report: Report, label: str, rel: str | None, expected: str | None
) -> None:
    """Compare a recorded hash against the file currently on disk."""
    if not rel or not expected:
        return
    path = report.output_dir / rel
    if not path.exists():
        report.errors.append(f"{label}: '{rel}' is referenced but missing on disk")
        return
    actual = sha256_file(path)
    if actual == expected:
        return
    report.hash_failures.setdefault((rel, expected, actual), []).append(label)


def _finalize_hash_failures(report: Report) -> None:
    """Turn collected hash mismatches into one error per distinct mismatch."""
    for (rel, expected, actual), labels in report.hash_failures.items():
        # Print both hashes in full. Truncating them meant a single mistyped character
        # at the end produced a message showing two identical-looking strings and
        # asserting they differed, which is the least useful moment to be imprecise: a
        # hand-authored run.json is exactly where typos come from.
        detail = (
            f"'{rel}' does not match the hash recorded for it\n"
            f"          recorded: {expected}\n"
            f"          on disk:  {actual}"
        )
        if len(expected) != 64:
            detail += (
                f"\n          the recorded value is {len(expected)} characters, not 64, "
                f"so it is malformed rather than stale"
            )
        elif sum(a != b for a, b in zip(expected, actual)) <= 2:
            detail += (
                "\n          they differ in one or two characters, which usually means "
                "a typo in the recorded hash rather than a changed file"
            )
        if len(labels) == 1:
            detail += f"\n          referenced by: {labels[0]}"
        else:
            shown = ", ".join(labels[:3])
            more = f", and {len(labels) - 3} more" if len(labels) > 3 else ""
            detail += (
                f"\n          referenced by {len(labels)} places: {shown}{more}"
            )
        report.errors.append(detail)


def check_run_doc(report: Report) -> dict | None:
    run_path = report.output_dir / "run.json"
    if not run_path.exists():
        report.errors.append(
            "run.json is missing, so nothing pins this output to its inputs. A tree "
            "written before 3.0.0 has no provenance to check: write a run.json "
            "(schema at skills/storyboard-architect/templates/run.schema.json) or "
            "re-run storyboard-architect. This is reported as an error rather than a "
            "warning so a pipeline gate cannot pass an unauditable tree"
        )
        return None

    run_doc, err = load_json(run_path)
    if err:
        report.errors.append(f"run.json: {err}")
        return None

    schema, s_err = load_json(RUN_SCHEMA)
    if s_err:
        report.errors.append(f"run.schema.json: {s_err}")
        return None

    validator = Draft202012Validator(schema)
    for e in sorted(validator.iter_errors(run_doc), key=lambda x: list(x.path)):
        loc = "/".join(str(p) for p in e.path) or "(root)"
        report.errors.append(f"run.json schema: {loc}: {e.message}")
    if report.errors:
        return None

    stamp = run_id_timestamp(run_doc["run_id"])
    expected = run_doc["created_at"].replace("-", "").replace(":", "")
    if stamp != expected:
        report.errors.append(
            f"run.json: run_id timestamp '{stamp}' disagrees with "
            f"created_at '{run_doc['created_at']}'"
        )

    if run_doc["inputs"].get("brand_lock_configured") is False:
        report.warnings.append(
            "run.json: brand_lock_configured is false, so this run was built against "
            "an unfilled template rather than a real brand-lock"
        )

    inputs = run_doc["inputs"]
    _check_hash(report, "inputs", inputs.get("shots_ref"), inputs.get("shots_sha256"))
    _check_hash(
        report,
        "inputs",
        inputs.get("text_overlays_ref"),
        inputs.get("text_overlays_sha256"),
    )
    _check_hash(
        report, "inputs", inputs.get("brand_lock_ref"), inputs.get("brand_lock_sha256")
    )

    numbers = [r["round"] for r in run_doc.get("rounds", [])]
    report.rounds_seen = sorted(numbers)
    if len(numbers) != len(set(numbers)):
        report.errors.append("run.json: duplicate round numbers")
    if numbers and sorted(numbers) != list(range(1, max(numbers) + 1)):
        report.errors.append(
            f"run.json: rounds must run 1..N with no gaps, got {sorted(numbers)}"
        )

    for rnd in run_doc.get("rounds", []):
        for prompt in rnd.get("prompts", []):
            _check_hash(
                report,
                f"round {rnd['round']} prompt",
                prompt.get("ref"),
                prompt.get("sha256"),
            )
        for shot_id in rnd.get("post_only_shots", []) or []:
            report.warnings.append(
                f"round {rnd['round']}: {shot_id} is recorded as post-only, so it owes "
                f"compositing work that no prompt or frame will show"
            )

    return run_doc


def _round_of(path: Path, output_dir: Path, data: dict) -> int:
    """
    Which round a critique belongs to.

    The directory name wins, because that is the addressing scheme. A legacy critique
    sitting at the output root has no directory to read, so fall back to its own
    `round` field and then to 1.
    """
    try:
        parent = path.relative_to(output_dir).parent.name
    except ValueError:
        parent = ""
    if parent.startswith("round-") and parent[len("round-"):].isdigit():
        return int(parent[len("round-"):])
    declared = data.get("round")
    return declared if isinstance(declared, int) and declared >= 1 else 1


def check_critiques(report: Report, run_doc: dict | None) -> None:
    critique_validator = Draft202012Validator(_load_critique_schema())
    seen: dict[tuple[str, int], Path] = {}

    # critique_paths() is the one definition of "where critiques live", shared with
    # validate_critique.py and shots-to-html.py. Walking the round directories directly
    # meant this tool ignored a legacy root critique.json that the other two read, so
    # the preview showed a verdict badge for a shot this tool called unreviewed.
    for path in critique_paths(report.output_dir):
        try:
            rel = path.relative_to(report.output_dir)
        except ValueError:
            rel = path
        data, err = load_json(path)
        if err:
            report.errors.append(f"{rel}: {err}")
            continue
        if not isinstance(data, dict):
            report.errors.append(f"{rel}: top level is not an object")
            continue

        errors, warnings = validate_critique_doc(data, critique_validator)
        report.errors.extend(f"{rel}: {e}" for e in errors)
        report.warnings.extend(f"{rel}: {w}" for w in warnings)
        if errors:
            continue

        round_no = _round_of(path, report.output_dir, data)
        in_round_dir = rel.parent.name.startswith("round-")

        if in_round_dir and data.get("round") not in (None, round_no):
            report.errors.append(
                f"{rel}: declares round {data.get('round')} but sits in round-{round_no}/"
            )
        if run_doc and data.get("run_id") not in (None, run_doc["run_id"]):
            report.errors.append(
                f"{rel}: run_id '{data.get('run_id')}' does not match run.json "
                f"'{run_doc['run_id']}'"
            )

        shot_id = data.get("shot_id")
        if shot_id:
            key = (shot_id, round_no)
            if key in seen:
                report.errors.append(
                    f"{rel}: a second critique for {shot_id} in round {round_no} "
                    f"already exists at {seen[key]}; "
                    f"two operators reviewed the same shot in the same round"
                )
            else:
                seen[key] = rel

        _check_hash(report, f"{rel} image", data.get("image_ref"), data.get("image_sha256"))
        _check_hash(report, f"{rel} prompt", data.get("prompt_ref"), data.get("prompt_sha256"))
        _check_hash(
            report,
            f"{rel} brand-lock",
            data.get("brand_lock_ref"),
            data.get("brand_lock_sha256"),
        )

        if shot_id:
            entry = report.shots.setdefault(shot_id, {"rounds": {}})
            entry["rounds"][str(round_no)] = {
                "verdict": data.get("verdict"),
                "confidence": data.get("confidence"),
                "critique_ref": str(rel),
                "issues": len(data.get("issues", [])),
            }


def check_coverage(report: Report, run_doc: dict | None) -> None:
    shots_rel = "shots.json"
    if run_doc:
        shots_rel = run_doc["inputs"].get("shots_ref", "shots.json")
    shots_data, err = load_json(report.output_dir / shots_rel)
    shot_ids: list[str] = []
    if err:
        report.warnings.append(f"coverage: cannot read {shots_rel}, skipped ({err})")
    elif isinstance(shots_data, dict):
        shot_ids = [
            s["id"] for s in shots_data.get("shots", []) if isinstance(s.get("id"), str)
        ]

    reviewed_by_round: dict[int, set[str]] = {}
    for shot_id, entry in report.shots.items():
        for rnd in entry["rounds"]:
            reviewed_by_round.setdefault(int(rnd), set()).add(shot_id)

    for round_no, directory in round_dirs(report.output_dir, "frames"):
        reviewed = reviewed_by_round.get(round_no, set())
        for path in sorted(directory.iterdir()):
            if path.suffix.lstrip(".").lower() not in IMAGE_EXTS:
                continue
            frame_shot = path.stem
            if frame_shot not in reviewed:
                report.errors.append(
                    f"coverage: frames/round-{round_no}/{path.name} has no critique for "
                    f"round {round_no}; it was never reviewed"
                )

    for shot_id in shot_ids:
        entry = report.shots.get(shot_id)
        if not entry:
            report.warnings.append(
                f"coverage: {shot_id} has no critique in any round"
            )
            continue
        latest = max(int(r) for r in entry["rounds"])
        entry["latest_round"] = latest
        entry["latest_verdict"] = entry["rounds"][str(latest)]["verdict"]

    for shot_id in report.shots:
        if shot_ids and shot_id not in shot_ids:
            report.errors.append(
                f"coverage: a critique names {shot_id}, which is not in {shots_rel}"
            )


def validate_tree(output_dir: Path) -> Report:
    report = Report(output_dir)
    if not output_dir.is_dir():
        report.errors.append(f"not a directory: {output_dir}")
        return report
    run_doc = check_run_doc(report)
    check_critiques(report, run_doc)
    check_coverage(report, run_doc)
    _finalize_hash_failures(report)
    return report


def outstanding(report: Report) -> list[str]:
    """Shots whose latest verdict is not ACCEPT."""
    return sorted(
        shot_id
        for shot_id, entry in report.shots.items()
        if entry.get("latest_verdict") not in (None, "ACCEPT")
    )


def selftest() -> int:
    """Run the bundled worked example, then tamper with a copy and prove drift is caught."""
    import shutil
    import tempfile

    ok = True

    clean = validate_tree(WORKED_RUN)
    if clean.errors:
        print(f"  FAIL  selftest: the bundled worked run should be clean, got: {clean.errors}")
        ok = False
    else:
        print("  ok    selftest: the bundled worked run passes")

    if outstanding(clean):
        print(f"  FAIL  selftest: worked run should have no outstanding shots, got {outstanding(clean)}")
        ok = False
    else:
        print("  ok    selftest: every shot in the worked run ends on ACCEPT")

    with tempfile.TemporaryDirectory() as tmp:
        scratch = Path(tmp) / "run"
        shutil.copytree(WORKED_RUN, scratch)
        frame = scratch / "frames" / "round-2" / "shot_02.png"
        frame.write_bytes(frame.read_bytes() + b"\x00")
        report = validate_tree(scratch)
        if any("does not match the hash recorded" in e for e in report.errors):
            print("  ok    selftest: a frame regenerated after its critique is caught")
        else:
            print(f"  FAIL  selftest: frame tampering was not caught, got: {report.errors}")
            ok = False

    with tempfile.TemporaryDirectory() as tmp:
        scratch = Path(tmp) / "run"
        shutil.copytree(WORKED_RUN, scratch)
        lock = scratch / "brand-lock.snapshot.md"
        lock.write_text(lock.read_text() + "\n<!-- edited mid-project -->\n")
        report = validate_tree(scratch)
        if any("brand-lock.snapshot.md' does not match" in e for e in report.errors):
            print("  ok    selftest: a brand-lock edited mid-project is caught")
        else:
            print(f"  FAIL  selftest: brand-lock drift was not caught, got: {report.errors}")
            ok = False

    with tempfile.TemporaryDirectory() as tmp:
        scratch = Path(tmp) / "run"
        shutil.copytree(WORKED_RUN, scratch)
        src = scratch / "critiques" / "round-2" / "shot_02.critique.json"
        (scratch / "critiques" / "round-2" / "shot_02.operator-b.json").write_text(
            src.read_text()
        )
        report = validate_tree(scratch)
        if any("two operators reviewed the same shot" in e for e in report.errors):
            print("  ok    selftest: two critiques for one shot in one round is caught")
        else:
            print(f"  FAIL  selftest: duplicate critique was not caught, got: {report.errors}")
            ok = False

    with tempfile.TemporaryDirectory() as tmp:
        scratch = Path(tmp) / "run"
        shutil.copytree(WORKED_RUN, scratch)
        source = scratch / "frames" / "round-2" / "shot_02.png"
        (scratch / "frames" / "round-2" / "shot_01.png").write_bytes(source.read_bytes())
        report = validate_tree(scratch)
        if any("was never reviewed" in e for e in report.errors):
            print("  ok    selftest: a frame with no critique for its round is caught")
        else:
            print(f"  FAIL  selftest: unreviewed frame was not caught, got: {report.errors}")
            ok = False

    # A legacy tree keeps its critique at the output root. validate_critique.py and
    # shots-to-html.py both read it, so this tool has to as well: reporting a shot as
    # unreviewed while the preview shows its verdict badge is the exact kind of
    # disagreement between consumers that this release exists to remove.
    with tempfile.TemporaryDirectory() as tmp:
        scratch = Path(tmp) / "legacy"
        scratch.mkdir()
        shutil.copy(WORKED_RUN / "shots.json", scratch / "shots.json")
        shutil.copy(
            WORKED_RUN / "critiques" / "round-1" / "shot_01.critique.json",
            scratch / "critique.json",
        )
        report = validate_tree(scratch)
        if "shot_01" in report.shots:
            print("  ok    selftest: a legacy root critique.json is still discovered")
        else:
            print(
                "  FAIL  selftest: legacy root critique.json was ignored; "
                f"shots seen: {sorted(report.shots)}"
            )
            ok = False

    print()
    print("Selftest passed." if ok else "Selftest FAILED.")
    return 0 if ok else 1


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print("Usage: python tools/validate_provenance.py <output-dir> [...]")
        print("       python tools/validate_provenance.py <output-dir> --require-accept")
        print("       python tools/validate_provenance.py --examples")
        print("       python tools/validate_provenance.py --selftest")
        return 2
    if "--selftest" in args:
        return selftest()

    require_accept = "--require-accept" in args
    as_json = "--json" in args
    targets_raw = [a for a in args if not a.startswith("--")]

    if "--examples" in args:
        targets = [WORKED_RUN]
    elif targets_raw:
        targets = [Path(t) for t in targets_raw]
    else:
        print("ERROR: no output directory given")
        return 2

    reports = [validate_tree(t) for t in targets]

    if as_json:
        print(json.dumps([r.as_dict() for r in reports], indent=2))
    else:
        print(f"Validating provenance for {len(reports)} output tree(s)")
        print()
        for report in reports:
            try:
                label = report.output_dir.relative_to(REPO_ROOT)
            except ValueError:
                label = report.output_dir
            if report.errors:
                print(f"  FAIL  {label}")
                for err in report.errors:
                    print(f"        - {err}")
            else:
                print(f"  ok    {label}  ({len(report.shots)} shot(s), rounds {report.rounds_seen or 'none'})")
            for warn in report.warnings:
                print(f"  warn  {label}: {warn}")
            for shot_id in sorted(report.shots):
                entry = report.shots[shot_id]
                verdict = entry.get("latest_verdict", "?")
                print(
                    f"        {shot_id}: {verdict} "
                    f"(round {entry.get('latest_round', '?')})"
                )
        print()

    failed = any(r.errors for r in reports)
    unresolved = {
        str(r.output_dir): outstanding(r) for r in reports if outstanding(r)
    }

    if not as_json:
        if failed:
            total = sum(len(r.errors) for r in reports)
            print(f"FAILED: {total} provenance error(s).")
        elif require_accept and unresolved:
            for path, shots in unresolved.items():
                print(f"NOT DONE: {path} still has non-ACCEPT shots: {', '.join(shots)}")
        else:
            print("Provenance chain intact.")

    if failed:
        return 1
    if require_accept and unresolved:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
