#!/usr/bin/env python3
"""
Validate the prompt files visual-prompt-forge writes.

The forge documents four hard rules and a quality-bar checklist, and until this file
existed every one of them was enforced by a model remembering to check its own work.
That is not a small gap. Rule 3, series_lock anchors appear verbatim in every prompt,
is the rule that produces visual consistency across a series, and it is also the
easiest one in the kit to break by paraphrasing while writing fluent prose. A careful
pass over a seven-shot storyboard drifted on it seven times out of seven with every
other validator green.

Checks:
  1. The header block names the storyboard, generator, aspect, brand-lock, run, round.
  2. The generator is an id in the capability matrix.
  3. The header aspect matches project.aspect in shots.json.
  4. No shot's prompt exceeds that generator's max_prompt_words ceiling.
  5. Every shot block names a shot that exists. A full pass covers every shot; a
     revision file covers a subset.
  6. Rule 1: no on-screen text content appears in any prompt. Text is composited.
  7. Rule 3: series_lock environment, lighting, and color_grade appear verbatim.
     The character anchor is a warning, because a shot with no person in it can
     legitimately omit it.
  8. No duplicate shot blocks in one file.

Usage:
    python tools/validate_prompts.py <output-dir>
    python tools/validate_prompts.py <output-dir>/prompts/round-1/flux.txt
    python tools/validate_prompts.py --examples
    python tools/validate_prompts.py --selftest
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from _shotkit import REPO_ROOT, capability_map, load_json

WORKED_RUN = REPO_ROOT / "skills" / "visual-asset-critic" / "examples" / "worked-run"

SHOT_HEADER = re.compile(
    r"^#\s*(?:revision\s+of\s+)?(shot_\d{2,3})\b(.*)$", re.IGNORECASE
)
COMMENT = re.compile(r"^\s*#")

HEADER_FIELDS = ("Storyboard", "Generator", "Aspect", "Brand-lock", "Run", "Round")

# series_lock keys that describe every frame, so every prompt has to carry them.
UNIVERSAL_ANCHORS = ("environment", "lighting", "color_grade")


def parse_blocks(text: str) -> tuple[dict[str, str], list[tuple[str, str]]]:
    """Return (header fields, [(shot_id, prompt body)])."""
    header: dict[str, str] = {}
    blocks: list[tuple[str, list[str]]] = []
    current: list[str] | None = None

    for line in text.splitlines():
        m = SHOT_HEADER.match(line)
        if m:
            current = []
            blocks.append((m.group(1), current))
            continue
        if current is None:
            hm = re.match(r"^#\s*([A-Za-z-]+)\s*:\s*(.+?)\s*$", line)
            if hm:
                header[hm.group(1).strip()] = hm.group(2).strip()
            continue
        if not COMMENT.match(line):
            current.append(line)

    return (header, [(sid, "\n".join(b).strip()) for sid, b in blocks])


def check_file(
    path: Path, shots_data: dict, caps: dict[str, dict]
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    label = path.name

    text = path.read_text(encoding="utf-8")
    header, blocks = parse_blocks(text)

    if not blocks:
        return ([f"{label}: no shot blocks found; expected '# shot_NN, ...' lines"], warnings)

    for field in HEADER_FIELDS:
        if field not in header:
            warnings.append(f"{label}: header is missing '# {field}:'")

    generator = header.get("Generator", "").split()[0] if header.get("Generator") else None
    entry = caps.get(generator) if generator else None
    if generator and entry is None:
        errors.append(
            f"{label}: header names generator '{generator}', which is not an id in "
            f"_capabilities.json"
        )
    if generator is None:
        # Fall back to the filename: flux.txt or revised-flux.txt
        stem = path.stem.replace("revised-", "")
        entry = caps.get(stem)
        if entry:
            warnings.append(
                f"{label}: no '# Generator:' header, inferred '{stem}' from the filename"
            )

    project = shots_data.get("project", {})
    if "Aspect" in header and header["Aspect"] != project.get("aspect"):
        errors.append(
            f"{label}: header aspect '{header['Aspect']}' does not match "
            f"project.aspect '{project.get('aspect')}'"
        )

    shot_ids = [s["id"] for s in shots_data.get("shots", [])]
    by_id = {s["id"]: s for s in shots_data.get("shots", [])}
    series = shots_data.get("series_lock", {})

    seen: set[str] = set()
    for sid, body in blocks:
        if sid in seen:
            errors.append(f"{label}: {sid} appears in more than one block")
        seen.add(sid)
        if sid not in by_id:
            errors.append(f"{label}: names {sid}, which is not in shots.json")
            continue
        if not body:
            errors.append(f"{label}: {sid} has a header but no prompt body")
            continue

        if entry:
            words = len(body.split())
            ceiling = entry["max_prompt_words"]
            if words > ceiling:
                errors.append(
                    f"{label}: {sid} is {words} words, over the "
                    f"{entry['id']} ceiling of {ceiling}"
                )

        low = body.lower()
        for key in UNIVERSAL_ANCHORS:
            value = series.get(key)
            if value and value.lower() not in low:
                errors.append(
                    f"{label}: {sid} does not carry the series_lock {key} verbatim. "
                    f"Paraphrasing an anchor is what makes shots stop matching each other"
                )
        character = series.get("character")
        if character and character.lower() not in low:
            warnings.append(
                f"{label}: {sid} does not carry the series_lock character verbatim; "
                f"correct only if this shot has no person in it"
            )

    # Rule 1: text is composited, never described.
    overlays_path = path.parent.parent.parent / "text-overlays.json"
    overlays_data, ov_err = load_json(overlays_path)
    if not ov_err and isinstance(overlays_data, dict):
        for overlay in overlays_data.get("overlays", []):
            content = overlay.get("content")
            if not isinstance(content, str) or len(content) < 8:
                continue
            needle = content.lower().rstrip(".!?")
            for sid, body in blocks:
                if needle in body.lower():
                    errors.append(
                        f"{label}: {sid} contains the copy of overlay "
                        f"{overlay.get('id')} verbatim. On-screen text is composited, "
                        f"never put in an image prompt"
                    )

    is_revision = path.name.startswith("revised-")
    if not is_revision:
        for missing in [s for s in shot_ids if s not in seen]:
            errors.append(f"{label}: full pass is missing a block for {missing}")

    return (errors, warnings)


def collect_prompt_files(target: Path) -> tuple[Path | None, list[Path]]:
    """Return (output_dir, prompt files). Accepts an output dir or a single file."""
    if target.is_file():
        # prompts/round-N/<file>.txt  ->  output dir is three levels up
        return (target.parent.parent.parent, [target])
    if target.is_dir():
        found = sorted(target.glob("prompts/round-*/*.txt"))
        if not found:
            found = sorted(target.glob("prompts/*.txt"))  # pre-3.0.0 flat layout
        return (target, found)
    return (None, [])


def validate_target(target: Path) -> tuple[list[str], list[str]]:
    out_dir, files = collect_prompt_files(target)
    if out_dir is None:
        return ([f"not a file or directory: {target}"], [])
    if not files:
        return ([f"no prompt files found under {target}"], [])

    shots_data, err = load_json(out_dir / "shots.json")
    if err:
        return ([f"cannot read shots.json next to the prompts: {err}"], [])

    caps = capability_map()
    errors: list[str] = []
    warnings: list[str] = []
    for path in files:
        e, w = check_file(path, shots_data, caps)
        errors += e
        warnings += w
    return (errors, warnings)


SHOTS_FIXTURE = {
    "project": {"aspect": "9:16"},
    "series_lock": {
        "character": "founder in a navy crewneck",
        "environment": "minimalist home office, oak desk",
        "lighting": "soft window light from camera-left",
        "color_grade": "warm filmic with muted teal shadows",
    },
    "shots": [{"id": "shot_01"}, {"id": "shot_02"}],
}


def _fixture(body_01: str, body_02: str | None = None, aspect: str = "9:16") -> str:
    out = [
        "# Storyboard: Fixture",
        "# Generator: flux",
        f"# Aspect: {aspect}",
        "# Brand-lock: brand-lock.snapshot.md",
        "# Run: 20260730T180000Z-7c41e0a9",
        "# Round: 1",
        "",
        "# shot_01, hook, 0.0-2.0s, MCU eye-level static",
        body_01,
        "",
    ]
    if body_02 is not None:
        out += ["# shot_02, pain, 2.0-6.0s, MS eye-level push", body_02, ""]
    return "\n".join(out)


def selftest() -> int:
    import tempfile

    ok = True
    sl = SHOTS_FIXTURE["series_lock"]
    good = (
        f"Medium close-up of a {sl['character']}. {sl['environment']}. "
        f"{sl['lighting']}. {sl['color_grade']}. Photorealistic."
    )
    drifted = (
        "Medium close-up of a founder in a navy sweater. A minimal home office with "
        "an oak desk. Soft light from the left. Warm grade with teal shadows."
    )

    cases = [
        ("a compliant full pass passes", _fixture(good, good), False),
        ("a paraphrased anchor is caught", _fixture(drifted, good), True),
        ("a missing shot in a full pass is caught", _fixture(good), True),
        ("an aspect mismatch is caught", _fixture(good, good, aspect="16:9"), True),
        (
            "an over-ceiling prompt is caught",
            _fixture(good + " extra" * 200, good),
            True,
        ),
        (
            "an unknown shot id is caught",
            _fixture(good, good).replace("# shot_02,", "# shot_09,"),
            True,
        ),
        (
            "a duplicate shot block is caught",
            _fixture(good, good).replace("# shot_02,", "# shot_01,"),
            True,
        ),
        (
            "an empty prompt body is caught",
            _fixture(good, ""),
            True,
        ),
    ]

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "output"
        (out / "prompts" / "round-1").mkdir(parents=True)
        (out / "shots.json").write_text(json.dumps(SHOTS_FIXTURE))
        caps = capability_map()
        for label, text, should_fail in cases:
            p = out / "prompts" / "round-1" / "flux.txt"
            p.write_text(text)
            errors, _ = check_file(p, SHOTS_FIXTURE, caps)
            if bool(errors) == should_fail:
                print(f"  ok    selftest: {label}")
            else:
                print(f"  FAIL  selftest: {label} -> {errors or '(no errors)'}")
                ok = False

        # Rule 1: overlay copy leaking into a prompt.
        (out / "text-overlays.json").write_text(
            json.dumps(
                {
                    "version": "1.0",
                    "overlays": [
                        {"id": "text_01", "content": "You are the bottleneck."}
                    ],
                }
            )
        )
        p = out / "prompts" / "round-1" / "flux.txt"
        p.write_text(_fixture(good + " The words You are the bottleneck appear.", good))
        errors, _ = check_file(p, SHOTS_FIXTURE, caps)
        if any("composited" in e for e in errors):
            print("  ok    selftest: overlay copy inside a prompt is caught")
        else:
            print(f"  FAIL  selftest: overlay leak not caught -> {errors}")
            ok = False

        # A revision file covers a subset, and that is not an error.
        rev = out / "prompts" / "round-2"
        rev.mkdir()
        rp = rev / "revised-flux.txt"
        rp.write_text(_fixture(good))
        errors, _ = check_file(rp, SHOTS_FIXTURE, caps)
        if not errors:
            print("  ok    selftest: a revision file may cover a subset of shots")
        else:
            print(f"  FAIL  selftest: revision subset flagged -> {errors}")
            ok = False

    print()
    print("Selftest passed." if ok else "Selftest FAILED.")
    return 0 if ok else 1


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print("Usage: python tools/validate_prompts.py <output-dir|prompt-file> [...]")
        print("       python tools/validate_prompts.py --examples")
        print("       python tools/validate_prompts.py --selftest")
        return 2
    if "--selftest" in args:
        return selftest()

    targets = [WORKED_RUN] if "--examples" in args else [Path(a) for a in args]

    print(f"Validating prompt files for {len(targets)} target(s)")
    print()

    total_errors = 0
    total_warnings = 0
    for target in targets:
        errors, warnings = validate_target(target)
        try:
            shown = target.relative_to(REPO_ROOT)
        except ValueError:
            shown = target
        total_warnings += len(warnings)
        if not errors:
            print(f"  ok    {shown}")
        else:
            total_errors += len(errors)
            print(f"  FAIL  {shown}")
            for e in errors:
                print(f"        - {e}")
        for w in warnings:
            print(f"  warn  {shown}: {w}")

    print()
    if total_errors == 0:
        print(f"All prompt files valid ({total_warnings} warning(s)).")
        return 0
    print(f"FAILED: {total_errors} error(s) across prompt files.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
