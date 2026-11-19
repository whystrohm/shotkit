#!/usr/bin/env python3
"""Draw frames in code from the brand lock. No model is involved.

  design.py output/            draw every card in output/design/cards.json
  design.py output/ --check    draw them again and say if any picture changed
  design.py output/ --list     what each card is and where its frame is
  design.py --kinds            the kinds of card and what each one takes
  design.py --selftest

An image generator is the wrong tool for a screen of interface, a number, a quote or a
logo card. It cannot spell and it does not know your product. A designed frame is drawn
by a page in a browser with no window: the brand's colours, the brand's body type, and
the words you gave it. On one computer, the same card, brand lock and Shotkit version
draw the same picture every time. Another operating system can set type a pixel
differently, so --check belongs on the computer that drew the frames.

A shot asks for one in shots.json:

    "source": {"type": "design", "card": "list"}

and the card itself is in output/design/cards.json, by shot id:

    {"version": "1.0", "cards": {"shot_02": {"kind": "list", "title": "Deploys", "rows": [...]}}}

The panel is placed where the shot's on-screen text is not. Frames go to
frames/round-N/, like any other frame, and design/receipt.json records the hash of the
cards, the brand lock, the template and each picture. The brand's typeface is fetched
once and kept in design/fonts.css, so later draws use the same bytes and need no
connection. Needs Chrome, Edge, Brave or Chromium.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _shotkit import (  # noqa: E402
    HEX_RE, REPO_ROOT, as_overlay_ids, critique_paths, load_json, parse_font_spec, parse_palette,
    parse_typography, round_dirs, sha256_file, sha256_text,
)
from export import SIZES, find_browser, plan_size, png_size  # noqa: E402

TEMPLATE = REPO_ROOT / "skills" / "storyboard-html-preview" / "templates" / "card.html.tpl"
CARDS = "design/cards.json"
RECEIPT = "design/receipt.json"

# kind: (what it is, required fields, optional fields)
KINDS = {
    "lines": ("A wall of monospaced lines, one of them flagged. For logs, code, raw data.",
              ("lines",), ()),
    "list": ("A titled panel of rows: a key, a line, a small line under it, a status.",
             ("title", "rows"), ("tag",)),
    "detail": ("One thing open: a very large value, a status, then a few rows.",
               ("big",), ("label", "chip", "status", "tone", "section", "rows", "foot")),
    "action": ("A problem, the button that fixes it, and the result.",
               ("alert", "button"), ("sub", "tone", "done", "done_right")),
    "notices": ("Up to three notices stacked, the newest in front.",
                ("items",), ()),
    "mark": ("The brand's mark and name, alone.",
             (), ("name",)),
    "stat": ("One number, very large, and the line that explains it.",
             ("value",), ("label", "text", "note")),
    "quote": ("One quotation and who said it.",
              ("text",), ("by",)),
}
TONES = ("good", "warn", "bad")
DEFAULTS = {"bg": "#0E0F12", "ink": "#F3F2EE", "acc": "#FF5A2B", "mut": "#8A9099", "rule": "#262A31"}


class Stop(Exception):
    """A problem to print as one line and exit on, not a traceback."""


def luminance(hex_val: str) -> float:
    n = int(hex_val.lstrip("#"), 16)
    out = 0.0
    for v, k in zip((n >> 16 & 255, n >> 8 & 255, n & 255), (0.2126, 0.7152, 0.0722)):
        v /= 255
        out += k * (v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4)
    return out


def brand_look(brand_text: str) -> dict:
    """The colours and body type a card is drawn in, from the brand lock."""
    palette = parse_palette(brand_text)
    colours = dict(DEFAULTS)
    for role, key in (("background", "bg"), ("ink", "ink"), ("accent", "acc"), ("muted", "mut"), ("rule", "rule")):
        value = palette.get(role)
        if isinstance(value, str) and HEX_RE.fullmatch(value):
            colours[key] = value.upper()
    colours["on_acc"] = "#0B0D10" if luminance(colours["acc"]) > 0.35 else "#FFFFFF"
    fonts = parse_typography(brand_text)
    body = parse_font_spec(fonts.get("body_font"))["family"] or "Inter"
    body = "".join(ch for ch in body if ch.isalnum() or ch in " _-").strip() or "Inter"
    return {"colours": colours, "body": body}


def read_cards(out_dir: Path) -> dict[str, dict]:
    doc, err = load_json(out_dir / CARDS)
    if err or not isinstance(doc, dict) or not isinstance(doc.get("cards"), dict):
        why = err or (CARDS + ' needs a "cards" object, by shot id')
        raise Stop(f"no cards to draw: {why}")
    return doc["cards"]


def check_cards(cards: dict[str, dict], shot_ids: list[str]) -> list[str]:
    """Everything wrong with the cards, one line each."""
    problems: list[str] = []
    for shot_id, card in cards.items():
        if shot_id not in shot_ids:
            problems.append(f"{shot_id} is not a shot in shots.json")
            continue
        if not isinstance(card, dict) or card.get("kind") not in KINDS:
            problems.append(f"{shot_id}: 'kind' must be one of {', '.join(KINDS)}")
            continue
        _, required, optional = KINDS[card["kind"]]
        for field in required:
            if card.get(field) in (None, "", []):
                problems.append(f"{shot_id}: a {card['kind']} card needs '{field}'")
        for field in card:
            if field != "kind" and field not in required and field not in optional:
                problems.append(f"{shot_id}: a {card['kind']} card has no '{field}'")
        if card.get("tone") not in (None, *TONES):
            problems.append(f"{shot_id}: 'tone' is good, warn or bad")
    return problems


def text_side(out_dir: Path, shot: dict) -> str | None:
    """Where the shot's main line of on-screen text sits, so the panel goes elsewhere."""
    doc, err = load_json(out_dir / "text-overlays.json")
    if err or not isinstance(doc, dict):
        return None
    by_id = {o.get("id"): o for o in doc.get("overlays") or [] if isinstance(o, dict)}
    for oid in as_overlay_ids(shot.get("on_screen_text")):
        overlay = by_id.get(oid) or {}
        if overlay.get("treatment") != "lockup" and isinstance(overlay.get("position"), str):
            return overlay["position"]
    return None


