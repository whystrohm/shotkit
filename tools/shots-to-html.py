#!/usr/bin/env python3
"""
Standalone helper: render an output folder into a single preview.html.

Renders skills/storyboard-html-preview/templates/preview.html.tpl, the same
structural template the storyboard-html-preview skill uses, so the two cannot drift.
All interpolated content is HTML-escaped: subjects, rationales, and VO lines are
model-generated prose, and one angle bracket in a rationale used to break the page a
client was looking at.

Two timestamps, deliberately distinct. "Run" is when the storyboard was produced, read
from run.json. "Rendered" is when this page was written. Collapsing them into one
"Generated" date meant re-rendering a preview six months later silently restamped the
run as today.

Usage:
    python tools/shots-to-html.py path/to/output-folder
    python tools/shots-to-html.py path/to/output-folder --out preview.html
    python tools/shots-to-html.py path/to/output-folder --inline-images
    python tools/shots-to-html.py path/to/output-folder --rendered-at 2026-07-30T00:00:00Z
    python tools/shots-to-html.py --selftest
"""

from __future__ import annotations

import argparse
import base64
import sys
from pathlib import Path

from _shotkit import (
    IMAGE_EXTS,
    PALETTE_ROLES,
    REPO_ROOT,
    as_overlay_ids,
    find_frame,
    iso_instant,
    load_json,
    parse_palette,
    parse_typography,
    round_dirs,
    sha256_file,
)
from _template import escape, render

TEMPLATE_DIR = REPO_ROOT / "skills" / "storyboard-html-preview" / "templates"

FALLBACK_BRAND = {
    "bg": "#FFFFFF",
    "ink": "#0F172A",
    "accent": "#3B82F6",
    "muted": "#64748B",
    "rule": "#E2E8F0",
    "display_font": "Inter",
    "body_font": "Inter",
}

FALLBACK_HEX = {
    "background": "#FFFFFF",
    "ink": "#0F172A",
    "accent": "#3B82F6",
    "muted": "#64748B",
    "rule": "#E2E8F0",
}


def read_template(name: str) -> str:
    return (TEMPLATE_DIR / name).read_text(encoding="utf-8")


def parse_brand_lock(path: Path) -> tuple[dict, list[str]]:
    """
    Pull palette and typography out of a brand-lock.

    Returns (values, warnings). Warnings name every role that fell back to a generic
    default, because a preview that quietly renders in someone else's blue is worse
    than one that tells you the palette did not parse.
    """
    if not path.exists():
        return (dict(FALLBACK_BRAND), [f"brand-lock not found at {path.name}"])

    text = path.read_text(encoding="utf-8")
    palette = parse_palette(text)
    warnings: list[str] = []

    def pick(role: str) -> str:
        # Exact role first, then any role containing it, e.g. "accent (warm)".
        if role in palette and not palette[role].startswith("#_"):
            return palette[role]
        for name, hex_val in palette.items():
            if role in name and not hex_val.startswith("#_"):
                return hex_val
        warnings.append(
            f"palette role '{role}' not found in the brand-lock, using a generic default"
        )
        return FALLBACK_HEX[role]

    values = {
        "bg": pick("background"),
        "ink": pick("ink"),
        "accent": pick("accent"),
        "muted": pick("muted"),
        "rule": pick("rule"),
    }

    fonts = parse_typography(text)
    values["display_font"] = fonts.get("display_font") or FALLBACK_BRAND["display_font"]
    values["body_font"] = fonts.get("body_font") or FALLBACK_BRAND["body_font"]
    for key in ("display_font", "body_font"):
        if not fonts.get(key):
            warnings.append(
                f"brand-lock declares no {key.replace('_', ' ')}, using "
                f"{FALLBACK_BRAND[key]}"
            )

    return (values, warnings)


def aspect_class(aspect: str) -> str:
    return "aspect-" + str(aspect).replace(":", "-")


def encode_image_b64(path: Path) -> str:
    ext = path.suffix.lstrip(".").lower()
    mime = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "webp": "image/webp",
    }.get(ext, "image/png")
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{data}"


