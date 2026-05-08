#!/usr/bin/env python3
"""
Standalone helper: render shots.json + text-overlays.json + brand-lock.snapshot.md
into a single preview.html.

This is the same logic the storyboard-html-preview skill applies, available
as a CLI for users who want to render previews without invoking Claude.

Usage:
    python tools/shots-to-html.py path/to/output-folder
    python tools/shots-to-html.py path/to/output-folder --out preview.html
    python tools/shots-to-html.py path/to/output-folder --inline-images
"""

from __future__ import annotations
import argparse
import base64
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = REPO_ROOT / "skills" / "storyboard-html-preview" / "templates"


def read_template(name: str) -> str:
    return (TEMPLATE_DIR / name).read_text(encoding="utf-8")


def parse_brand_lock(path: Path) -> dict:
    """Extract palette, typography, and a few useful fields from brand-lock.snapshot.md."""
    if not path.exists():
        return {
            "bg": "#FFFFFF",
            "ink": "#0F172A",
            "accent": "#3B82F6",
            "muted": "#64748B",
            "rule": "#E2E8F0",
            "display_font": "Inter",
            "body_font": "Inter",
        }
    text = path.read_text(encoding="utf-8")
    palette = {}
    for line in text.splitlines():
        m = re.match(r"^\|\s*([A-Za-z][A-Za-z\s]*?)\s*\|\s*`?(#[0-9A-Fa-f]{6})`?\s*\|", line)
        if m:
            role = m.group(1).strip().lower()
            hex_val = m.group(2).strip()
            palette[role] = hex_val

    def pick(keys: list[str], default: str) -> str:
        for k in keys:
            for role, hex_val in palette.items():
                if k in role:
                    return hex_val
        return default

    return {
        "bg": pick(["background"], "#FFFFFF"),
        "ink": pick(["ink"], "#0F172A"),
        "accent": pick(["accent (warm)", "accent"], "#3B82F6"),
        "muted": pick(["muted"], "#64748B"),
        "rule": pick(["rule"], "#E2E8F0"),
        "display_font": "Inter",
        "body_font": "Inter",
    }


def aspect_class(aspect: str) -> str:
    return "aspect-" + aspect.replace(":", "-")


def find_image(generated_dir: Path, shot_id: str) -> Path | None:
    if not generated_dir.exists():
        return None
    for ext in ("png", "jpg", "jpeg", "webp"):
        p = generated_dir / f"{shot_id}.{ext}"
        if p.exists():
            return p
    return None


def encode_image_b64(path: Path) -> str:
    ext = path.suffix.lstrip(".").lower()
    mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"}.get(ext, "image/png")
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{data}"