FONTS = "design/fonts.css"
_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"


def fetch_fonts(body: str) -> str | None:
    """
    The brand's body type and the mono face as one stylesheet with the font files inside
    it. Fetched once, so every later draw uses the same bytes and needs no connection.
    None when it cannot be fetched.
    """
    import base64
    import re
    import urllib.request

    url = ("https://fonts.googleapis.com/css2?family=" + body.replace(" ", "+")
           + ":wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=block")
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": _AGENT}), timeout=12) as res:
            css = res.read().decode("utf-8")
        out = []
        # Latin only. The other alphabets are large and a card can still fall back for them.
        for label, block in re.findall(r"/\*\s*([a-z-]+)\s*\*/\s*(@font-face\s*{[^}]*})", css):
            if label not in ("latin", "latin-ext"):
                continue
            src = re.search(r"url\((https://[^)]+\.woff2)\)", block)
            if not src:
                continue
            with urllib.request.urlopen(urllib.request.Request(src.group(1), headers={"User-Agent": _AGENT}), timeout=12) as res:
                data = base64.b64encode(res.read()).decode("ascii")
            out.append(block.replace(src.group(1), "data:font/woff2;base64," + data))
        return "\n".join(out) if out else None
    except Exception:
        return None


def fonts_css(out_dir: Path, body: str, web_fonts: bool = True) -> tuple[str, str]:
    """(stylesheet, "brand" or "system"). The stylesheet is kept in design/fonts.css."""
    if not web_fonts:
        return "", "system"
    cache = out_dir / FONTS
    head = f"/* {body} */\n"
    if cache.is_file() and cache.read_text(encoding="utf-8").startswith(head):
        return cache.read_text(encoding="utf-8"), "brand"
    css = fetch_fonts(body)
    if not css:
        return "", "system"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(head + css, encoding="utf-8")
    return head + css, "brand"