def frame_for_shot(out_dir: Path, shot: dict) -> tuple[Path | None, str | None]:
    """
    Resolve a shot's frame, preferring what the data says over what the tree implies.

    Order: an accepted entry in shot.assets.generated, then the newest entry there,
    then the frames/round-N path convention, then the legacy generated/ directory.
    Returns (path, note) where note explains a non-obvious pick.
    """
    generated = (shot.get("assets") or {}).get("generated") or []
    accepted = [g for g in generated if g.get("accepted") is True and g.get("path")]
    pool = accepted or [g for g in generated if g.get("path")]
    if pool:
        chosen = max(pool, key=lambda g: g.get("round") or 0)
        path = out_dir / chosen["path"]
        if path.exists():
            note = None
            if chosen.get("sha256"):
                actual = sha256_file(path)
                if actual != chosen["sha256"]:
                    note = "frame has changed since it was recorded in shots.json"
            elif not accepted:
                note = "frame is not marked accepted"
            return (path, note)
        return (None, f"assets names {chosen['path']}, which is missing on disk")

    found = find_frame(out_dir, shot["id"])
    if found is None:
        return (None, None)
    return (found, None)


def latest_verdicts(out_dir: Path) -> dict[str, dict]:
    """Newest verdict per shot, read from the critique tree. Empty when there is none."""
    verdicts: dict[str, dict] = {}
    for round_no, directory in round_dirs(out_dir, "critiques"):
        for path in sorted(directory.glob("*.json")):
            data, err = load_json(path)
            if err or not isinstance(data, dict):
                continue
            shot_id = data.get("shot_id")
            if not shot_id:
                continue
            current = verdicts.get(shot_id)
            if current is None or round_no >= current["round"]:
                verdicts[shot_id] = {
                    "round": round_no,
                    "verdict": data.get("verdict"),
                }
    legacy, err = load_json(out_dir / "critique.json")
    if not err and isinstance(legacy, dict) and legacy.get("shot_id"):
        verdicts.setdefault(
            legacy["shot_id"],
            {"round": legacy.get("round") or 1, "verdict": legacy.get("verdict")},
        )
    return verdicts


def position_class(position) -> str:
    """Named positions map to a CSS class; explicit coordinates fall back to center."""
    if isinstance(position, str):
        return position
    return "center"


def position_label(position) -> str:
    if isinstance(position, dict):
        return f"x{position.get('x')}% y{position.get('y')}%"
    return str(position)


