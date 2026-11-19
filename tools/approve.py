#!/usr/bin/env python3
"""Record that a person approved a plan or a set of frames.

A critique is a model's review. It is not a person saying yes. This tool writes the
second thing down: who approved, when, and exactly what they approved, by hash.

  approve.py output/ --by "Dana Reyes"                  approve the plan (shots.json)
  approve.py output/ --by "Dana Reyes" --what frames    approve the accepted frames
  approve.py output/ --by "Dana Reyes" --note "ok to shoot"
  approve.py output/ --list                             every approval, and if it still holds
  approve.py --selftest

Each approval is one new file in output/approvals/. Nothing is edited, so run.json and
the pinned plan are left alone. An approval of the plan holds while shots.json has the
hash it had. An approval of the frames holds while each shot's latest critique is the
one that was approved. `sk validate` and the board say when one no longer holds.

What this is not. The name is whatever was typed. It is a record, not a signature, and
it does not prove who was at the keyboard.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _shotkit import (  # noqa: E402
    ISO_INSTANT_RE, RUN_ID_RE, critique_paths, iso_instant, load_json, sha256_file,
)

WHAT = ("plan", "frames")
SHA_RE = re.compile(r"^[0-9a-f]{64}$")


class Stop(Exception):
    """A problem to print as one line and exit on, not a traceback."""


def _latest_critiques(out_dir: Path) -> dict[str, dict]:
    """Each shot's latest critique, read straight from the critique files."""
    latest: dict[str, dict] = {}
    for path in critique_paths(out_dir):
        doc, err = load_json(path)
        if err or not isinstance(doc, dict) or not isinstance(doc.get("shot_id"), str):
            continue
        number = doc.get("round") if isinstance(doc.get("round"), int) else 1
        if doc["shot_id"] in latest and latest[doc["shot_id"]]["round"] >= number:
            continue
        latest[doc["shot_id"]] = {
            "round": number,
            "verdict": doc.get("verdict"),
            "critique_ref": str(path.relative_to(out_dir)),
            "critique_sha256": sha256_file(path),
        }
    return latest


def _shot_ids(out_dir: Path) -> list[str]:
    doc, err = load_json(out_dir / "shots.json")
    if err or not isinstance(doc, dict):
        return []
    return [s["id"] for s in doc.get("shots") or [] if isinstance(s, dict) and isinstance(s.get("id"), str)]


def read_approvals(out_dir: Path) -> tuple[list[dict], list[str]]:
    """Every approval file, oldest first, with what is wrong with any that is malformed."""
    folder = out_dir / "approvals"
    docs: list[dict] = []
    errors: list[str] = []
    if not folder.is_dir():
        return docs, errors
    for path in sorted(folder.glob("*.json")):
        rel = f"approvals/{path.name}"
        doc, err = load_json(path)
        if err or not isinstance(doc, dict):
            errors.append(f"{rel}: {err or 'is not a JSON object'}")
            continue
        problems = []
        if not isinstance(doc.get("by"), str) or not doc["by"].strip():
            problems.append("'by' is missing")
        if doc.get("what") not in WHAT:
            problems.append("'what' must be plan or frames")
        if not isinstance(doc.get("at"), str) or not ISO_INSTANT_RE.match(doc["at"]):
            problems.append("'at' must be a UTC time like 2026-01-31T09:00:00Z")
        if not isinstance(doc.get("shots_sha256"), str) or not SHA_RE.match(doc["shots_sha256"]):
            problems.append("'shots_sha256' must be a SHA-256")
        if doc.get("what") == "frames" and not isinstance(doc.get("frames"), dict):
            problems.append("a frames approval needs 'frames'")
        if problems:
            errors.append(f"{rel}: " + "; ".join(problems))
            continue
        doc["_ref"] = rel
        docs.append(doc)
    return docs, errors