def page_html(card: dict, look: dict, text: str | None, font_css: str = "") -> str:
    data = {"card": card, "colours": look["colours"], "body": look["body"], "text": text}
    fonts = f"<style>{font_css}</style>" if font_css else ""
    # A "</" in a card's words must not close the data element.
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return TEMPLATE.read_text(encoding="utf-8").replace("/*__FONTS__*/", fonts).replace("/*__DATA__*/null", payload)


def shoot(browser: str, page: Path, dest: Path, size: tuple[int, int], scratch: Path) -> bool:
    profile = scratch / f"profile-{dest.stem}"
    base = [browser, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run", "--no-default-browser-check",
            "--force-device-scale-factor=1", f"--user-data-dir={profile}", f"--window-size={size[0]},{size[1]}",
            "--virtual-time-budget=10000", f"--screenshot={dest}", page.as_uri()]
    for extra in ([], ["--no-sandbox"]):
        dest.unlink(missing_ok=True)
        try:
            subprocess.run(base + extra, capture_output=True, timeout=45)
        except (OSError, subprocess.TimeoutExpired):
            continue
        if png_size(dest) == size:
            shutil.rmtree(profile, ignore_errors=True)
            return True
    shutil.rmtree(profile, ignore_errors=True)
    return False


def target_round(out_dir: Path, shot_id: str) -> int:
    """Round 1, or the round after the last one a critic reviewed, so a review is never overwritten."""
    reviewed = 0
    for path in critique_paths(out_dir):
        doc, err = load_json(path)
        if not err and isinstance(doc, dict) and doc.get("shot_id") == shot_id and isinstance(doc.get("round"), int):
            reviewed = max(reviewed, doc["round"])
    return reviewed + 1


def plan(out_dir: Path) -> tuple[dict, dict[str, dict], dict, tuple[int, int]]:
    shots_doc, err = load_json(out_dir / "shots.json")
    if err or not isinstance(shots_doc, dict):
        raise Stop(f"no plan to draw for: {err or 'shots.json is not an object'}")
    shots = {s["id"]: s for s in shots_doc.get("shots") or [] if isinstance(s, dict) and isinstance(s.get("id"), str)}
    cards = read_cards(out_dir)
    problems = check_cards(cards, list(shots))
    if problems:
        raise Stop("the cards need fixing:\n  " + "\n  ".join(problems))
    brand_path = out_dir / (shots_doc.get("brand_lock_ref") or "brand-lock.snapshot.md")
    look = brand_look(brand_path.read_text(encoding="utf-8") if brand_path.is_file() else "")
    look["brand_sha256"] = sha256_file(brand_path) if brand_path.is_file() else None
    size = SIZES[plan_size((shots_doc.get("project") or {}).get("aspect"))]
    return shots, cards, look, size