def build_context(out_dir: Path, args) -> tuple[dict, list[str]]:
    warnings: list[str] = []

    shots_data, err = load_json(out_dir / "shots.json")
    if err:
        raise SystemExit(f"ERROR: {err}")

    overlays_data, ov_err = load_json(out_dir / "text-overlays.json")
    if ov_err:
        overlays_data = {"overlays": []}
    overlays_by_id = {
        o["id"]: o for o in (overlays_data or {}).get("overlays", []) if o.get("id")
    }

    project = shots_data["project"]
    series = shots_data["series_lock"]
    shots = shots_data["shots"]
    aspect = project["aspect"]

    brand_ref = shots_data.get("brand_lock_ref") or "brand-lock.snapshot.md"
    brand_path = out_dir / brand_ref
    brand, brand_warnings = parse_brand_lock(brand_path)
    warnings.extend(brand_warnings)

    run_doc, run_err = load_json(out_dir / "run.json")
    if run_err or not isinstance(run_doc, dict):
        run_doc = {}
        warnings.append(
            "no run.json in this output tree, so the page cannot state when the run "
            "happened or which inputs it used"
        )

    verdicts = latest_verdicts(out_dir)
    provenance_notes: list[str] = []

    shot_contexts = []
    for shot in shots:
        frame_path, frame_note = frame_for_shot(out_dir, shot)
        if frame_note:
            provenance_notes.append(f"{shot['id']}: {frame_note}")
            warnings.append(f"{shot['id']}: {frame_note}")

        image_path = None
        if frame_path is not None:
            if args.inline_images:
                image_path = encode_image_b64(frame_path)
            else:
                try:
                    image_path = str(frame_path.relative_to(out_dir))
                except ValueError:
                    image_path = frame_path.name

        overlays = []
        for oid in as_overlay_ids(shot.get("on_screen_text")):
            overlay = overlays_by_id.get(oid)
            if overlay is None:
                warnings.append(
                    f"{shot['id']} references overlay {oid}, which is not in "
                    f"text-overlays.json"
                )
                continue
            overlays.append(
                {
                    "id": overlay["id"],
                    "content": overlay.get("content"),
                    "font": overlay.get("font"),
                    "weight": overlay.get("weight"),
                    "color": overlay.get("color"),
                    "size": overlay.get("size"),
                    "position_class": position_class(overlay.get("position")),
                    "position_label": position_label(overlay.get("position")),
                    "enter_at": (overlay.get("enter") or {}).get("at"),
                    "enter_animation": (overlay.get("enter") or {}).get("animation"),
                    "exit_at": (overlay.get("exit") or {}).get("at"),
                    "exit_animation": (overlay.get("exit") or {}).get("animation"),
                }
            )

        verdict = verdicts.get(shot["id"])
        shot_contexts.append(
            {
                "id": shot["id"],
                "id_short": shot["id"].replace("shot_", ""),
                "beat": shot.get("beat"),
                "start": shot.get("start"),
                "end": shot.get("end"),
                "framing": shot.get("framing"),
                "angle": shot.get("angle"),
                "motion": shot.get("motion"),
                "depth_of_field": shot.get("depth_of_field"),
                "subject": shot.get("subject"),
                "vo": shot.get("vo"),
                "rationale": shot.get("rationale"),
                "aspect_class": aspect_class(aspect),
                "has_image": image_path is not None,
                "has_no_image": image_path is None,
                "image_path": image_path,
                "overlays": overlays,
                "has_overlays": bool(overlays),
                "has_verdict": verdict is not None,
                "verdict": (verdict or {}).get("verdict"),
                "verdict_round": (verdict or {}).get("round"),
                "verdict_class": str((verdict or {}).get("verdict", "")).lower(),
            }
        )

    css = (
        read_template("styles.css.tpl")
        .replace("{{BG_COLOR}}", brand["bg"])
        .replace("{{INK_COLOR}}", brand["ink"])
        .replace("{{ACCENT_COLOR}}", brand["accent"])
        .replace("{{MUTED_COLOR}}", brand["muted"])
        .replace("{{RULE_COLOR}}", brand["rule"])
        .replace("{{DISPLAY_FONT}}", brand["display_font"])
        .replace("{{BODY_FONT}}", brand["body_font"])
        .replace("{{INLINE_PRINT_CSS}}", read_template("print.css.tpl"))
    )

    brand_sha = sha256_file(brand_path) if brand_path.exists() else None
    recorded_sha = (run_doc.get("inputs") or {}).get("brand_lock_sha256")
    if brand_sha and recorded_sha and brand_sha != recorded_sha:
        provenance_notes.append(
            "the brand-lock on disk no longer matches the one recorded in run.json"
        )
        warnings.append(
            "brand-lock has changed since the run; this preview does not show the "
            "brand state the frames were produced against"
        )

    context = {
        "PROJECT_TITLE": project["title"],
        "DURATION": project["duration_s"],
        "ASPECT": aspect,
        "FRAMEWORK": project.get("framework") or "not specified",
        "SHOTS_VERSION": shots_data.get("version", "unknown"),
        "BRIEF": None,
        "SERIES_CHARACTER": series["character"],
        "SERIES_ENVIRONMENT": series["environment"],
        "SERIES_LIGHTING": series["lighting"],
        "SERIES_COLOR_GRADE": series["color_grade"],
        "BRAND_LOCK_REF": brand_ref,
        "BRAND_LOCK_SHA_SHORT": brand_sha[:12] if brand_sha else None,
        "RUN_ID": run_doc.get("run_id") or "not recorded",
        "RUN_CREATED_AT": run_doc.get("created_at") or "not recorded",
        "RENDERED_AT": args.rendered_at or iso_instant(),
        "PROVENANCE_NOTE": " ".join(provenance_notes) or None,
        "INLINE_CSS": css,
        "shots": shot_contexts,
    }
    return (context, warnings)