def status(out_dir: Path) -> tuple[list[dict], list[str]]:
    """Approvals with `holds` and `why` filled in, and the malformed-file errors."""
    docs, errors = read_approvals(out_dir)
    if not docs:
        return docs, errors
    run_doc, _ = load_json(out_dir / "run.json")
    run_id = run_doc.get("run_id") if isinstance(run_doc, dict) else None
    shots_path = out_dir / "shots.json"
    shots_now = sha256_file(shots_path) if shots_path.is_file() else None
    latest = _latest_critiques(out_dir)
    for doc in docs:
        why = []
        if doc.get("run_id") and run_id and doc["run_id"] != run_id:
            why.append("it belongs to another run")
        if doc["shots_sha256"] != shots_now:
            why.append("the plan has changed since")
        if doc["what"] == "frames":
            for shot_id, was in sorted(doc["frames"].items()):
                now = latest.get(shot_id)
                if not now or now.get("critique_sha256") != (was or {}).get("critique_sha256"):
                    why.append(f"{shot_id} has changed since")
            extra = sorted(set(latest) - set(doc["frames"]))
            if extra:
                why.append("it does not cover " + ", ".join(extra))
        doc["holds"] = not why
        doc["why"] = "; ".join(why)
    return docs, errors


def approve(out_dir: Path, by: str, what: str, note: str | None, at: str | None = None) -> Path:
    by = (by or "").strip()
    if not by:
        raise Stop("say who is approving: --by \"Name\"")
    if what not in WHAT:
        raise Stop("--what is plan or frames")
    shots_path = out_dir / "shots.json"
    if not shots_path.is_file():
        raise Stop(f"no shots.json in {out_dir}")
    run_doc, _ = load_json(out_dir / "run.json")
    run_id = run_doc.get("run_id") if isinstance(run_doc, dict) else None
    if not isinstance(run_id, str) or not RUN_ID_RE.match(run_id):
        raise Stop(f"no run.json with a run id in {out_dir}. An approval has to name the run it is for.")
    doc: dict = {
        "version": "1.0",
        "run_id": run_id,
        "by": by,
        "at": at or iso_instant(),
        "what": what,
        "shots_sha256": sha256_file(shots_path),
    }
    if note and note.strip():
        doc["note"] = note.strip()
    if what == "frames":
        from validate_provenance import validate_tree  # here, because that module reads this one

        chain_errors = validate_tree(out_dir, frames_optional=True, with_approvals=False).errors
        latest, shot_ids = _latest_critiques(out_dir), _shot_ids(out_dir)
        if chain_errors:
            raise Stop("the run does not pass its checks, so its frames cannot be approved. Run: sk validate "
                       f"{out_dir}")
        open_shots = [s for s in shot_ids if (latest.get(s) or {}).get("verdict") != "ACCEPT"]
        if open_shots or not shot_ids:
            raise Stop("frames can be approved when every shot's latest critique is ACCEPT. Still open: "
                       + (", ".join(open_shots) or "every shot"))
        doc["frames"] = {s: {k: latest[s][k] for k in ("round", "critique_ref", "critique_sha256")} for s in shot_ids}
    folder = out_dir / "approvals"
    folder.mkdir(exist_ok=True)
    stamp = re.sub(r"[-:]", "", doc["at"])
    path = folder / f"{stamp}-{what}.json"
    n = 2
    while path.exists():
        path = folder / f"{stamp}-{what}-{n}.json"
        n += 1
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def show(out_dir: Path) -> int:
    docs, errors = status(out_dir)
    for err in errors:
        print(f"  FAIL  {err}")
    if not docs and not errors:
        print("No approvals recorded.")
        return 0
    for doc in docs:
        state = "holds" if doc["holds"] else "no longer holds: " + doc["why"]
        note = f"  \"{doc['note']}\"" if doc.get("note") else ""
        print(f"  {doc['what']:<6} {doc['by']}, {doc['at']}. {state}{note}")
    return 1 if errors else 0


