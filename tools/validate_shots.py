#!/usr/bin/env python3
"""
Validate a storyboard output set: shots.json and text-overlays.json, as instances.

Schema validation alone was never enough here. Every rule below is documented in
skills/storyboard-architect/SKILL.md as a quality-bar checkbox, which means it was
enforced by a model remembering to check it. These are the same rules, executable.

Checks:
  1. shots.json validates against shots.schema.json.
  2. text-overlays.json validates against text-overlays.schema.json.
  3. Timing: end > start, no duplicate ids, no gaps, no overlaps, and the covered
     span matches project.duration_s within TIMING_TOLERANCE_S.
  4. Reference integrity, both directions: every shot.on_screen_text resolves to an
     overlay, every overlay.shot_id resolves to a shot, and every overlay is
     reachable from at least one shot.
  5. Overlay timing sits inside its shot window and exit is after enter.
  6. Every overlay color appears in the brand-lock palette.
  7. brand_lock_ref resolves on disk.
  8. Every assets.generated[].generator is a real id in the capability matrix.
  9. Warnings for prose leaks: on-screen copy repeated in a shot subject, raw hex in
     a shot subject, shot ids out of chronological order, overlay fonts not named in
     the brand-lock typography section.

Usage:
    python tools/validate_shots.py <output-dir> [...]
    python tools/validate_shots.py path/to/shots.json [...]
    python tools/validate_shots.py --examples          # every bundled example
    python tools/validate_shots.py --selftest          # prove the checks fire
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from jsonschema import Draft202012Validator
except ImportError:
    print("ERROR: jsonschema not installed. Run: pip install pyyaml jsonschema")
    sys.exit(1)

from _shotkit import (
    HEX_RE,
    REPO_ROOT,
    as_overlay_ids,
    as_shot_ids,
    capability_ids,
    load_json,
    palette_hexes,
    parse_typography,
)

SHOTS_SCHEMA = (
    REPO_ROOT / "skills" / "storyboard-architect" / "templates" / "shots.schema.json"
)
OVERLAYS_SCHEMA = (
    REPO_ROOT
    / "skills"
    / "storyboard-architect"
    / "templates"
    / "text-overlays.schema.json"
)
EXAMPLES_DIR = REPO_ROOT / "skills" / "storyboard-architect" / "examples"

TIMING_TOLERANCE_S = 0.1


def _schema_errors(data, validator: Draft202012Validator, label: str) -> list[str]:
    out = []
    for err in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
        loc = "/".join(str(p) for p in err.path) or "(root)"
        out.append(f"{label} schema: {loc}: {err.message}")
    return out


def check_timing(shots: list[dict], duration_s: float) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    seen: set[str] = set()
    for shot in shots:
        sid = shot.get("id", "?")
        if sid in seen:
            errors.append(f"timing: duplicate shot id '{sid}'")
        seen.add(sid)
        start, end = shot.get("start"), shot.get("end")
        if isinstance(start, (int, float)) and isinstance(end, (int, float)):
            if end <= start:
                errors.append(
                    f"timing: {sid} has end ({end}) not after start ({start})"
                )

    timed = [
        s
        for s in shots
        if isinstance(s.get("start"), (int, float))
        and isinstance(s.get("end"), (int, float))
    ]
    if not timed:
        return errors, warnings

    ordered = sorted(timed, key=lambda s: (s["start"], s["end"]))
    for a, b in zip(ordered, ordered[1:]):
        if b["start"] > a["end"] + 1e-9:
            errors.append(
                f"timing: gap between {a['id']} (ends {a['end']}) and "
                f"{b['id']} (starts {b['start']})"
            )
        elif b["start"] < a["end"] - 1e-9:
            errors.append(
                f"timing: overlap between {a['id']} (ends {a['end']}) and "
                f"{b['id']} (starts {b['start']})"
            )

    span = max(s["end"] for s in timed) - min(s["start"] for s in timed)
    if abs(span - duration_s) > TIMING_TOLERANCE_S:
        errors.append(
            f"timing: covered span {span:g}s does not match project.duration_s "
            f"{duration_s:g}s (tolerance {TIMING_TOLERANCE_S}s)"
        )

    if [s["id"] for s in timed] != [s["id"] for s in ordered]:
        warnings.append(
            "timing: shot ids are not in chronological order; readers assume they are"
        )

    return errors, warnings


def check_version_features(shots: list[dict], version: str) -> list[str]:
    """Features may not be used below the version that introduced them."""
    errors: list[str] = []
    if version in ("1.0", "1.1"):
        for shot in shots:
            if isinstance(shot.get("on_screen_text"), list):
                errors.append(
                    f"version: {shot.get('id')} uses the array form of on_screen_text, "
                    f"which requires version 1.2 (file declares {version})"
                )
    if version == "1.0":
        for shot in shots:
            if shot.get("assets") is not None:
                errors.append(
                    f"version: {shot.get('id')} carries an assets block, which "
                    f"requires version 1.1 or later (file declares 1.0)"
                )
    return errors


def check_references(
    shots: list[dict], overlays: list[dict]
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    shot_ids = {s.get("id") for s in shots}
    overlay_ids: set[str] = set()
    for overlay in overlays:
        oid = overlay.get("id")
        if oid in overlay_ids:
            errors.append(f"reference: duplicate overlay id '{oid}'")
        overlay_ids.add(oid)

    referenced: set[str] = set()
    for shot in shots:
        for oid in as_overlay_ids(shot.get("on_screen_text")):
            referenced.add(oid)
            if oid not in overlay_ids:
                errors.append(
                    f"reference: {shot.get('id')}.on_screen_text '{oid}' has no "
                    f"entry in text-overlays.json"
                )

    for overlay in overlays:
        oid = overlay.get("id")
        for sid in as_shot_ids(overlay.get("shot_id")):
            if sid not in shot_ids:
                errors.append(
                    f"reference: overlay {oid}.shot_id '{sid}' has no entry in shots.json"
                )
        if oid not in referenced:
            errors.append(
                f"reference: overlay {oid} is not reachable from any "
                f"shot.on_screen_text, so no renderer will show it"
            )

    return errors, warnings


def check_overlay_windows(shots: list[dict], overlays: list[dict]) -> list[str]:
    errors: list[str] = []
    by_id = {
        s["id"]: s
        for s in shots
        if isinstance(s.get("start"), (int, float))
        and isinstance(s.get("end"), (int, float))
    }

    for overlay in overlays:
        oid = overlay.get("id")
        enter = (overlay.get("enter") or {}).get("at")
        exit_at = (overlay.get("exit") or {}).get("at")
        if not isinstance(enter, (int, float)) or not isinstance(exit_at, (int, float)):
            continue
        if exit_at <= enter:
            errors.append(
                f"overlay: {oid} exit ({exit_at}) is not after enter ({enter})"
            )
        windows = [by_id[s] for s in as_shot_ids(overlay.get("shot_id")) if s in by_id]
        if not windows:
            continue
        lo = min(w["start"] for w in windows)
        hi = max(w["end"] for w in windows)
        if enter < lo - 1e-9 or exit_at > hi + 1e-9:
            errors.append(
                f"overlay: {oid} timing {enter}-{exit_at}s falls outside its shot "
                f"window {lo:g}-{hi:g}s"
            )

    return errors


def check_brand_alignment(
    shots: list[dict], overlays: list[dict], brand_lock_text: str | None
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if brand_lock_text is None:
        warnings.append(
            "brand: brand_lock_ref did not resolve, so palette and font checks were skipped"
        )
        return errors, warnings

    allowed = palette_hexes(brand_lock_text)
    for overlay in overlays:
        color = overlay.get("color")
        if isinstance(color, str) and color.lower() not in allowed:
            errors.append(
                f"brand: overlay {overlay.get('id')} color {color} is not in the "
                f"brand-lock palette"
            )

    fonts = {v.lower() for v in parse_typography(brand_lock_text).values() if v}
    if fonts:
        for overlay in overlays:
            font = overlay.get("font")
            if isinstance(font, str) and font.lower() not in fonts:
                warnings.append(
                    f"brand: overlay {overlay.get('id')} font '{font}' is not a font "
                    f"declared in the brand-lock typography section"
                )

    for shot in shots:
        subject = shot.get("subject")
        if not isinstance(subject, str):
            continue
        for hex_val in HEX_RE.findall(subject):
            warnings.append(
                f"brand: {shot.get('id')}.subject names a raw hex ({hex_val}); "
                f"colors belong in series_lock and the brand-lock"
            )

    return errors, warnings


def check_text_leak(shots: list[dict], overlays: list[dict]) -> list[str]:
    """On-screen copy repeated inside a shot subject. Text is a separate layer."""
    warnings: list[str] = []
    contents = {
        o.get("id"): o.get("content")
        for o in overlays
        if isinstance(o.get("content"), str) and len(o.get("content", "")) >= 8
    }
    for shot in shots:
        subject = shot.get("subject")
        if not isinstance(subject, str):
            continue
        lowered = subject.lower()
        for oid in as_overlay_ids(shot.get("on_screen_text")):
            content = contents.get(oid)
            if content and content.lower().rstrip(".!?") in lowered:
                warnings.append(
                    f"text: {shot.get('id')}.subject repeats overlay {oid} copy "
                    f"verbatim; on-screen text is composited, never described"
                )
    return warnings


def check_assets(shots: list[dict], known_generators: set[str]) -> list[str]:
    errors: list[str] = []
    if not known_generators:
        return errors
    for shot in shots:
        for entry in (shot.get("assets") or {}).get("generated", []) or []:
            gen = entry.get("generator")
            if isinstance(gen, str) and gen not in known_generators:
                errors.append(
                    f"assets: {shot.get('id')} generated frame names generator "
                    f"'{gen}', which is not in the capability matrix"
                )
            if entry.get("accepted") is True and not entry.get("critique_ref"):
                errors.append(
                    f"assets: {shot.get('id')} has an accepted frame with no "
                    f"critique_ref, which is an unsourced approval"
                )
    return errors


def validate_set(shots_path: Path) -> tuple[list[str], list[str]]:
    """Validate one shots.json plus the siblings it points at."""
    errors: list[str] = []
    warnings: list[str] = []

    shots_data, err = load_json(shots_path)
    if err:
        return ([err], warnings)
    if not isinstance(shots_data, dict):
        return ([f"{shots_path}: top level is not an object"], warnings)

    shots_schema, s_err = load_json(SHOTS_SCHEMA)
    overlays_schema, o_err = load_json(OVERLAYS_SCHEMA)
    if s_err or o_err:
        return ([s_err or o_err], warnings)

    errors += _schema_errors(
        shots_data, Draft202012Validator(shots_schema), "shots.json"
    )

    base = shots_path.parent
    overlays_path = base / "text-overlays.json"
    overlays: list[dict] = []
    if overlays_path.exists():
        overlays_data, ov_err = load_json(overlays_path)
        if ov_err:
            errors.append(f"text-overlays.json: {ov_err}")
        else:
            errors += _schema_errors(
                overlays_data,
                Draft202012Validator(overlays_schema),
                "text-overlays.json",
            )
            overlays = overlays_data.get("overlays", []) or []
    else:
        for shot in shots_data.get("shots", []) or []:
            if as_overlay_ids(shot.get("on_screen_text")):
                errors.append(
                    "reference: shots.json references on-screen text but "
                    "text-overlays.json is missing"
                )
                break

    if errors:
        # Structure-dependent checks assume schema-valid input.
        return (errors, warnings)

    shots = shots_data.get("shots", []) or []
    duration = shots_data.get("project", {}).get("duration_s")

    errors += check_version_features(shots, shots_data.get("version", ""))

    if isinstance(duration, (int, float)):
        t_err, t_warn = check_timing(shots, float(duration))
        errors += t_err
        warnings += t_warn

    r_err, r_warn = check_references(shots, overlays)
    errors += r_err
    warnings += r_warn
    errors += check_overlay_windows(shots, overlays)

    brand_ref = shots_data.get("brand_lock_ref")
    brand_text: str | None = None
    if isinstance(brand_ref, str):
        brand_path = base / brand_ref
        if brand_path.exists():
            brand_text = brand_path.read_text(encoding="utf-8")
        else:
            errors.append(
                f"brand: brand_lock_ref '{brand_ref}' does not resolve from {base}"
            )
    b_err, b_warn = check_brand_alignment(shots, overlays, brand_text)
    errors += b_err
    warnings += b_warn

    warnings += check_text_leak(shots, overlays)
    errors += check_assets(shots, capability_ids())

    return (errors, warnings)


def _resolve_target(raw: str) -> Path | None:
    path = Path(raw)
    if path.is_dir():
        candidate = path / "shots.json"
        return candidate if candidate.exists() else None
    return path if path.exists() else None


def selftest() -> int:
    """Prove the cross-field checks fire. Fixtures are in-memory, no files touched."""
    ok = True
    cases = [
        (
            "end not after start",
            lambda: check_timing(
                [{"id": "shot_01", "start": 5.0, "end": 3.0}], 30.0
            )[0],
        ),
        (
            "gap between shots",
            lambda: check_timing(
                [
                    {"id": "shot_01", "start": 0.0, "end": 2.0},
                    {"id": "shot_02", "start": 4.0, "end": 30.0},
                ],
                30.0,
            )[0],
        ),
        (
            "overlap between shots",
            lambda: check_timing(
                [
                    {"id": "shot_01", "start": 0.0, "end": 5.0},
                    {"id": "shot_02", "start": 3.0, "end": 30.0},
                ],
                30.0,
            )[0],
        ),
        (
            "span disagrees with duration",
            lambda: check_timing(
                [{"id": "shot_01", "start": 0.0, "end": 10.0}], 30.0
            )[0],
        ),
        (
            "dangling on_screen_text",
            lambda: check_references(
                [{"id": "shot_01", "on_screen_text": "text_09"}], []
            )[0],
        ),
        (
            "unreachable overlay",
            lambda: check_references(
                [{"id": "shot_01", "on_screen_text": None}],
                [{"id": "text_01", "shot_id": "shot_01"}],
            )[0],
        ),
        (
            "overlay outside its shot window",
            lambda: check_overlay_windows(
                [{"id": "shot_01", "start": 0.0, "end": 2.0}],
                [
                    {
                        "id": "text_01",
                        "shot_id": "shot_01",
                        "enter": {"at": 0.0},
                        "exit": {"at": 9.0},
                    }
                ],
            ),
        ),
        (
            "off-palette overlay color",
            lambda: check_brand_alignment(
                [],
                [{"id": "text_01", "color": "#ABCDEF"}],
                "## Palette\n\n| Role | Hex |\n|---|---|\n| Ink | `#2A2A32` |\n",
            )[0],
        ),
        (
            "accepted frame with no critique_ref",
            lambda: check_assets(
                [
                    {
                        "id": "shot_01",
                        "assets": {"generated": [{"path": "a.png", "accepted": True}]},
                    }
                ],
                {"flux"},
            ),
        ),
        (
            "unknown generator id",
            lambda: check_assets(
                [
                    {
                        "id": "shot_01",
                        "assets": {
                            "generated": [{"path": "a.png", "generator": "runway-sora"}]
                        },
                    }
                ],
                {"flux"},
            ),
        ),
        (
            "1.2 feature used in a 1.0 file",
            lambda: check_version_features(
                [{"id": "shot_01", "on_screen_text": ["text_01", "text_02"]}], "1.0"
            ),
        ),
    ]

    for label, fn in cases:
        produced = fn()
        if produced:
            print(f"  ok    selftest: {label} is caught")
        else:
            print(f"  FAIL  selftest: {label} was not caught")
            ok = False

    clean, clean_warn = check_timing(
        [
            {"id": "shot_01", "start": 0.0, "end": 2.0},
            {"id": "shot_02", "start": 2.0, "end": 30.0},
        ],
        30.0,
    )
    if clean or clean_warn:
        print(f"  FAIL  selftest: a clean shot list should pass, got: {clean + clean_warn}")
        ok = False
    else:
        print("  ok    selftest: a clean shot list passes")

    print()
    print("Selftest passed." if ok else "Selftest FAILED.")
    return 0 if ok else 1


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print("Usage: python tools/validate_shots.py <output-dir|shots.json> [...]")
        print("       python tools/validate_shots.py --examples")
        print("       python tools/validate_shots.py --selftest")
        return 2

    if "--selftest" in args:
        return selftest()

    if "--examples" in args:
        targets = sorted(EXAMPLES_DIR.glob("*/shots.json"))
        if not targets:
            print(f"ERROR: no bundled examples found under {EXAMPLES_DIR}")
            return 1
    else:
        targets = []
        for raw in args:
            resolved = _resolve_target(raw)
            if resolved is None:
                print(f"  FAIL  {raw}")
                print("        - no shots.json found at this path")
                return 1
            targets.append(resolved)

    print(f"Validating {len(targets)} storyboard set(s)")
    print()

    total_errors = 0
    total_warnings = 0
    for shots_path in targets:
        try:
            rel = shots_path.relative_to(REPO_ROOT)
        except ValueError:
            rel = shots_path
        errors, warnings = validate_set(shots_path)
        total_warnings += len(warnings)
        if not errors:
            print(f"  ok    {rel}")
        else:
            total_errors += len(errors)
            print(f"  FAIL  {rel}")
            for err in errors:
                print(f"        - {err}")
        for warn in warnings:
            print(f"  warn  {rel}: {warn}")

    print()
    if total_errors == 0:
        print(f"All storyboard sets valid ({total_warnings} warning(s)).")
        return 0
    print(f"FAILED: {total_errors} error(s) across storyboard sets.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