def selftest() -> int:
    """Render the bundled worked run twice and prove the output is byte-identical."""
    worked = REPO_ROOT / "skills" / "visual-asset-critic" / "examples" / "worked-run"
    ok = True

    class Args:
        inline_images = False
        rendered_at = "2026-07-30T00:00:00Z"

    first, _ = build_context(worked, Args())
    second, _ = build_context(worked, Args())
    html_a = render(read_template("preview.html.tpl"), first)
    html_b = render(read_template("preview.html.tpl"), second)

    if html_a == html_b:
        print("  ok    selftest: two renders with a pinned timestamp are identical")
    else:
        print("  FAIL  selftest: two renders differed")
        ok = False

    # shot_06 of the shotkit-explainer example carries two overlays. A renderer that
    # resolves only the first drops the second silently, which is what used to happen.
    explainer = (
        REPO_ROOT
        / "skills"
        / "storyboard-architect"
        / "examples"
        / "shotkit-explainer"
    )
    multi_ctx, _ = build_context(explainer, Args())
    shot_06 = next(s for s in multi_ctx["shots"] if s["id"] == "shot_06")
    multi_html = render(read_template("preview.html.tpl"), multi_ctx)

    checks = [
        ("escapes angle brackets", "<script>alert(1)</script>" not in render(
            "{{subject}}", {"subject": "<script>alert(1)</script>"}
        )),
        ("escapes quotes inside a style attribute", "&quot;" in render(
            '<span style="font-family: {{font}};">x</span>', {"font": '"><script>'}
        )),
        ("resolves every overlay on a multi-overlay shot", len(shot_06["overlays"]) == 2),
        (
            "renders every overlay on a multi-overlay shot",
            all(
                escape(overlay["content"]) in multi_html
                for overlay in shot_06["overlays"]
            ),
        ),
        ("states the run date, not the render date, in the header", "2026-07-30T14:23:00Z" in html_a),
        ("labels the render separately", "rendered 2026-07-30T00:00:00Z" in html_a),
        ("shows a verdict badge", "sb-verdict-accept" in html_a),
        ("uses the brand-lock ref from shots.json", 'href="brand-lock.snapshot.md"' in html_a),
        ("carries no unrendered template tags", "{{" not in html_a),
    ]
    for label, passed in checks:
        if passed:
            print(f"  ok    selftest: {label}")
        else:
            print(f"  FAIL  selftest: {label}")
            ok = False

    print()
    print("Selftest passed." if ok else "Selftest FAILED.")
    return 0 if ok else 1


def main() -> int:
    p = argparse.ArgumentParser(
        description="Render a shotkit output folder into a single preview.html."
    )
    p.add_argument(
        "output_dir",
        nargs="?",
        type=Path,
        help="Directory containing shots.json, text-overlays.json, run.json",
    )
    p.add_argument("--out", default="preview.html", help="Output filename, relative to output_dir")
    p.add_argument(
        "--inline-images",
        action="store_true",
        help="Embed frames as base64 so the file is portable on its own",
    )
    p.add_argument(
        "--rendered-at",
        help="Pin the render timestamp (UTC ISO-8601). Makes output reproducible.",
    )
    p.add_argument("--selftest", action="store_true", help="Prove the renderer's guarantees")
    args = p.parse_args()

    if args.selftest:
        return selftest()
    if args.output_dir is None:
        p.error("output_dir is required unless --selftest is given")

    out_dir: Path = args.output_dir
    if not out_dir.is_dir():
        print(f"ERROR: output directory not found: {out_dir}")
        return 1
    if not (out_dir / "shots.json").exists():
        print(f"ERROR: shots.json not found in {out_dir}")
        return 1

    context, warnings = build_context(out_dir, args)
    html_out = render(read_template("preview.html.tpl"), context)

    out_path = out_dir / args.out
    out_path.write_text(html_out, encoding="utf-8")
    print(f"  wrote {out_path}")
    for warn in warnings:
        print(f"  warn  {warn}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