def render_shot_block(shot: dict, overlay: dict | None, aspect: str, image_src: str | None) -> str:
    aspect_cls = aspect_class(aspect)
    id_short = shot["id"].replace("shot_", "")

    if image_src:
        frame_inner = f'<img src="{image_src}" alt="{shot["id"]}: {shot["beat"]}" loading="lazy">'
    else:
        frame_inner = (
            f'<div class="sb-placeholder">'
            f'<div class="sb-placeholder-id">{id_short}</div>'
            f'<div class="sb-placeholder-meta">{shot["framing"]} · {shot["angle"]} · {shot["motion"]}</div>'
            f'</div>'
        )

    overlay_block = ""
    if overlay:
        pos = overlay.get("position", "center")
        if isinstance(pos, dict):
            pos = "center"
        overlay_block = (
            f'<div class="sb-overlay sb-overlay-{pos}">'
            f'<span class="sb-overlay-text" '
            f'style=\'font-family: {overlay["font"]}; font-weight: {overlay["weight"]}; color: {overlay["color"]};\'>'
            f'{overlay["content"]}</span>'
            f'</div>'
        )

    text_block = ""
    if overlay:
        enter = overlay["enter"]
        exit_ = overlay["exit"]
        text_block = (
            f'<div class="sb-shot-text"><h3>On-screen text</h3>'
            f'<p class="sb-text-content">"{overlay["content"]}"</p>'
            f'<p class="sb-text-meta">{overlay["size"]} · {overlay.get("position", "center")} · '
            f'enter {enter["at"]}s ({enter["animation"]}) · exit {exit_["at"]}s</p></div>'
        )

    vo_block = ""
    if shot.get("vo"):
        vo_block = f'<div class="sb-shot-vo"><h3>VO</h3><p>"{shot["vo"]}"</p></div>'

    dof_block = ""
    if shot.get("depth_of_field"):
        dof_block = f'<div><dt>DOF</dt><dd>{shot["depth_of_field"]}</dd></div>'

    return f"""
  <article class="sb-shot" id="{shot['id']}">
    <div class="sb-shot-frame {aspect_cls}">
      {frame_inner}
      {overlay_block}
    </div>
    <div class="sb-shot-body">
      <header class="sb-shot-header">
        <span class="sb-shot-id">{id_short}</span>
        <span class="sb-shot-time">{shot['start']}–{shot['end']}s</span>
        <span class="sb-shot-beat">{shot['beat']}</span>
      </header>
      <dl class="sb-shot-meta">
        <div><dt>Framing</dt><dd>{shot['framing']}</dd></div>
        <div><dt>Angle</dt><dd>{shot['angle']}</dd></div>
        <div><dt>Motion</dt><dd>{shot['motion']}</dd></div>
        {dof_block}
      </dl>
      <div class="sb-shot-subject"><h3>Subject</h3><p>{shot['subject']}</p></div>
      {vo_block}
      {text_block}
      <div class="sb-shot-rationale"><h3>Rationale</h3><p>{shot['rationale']}</p></div>
    </div>
  </article>
"""


def render_nav(shots: list[dict]) -> str:
    items = "\n".join(
        f'<li><a href="#{s["id"]}">{s["id"].replace("shot_", "")}</a></li>'
        for s in shots
    )
    return f'<ul>{items}</ul>'


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("output_dir", type=Path, help="Directory containing shots.json, text-overlays.json, etc.")
    p.add_argument("--out", type=str, default="preview.html", help="Output filename (relative to output_dir)")
    p.add_argument("--inline-images", action="store_true", help="Embed generated images as base64 (single-file portable)")
    args = p.parse_args()

    out_dir: Path = args.output_dir
    if not out_dir.exists():
        print(f"ERROR: output directory not found: {out_dir}")
        return 1

    shots_path = out_dir / "shots.json"
    overlays_path = out_dir / "text-overlays.json"
    brand_lock_path = out_dir / "brand-lock.snapshot.md"
    generated_dir = out_dir / "generated"

    if not shots_path.exists():
        print(f"ERROR: shots.json not found in {out_dir}")
        return 1

    shots_data = json.loads(shots_path.read_text(encoding="utf-8"))
    overlays_data = (
        json.loads(overlays_path.read_text(encoding="utf-8"))
        if overlays_path.exists() else {"overlays": []}
    )
    overlays_by_id = {o["id"]: o for o in overlays_data.get("overlays", [])}

    brand = parse_brand_lock(brand_lock_path)

    project = shots_data["project"]
    series = shots_data["series_lock"]
    shots = shots_data["shots"]
    aspect = project["aspect"]

    # Build CSS
    css_template = read_template("styles.css.tpl")
    print_css = read_template("print.css.tpl")
    css = (
        css_template
        .replace("{{BG_COLOR}}", brand["bg"])
        .replace("{{INK_COLOR}}", brand["ink"])
        .replace("{{ACCENT_COLOR}}", brand["accent"])
        .replace("{{MUTED_COLOR}}", brand["muted"])
        .replace("{{RULE_COLOR}}", brand["rule"])
        .replace("{{DISPLAY_FONT}}", brand["display_font"])
        .replace("{{BODY_FONT}}", brand["body_font"])
        .replace("{{INLINE_PRINT_CSS}}", print_css)
    )

    # Build shot blocks
    shot_blocks = []
    for shot in shots:
        overlay = overlays_by_id.get(shot.get("on_screen_text")) if shot.get("on_screen_text") else None

        image_src = None
        img_path = find_image(generated_dir, shot["id"])
        if img_path:
            if args.inline_images:
                image_src = encode_image_b64(img_path)
            else:
                image_src = f"generated/{img_path.name}"

        shot_blocks.append(render_shot_block(shot, overlay, aspect, image_src))

    # Assemble final HTML, using a simpler direct render rather than the templated one,
    # to avoid full handlebars dependency. Output is equivalent.
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    nav = render_nav(shots)
    shots_html = "\n".join(shot_blocks)
    framework = project.get("framework", " ")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="generator" content="storyboard-html-preview / WhyStrohm">