def selftest() -> int:
    worked = Path(__file__).resolve().parent.parent / "skills" / "visual-asset-critic" / "examples" / "worked-run"
    checks: list[tuple[str, bool]] = []
    with tempfile.TemporaryDirectory() as tmp:
        run = Path(tmp) / "run"
        shutil.copytree(worked, run)
        before = {p.name: sha256_file(p) for p in (run / "run.json", run / "shots.json")}
        plan = approve(run, "Dana Reyes", "plan", "ok to shoot", at="2026-01-31T09:00:00Z")
        frames = approve(run, "Dana Reyes", "frames", None, at="2026-01-31T09:05:00Z")
        after = {p.name: sha256_file(p) for p in (run / "run.json", run / "shots.json")}
        checks.append(("an approval is a new file and run.json and shots.json are untouched",
                       plan.is_file() and frames.is_file() and before == after))
        docs, errors = status(run)
        checks.append(("a fresh approval holds", len(docs) == 2 and not errors and all(d["holds"] for d in docs)))
        again = approve(run, "Dana Reyes", "plan", None, at="2026-01-31T09:00:00Z")
        checks.append(("a second approval in the same second gets its own file", again != plan and again.is_file()))
        try:
            approve(run, "  ", "plan", None)
            named = False
        except Stop:
            named = True
        checks.append(("an approval with no name is refused", named))

        latest_round = max(int(p.parent.name.split("-")[1]) for p in run.glob("critiques/round-*/shot_01.critique.json"))
        target = run / "critiques" / f"round-{latest_round}" / "shot_01.critique.json"
        target.write_text(target.read_text() + "\n")
        by_what = {d["what"]: d for d in status(run)[0] if d["_ref"] != f"approvals/{again.name}"}
        checks.append(("a frames approval stops holding when a shot's critique changes",
                       not by_what["frames"]["holds"] and by_what["plan"]["holds"]))

        shots = run / "shots.json"
        shots.write_text(shots.read_text() + "\n")
        checks.append(("a plan approval stops holding when shots.json changes",
                       not [d for d in status(run)[0] if d["what"] == "plan"][0]["holds"]))

        (run / "approvals" / "bad.json").write_text('{"by": "", "what": "film"}')
        checks.append(("a malformed approval file is reported", any("bad.json" in e for e in status(run)[1])))

    with tempfile.TemporaryDirectory() as tmp:
        run = Path(tmp) / "run"
        shutil.copytree(worked, run)
        for path in run.glob("critiques/round-*/shot_02.critique.*"):
            path.unlink()
        for path in run.glob("frames/round-*/shot_02.*"):
            path.unlink()
        try:
            approve(run, "Dana Reyes", "frames", None)
            refused = False
        except Stop as stop:
            refused = "shot_02" in str(stop)
        checks.append(("frames are not approved while a shot is still open", refused))

    ok = True
    for label, passed in checks:
        print(f"  {'ok  ' if passed else 'FAIL'}  selftest: {label}")
        ok = ok and passed
    print()
    print("Selftest passed." if ok else "Selftest FAILED.")
    return 0 if ok else 1


def main() -> int:
    p = argparse.ArgumentParser(description="Record that a person approved a plan or a set of frames.")
    p.add_argument("output_dir", nargs="?", type=Path, help="Folder that holds shots.json and run.json")
    p.add_argument("--by", help="Who is approving")
    p.add_argument("--what", default="plan", choices=WHAT, help="plan (default) or frames")
    p.add_argument("--note", help="A line to keep with the approval")
    p.add_argument("--list", action="store_true", help="Show every approval and whether it still holds")
    p.add_argument("--selftest", action="store_true", help="Prove the tool's guarantees")
    args = p.parse_args()
    if args.selftest:
        return selftest()
    if not args.output_dir:
        p.print_usage()
        return 2
    try:
        if args.list or not args.by:
            return show(args.output_dir)
        path = approve(args.output_dir, args.by, args.what, args.note)
    except Stop as stop:
        print(f"shotkit: {stop}", file=sys.stderr)
        return 1
    print(f"Recorded: {args.by} approved the {args.what}. {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