def draw(out_dir: Path, browser: str | None = "find", into: Path | None = None, web_fonts: bool = True) -> dict:
    """Draw every card. With `into`, the pictures go there and nothing in out_dir changes."""
    out_dir = out_dir.resolve()
    shots, cards, look, size = plan(out_dir)
    browser = find_browser() if browser == "find" else browser
    if not browser:
        raise Stop("drawing a frame needs Chrome, Edge, Brave or Chromium on this computer. None was found. "
                   "Set SHOTKIT_BROWSER to the browser's path if it is somewhere unusual.")
    font_css, font_kind = fonts_css(out_dir, look["body"], web_fonts)
    frames: dict[str, dict] = {}
    with tempfile.TemporaryDirectory() as tmp:
        scratch = Path(tmp)
        for shot_id, card in sorted(cards.items()):
            page = scratch / f"{shot_id}.html"
            page.write_text(page_html(card, look, text_side(out_dir, shots[shot_id]), font_css), encoding="utf-8")
            if into:
                dest = into / f"{shot_id}.png"
            else:
                dest = out_dir / "frames" / f"round-{target_round(out_dir, shot_id)}" / f"{shot_id}.png"
            dest.parent.mkdir(parents=True, exist_ok=True)
            if not shoot(browser, page, dest, size, scratch):
                raise Stop(f"the browser at {browser} did not return a picture for {shot_id}. Open that browser once by "
                           "hand, or set SHOTKIT_BROWSER to another one, and run this again.")
            rel = str(dest.relative_to(out_dir)) if not into else dest.name
            frames[shot_id] = {"kind": card["kind"], "path": rel, "sha256": sha256_file(dest)}
    receipt = {
        "version": "1.0",
        "cards_sha256": sha256_file(out_dir / CARDS),
        "brand_lock_sha256": look["brand_sha256"],
        "template_sha256": sha256_text(TEMPLATE.read_text(encoding="utf-8")),
        "size": f"{size[0]}x{size[1]}",
        "fonts": font_kind,
        "frames": frames,
    }
    if not into:
        (out_dir / RECEIPT).write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


def check(out_dir: Path) -> tuple[list[str], list[str]]:
    """Draw again and compare with the receipt. Returns (same, changed)."""
    out_dir = out_dir.resolve()
    receipt, err = load_json(out_dir / RECEIPT)
    if err or not isinstance(receipt, dict):
        raise Stop(f"nothing to check against: {err or RECEIPT + ' is not an object'}. Run design first.")
    with tempfile.TemporaryDirectory() as tmp:
        again = draw(out_dir, into=Path(tmp), web_fonts=receipt.get("fonts") != "system")
    if again.get("fonts") != receipt.get("fonts", "brand"):
        raise Stop("the brand's typeface could not be loaded this time, so the pictures cannot be compared. "
                   "Connect once and run this again.")
    same, changed = [], []
    for shot_id, was in sorted((receipt.get("frames") or {}).items()):
        now = (again["frames"].get(shot_id) or {}).get("sha256")
        on_disk = out_dir / str(was.get("path"))
        if now == was.get("sha256") and on_disk.is_file() and sha256_file(on_disk) == now:
            same.append(shot_id)
        else:
            changed.append(shot_id)
    return same, changed