<title>{project['title']} · Storyboard</title>
<style>
{css}
</style>
</head>
<body>

<header class="sb-header">
  <div class="sb-header-inner">
    <div class="sb-eyebrow">Storyboard · v1.0</div>
    <h1 class="sb-title">{project['title']}</h1>
    <dl class="sb-meta">
      <div><dt>Duration</dt><dd>{project['duration_s']}s</dd></div>
      <div><dt>Aspect</dt><dd>{aspect}</dd></div>
      <div><dt>Framework</dt><dd>{framework}</dd></div>
      <div><dt>Generated</dt><dd>{timestamp}</dd></div>
    </dl>
  </div>
</header>

<nav class="sb-nav" aria-label="Shot navigation">
  {nav}
</nav>

<section class="sb-section sb-series-lock">
  <h2>Series lock</h2>
  <dl class="sb-series-grid">
    <div><dt>Character</dt><dd>{series['character']}</dd></div>
    <div><dt>Environment</dt><dd>{series['environment']}</dd></div>
    <div><dt>Lighting</dt><dd>{series['lighting']}</dd></div>
    <div><dt>Color grade</dt><dd>{series['color_grade']}</dd></div>
  </dl>
</section>

<section class="sb-section sb-shots">
  <h2>Shots</h2>
  {shots_html}
</section>

<footer class="sb-footer">
  <div class="sb-footer-inner">
    <div>Generated against <a href="brand-lock.snapshot.md"><code>brand-lock.snapshot.md</code></a> on {timestamp}.</div>
    <div>Built with <a href="https://github.com/whystrohm/shotkit">shotkit</a> · WhyStrohm</div>
  </div>
</footer>

<script>
(function() {{
  const shots = Array.from(document.querySelectorAll('.sb-shot'));
  if (!shots.length) return;
  function shotInView() {{
    const mid = window.innerHeight / 2;
    let best = 0, bestDist = Infinity;
    shots.forEach((shot, i) => {{
      const rect = shot.getBoundingClientRect();
      const dist = Math.abs(rect.top + rect.height / 2 - mid);
      if (dist < bestDist) {{ bestDist = dist; best = i; }}
    }});
    return best;
  }}
  document.addEventListener('keydown', function(e) {{
    if (e.target.matches('input, textarea')) return;
    const i = shotInView();
    if (e.key === 'ArrowDown' || e.key === 'j') {{
      e.preventDefault();
      shots[Math.min(shots.length - 1, i + 1)].scrollIntoView({{ behavior: 'smooth', block: 'start' }});
    }}
    if (e.key === 'ArrowUp' || e.key === 'k') {{
      e.preventDefault();
      shots[Math.max(0, i - 1)].scrollIntoView({{ behavior: 'smooth', block: 'start' }});
    }}
  }});
}})();
</script>

</body>
</html>
"""

    out_path = out_dir / args.out
    out_path.write_text(html, encoding="utf-8")
    print(f"  wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
