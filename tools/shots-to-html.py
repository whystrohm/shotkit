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

Fonts. A brand-lock font value such as `Archivo Bold 700 wdth 80` is split into a
family, a weight and a width. The family goes into font-family quoted, ahead of a
system fallback stack, and the weight and width are set as separate properties. The
mono font comes from the brand-lock's Mono line when it has one.

By default the page links the brand's fonts from Google Fonts, so a reader who is
online sees the real typefaces. Offline, or for a family Google does not host, the
page falls back to the system stack and nothing else changes. --no-web-fonts drops
the links, for a page that makes no network request at all.

Usage:
    python tools/shots-to-html.py path/to/output-folder
    python tools/shots-to-html.py path/to/output-folder --out preview.html
    python tools/shots-to-html.py path/to/output-folder --inline-images
    python tools/shots-to-html.py path/to/output-folder --rendered-at 2026-07-30T00:00:00Z
    python tools/shots-to-html.py path/to/output-folder --no-web-fonts
    python tools/shots-to-html.py --selftest
"""

from __future__ import annotations

import argparse
import base64
import re
import sys
from pathlib import Path

from _shotkit import (
    IMAGE_EXTS,
    OVERLAY_WEIGHTS,
    PALETTE_ROLES,
    REPO_ROOT,
    as_overlay_ids,
    find_frame,
    iso_instant,
    load_json,
    parse_font_spec,
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
    "display_font": "Inter Black 900",
    "body_font": "Inter Regular 400",
    "mono_font": None,
}

SANS_FALLBACK = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
MONO_FALLBACK = 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace'

# A family name lands inside inlined CSS, which is written raw. Anything outside this
# set is dropped, so a brand-lock can never close the style block or add a rule.
_UNSAFE_FAMILY_CHARS = re.compile(r"[^A-Za-z0-9 _-]")

GOOGLE_FONTS_CSS = "https://fonts.googleapis.com/css2"

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
    values["mono_font"] = fonts.get("mono_font")
    for key in ("display_font", "body_font"):
        if not fonts.get(key):
            warnings.append(
                f"brand-lock declares no {key.replace('_', ' ')}, using "
                f"{FALLBACK_BRAND[key]}"
            )

    return (values, warnings)


def css_family(family: str | None, fallback: str) -> str:
    """A quoted family ahead of a fallback stack, e.g. '"Archivo", -apple-system, ...'."""
    clean = _UNSAFE_FAMILY_CHARS.sub("", family or "").strip()
    return f'"{clean}", {fallback}' if clean else fallback


def css_stretch(width) -> str:
    """A font-stretch value from a brand-lock width. 'normal' when none is given."""
    return f"{width}%" if width is not None else "normal"


def font_css(brand: dict) -> dict:
    """The CSS values the stylesheet needs for the display, body and mono fonts."""
    display = parse_font_spec(brand["display_font"])
    body = parse_font_spec(brand["body_font"])
    mono = parse_font_spec(brand.get("mono_font"))
    return {
        "DISPLAY_FONT_STACK": css_family(display["family"], SANS_FALLBACK),
        "DISPLAY_WEIGHT": str(display["weight"] or 800),
        "DISPLAY_STRETCH": css_stretch(display["width"]),
        "BODY_FONT_STACK": css_family(body["family"], SANS_FALLBACK),
        "BODY_WEIGHT": str(body["weight"] or 400),
        "BODY_STRETCH": css_stretch(body["width"]),
        "MONO_FONT_STACK": css_family(mono["family"], MONO_FALLBACK),
    }


def google_fonts_links(faces: dict[str, set[tuple]]) -> list[dict]:
    """
    One Google Fonts stylesheet link per family.

    `faces` maps a family to the (width, weight) pairs the page uses. One link per
    family, because the API rejects a whole request when any one family in it is
    unknown, and one brand font Google does not host should not cost the others.
    """
    links: list[dict] = []
    for family in sorted(faces):
        clean = _UNSAFE_FAMILY_CHARS.sub("", family).strip()
        if not clean:
            continue
        pairs = faces[family]
        name = clean.replace(" ", "+")
        if any(width is not None for width, _ in pairs):
            tuples = sorted({(width if width is not None else 100, weight) for width, weight in pairs})
            axes = "wdth,wght@" + ";".join(f"{w},{wt}" for w, wt in tuples)
        else:
            axes = "wght@" + ";".join(str(wt) for wt in sorted({wt for _, wt in pairs}))
        links.append({"href": f"{GOOGLE_FONTS_CSS}?family={name}:{axes}&display=swap"})
    return links


def collect_faces(brand: dict, overlay_fonts: list[tuple[str | None, int]]) -> dict[str, set[tuple]]:
    """Every family the page uses, with the weights and widths it asks for."""
    faces: dict[str, set[tuple]] = {}

    def add(value: str | None, weight: int | None = None) -> None:
        spec = parse_font_spec(value)
        if not spec["family"]:
            return
        entry = faces.setdefault(spec["family"], set())
        entry.add((spec["width"], weight or spec["weight"] or 400))
        entry.add((None if spec["width"] is None else 100, 400))

    add(brand["display_font"])
    add(brand["body_font"])
    add(brand.get("mono_font"))
    for value, weight in overlay_fonts:
        add(value, weight)
    return faces


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
    overlay_fonts: list[tuple[str | None, int]] = []
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
            font_spec = parse_font_spec(overlay.get("font"))
            weight_css = OVERLAY_WEIGHTS.get(
                str(overlay.get("weight") or "").lower(), font_spec["weight"] or 400
            )
            overlay_fonts.append((overlay.get("font"), weight_css))
            overlays.append(
                {
                    "id": overlay["id"],
                    "content": overlay.get("content"),
                    "font": overlay.get("font"),
                    "font_css": css_family(font_spec["family"], SANS_FALLBACK),
                    "weight_css": weight_css,
                    # Always set, so an overlay never inherits the body font's width.
                    "stretch_css": css_stretch(font_spec["width"]),
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
    )
    for key, value in font_css(brand).items():
        css = css.replace("{{" + key + "}}", value)
    css = css.replace("{{INLINE_PRINT_CSS}}", read_template("print.css.tpl"))

    font_links = []
    if not getattr(args, "no_web_fonts", False):
        font_links = google_fonts_links(collect_faces(brand, overlay_fonts))

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
        "FONT_LINKS": font_links,
        "HAS_FONT_LINKS": bool(font_links),
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
        no_web_fonts = False

    first, _ = build_context(worked, Args())
    second, _ = build_context(worked, Args())
    html_a = render(read_template("preview.html.tpl"), first)
    html_b = render(read_template("preview.html.tpl"), second)

    if html_a == html_b:
        print("  ok    selftest: two renders with a pinned timestamp are identical")
    else:
        print("  FAIL  selftest: two renders differed")
        ok = False

    import json
    import shutil
    import tempfile

    # A shot with two overlays. A renderer that resolves only the first drops the
    # second silently, which is what used to happen.
    with tempfile.TemporaryDirectory() as tmp:
        multi = Path(tmp) / "multi"
        shutil.copytree(worked, multi)
        shots_doc = json.loads((multi / "shots.json").read_text())
        shots_doc["shots"][1]["on_screen_text"] = ["text_02", "text_03"]
        (multi / "shots.json").write_text(json.dumps(shots_doc))
        ov_doc = json.loads((multi / "text-overlays.json").read_text())
        extra = dict(ov_doc["overlays"][1])
        extra.update({"id": "text_03", "content": "A second line on the same shot.",
                      "weight": "semibold", "position": "upper-third"})
        ov_doc["overlays"].append(extra)
        (multi / "text-overlays.json").write_text(json.dumps(ov_doc))
        multi_ctx, _ = build_context(multi, Args())
        shot_02 = next(s for s in multi_ctx["shots"] if s["id"] == "shot_02")
        multi_html = render(read_template("preview.html.tpl"), multi_ctx)

        # Fonts. A brand-lock value with a weight in it, a width, and a mono line.
        fonts = Path(tmp) / "fonts"
        shutil.copytree(worked, fonts)
        lock = fonts / "brand-lock.snapshot.md"
        text = lock.read_text()
        text = re.sub(r"\*\*Display font:\*\* `[^`]+`", "**Display font:** `Archivo SemiBold 600 wdth 80`", text)
        text = re.sub(r"\*\*Mono font:\*\* `[^`]+`", "**Mono font:** `IBM Plex Mono Regular`", text)
        lock.write_text(text)
        font_ctx, _ = build_context(fonts, Args())
        font_html = render(read_template("preview.html.tpl"), font_ctx)

        class Offline(Args):
            no_web_fonts = True

        offline_html = render(read_template("preview.html.tpl"), build_context(fonts, Offline())[0])

        nomono = Path(tmp) / "nomono"
        shutil.copytree(worked, nomono)
        lock = nomono / "brand-lock.snapshot.md"
        lock.write_text(re.sub(r"\*\*Mono font:\*\*[^\n]*\n", "", lock.read_text()))
        nomono_css = build_context(nomono, Args())[0]["INLINE_CSS"]

        hostile = Path(tmp) / "hostile"
        shutil.copytree(worked, hostile)
        lock = hostile / "brand-lock.snapshot.md"
        lock.write_text(re.sub(
            r"\*\*Display font:\*\* `[^`]+`",
            "**Display font:** `Evil\"; } </style><script>x()</script> 700`",
            lock.read_text(),
        ))
        hostile_css = build_context(hostile, Args())[0]["INLINE_CSS"]

    overlay_weights = [o["weight_css"] for o in shot_02["overlays"]]

    checks = [
        ("escapes angle brackets", "<script>alert(1)</script>" not in render(
            "{{subject}}", {"subject": "<script>alert(1)</script>"}
        )),
        ("escapes quotes inside a style attribute", "&quot;" in render(
            '<span style="font-family: {{font}};">x</span>', {"font": '"><script>'}
        )),
        ("resolves every overlay on a multi-overlay shot", len(shot_02["overlays"]) == 2),
        (
            "renders every overlay on a multi-overlay shot",
            all(escape(o["content"]) in multi_html for o in shot_02["overlays"]),
        ),
        ("maps the semibold overlay weight to 600", overlay_weights == [900, 600]),
        (
            "quotes a brand-lock family that carries a weight token",
            '--sb-font-display: "Archivo", ' in font_ctx["INLINE_CSS"]
            and "Archivo SemiBold" not in font_ctx["INLINE_CSS"],
        ),
        (
            "sets the display weight and width as separate properties",
            "--sb-font-display-weight: 600;" in font_ctx["INLINE_CSS"]
            and "--sb-font-display-stretch: 80%;" in font_ctx["INLINE_CSS"],
        ),
        (
            "takes the mono font from the brand-lock",
            '--sb-font-mono: "IBM Plex Mono", ' in font_ctx["INLINE_CSS"],
        ),
        (
            "falls back to the system mono stack when the lock has no mono font",
            "--sb-font-mono: ui-monospace," in nomono_css,
        ),
        (
            "quotes the overlay family in its style attribute",
            "font-family: &quot;Inter&quot;, " in html_a,
        ),
        (
            "links the brand fonts, with the width axis when one is declared",
            "family=Archivo:wdth,wght@80,600;100,400" in font_html
            and "family=IBM+Plex+Mono:wght@400" in font_html,
        ),
        ("--no-web-fonts makes no font request", "fonts.googleapis.com" not in offline_html),
        (
            "a hostile family name cannot close the style block",
            "</style>" not in hostile_css and "<script>" not in hostile_css,
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
    p.add_argument(
        "--no-web-fonts",
        action="store_true",
        help="Do not link the brand fonts from Google Fonts; use the system stack only",
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