def selftest() -> int:
    worked = REPO_ROOT / "skills" / "visual-asset-critic" / "examples" / "worked-run"
    checks: list[tuple[str, bool]] = []
    notes: list[str] = []
    cards = {"shot_01": {"kind": "list", "title": "Deploys", "rows": [{"key": "#1", "title": "A </script><b>row</b>", "status": "Live"}]},
             "shot_02": {"kind": "stat", "value": "42 s", "text": "from merge to live"}}
    with tempfile.TemporaryDirectory() as tmp:
        run = Path(tmp) / "run"
        shutil.copytree(worked, run)
        shutil.rmtree(run / "frames")
        shutil.rmtree(run / "critiques")
        (run / "design").mkdir()
        (run / CARDS).write_text(json.dumps({"version": "1.0", "cards": cards}))
        ids = ["shot_01", "shot_02"]
        checks.append(("good cards have nothing wrong", check_cards(cards, ids) == []))
        checks.append(("a card for a shot that is not in the plan is caught", bool(check_cards({"shot_09": cards["shot_01"]}, ids))))
        checks.append(("an unknown kind is caught", bool(check_cards({"shot_01": {"kind": "hologram"}}, ids))))
        checks.append(("a missing field is caught", bool(check_cards({"shot_01": {"kind": "list", "title": "x"}}, ids))))
        checks.append(("a field the kind does not take is caught", bool(check_cards({"shot_02": {"kind": "stat", "value": "1", "rows": []}}, ids))))
        look = brand_look((run / "brand-lock.snapshot.md").read_text())
        html = page_html(cards["shot_01"], look, "upper-third")
        checks.append(("a card's words cannot close the data element", "</script><b>" not in html))
        checks.append(("the card is drawn in the brand's own colours", look["colours"]["bg"] != DEFAULTS["bg"] or look["colours"]["acc"] != DEFAULTS["acc"]))
        try:
            draw(run, browser=None)
            refused = False
        except Stop as stop:
            refused = "Chrome" in str(stop)
        checks.append(("with no browser it stops with the reason", refused))
        if find_browser():
            try:
                receipt = draw(run, web_fonts=False)
            except Stop:
                receipt = None
                notes.append("the browser here did not answer, so no frame was drawn")
            if receipt:
                paths = [run / f["path"] for f in receipt["frames"].values()]
                size = tuple(int(n) for n in receipt["size"].split("x"))
                checks.append(("a frame is exactly the plan's size and lands in frames/round-1", all(png_size(p) == size and "round-1" in str(p) for p in paths)))
                same, changed = check(run)
                checks.append(("drawn twice, the picture is the same", len(same) == 2 and not changed))
                cards["shot_02"]["value"] = "43 s"
                (run / CARDS).write_text(json.dumps({"version": "1.0", "cards": cards}))
                same, changed = check(run)
                checks.append(("a changed card is a changed picture", changed == ["shot_02"]))
        else:
            notes.append("no browser here, so no frame was drawn")
    ok = True
    for label, passed in checks:
        print(f"  {'ok  ' if passed else 'FAIL'}  selftest: {label}")
        ok = ok and passed
    for note in notes:
        print(f"  note  {note}")
    print()
    print("Selftest passed." if ok else "Selftest FAILED.")
    return 0 if ok else 1


def main() -> int:
    p = argparse.ArgumentParser(description="Draw frames in code from the brand lock.")
    p.add_argument("output_dir", nargs="?", type=Path, help="Folder that holds shots.json and design/cards.json")
    p.add_argument("--check", action="store_true", help="Draw again and say if any picture changed")
    p.add_argument("--list", action="store_true", help="What each card is and where its frame is")
    p.add_argument("--kinds", action="store_true", help="The kinds of card and what each one takes")
    p.add_argument("--selftest", action="store_true", help="Prove the tool's guarantees")
    args = p.parse_args()
    if args.selftest:
        return selftest()
    if args.kinds:
        for kind, (what, required, optional) in KINDS.items():
            print(f"  {kind:<8} {what}")
            print(f"           needs: {', '.join(required) or 'nothing'}" + (f". can take: {', '.join(optional)}" if optional else ""))
        return 0
    if not args.output_dir:
        p.print_usage()
        return 2
    try:
        if args.list:
            _, cards, _, _ = plan(args.output_dir.resolve())
            receipt, _ = load_json(args.output_dir / RECEIPT)
            done = (receipt or {}).get("frames") or {} if isinstance(receipt, dict) else {}
            for shot_id, card in sorted(cards.items()):
                print(f"  {shot_id}  {card['kind']:<8} {(done.get(shot_id) or {}).get('path') or 'not drawn yet'}")
            return 0
        if args.check:
            same, changed = check(args.output_dir)
            for shot_id in same:
                print(f"  ok    {shot_id} is the same picture")
            for shot_id in changed:
                print(f"  FAIL  {shot_id} is not the picture the receipt records")
            return 1 if changed else 0
        receipt = draw(args.output_dir)
    except Stop as stop:
        print(f"shotkit: {stop}", file=sys.stderr)
        return 1
    for shot_id, frame in sorted(receipt["frames"].items()):
        print(f"  {shot_id}  {frame['kind']:<8} {frame['path']}")
    if receipt["fonts"] == "system":
        print("  note  the brand's typeface could not be fetched, so these are set in a system font. Connect and run this again.")
    print(f"Drew {len(receipt['frames'])} frames at {receipt['size']}. Receipt: {RECEIPT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
