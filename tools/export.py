#!/usr/bin/env python3
"""Turn a run into files you can post, present and play.

  export.py output/                  everything this computer can make
  export.py output/ stills           one image per shot, with its text on it
  export.py output/ stills --size 4x5 --size 9x16
  export.py output/ deck             a PowerPoint deck: scenes, a slide per shot, the script
  export.py output/ cut              a rough cut: the shots in order, as one video
  export.py output/ cut --music track.wav
  export.py output/ edit             the hand-off for a shoot and an edit
  export.py --selftest

Everything is written to output/export/. Nothing else in the folder is changed.

  stills   export/stills-<size>/shot_NN.png and export/stills.zip. The text is drawn by
           the board's own page, so a still looks like the board. Needs Chrome, Edge,
           Brave or Chromium on this computer.
  deck     export/storyboard.pptx. Opens in PowerPoint, Keynote and Google Slides. A
           cover, the scene breakdown, a picture-and-script slide per shot, the script
           sheet on paper, and the brand lock, set in the brand's colours and faces.
           Every word is text you can edit and every slide has speaker notes. Needs
           nothing: the frames go in as they are, cropped to the plan's aspect.
  cut      export/rough-cut.mp4. Each shot runs for its planned length. A shot with a
           clip plays the clip, and a shot with only a frame holds the frame. The text
           comes in and out at its planned times. Needs ffmpeg, and a browser for the
           text. It is a rough cut: hard cuts, no clip sound, no motion on stills.

  edit     export/edit/: shot-list.csv in a crew's words (close-up, eye level, push in),
           text.srt with every on-screen line at its planned time, and cut.edl, an edit
           decision list that Premiere, Resolve and Final Cut read. Needs nothing.

A shot with no frame is left out of the stills and the cut, and named in the report.
"""

from __future__ import annotations

import argparse
import math
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))
import board  # noqa: E402
from _shotkit import HEX_RE  # noqa: E402

SIZES = {
    "9x16": (1080, 1920), "4x5": (1080, 1350), "1x1": (1080, 1080), "16x9": (1920, 1080),
    "3x4": (1080, 1440), "2x3": (1080, 1620),
}
WHAT = ("stills", "deck", "cut", "edit")
FPS = 30


class Stop(Exception):
    """A problem to print as one line and exit on, not a traceback."""


# --------------------------------------------------------------------------
# What this computer has
# --------------------------------------------------------------------------

def find_browser() -> str | None:
    """A Chromium-family browser that can photograph a page without a window."""
    named = os.environ.get("SHOTKIT_BROWSER")
    if named:
        return named if Path(named).is_file() or shutil.which(named) else None
    for app in ("Google Chrome", "Chromium", "Microsoft Edge", "Brave Browser"):
        path = Path(f"/Applications/{app}.app/Contents/MacOS/{app}")
        if path.is_file():
            return str(path)
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "microsoft-edge", "brave-browser"):
        found = shutil.which(name)
        if found:
            return found
    for base in (os.environ.get("PROGRAMFILES"), os.environ.get("PROGRAMFILES(X86)"), os.environ.get("LOCALAPPDATA")):
        if not base:
            continue
        for rel in ("Google/Chrome/Application/chrome.exe", "Microsoft/Edge/Application/msedge.exe"):
            path = Path(base) / rel
            if path.is_file():
                return str(path)
    return None


def find_ffmpeg() -> str | None:
    return shutil.which("ffmpeg")


def png_size(path: Path) -> tuple[int, int] | None:
    try:
        with path.open("rb") as fh:
            head = fh.read(24)
    except OSError:
        return None
    if len(head) < 24 or head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", head[16:24])


def plan_size(aspect: str | None) -> str:
    key = (aspect or "16:9").replace(":", "x")
    return key if key in SIZES else "16x9"


# --------------------------------------------------------------------------
# The page a still is photographed from
# --------------------------------------------------------------------------

class Page:
    """The board of a run, written once to a scratch folder, and a browser to shoot it."""

    def __init__(self, out_dir: Path, scratch: Path, browser: str | None):
        self.out_dir, self.scratch, self.browser = out_dir, scratch, browser
        self.data, _ = board.build(out_dir)
        for shot in self.data["shots"]:
            for frame in shot["frames"]:
                frame["src"] = (out_dir / frame["path"]).resolve().as_uri()
        self.file = scratch / "still.html"
        self.file.write_text(board.render(self.data), encoding="utf-8")
        self.count = 0
        self.dead = False  # set when the browser did not answer, so later shots do not wait on it

    @property
    def shots(self) -> list[dict]:
        return self.data["shots"]

    def shoot(self, shot_id: str, dest: Path, size: tuple[int, int], layer: str | None = None,
              only: str | None = None) -> bool:
        """Photograph one shot at an exact pixel size. True when the file is right."""
        if not self.browser or self.dead:
            return False
        query = f"still={shot_id}" + (f"&layer={layer}" if layer else "") + (f"&only={only}" if only else "")
        self.count += 1
        profile = self.scratch / f"profile-{self.count}-{dest.stem}"
        base = [
            self.browser, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
            "--no-default-browser-check", "--force-device-scale-factor=1", f"--user-data-dir={profile}",
            f"--window-size={size[0]},{size[1]}", "--virtual-time-budget=10000", f"--screenshot={dest}",
        ]
        if layer:
            base.append("--default-background-color=00000000")
        url = self.file.as_uri() + "?" + query
        for extra in ([], ["--no-sandbox"]):
            dest.unlink(missing_ok=True)
            try:
                subprocess.run(base + extra + [url], capture_output=True, timeout=45)
            except (OSError, subprocess.TimeoutExpired):
                continue
            if png_size(dest) == size:
                shutil.rmtree(profile, ignore_errors=True)
                return True
        shutil.rmtree(profile, ignore_errors=True)
        self.dead = True
        return False

    def shoot_all(self, jobs: list[tuple]) -> list[bool]:
        """The first shot alone, to find out if the browser answers. Then the rest, four at a time."""
        if not jobs:
            return []
        first = self.shoot(*jobs[0])
        if not first:
            return [False] * len(jobs)
        with ThreadPoolExecutor(max_workers=4) as pool:
            return [first] + list(pool.map(lambda job: self.shoot(*job), jobs[1:]))


def framed(shots: list[dict]) -> tuple[list[dict], list[str]]:
    """The shots that have a frame, and the ids of those that do not."""
    return [s for s in shots if s["frames"]], [s["id"] for s in shots if not s["frames"]]


# --------------------------------------------------------------------------
# Stills
# --------------------------------------------------------------------------

def make_stills(page: Page, dest: Path, sizes: list[str]) -> dict:
    if not page.browser:
        raise Stop("stills need Chrome, Edge, Brave or Chromium on this computer. None was found. "
                   "Set SHOTKIT_BROWSER to the browser's path if it is somewhere unusual.")
    shots, missing = framed(page.shots)
    if not shots:
        raise Stop("no shot has a frame yet, so there is nothing to export")
    jobs = []
    for size in sizes:
        folder = dest / f"stills-{size}"
        if folder.exists():
            shutil.rmtree(folder)
        folder.mkdir(parents=True)
        for shot in shots:
            jobs.append((shot["id"], folder / f"{shot['id']}.png", SIZES[size]))
    done = page.shoot_all(jobs)
    failed = [str(job[1].relative_to(dest)) for job, ok in zip(jobs, done) if not ok]
    if failed:
        raise Stop(f"the browser at {page.browser} did not return a picture, so no stills were made. "
                   "Open that browser once by hand, or set SHOTKIT_BROWSER to another one, and run this again.")
    archive = dest / "stills.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_STORED) as zf:
        for _, path, _ in jobs:
            zf.write(path, str(path.relative_to(dest)))
    return {"files": [str(job[1]) for job in jobs], "archive": str(archive), "missing": missing, "sizes": sizes}


# --------------------------------------------------------------------------
# Deck
# --------------------------------------------------------------------------
#
# The deck is PowerPoint XML written by hand, so it needs nothing installed. Every word is
# a text box, every rule and panel is a shape, and each frame is a picture cropped to the
# plan's aspect (a crop, so it can be undone in the app). Positions are in points on a
# 960 x 540 slide, which is the 13.333 x 7.5 inch widescreen size.

PT = 12700  # EMU per point
SW, SH = 960, 540
M = 44  # the margin every slide keeps
NS = ('xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
      'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"')
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
XML = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
LABEL_SPACING = 0.14  # letter-spacing of every mono label, in em
MONO_DEFAULT = "IBM Plex Mono"


def emu(points: float) -> int:
    return int(round(points * PT))


def luminance(hex_val: str) -> float:
    n = int(hex_val.lstrip("#"), 16)
    parts = []
    for v in (n >> 16 & 255, n >> 8 & 255, n & 255):
        v /= 255
        parts.append(v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4)
    return 0.2126 * parts[0] + 0.7152 * parts[1] + 0.0722 * parts[2]


def contrast(a: str, b: str) -> float:
    la, lb = luminance(a), luminance(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def mix(a: str, b: str, amount: float) -> str:
    """`amount` of colour a over colour b."""
    na, nb = int(a.lstrip("#"), 16), int(b.lstrip("#"), 16)
    out = 0
    for shift in (16, 8, 0):
        out |= int(round((na >> shift & 255) * amount + (nb >> shift & 255) * (1 - amount))) << shift
    return f"{out:06X}"


def _pure(hex_val: str) -> bool:
    return hex_val in ("FFFFFF", "000000")


def deck_colours(brand: dict) -> dict:
    """
    The deck's colours, from the brand lock when they read and plain ones when not.

    The slides sit on the brand's background with its most readable neutral as ink. A
    tinted neutral (ivory, bone) wins over pure white or black, because it is the one the
    brand chose. The script sheet is "paper": the brand's light colour as ground with its
    dark ink, so it prints. Every other tone is a mix of ink into ground, so a deck never
    carries a colour the brand does not.
    """
    rows = []
    for row in brand.get("palette") or []:
        hex_val = str(row.get("hex") or "")
        if HEX_RE.fullmatch(hex_val):
            rows.append((str(row.get("role") or "").lower(), hex_val.lstrip("#").upper()))
    bg = next((h for r, h in rows if r.startswith(("background", "ground", "base"))), "0B0B0B")

    def readable(on: str, floor: float, prefer: tuple) -> str | None:
        found = [(r, h) for r, h in rows if contrast(on, h) >= floor]
        if not found:
            return None
        named = [h for r, h in found if any(k in r for k in prefer) and not _pure(h)]
        tinted = [h for _, h in found if not _pure(h)]
        return (named or tinted or [max(found, key=lambda x: contrast(on, x[1]))[1]])[0]

    keys = ("ink", "text", "neutral", "foreground", "paper", "ivory", "cream", "bone")
    ink = readable(bg, 10, keys) or readable(bg, 4.5, keys)
    if not ink:
        bg, ink = "0B0B0B", "F2EDE4"
    if luminance(bg) > 0.5:
        paper, paper_ink = bg, ink
    else:
        paper = ink
        paper_ink = next((h for r, h in rows if r.startswith("ink") and contrast(paper, h) >= 10), None) or bg
    accent = next((h for r, h in rows if r.startswith("accent") and contrast(bg, h) >= 2.5), ink)
    surface = next((h for r, h in rows if r.startswith(("surface", "panel")) and contrast(ink, h) >= 7), mix(ink, bg, 0.06))
    return {
        "bg": bg, "ink": ink, "ink2": mix(ink, bg, 0.88), "ink3": mix(ink, bg, 0.76), "muted": mix(ink, bg, 0.55),
        "rule": mix(ink, bg, 0.17), "surface": surface, "accent": accent,
        "paper": paper, "p_ink": paper_ink, "p_ink2": mix(paper_ink, paper, 0.84), "p_ink3": mix(paper_ink, paper, 0.74),
        "p_muted": mix(paper_ink, paper, 0.6), "p_rule": mix(paper_ink, paper, 0.14), "p_surface": mix(paper_ink, paper, 0.05),
    }


def clean(text) -> str:
    """Text that is safe inside XML: no control characters, and escaped."""
    return escape(re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", str(text if text is not None else "")))


# Advance widths of a plain sans (Helvetica), per 1000 of the type size. Used to break
# lines before writing them, so a box is sized to its text in every app that opens it.
_ADV = dict(zip(" !\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~", (278, 278, 355, 556, 556, 889, 667, 191, 333, 333, 389, 584, 278, 333, 278,
                                                       278, 278, 278, 584, 584, 584, 556, 1015, 278, 278, 278, 469, 556, 333, 334,
                                                       260, 334, 584)))
_ADV.update(dict(zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ", (667, 667, 722, 722, 667, 611, 778, 722, 278, 500, 667, 556, 833, 722, 778, 667,
                                                    778, 722, 667, 611, 722, 667, 944, 667, 667, 611))))
_ADV.update(dict(zip("abcdefghijklmnopqrstuvwxyz", (556, 556, 500, 556, 556, 278, 556, 556, 222, 222, 500, 222, 833, 556, 556, 556,
                                                    556, 333, 500, 278, 556, 500, 722, 500, 500, 500))))
_ADV.update({d: 556 for d in "0123456789"})
_ADV.update({"‘": 222, "’": 222, "“": 333, "”": 333, "·": 278, "…": 1000, "–": 556})
SERIF_HINTS = ("serif", "playfair", "garamond", "georgia", "times", "lora", "merriweather", "fraunces", "baskerville",
               "cormorant", "crimson", "caslon", "bodoni", "didot", "spectral", "newsreader", "instrument")


class Face:
    """A typeface as the deck names it, and how wide it sets."""

    def __init__(self, family: str, kind: str, weight: int = 400):
        self.family, self.kind, self.weight = family, kind, weight
        # A display face set heavy runs wide. The margin also covers the fallback an app
        # uses when the face is not installed.
        self.factor = {"serif": 1.0, "sans": 1.08, "mono": 1.0}[kind] * (1.1 if weight >= 700 else 1.0)

    @property
    def bold(self) -> bool:
        return self.weight >= 600

    @property
    def pitch(self) -> int:
        return {"serif": 18, "sans": 34, "mono": 49}[self.kind]

    def width(self, text: str, size: float, spacing: float = 0.0, caps: bool = False) -> float:
        text = text.upper() if caps else text
        if self.kind == "mono":
            per = sum(600 for _ in text)
        else:
            per = sum(_ADV.get(ch, 700 if ch.isupper() else 556) for ch in text) * self.factor
        return per / 1000 * size + len(text) * spacing * size


def face_from(spec: str | None, fallback: str, kind: str | None = None) -> Face:
    from _shotkit import parse_font_spec

    parsed = parse_font_spec(spec) if spec else {"family": None, "weight": None}
    family = board.css_family(spec) if spec else None
    family = family or fallback
    if kind is None:
        low = family.lower()
        kind = "mono" if "mono" in low or "code" in low else "serif" if any(h in low for h in SERIF_HINTS) else "sans"
    return Face(family, kind, int(parsed.get("weight") or 400))


def wrap(text: str, width: float, size: float, face: Face, spacing: float = 0.0, caps: bool = False) -> list[str]:
    """The lines a text breaks into in a box `width` points wide."""
    width *= 0.95
    lines: list[str] = []
    for para in str(text).split("\n"):
        line = ""
        for word in para.split():
            trial = f"{line} {word}" if line else word
            if line and face.width(trial, size, spacing, caps) > width:
                lines.append(line)
                line = word
            else:
                line = trial
        lines.append(line)
    return lines


def fit(text: str, width: float, size: float, face: Face, max_lines: int, spacing: float = 0.0,
        caps: bool = False) -> list[str]:
    """The text broken into lines, cut at a word with an ellipsis when it runs past `max_lines`."""
    lines = wrap(text, width, size, face, spacing, caps)
    if len(lines) <= max_lines:
        return lines
    kept = lines[:max_lines]
    last = kept[-1]
    while last and face.width(last + "…", size, spacing, caps) > width * 0.95:
        last = last.rsplit(" ", 1)[0] if " " in last else last[:-1]
    kept[-1] = last.rstrip(",;:.- ") + "…"
    return kept


class Slide:
    """One slide: a name, a ground colour, the shapes on it and its speaker notes."""

    def __init__(self, name: str, ground: str):
        self.name, self.ground = name, ground
        self.shapes: list[str] = []
        self.media: list[tuple[str, Path]] = []
        self.notes: list[str] = []
        self.next_id = 2

    def _id(self) -> int:
        self.next_id += 1
        return self.next_id - 1

    @staticmethod
    def _rpr(size: float, colour: str, face: Face, bold: bool | None, italic: bool, spacing: float, caps: bool) -> str:
        bold = face.bold if bold is None else bold
        name = clean(face.family)
        cap = ' cap="all"' if caps else ""
        return (f'<a:rPr lang="en-US" sz="{int(round(size * 100))}" b="{int(bold)}" i="{int(italic)}" '
                f'spc="{int(round(spacing * size * 100))}"{cap} dirty="0">'
                f'<a:solidFill><a:srgbClr val="{colour}"/></a:solidFill>'
                f'<a:latin typeface="{name}" pitchFamily="{face.pitch}" charset="0"/>'
                f'<a:cs typeface="{name}" pitchFamily="{face.pitch}" charset="0"/></a:rPr>')

    def text(self, x: float, y: float, w: float, h: float, paras, size: float, colour: str, face: Face,
             bold: bool | None = None, italic: bool = False, spacing: float = 0.0, caps: bool = False,
             align: str = "l", anchor: str = "t", lead: float | None = None, gap: float = 0.0,
             name: str | None = None) -> None:
        """
        A text box. `paras` is a string or a list of paragraphs, and a paragraph is a string
        or a list of runs, each (text, {overrides}) with keys size, colour, face, bold, italic.
        `lead` is the line height in points, set exactly so every app breaks the same way.
        """
        lead = lead or size * 1.2
        body = ""
        for i, para in enumerate(paras if isinstance(paras, list) else [paras]):
            runs = para if isinstance(para, list) else [(para, {})]
            before = f'<a:spcBef><a:spcPts val="{int(gap * 100)}"/></a:spcBef>' if i and gap else '<a:spcBef><a:spcPts val="0"/></a:spcBef>'
            out = (f'<a:p><a:pPr algn="{align}"><a:lnSpc><a:spcPts val="{int(round(lead * 100))}"/></a:lnSpc>{before}'
                   '<a:spcAft><a:spcPts val="0"/></a:spcAft><a:buNone/></a:pPr>')
            for content, extra in runs:
                rpr = self._rpr(extra.get("size", size), extra.get("colour", colour), extra.get("face", face),
                                extra.get("bold", bold), extra.get("italic", italic), spacing, caps)
                out += f'<a:r>{rpr}<a:t>{clean(content)}</a:t></a:r>'
            body += out + f'<a:endParaRPr lang="en-US" sz="{int(round(size * 100))}" dirty="0"/></a:p>'
        n = self._id()
        self.shapes.append(
            f'<p:sp><p:nvSpPr><p:cNvPr id="{n}" name="{clean(name or f"Text {n}")}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>'
            f'<p:txBody><a:bodyPr wrap="square" lIns="0" tIns="0" rIns="0" bIns="0" anchor="{anchor}" rtlCol="0">'
            f'<a:noAutofit/></a:bodyPr><a:lstStyle/>{body}</p:txBody></p:sp>')

    def rect(self, x: float, y: float, w: float, h: float, fill: str | None, outline: str | None = None,
             weight: float = 0.75, name: str | None = None) -> None:
        n = self._id()
        paint = f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>' if fill else "<a:noFill/>"
        edge = (f'<a:ln w="{emu(weight)}"><a:solidFill><a:srgbClr val="{outline}"/></a:solidFill><a:miter lim="800000"/></a:ln>'
                if outline else "<a:ln><a:noFill/></a:ln>")
        self.shapes.append(
            f'<p:sp><p:nvSpPr><p:cNvPr id="{n}" name="{clean(name or f"Shape {n}")}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>{paint}{edge}</p:spPr>'
            f'<p:txBody><a:bodyPr rtlCol="0" anchor="ctr"/><a:lstStyle/><a:p><a:endParaRPr lang="en-US" dirty="0"/></a:p></p:txBody></p:sp>')

    def rule(self, x: float, y: float, w: float, colour: str, weight: float = 0.75) -> None:
        """A hairline: a filled shape, so it draws the same thickness in every app."""
        self.rect(x, y, w, weight, colour, name="Rule")

    def picture(self, x: float, y: float, w: float, h: float, path: Path, name: str,
                crop: tuple[float, float, float, float] = (0, 0, 0, 0)) -> None:
        n = self._id()
        rid = f"rId{len(self.media) + 2}"
        self.media.append((rid, path))
        l, t, r, b = (int(round(v * 100000)) for v in crop)
        src = f'<a:srcRect l="{l}" t="{t}" r="{r}" b="{b}"/>' if any((l, t, r, b)) else ""
        self.shapes.append(
            f'<p:pic><p:nvPicPr><p:cNvPr id="{n}" name="{clean(name)}" descr="{clean(name)}"/>'
            f'<p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr>'
            f'<p:blipFill><a:blip r:embed="{rid}"/>{src}<a:stretch><a:fillRect/></a:stretch></p:blipFill>'
            f'<p:spPr><a:xfrm><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic>')

    def xml(self) -> str:
        return (XML + f'<p:sld {NS}><p:cSld name="{clean(self.name)}"><p:bg><p:bgPr><a:solidFill><a:srgbClr val="{self.ground}"/>'
                '</a:solidFill><a:effectLst/></p:bgPr></p:bg><p:spTree>' + TREE_HEAD + "".join(self.shapes)
                + '</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>')

    def notes_xml(self) -> str:
        paras = "".join(f'<a:p><a:r><a:rPr lang="en-US" dirty="0"/><a:t>{clean(line)}</a:t></a:r></a:p>' for line in self.notes)
        paras = paras or '<a:p><a:endParaRPr lang="en-US" dirty="0"/></a:p>'  # a text body needs one paragraph
        return (XML + f'<p:notes {NS}><p:cSld><p:spTree>{TREE_HEAD}'
                '<p:sp><p:nvSpPr><p:cNvPr id="2" name="Slide Image Placeholder 1"/><p:cNvSpPr><a:spLocks noGrp="1" noRot="1" '
                'noChangeAspect="1"/></p:cNvSpPr><p:nvPr><p:ph type="sldImg"/></p:nvPr></p:nvSpPr><p:spPr/></p:sp>'
                '<p:sp><p:nvSpPr><p:cNvPr id="3" name="Notes Placeholder 2"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
                '<p:nvPr><p:ph type="body" idx="1"/></p:nvPr></p:nvSpPr><p:spPr/><p:txBody><a:bodyPr/><a:lstStyle/>'
                f'{paras}</p:txBody></p:sp></p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:notes>')


TREE_HEAD = ('<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm>'
             '<a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>')


def theme_xml(c: dict, display: Face, body: Face) -> str:
    """The theme carries the brand, so a slide or a text box added in the app starts on brand."""
    def font(face: Face) -> str:
        return f'<a:latin typeface="{clean(face.family)}"/><a:ea typeface=""/><a:cs typeface=""/>'

    fills = '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>' * 3
    return (XML + '<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Shotkit">'
            '<a:themeElements><a:clrScheme name="Shotkit">'
            f'<a:dk1><a:srgbClr val="{c["p_ink"]}"/></a:dk1><a:lt1><a:srgbClr val="{c["paper"]}"/></a:lt1>'
            f'<a:dk2><a:srgbClr val="{c["bg"]}"/></a:dk2><a:lt2><a:srgbClr val="{c["ink"]}"/></a:lt2>'
            f'<a:accent1><a:srgbClr val="{c["accent"]}"/></a:accent1><a:accent2><a:srgbClr val="{c["muted"]}"/></a:accent2>'
            f'<a:accent3><a:srgbClr val="{c["ink3"]}"/></a:accent3><a:accent4><a:srgbClr val="{c["rule"]}"/></a:accent4>'
            f'<a:accent5><a:srgbClr val="{c["p_muted"]}"/></a:accent5><a:accent6><a:srgbClr val="{c["surface"]}"/></a:accent6>'
            f'<a:hlink><a:srgbClr val="{c["accent"]}"/></a:hlink><a:folHlink><a:srgbClr val="{c["muted"]}"/></a:folHlink></a:clrScheme>'
            f'<a:fontScheme name="Shotkit"><a:majorFont>{font(display)}</a:majorFont><a:minorFont>{font(body)}</a:minorFont></a:fontScheme>'
            f'<a:fmtScheme name="Shotkit"><a:fillStyleLst>{fills}</a:fillStyleLst>'
            '<a:lnStyleLst><a:ln w="6350"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>'
            '<a:ln w="12700"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>'
            '<a:ln w="19050"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst>'
            '<a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst/></a:effectStyle>'
            '<a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst>'
            f'<a:bgFillStyleLst>{fills}</a:bgFillStyleLst></a:fmtScheme></a:themeElements></a:theme>')


CLR_MAP = ('<p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" '
           'accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>')


def master_xml(c: dict) -> str:
    """A blank master on the deck's ground, with text in the deck's ink and body face."""
    style = (f'<a:lvl1pPr><a:defRPr sz="{{sz}}"><a:solidFill><a:srgbClr val="{c["ink"]}"/></a:solidFill>'
             '<a:latin typeface="{font}"/></a:defRPr></a:lvl1pPr>')
    return (XML + f'<p:sldMaster {NS}><p:cSld><p:bg><p:bgPr><a:solidFill><a:srgbClr val="{c["bg"]}"/></a:solidFill>'
            f'<a:effectLst/></p:bgPr></p:bg><p:spTree>{TREE_HEAD}</p:spTree></p:cSld>{CLR_MAP}'
            '<p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>'
            '<p:txStyles><p:titleStyle>' + style.format(sz=4000, font="+mj-lt") + '</p:titleStyle>'
            '<p:bodyStyle>' + style.format(sz=1600, font="+mn-lt") + '</p:bodyStyle>'
            '<p:otherStyle>' + style.format(sz=1400, font="+mn-lt") + '</p:otherStyle></p:txStyles></p:sldMaster>')


LAYOUT = (XML + f'<p:sldLayout {NS} type="blank" preserve="1"><p:cSld name="Blank"><p:spTree>{TREE_HEAD}</p:spTree></p:cSld>'
          '<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>')
NOTES_MASTER = (
    XML + f'<p:notesMaster {NS}><p:cSld><p:bg><p:bgRef idx="1001"><a:schemeClr val="bg1"/></p:bgRef></p:bg><p:spTree>{TREE_HEAD}'
    '<p:sp><p:nvSpPr><p:cNvPr id="2" name="Slide Image Placeholder 1"/><p:cNvSpPr><a:spLocks noGrp="1" noRot="1" noChangeAspect="1"/>'
    '</p:cNvSpPr><p:nvPr><p:ph type="sldImg" idx="2"/></p:nvPr></p:nvSpPr><p:spPr><a:xfrm><a:off x="381000" y="685800"/>'
    '<a:ext cx="6096000" cy="3429000"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln w="12700">'
    '<a:solidFill><a:prstClr val="black"/></a:solidFill></a:ln></p:spPr></p:sp>'
    '<p:sp><p:nvSpPr><p:cNvPr id="3" name="Notes Placeholder 2"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
    '<p:nvPr><p:ph type="body" sz="quarter" idx="3"/></p:nvPr></p:nvSpPr><p:spPr><a:xfrm><a:off x="685800" y="4343400"/>'
    '<a:ext cx="5486400" cy="4114800"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr>'
    '<p:txBody><a:bodyPr vert="horz" lIns="91440" tIns="45720" rIns="91440" bIns="45720" rtlCol="0"/><a:lstStyle/>'
    '<a:p><a:endParaRPr lang="en-US"/></a:p></p:txBody></p:sp></p:spTree></p:cSld>' + CLR_MAP +
    '<p:notesStyle><a:lvl1pPr marL="0" algn="l" defTabSz="914400" rtl="0" eaLnBrk="1" latinLnBrk="0" hangingPunct="1">'
    '<a:defRPr sz="1200" kern="1200"><a:solidFill><a:schemeClr val="tx1"/></a:solidFill><a:latin typeface="+mn-lt"/>'
    '<a:ea typeface="+mn-ea"/><a:cs typeface="+mn-cs"/></a:defRPr></a:lvl1pPr></p:notesStyle></p:notesMaster>')


def rels(entries: list[tuple[str, str, str]]) -> str:
    rows = "".join(f'<Relationship Id="{rid}" Type="{REL}/{kind}" Target="{target}"/>' for rid, kind, target in entries)
    return XML + f'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{rows}</Relationships>'


def write_pptx(dest: Path, slides: list[Slide], title: str, created: str, theme: str, master: str) -> None:
    media_names: dict[Path, str] = {}
    ct = "application/vnd.openxmlformats-officedocument"
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
        overrides = ""
        slide_rels = []
        for i, slide in enumerate(slides, 1):
            entries = [("rId1", "slideLayout", "../slideLayouts/slideLayout1.xml")]
            for rid, path in slide.media:
                if path not in media_names:
                    media_names[path] = f"image{len(media_names) + 1}{path.suffix.lower()}"
                    zf.write(path, f"ppt/media/{media_names[path]}", zipfile.ZIP_STORED)
                entries.append((rid, "image", f"../media/{media_names[path]}"))
            entries.append((f"rId{len(slide.media) + 2}", "notesSlide", f"../notesSlides/notesSlide{i}.xml"))
            zf.writestr(f"ppt/slides/slide{i}.xml", slide.xml())
            zf.writestr(f"ppt/slides/_rels/slide{i}.xml.rels", rels(entries))
            zf.writestr(f"ppt/notesSlides/notesSlide{i}.xml", slide.notes_xml())
            zf.writestr(f"ppt/notesSlides/_rels/notesSlide{i}.xml.rels", rels(
                [("rId1", "notesMaster", "../notesMasters/notesMaster1.xml"), ("rId2", "slide", f"../slides/slide{i}.xml")]))
            overrides += (f'<Override PartName="/ppt/slides/slide{i}.xml" ContentType="{ct}.presentationml.slide+xml"/>'
                          f'<Override PartName="/ppt/notesSlides/notesSlide{i}.xml" ContentType="{ct}.presentationml.notesSlide+xml"/>')
            slide_rels.append((f"rId{i + 3}", "slide", f"slides/slide{i}.xml"))
        ids = "".join(f'<p:sldId id="{255 + i}" r:id="rId{i + 3}"/>' for i in range(1, len(slides) + 1))
        zf.writestr("ppt/presentation.xml", XML + (
            f'<p:presentation {NS} saveSubsetFonts="1"><p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>'
            '<p:notesMasterIdLst><p:notesMasterId r:id="rId3"/></p:notesMasterIdLst>'
            f'<p:sldIdLst>{ids}</p:sldIdLst><p:sldSz cx="{emu(SW)}" cy="{emu(SH)}"/>'
            '<p:notesSz cx="6858000" cy="9144000"/></p:presentation>'))
        zf.writestr("ppt/_rels/presentation.xml.rels", rels(
            [("rId1", "slideMaster", "slideMasters/slideMaster1.xml"), ("rId2", "theme", "theme/theme1.xml"),
             ("rId3", "notesMaster", "notesMasters/notesMaster1.xml")] + slide_rels))
        zf.writestr("ppt/theme/theme1.xml", theme)
        zf.writestr("ppt/theme/theme2.xml", theme)
        zf.writestr("ppt/slideMasters/slideMaster1.xml", master)
        zf.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", rels(
            [("rId1", "slideLayout", "../slideLayouts/slideLayout1.xml"), ("rId2", "theme", "../theme/theme1.xml")]))
        zf.writestr("ppt/slideLayouts/slideLayout1.xml", LAYOUT)
        zf.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", rels([("rId1", "slideMaster", "../slideMasters/slideMaster1.xml")]))
        zf.writestr("ppt/notesMasters/notesMaster1.xml", NOTES_MASTER)
        zf.writestr("ppt/notesMasters/_rels/notesMaster1.xml.rels", rels([("rId1", "theme", "../theme/theme2.xml")]))
        zf.writestr("docProps/core.xml", XML + (
            '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
            'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            f'<dc:title>{clean(title)}</dc:title><dcterms:created xsi:type="dcterms:W3CDTF">{clean(created)}</dcterms:created>'
            f'<dcterms:modified xsi:type="dcterms:W3CDTF">{clean(created)}</dcterms:modified></cp:coreProperties>'))
        zf.writestr("_rels/.rels", XML + (
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            f'<Relationship Id="rId1" Type="{REL}/officeDocument" Target="ppt/presentation.xml"/>'
            '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" '
            'Target="docProps/core.xml"/></Relationships>'))
        zf.writestr("[Content_Types].xml", XML + (
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/><Default Extension="png" ContentType="image/png"/>'
            '<Default Extension="jpg" ContentType="image/jpeg"/><Default Extension="jpeg" ContentType="image/jpeg"/>'
            f'<Override PartName="/ppt/presentation.xml" ContentType="{ct}.presentationml.presentation.main+xml"/>'
            f'<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="{ct}.presentationml.slideMaster+xml"/>'
            f'<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="{ct}.presentationml.slideLayout+xml"/>'
            f'<Override PartName="/ppt/notesMasters/notesMaster1.xml" ContentType="{ct}.presentationml.notesMaster+xml"/>'
            f'<Override PartName="/ppt/theme/theme1.xml" ContentType="{ct}.theme+xml"/>'
            f'<Override PartName="/ppt/theme/theme2.xml" ContentType="{ct}.theme+xml"/>'
            '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
            + overrides + '</Types>'))


def seconds(value) -> str:
    if not isinstance(value, (int, float)):
        return "?"
    return str(int(value)) if float(value).is_integer() else f"{value:.1f}"


def clock(value: float, tenths: bool = True) -> str:
    """0:02.0, or 0:18 without tenths. `tenths=None` drops them only on a whole second."""
    if tenths is None:
        tenths = not float(value).is_integer()
    value = max(0.0, float(value))
    if not tenths:
        whole = int(round(value))
        return f"{whole // 60}:{whole % 60:02d}"
    minutes = int(value // 60)
    return f"{minutes}:{value - minutes * 60:04.1f}"


_ONES = ("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen "
         "seventeen eighteen nineteen").split()
_TENS = {2: "twenty", 3: "thirty", 4: "forty", 5: "fifty", 6: "sixty", 7: "seventy", 8: "eighty", 9: "ninety"}


def in_words(n: int) -> str:
    if 0 <= n < 20:
        return _ONES[n]
    if n < 100:
        return _TENS[n // 10] + (f"-{_ONES[n % 10]}" if n % 10 else "")
    return str(n)


def jpeg_size(path: Path) -> tuple[int, int] | None:
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if data[:2] != b"\xff\xd8":
        return None
    i = 2
    while i + 9 < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7 or marker == 0xFF:
            i += 1 if marker == 0xFF else 2
            continue
        length = struct.unpack(">H", data[i + 2:i + 4])[0]
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            h, w = struct.unpack(">HH", data[i + 5:i + 9])
            return w, h
        i += 2 + length
    return None


def image_size(path: Path) -> tuple[int, int] | None:
    return png_size(path) or jpeg_size(path)


def cover_crop(size: tuple[int, int] | None, box_ratio: float) -> tuple[float, float, float, float]:
    """The share to trim from each side (left, top, right, bottom) so a picture fills a box."""
    if not size or not size[1] or not box_ratio:
        return (0, 0, 0, 0)
    ratio = size[0] / size[1]
    if abs(ratio - box_ratio) < 0.005:
        return (0, 0, 0, 0)
    if ratio > box_ratio:
        side = (1 - box_ratio / ratio) / 2
        return (side, 0, side, 0)
    side = (1 - ratio / box_ratio) / 2
    return (0, side, 0, side)


# What the plan's short words say, for people.
GENERATOR_NAMES = {"flux": "Flux", "nano-banana": "Nano Banana", "seedream": "Seedream", "ideogram": "Ideogram",
                   "gpt-image": "GPT Image", "kling": "Kling", "seedance": "Seedance", "hailuo": "Hailuo",
                   "midjourney": "Midjourney", "veo": "Veo", "runway": "Runway", "sora": "Sora"}
VERDICT_WORDS = {"ACCEPT": "accepted", "REVISE": "sent back to revise", "REJECT": "rejected"}
MEDIA_ID = re.compile(r"\bm\d{1,4}\b")


def plain_name(name: str) -> str:
    """portrait-room_chocolate_back.jpg reads as portrait-room chocolate back."""
    stem = Path(str(name)).stem
    return re.sub(r"\s+", " ", stem.replace("_", " ")).strip() or str(name)


class Words:
    """A run's shots put into the words a deck reads in: no internal ids, plain names."""

    def __init__(self, data: dict):
        self.media = {m["id"]: m for m in (data.get("media") or {}).get("items") or [] if isinstance(m, dict) and m.get("id")}

    def scrub(self, text) -> str:
        """Internal ids out: a media id becomes its file's name, shot_04 becomes shot 04."""
        text = " ".join(str(text or "").split())
        text = MEDIA_ID.sub(lambda m: plain_name(self.media[m.group(0)]["name"]) if m.group(0) in self.media and self.media[m.group(0)].get("name") else "a file of yours", text)
        text = re.sub(r"\bshot_(\d+)\b", r"shot \1", text)
        text = re.sub(r"\btext_\d+\b", "the on-screen line", text)
        text = re.sub(r"\b(shots|run|review|media)\.json\b", "the plan", text)
        return text

    def generator(self, shot: dict) -> str:
        source = shot.get("source") or {}
        name = source.get("model") or next(iter(shot.get("prompts") or {}), None)
        crit = next((c for c in reversed(shot.get("critiques") or []) if c.get("generator")), None)
        name = name or (crit or {}).get("generator")
        words = GENERATOR_NAMES.get(str(name or "").lower(), str(name or "").replace("-", " ").title())
        model = (crit or {}).get("model")
        if words and model and str(model).lower() not in words.lower():
            words = f"{words} {model}"
        return self.scrub(words)

    def picture(self, shot: dict) -> str:
        source = shot.get("source") or {}
        kind = source.get("type")
        has = bool(shot["frames"] or shot["clips"])
        if kind == "own":
            item = self.media.get(source.get("media") or "") or {}
            clip = item.get("kind") == "video" or "in" in source
            text = ("Your clip" if clip else "Your photo") + (f" · {plain_name(item['name'])}" if item.get("name") else "")
            if "in" in source and "out" in source:
                text += f" · {seconds(source['in'])} to {seconds(source['out'])} s"
            return text
        if kind == "design":
            return "Drawn from the brand lock" + (f" · {source['card']} card" if source.get("card") else "")
        if kind == "missing":
            return "To shoot"
        gen = self.generator(shot)
        return ("Generated" if has else "To generate") + (f" · {gen}" if gen else "")

    def to_make(self, shot: dict) -> str:
        kind = (shot.get("source") or {}).get("type")
        return {"missing": "To shoot", "own": "To place", "design": "To draw"}.get(kind, "To make")

    def critic(self, shot: dict) -> str:
        if not shot.get("critiques"):
            return ""
        last = shot["critiques"][-1]
        verdict = VERDICT_WORDS.get(str(last.get("verdict") or "").upper(), str(last.get("verdict") or "checked").lower())
        rnd = f", round {last['round']}" if last.get("round") and len(shot["critiques"]) > 1 else ""
        order = {"critical": 0, "major": 1, "minor": 2}
        issues = sorted((i for i in last.get("issues") or [] if isinstance(i, dict)), key=lambda i: order.get(str(i.get("severity")), 3))
        main = ""
        if issues:
            top = issues[0]
            main = top.get("fix") if str(last.get("verdict")).upper() != "ACCEPT" and top.get("fix") else top.get("note") or top.get("fix") or ""
        elif last.get("working"):
            main = last["working"][0]
        main = self.scrub(main)
        return f"Critic: {verdict}{rnd}." + (f" {main[:1].upper()}{main[1:]}" if main else "")


def moves(shot: dict) -> str:
    return MOTION_WORDS.get(shot.get("motion"), str(shot.get("motion") or "").replace("-", " ").capitalize())


def timed(shot: dict) -> bool:
    return (isinstance(shot.get("start"), (int, float)) and isinstance(shot.get("end"), (int, float))
            and shot["end"] > shot["start"])


def scenes_of(shots: list[dict]) -> list[dict]:
    """Consecutive shots with the same beat are one scene."""
    out: list[dict] = []
    for shot in shots:
        beat = str(shot.get("beat") or "").strip()
        if not out or out[-1]["beat"].lower() != beat.lower():
            out.append({"n": len(out) + 1, "beat": beat, "shots": []})
        out[-1]["shots"].append(shot)
    for scene in out:
        run = [s for s in scene["shots"] if timed(s)]
        scene["start"] = min((s["start"] for s in run), default=None)
        scene["end"] = max((s["end"] for s in run), default=None)
        name = scene["beat"] or f"Scene {scene['n']}"
        scene["name"] = name[:1].upper() + name[1:]
        scene["purpose"] = next((s.get("rationale") for s in scene["shots"] if s.get("rationale")), "")
    return out


def make_deck(page: Page, dest: Path, scratch: Path) -> dict:
    data = page.data
    shots = data["shots"]
    if not shots:
        raise Stop("there is no plan in this folder yet, so there is nothing to put in a deck")
    c = deck_colours(data["brand"])
    fonts = data["brand"].get("fonts") or {}
    display = face_from(fonts.get("display_font"), "Georgia")
    body = face_from(fonts.get("body_font"), "Arial", "sans" if not fonts.get("body_font") else None)
    if body.kind == "mono":
        body = Face(body.family, "sans", body.weight)
    body = Face(body.family, body.kind, min(body.weight, 500))
    mono = face_from(fonts.get("mono_font"), MONO_DEFAULT, "mono")
    mono = Face(mono.family, "mono", 400)
    words = Words(data)
    project = data["project"]
    size_key = plan_size(project.get("aspect"))
    px = SIZES[size_key]
    ratio = px[0] / px[1]
    title = project.get("title") or "Storyboard"
    brand_name = data["brand"].get("name") or ""
    short_title = title.split(":")[0].strip() or title
    if short_title.lower() == brand_name.lower():
        short_title = title.split(":", 1)[-1].strip() if ":" in title else ""
    kicker = " · ".join(v for v in (brand_name, short_title) if v)
    scenes = scenes_of(shots)
    scene_of = {s["id"]: sc for sc in scenes for s in sc["shots"]}
    in_cut = [s for s in shots if timed(s)]
    total = max((s["end"] for s in in_cut), default=float(project.get("duration_s") or 0))
    shown = [s for s in shots if timed(s) or s["frames"]]  # a zero-length optional shot gets a slide only with a picture
    sp = LABEL_SPACING

    # Each frame once, made small enough to email when ffmpeg is here.
    ffmpeg = find_ffmpeg()
    folder = scratch / "deck"
    folder.mkdir(exist_ok=True)
    pictures: dict[str, tuple[Path, tuple[int, int] | None]] = {}
    for shot in shots:
        if not shot["frames"]:
            continue
        path = page.out_dir / shot["frames"][-1]["path"]
        if path.suffix.lower() not in (".png", ".jpg", ".jpeg") or not path.is_file():
            continue
        size = image_size(path)
        if ffmpeg and (path.stat().st_size > 1_200_000 or (size and max(size) > 2200)):
            small = folder / f"{shot['id']}.jpg"
            done = subprocess.run([ffmpeg, "-v", "error", "-y", "-i", str(path), "-vf",
                                   "scale=w=1800:h=1800:force_original_aspect_ratio=decrease", "-q:v", "3", str(small)],
                                  capture_output=True)
            if done.returncode == 0 and small.is_file():
                path, size = small, image_size(small)
        pictures[shot["id"]] = (path, size)

    def label(s: Slide, x: float, y: float, w: float, text: str, colour: str, size: float = 8.5,
              align: str = "l") -> None:
        s.text(x, y, w, size * 1.4, text, size, colour, mono, spacing=sp, caps=True, align=align, lead=size * 1.3)

    def frame(s: Slide, shot: dict, x: float, y: float, w: float, h: float, paper: bool = False, small: bool = False) -> None:
        """The shot's frame cropped to the box, or a drawn panel that says what is still to make."""
        got = pictures.get(shot["id"])
        if got:
            s.picture(x, y, w, h, got[0], f"Shot {shot['n']} frame", cover_crop(got[1], w / h))
            return
        ground, line, ink, muted = ((c["p_surface"], c["p_rule"], c["p_ink"], c["p_muted"]) if paper
                                    else (c["surface"], c["rule"], c["ink"], c["muted"]))
        s.rect(x, y, w, h, ground, line, name=f"Shot {shot['n']} panel")
        if small:
            return
        framing = FRAMING_WORDS.get(shot.get("framing"), shot.get("framing") or "")
        big = max(11.0, min(22.0, w / 9))
        mid = y + h / 2
        if framing and w > 70:
            label(s, x + 8, mid - big * 0.9 - 14, w - 16, framing, muted, size=min(8.5, max(7, w / 22)), align="c")
        s.text(x + 6, mid - big * 0.6, w - 12, big * 1.4, words.to_make(shot), big, ink, display, italic=True,
               align="c", lead=big * 1.2)

    slides: list[Slide] = []
    date = str(data.get("rendered_at") or "")[:10]
    try:
        from datetime import date as _date
        day = _date.fromisoformat(date)
        pretty_date = f"{day.day} {day.strftime('%b %Y')}"
    except ValueError:
        pretty_date = date

    # 1. Cover: the title in the display face, one line on what it is, the facts, a hero frame.
    s = Slide("Cover", c["bg"])
    hero = next((x for x in reversed(in_cut) if x["id"] in pictures and x.get("status") == "accept"), None) \
        or next((x for x in reversed(in_cut) if x["id"] in pictures), None)
    hero_w = 430 if hero else 0
    if hero:
        frame(s, hero, SW - hero_w, 0, hero_w, SH)
    lx, lw = 52, SW - hero_w - 52 - 52
    label(s, lx, 44, lw, " · ".join(v for v in (brand_name, "Storyboard", pretty_date) if v), c["muted"], 9.5)
    kinds = {(x.get("source") or {}).get("type") for x in in_cut}
    made_of = ("the brand's own photos and clips" if kinds == {"own"} else "frames drawn from the brand lock" if kinds == {"design"}
               else "generated frames" if kinds <= {None, "generate"} else "the brand's own media and new frames")
    form = "reel" if ratio < 0.9 else "film"
    names = [sc["name"] for sc in scenes if sc["start"] is not None]
    listed = [names[0]] + [n[:1].lower() + n[1:] if n[1:2].islower() else n for n in names[1:]] if names else []
    summary = f"A {project.get('aspect') or size_key.replace('x', ':')} {form} from {made_of}."
    if len(listed) > 1:
        summary += " " + ", ".join(listed[:-1]) + " and " + listed[-1] + "."
    facts_y = 452
    s.rule(lx, facts_y, lw, c["rule"])
    sizes = default_sizes(project.get("aspect"))
    facts = [(clock(total, tenths=False), "Runs"), (str(len([x for x in scenes if x["start"] is not None])), "Scenes"),
             (str(len(in_cut)), "Shots"),
             (size_key.replace("x", ":"), ("Plus " + " ".join(z.replace("x", ":") for z in sizes[1:])) if len(sizes) > 1 else "Size")]
    fx = lx
    for value, name in facts:
        width = max(display.width(value, 22), mono.width(name, 8.5, sp, True)) + 26
        s.text(fx, facts_y + 13, width, 28, value, 22, c["ink"], display, lead=26)
        label(s, fx, facts_y + 42, width, name, c["muted"])
        fx += width
    sub_lines = fit(summary, min(lw, 400), 14, body, 3)
    sub_h = len(sub_lines) * 21
    sub_y = facts_y - 26 - sub_h
    s.text(lx, sub_y, min(lw, 400), sub_h + 4, " ".join(sub_lines), 14, c["ink3"], body, lead=21, name="Summary")
    for size in (50, 44, 38, 32):
        title_lines = wrap(title, lw, size, display)
        if len(title_lines) <= 3:
            break
    title_lines = fit(title, lw, size, display, 4)
    lead = size * 1.04
    s.text(lx, sub_y - 14 - len(title_lines) * lead, lw, len(title_lines) * lead + 6, " ".join(title_lines),
           size, c["ink"], display, lead=lead, name="Title")
    for approval in data.get("approvals") or []:
        if approval.get("holds"):
            label(s, lx, 62, lw, f"Approved: the {approval['what']}, by {approval['by']}, {str(approval['at'])[:10]}", c["ink3"])
            break
    s.notes = [title, summary, f"Runs {clock(total, False)}. {len(in_cut)} shots in {len(names)} scenes.",
               "Every word on these slides is text you can edit. The frames are cropped to the plan's aspect; "
               "reset the crop in your app to see the whole picture."]
    slides.append(s)

    # 2. Scene breakdown: one column per scene with its frames filling the column. A wide
    # plan reads better as one row per scene, its frames side by side.
    real = [sc for sc in scenes if sc["start"] is not None]
    tall = ratio < 1
    per_slide = 6 if tall else 5
    for part in range(0, len(real), per_slide):
        group = real[part:part + per_slide]
        s = Slide("Scenes" if part == 0 else f"Scenes {part // per_slide + 1}", c["bg"])
        label(s, M, 30, 600, kicker, c["muted"], 9.5)
        label(s, SW - M - 200, 30, 200, "Scene breakdown", c["muted"], 9.5, align="r")
        n_sc = len(real)
        head = (f"{in_words(n_sc).capitalize()} scene{'s' if n_sc != 1 else ''}, "
                f"{in_words(int(round(total)))} second{'s' if round(total) != 1 else ''}.")
        s.text(M, 54, SW - 2 * M, 40, head, 28, c["ink"], display, lead=34)
        gap, top, bottom = 12, 116, 500
        tiles = [[x for x in sc["shots"] if timed(x) or x["id"] in pictures] for sc in group]

        def scene_head(sc: dict, x: float, y: float, w: float) -> None:
            s.rule(x, y, w, c["ink"])
            s.text(x, y + 9, 40, 26, str(sc["n"]), 22, c["ink"], display, italic=True, lead=24)
            label(s, x, y + 36, w, f"{clock(sc['start'], None)} to {clock(sc['end'], None)}", c["ink3"], 8.5)

        if tall:
            avail = SW - 2 * M - gap * (len(group) - 1)
            min_w = 92

            # The widest frame that lets every column fit: a column is as wide as its frames
            # side by side, and never narrower than its words need.
            def need(tw: float) -> list[float]:
                return [max(len(t) * tw + 4 * (len(t) - 1), min_w) for t in tiles]

            lo, hi = 8.0, (bottom - top - 120) * ratio
            for _ in range(30):
                mid = (lo + hi) / 2
                lo, hi = (mid, hi) if sum(need(mid)) <= avail else (lo, mid)
            tw = lo
            widths = need(tw)
            spare = (avail - sum(widths)) / len(group)
            widths = [w + spare for w in widths]
            # The words are laid out first, so every column's frames start on one line.
            texts = [(fit(sc["name"], w, 15, display, 2), fit(words.scrub(sc["purpose"]), w, 10.5, body, 4))
                     for sc, w in zip(group, widths)]
            name_h = max(len(n) for n, _ in texts) * 17
            frames_top = top + 52 + name_h + 6 + max(len(p) for _, p in texts) * 15 + 14
            x = M
            for sc, w, tile, (name_lines, purpose) in zip(group, widths, tiles, texts):
                scene_head(sc, x, top, w)
                s.text(x, top + 52, w, len(name_lines) * 17 + 2, " ".join(name_lines), 15, c["ink"], display, lead=17)
                s.text(x, top + 58 + name_h, w, len(purpose) * 15 + 2, " ".join(purpose), 10.5, c["ink3"], body, lead=15)
                fh = min(bottom - frames_top, tw / ratio)
                fw = min(fh * ratio, (w - 4 * (len(tile) - 1)) / max(1, len(tile)))
                fx = x
                for shot in tile:
                    frame(s, shot, fx, frames_top, fw, fh, small=fw < 60)
                    fx += fw + 4
                x += w + gap
        else:
            row_h = min(150.0, (bottom - top) / len(group))
            text_x, text_w = M + 96, 300
            fx0 = text_x + text_w + 28
            for k, (sc, tile) in enumerate(zip(group, tiles)):
                y = top + k * row_h
                scene_head(sc, M, y, SW - 2 * M)
                s.text(text_x, y + 11, text_w, 20, sc["name"], 15, c["ink"], display, lead=17)
                purpose = fit(words.scrub(sc["purpose"]), text_w, 10.5, body, max(1, int((row_h - 40) // 15)))
                s.text(text_x, y + 34, text_w, len(purpose) * 15 + 2, " ".join(purpose), 10.5, c["ink3"], body, lead=15)
                fh = row_h - 18
                fw = fh * ratio
                room = SW - M - fx0
                if tile and len(tile) * fw + 6 * (len(tile) - 1) > room:
                    fw = (room - 6 * (len(tile) - 1)) / len(tile)
                    fh = fw / ratio
                fx = fx0
                for shot in tile:
                    frame(s, shot, fx, y + 9, fw, fh, small=fw < 60)
                    fx += fw + 6
        s.notes = [f"Scene {sc['n']}, {sc['name']}, {clock(sc['start'])} to {clock(sc['end'])}: {words.scrub(sc['purpose'])}"
                   for sc in group]
        slides.append(s)

    # 3. One slide per shot: the picture and the script.
    def cut_words(shot: dict) -> str:
        i = shots.index(shot)
        after = shots[i + 1:]
        nxt = next((x for x in after if timed(x)), None)
        bridge = next((x for x in after[:after.index(nxt)] if (x.get("source") or {}).get("type") == "generate"), None) if nxt else None
        move = moves(shot) or "Held"
        if not timed(shot):
            return f"{move}. Optional, not in the cut."
        if not nxt:
            return f"{move}. Last shot: the film ends here."
        if bridge and bridge["clips"]:
            join = f"A generated move carries it into {nxt['n']}."
        elif bridge:
            join = f"Hard cut to {nxt['n']}. An optional generated move could bridge it."
        elif scene_of[nxt["id"]] is not scene_of[shot["id"]]:
            join = f"Hard cut to {nxt['n']}, the next scene."
        else:
            join = f"Hard cut to {nxt['n']}."
        return f"{move}. {join}"

    def notes_for(shot: dict) -> list[tuple[str, str, int]]:
        """(lead word, text, most lines) for the NOTES cell, most useful first."""
        out = []
        critic = words.critic(shot)
        if critic:
            out.append(("Critic", critic.split(": ", 1)[1], 2))
        source = shot.get("source") or {}
        if source.get("why") and source.get("type") in ("own", "design", "generate"):
            out.append(("Picked" if source["type"] != "generate" else "Why", words.scrub(source["why"]), 2))
        flag = next((f for f in shot.get("flags") or [] if f.get("level") in ("weak", "missing")), None)
        if flag:
            out.append(("Needed" if flag["level"] == "missing" else "Check", words.scrub(flag["note"]), 2))
        if shot.get("rationale") and len(out) < 2:
            out.append(("Plan", words.scrub(shot["rationale"]), 2))
        return out

    count = len(shots)
    segs = [(x, x["end"] - x["start"]) for x in in_cut]
    for shot in shown:
        s = Slide(f"Shot {shot['n']}", c["bg"])
        sc = scene_of[shot["id"]]
        if ratio < 0.9:
            pw = min(round(SH * ratio), 432)
            frame(s, shot, 0, 0, pw, SH)
            rx, rw = pw + 52, SW - M - (pw + 52)
            top_y, grid_x, grid_w, cols = 34, rx, rw, 2
        else:
            ph = 300
            pw = min(ph * ratio, 560)
            ph = pw / ratio
            frame(s, shot, 0, 0, pw, ph)
            rx, rw = pw + 40, SW - M - (pw + 40)
            top_y, grid_x, grid_w, cols = 34, M, SW - 2 * M, 4
        label(s, rx, top_y, rw - 110, kicker, c["muted"], 9.5)
        label(s, SW - M - 110, top_y, 110, f"Shot {shot['n']} of {count:02d}", c["muted"], 9.5, align="r")
        num = 92 if cols == 2 else 76
        y = top_y + 22
        s.text(rx - 3, y, rw, num * 0.95, shot["n"], num, c["ink"], display, italic=True, lead=num * 0.92, name="Shot number")
        y += num * 0.95 + 8
        spec = [f"Scene {sc['n']}", sc["name"], shot.get("framing"),
                ANGLE_WORDS.get(shot.get("angle"), shot.get("angle") or "").lower(), (moves(shot) or "").lower()]
        if not timed(shot):
            spec.append("optional")
        spec_lines = fit(" · ".join(v for v in spec if v), rw, 9.5, mono, 2, sp, True)
        s.text(rx, y, rw, 13 * len(spec_lines) + 2, " ".join(spec_lines), 9.5, c["ink3"], mono, spacing=sp, caps=True, lead=13)
        y += 13 * len(spec_lines) + 10
        subject = words.scrub(shot.get("subject") or sc["name"])
        subject = subject[:1].upper() + subject[1:]
        limit_y = (SH - 70) if cols == 2 else ph - 6
        for size in ((28, 24, 21) if cols == 2 else (22, 19, 17)):
            head = wrap(subject, rw, size, display)
            if len(head) <= 2:
                break
        head = fit(subject, rw, size, display, 3 if cols == 2 else max(1, int((limit_y - y) // (size * 1.12))))
        lead = size * 1.12
        s.text(rx, y, rw, len(head) * lead + 4, " ".join(head), size, c["ink"], display, lead=lead, name="Shot title")
        y += len(head) * lead + 16
        if cols == 2:
            s.rule(rx, y, rw, c["rule"])
            y += 18
        else:
            y = max(ph, y) + 22
            s.rule(M, y - 10, SW - 2 * M, c["rule"])

        floor = SH - 54  # the running-time bar sits below this line
        gap_x = 30 if cols == 2 else 24
        cw = (grid_w - gap_x * (cols - 1)) / cols
        said = [words.scrub(o["content"]) for o in shot["overlays"] if o.get("content")]
        vo = words.scrub(shot.get("vo") or "")
        picture_text = words.picture(shot)
        cut_text = cut_words(shot)
        notes = notes_for(shot)

        def cell_label(x: float, y0: float, name: str) -> None:
            label(s, x, y0, cw, name, c["muted"])

        def on_screen(x: float, y0: float, max_h: float) -> float:
            if not said:
                s.text(x, y0, cw, 20, "No on-screen text", 12.5, c["muted"], body, italic=True, lead=18)
                return 18
            yy = y0
            for k, line in enumerate(said):
                size = 19 if k == 0 else 13
                if k == 0 and display.width(line, size) > (cw - 22) * 1.6:
                    size = 16
                lines = fit(line, cw - 22, size, display, 3)
                bw = min(cw, max(display.width(ln, size) for ln in lines) * 1.08 + 24)
                bh = len(lines) * size * 1.16 + 15
                if yy + bh - y0 > max_h and k:
                    break
                s.rect(x, yy, bw, bh, None, c["ink"], 0.75, name="On-screen line")
                s.text(x + 11, yy + 7, bw - 18, bh - 12, " ".join(lines), size, c["ink"], display, lead=size * 1.16, name="On-screen text")
                yy += bh + 6
            return yy - 6 - y0

        def para(x: float, y0: float, text: str, max_lines: int, italic: bool = False, colour: str | None = None,
                 width: float | None = None) -> float:
            lines = fit(text, width or cw, 12.5, body, max_lines)
            s.text(x, y0, width or cw, len(lines) * 18 + 4, " ".join(lines), 12.5, colour or c["ink2"], body,
                   italic=italic, lead=18)
            return len(lines) * 18

        vo_text = f"“{vo}”" if vo else "No voiceover"
        vo_colour = c["ink2"] if vo else c["muted"]
        if cols == 2:
            xs = [grid_x, grid_x + cw + gap_x]
            cell_label(xs[0], y, "On screen")
            cell_label(xs[1], y, "Voiceover")
            h1 = on_screen(xs[0], y + 15, 120)
            h2 = para(xs[1], y + 15, vo_text, 4, italic=bool(vo), colour=vo_colour)
            y += 15 + max(h1, h2) + 16
            cell_label(xs[0], y, "Picture")
            cell_label(xs[1], y, "Cut")
            h1 = para(xs[0], y + 15, picture_text, 3)
            h2 = para(xs[1], y + 15, cut_text, 3)
            y += 15 + max(h1, h2) + 16
        else:
            xs = [grid_x + k * (cw + gap_x) for k in range(4)]
            for xx, name in zip(xs, ("On screen", "Voiceover", "Picture", "Cut")):
                cell_label(xx, y, name)
            h = max(on_screen(xs[0], y + 15, 90), para(xs[1], y + 15, vo_text, 4, italic=bool(vo), colour=vo_colour),
                    para(xs[2], y + 15, picture_text, 3), para(xs[3], y + 15, cut_text, 3))
            y += 15 + h + 14
        room = int((floor - y - 15 + 4) // 18)
        if notes and room >= 1:
            cell_label(grid_x, y, "Notes")
            paras, used = [], 0
            for lead_word, text, most in notes:
                left = int(min(most, room - used))
                if left < 1:
                    break
                lead_text = f"{lead_word}: "
                lines = fit(lead_text + text, grid_w, 12.5, body, left)
                rest = " ".join(lines)[len(lead_text):]
                paras.append([(lead_text, {"colour": c["ink"]}), (rest, {})])
                used += len(lines)
                room -= 0.25  # the space between notes
            s.text(grid_x, y + 15, grid_w, used * 18 + len(paras) * 5 + 4, paras, 12.5, c["ink2"], body, lead=18, gap=4.5,
                   name="Notes")

        # The running time: a segment per shot in the cut, sized by its length.
        bx = rx if cols == 2 else M
        bw = SW - M - bx
        by = SH - 36
        seg_gap = 3
        span = bw - seg_gap * (len(segs) - 1)
        cx = bx
        for other, length in segs:
            w = span * length / total if total else 0
            s.rect(cx, by, max(w, 1), 2.5, c["ink"] if other is shot else c["rule"], name="Running time")
            cx += w + seg_gap
        if timed(shot):
            where = f"{clock(shot['start'])} to {clock(shot['end'])} · {seconds(shot['end'] - shot['start'])} s"
        else:
            where = f"Optional · at {clock(shot.get('start') or 0)} · not in the cut"
        label(s, bx, by + 9, bw / 2, where, c["muted"])
        label(s, bx + bw / 2, by + 9, bw / 2, f"Runs {clock(total, False)}", c["muted"], align="r")

        s.notes = [f"Shot {shot['n']}, scene {sc['n']} ({sc['name']}). "
                   + (f"{clock(shot['start'])} to {clock(shot['end'])}." if timed(shot) else "Optional, not in the cut.")]
        s.notes.append("What we see: " + words.scrub(shot.get("subject") or ""))
        camera = ", ".join(v for v in (FRAMING_WORDS.get(shot.get("framing"), shot.get("framing") or ""),
                                       ANGLE_WORDS.get(shot.get("angle"), shot.get("angle") or ""), moves(shot)) if v)
        if camera:
            s.notes.append("Camera: " + camera + ".")
        s.notes.append("On screen: " + (" / ".join(said) if said else "nothing."))
        s.notes.append("Voiceover: " + (vo if vo else "none."))
        s.notes.append("Picture: " + picture_text + ".")
        s.notes.append("Cut: " + cut_text)
        if shot.get("rationale"):
            s.notes.append("Why this shot: " + words.scrub(shot["rationale"]))
        source = shot.get("source") or {}
        if source.get("why"):
            s.notes.append("Why this picture: " + words.scrub(source["why"]))
        if source.get("considered"):
            s.notes.append(f"Also weighed: {', '.join(words.scrub(x) for x in source['considered'])}.")
        for crit in shot.get("critiques") or []:
            verdict = VERDICT_WORDS.get(str(crit.get("verdict") or "").upper(), str(crit.get("verdict") or "").lower())
            s.notes.append(f"Critic, round {crit.get('round')}: {verdict}.")
            for issue in crit.get("issues") or []:
                if isinstance(issue, dict):
                    s.notes.append(words.scrub(f"{issue.get('layer') or 'Note'} ({issue.get('severity') or 'note'}): "
                                               f"{issue.get('note') or ''}" + (f" Fix: {issue['fix']}" if issue.get("fix") else "")))
        for flag in shot.get("flags") or []:
            s.notes.append(words.scrub(f"Flag: {flag.get('short') or flag.get('level')}. {flag.get('note') or ''}"))
        slides.append(s)

    # 4. Script sheet: paper, one row per shot, the optional ones marked.
    def script_note(shot: dict) -> str:
        """The picture in plain words, then what still needs a hand."""
        bits = []
        if not timed(shot):
            bits.append("Optional, not in the cut.")
        source = shot.get("source") or {}
        need = next((f["note"] for f in shot.get("flags") or [] if f.get("level") == "missing"), "")
        if source.get("type") == "missing":
            bits.append("To shoot." + (f" {need}" if need else ""))
        else:
            bits.append(words.picture(shot) + ".")
        crit = shot["critiques"][-1] if shot.get("critiques") else None
        if crit and str(crit.get("verdict")).upper() != "ACCEPT":
            bits.append(words.critic(shot).split(". ", 1)[0] + ".")
        for flag in shot.get("flags") or []:
            if flag.get("level") == "weak" and flag.get("short"):
                bits.append(flag["short"][:1].upper() + flag["short"][1:] + ".")
        return words.scrub(" ".join(bits))

    col_x = {"n": 0, "time": 44, "thumb": 128, "os": 180, "vo": 428, "notes": 650}
    col_w = {"n": 40, "time": 80, "os": 230, "vo": 204, "notes": SW - 2 * M - 650}
    thumb_h = 40 if ratio < 1 else 31.5
    thumb_w = thumb_h * ratio if ratio < 1 else 56
    col_x["os"] = col_x["thumb"] + max(thumb_w, 28) + 16
    col_w["os"] = col_x["vo"] - 14 - col_x["os"]
    rows = []
    for shot in shots:
        os_lines = fit(" / ".join(words.scrub(o["content"]) for o in shot["overlays"] if o.get("content")) or "No on-screen text",
                       col_w["os"], 12, display, 3)
        vo_lines = fit(f"“{words.scrub(shot['vo'])}”" if shot.get("vo") else "No voiceover", col_w["vo"], 10.5, body, 3)
        note_lines = fit(script_note(shot), col_w["notes"], 9.5, body, 4)
        h = max(thumb_h, len(os_lines) * 15, len(vo_lines) * 14, len(note_lines) * 13) + 10
        rows.append((shot, os_lines, vo_lines, note_lines, h))
    pages: list[list] = [[]]
    room = SH - 108 - 48
    used = 0.0
    for row in rows:
        if pages[-1] and (used + row[4] > room or len(pages[-1]) >= 8):
            pages.append([])
            used = 0.0
        pages[-1].append(row)
        used += row[4]
    if len(pages) > 1:
        # The same number of rows on each page, when they fit: 5 and 5 reads better than 8 and 2.
        per = math.ceil(len(rows) / len(pages))
        even = [rows[i:i + per] for i in range(0, len(rows), per)]
        if all(sum(r[4] for r in page_rows) <= room for page_rows in even):
            pages = even
    for k, rows_here in enumerate(pages, 1):
        s = Slide("Script" if k == 1 else f"Script {k}", c["paper"])
        for head_pt in (24, 21, 18):
            if len(wrap(title, 600, head_pt, display)) == 1:
                break
        head = fit(title, 600, head_pt, display, 1)
        s.text(M, 30 + (24 - head_pt) * 0.6, 640, 32, head[0], head_pt, c["p_ink"], display, lead=28, name="Title")
        meta = [" · ".join(v for v in (brand_name, size_key.replace("x", ":")) if v),
                f"{len(shots)} shots · runs {clock(total, False)}" + (f" · page {k} of {len(pages)}" if len(pages) > 1 else "")]
        s.text(SW - M - 260, 30, 260, 26, meta, 8.5, c["p_muted"], mono, spacing=sp, caps=True, align="r", lead=12)
        hy = 82
        for key, name in (("n", "#"), ("time", "Time"), ("os", "On screen"), ("vo", "Voiceover"), ("notes", "Notes")):
            label(s, M + col_x[key], hy, col_w[key], name, c["p_muted"], 8)
        s.rule(M, hy + 16, SW - 2 * M, c["p_ink"])
        y = hy + 22
        for shot, os_lines, vo_lines, note_lines, h in rows_here:
            optional = not timed(shot)
            ink = c["p_muted"] if optional else c["p_ink"]
            # Every cell spans the row and centres its text, so a line that wraps differently
            # in another app still sits on the row's middle.
            cy, ch = y + 2, h - 5
            s.text(M + col_x["n"], cy, col_w["n"], ch, shot["n"], 19, ink, display, italic=True, lead=22, anchor="ctr")
            when = (f"{clock(shot.get('start') or 0)} \u00b7 {shot['end'] - shot['start']:.1f}" if not optional
                    else f"{clock(shot.get('start') or 0)} \u00b7 opt")
            s.text(M + col_x["time"], cy, col_w["time"], ch, when, 9, c["p_ink3"], mono, spacing=0.04, caps=True, lead=12,
                   anchor="ctr")
            frame(s, shot, M + col_x["thumb"], y + (h - thumb_h) / 2 - 1, thumb_w, thumb_h, paper=True, small=True)
            s.text(M + col_x["os"], cy, col_w["os"], ch, " ".join(os_lines), 12,
                   ink if any(o.get("content") for o in shot["overlays"]) else c["p_muted"], display, lead=15, anchor="ctr")
            s.text(M + col_x["vo"], cy, col_w["vo"], ch, " ".join(vo_lines), 10.5,
                   c["p_ink2"] if shot.get("vo") else c["p_muted"], body, italic=bool(shot.get("vo")), lead=14, anchor="ctr")
            s.text(M + col_x["notes"], cy, col_w["notes"], ch, " ".join(note_lines), 9.5,
                   c["p_muted"] if not optional else c["p_ink3"], body, lead=13, anchor="ctr")
            y += h
            s.rule(M, y - 1, SW - 2 * M, c["p_rule"])
        optional_n = sum(1 for x in shots if not timed(x))
        label(s, M, SH - 30, 500, f"{optional_n} optional shot{'s' if optional_n != 1 else ''} listed, not in the cut"
              if optional_n else "Every shot is in the cut", c["p_muted"])
        label(s, SW - M - 200, SH - 30, 200, "Exported by Shotkit", c["p_muted"], align="r")
        s.notes = ["The script, shot by shot: time, on-screen text, voiceover and what the picture is. Optional shots are "
                   "listed but are not in the cut. It is on paper so it prints."]
        slides.append(s)

    # 5. The brand lock: the palette, the typefaces and what holds in every shot.
    s = Slide("Brand lock", c["bg"])
    label(s, M, 30, 600, " · ".join(v for v in (brand_name, "Brand lock") if v), c["muted"], 9.5)
    label(s, SW - M - 200, 30, 200, "Holds in every shot", c["muted"], 9.5, align="r")
    s.text(M, 54, SW - 2 * M, 40, f"{brand_name or 'The brand'}, locked.", 28, c["ink"], display, lead=34)
    palette = [p for p in data["brand"].get("palette") or [] if HEX_RE.fullmatch(str(p.get("hex") or ""))][:8]
    if palette:
        gap = 12
        sw_w = min(120, (SW - 2 * M - gap * (len(palette) - 1)) / len(palette))
        for i, row in enumerate(palette):
            x = M + i * (sw_w + gap)
            s.rule(x, 116, sw_w, c["ink"])
            s.rect(x, 126, sw_w, 58, row["hex"].lstrip("#").upper(), c["rule"], name=f"Swatch {row['hex']}")
            label(s, x, 192, sw_w, "#" + row["hex"].lstrip("#").upper(), c["ink"], 8.5)
            label(s, x, 205, sw_w, fit(str(row.get("role") or ""), sw_w, 8, mono, 1, sp, True)[0], c["muted"], 8)
            use = fit(str(row.get("use") or ""), sw_w, 9.5, body, 3)
            s.text(x, 222, sw_w, len(use) * 13 + 2, " ".join(use), 9.5, c["ink3"], body, lead=13)
    ty = 300
    s.rule(M, ty, SW - 2 * M, c["rule"])
    tw_col = 260
    faces = [("Display", fonts.get("display_font"), display), ("Body", fonts.get("body_font"), body),
             ("Labels", fonts.get("mono_font") or mono.family, mono)]
    yy = ty + 16
    for name, spec, face in faces:
        if not spec:
            continue
        s.text(M, yy - 2, 64, 40, "Aa", 30, c["ink"], face, lead=34)
        label(s, M + 72, yy + 2, tw_col - 72, name, c["muted"])
        s.text(M + 72, yy + 16, tw_col - 72, 18, board.css_family(spec) or spec, 12.5, c["ink2"], body, lead=16)
        yy += 56
    lock = data.get("series_lock") or {}
    fields = [(k.replace("_", " ").capitalize().replace("Color", "Colour"), lock.get(k))
              for k in ("character", "environment", "lighting", "color_grade") if lock.get(k)]
    gx = M + tw_col + 40
    gw = SW - M - gx
    cw = (gw - 30) / 2
    for i, (name, value) in enumerate(fields):
        x = gx + (i % 2) * (cw + 30)
        y = ty + 16 + (i // 2) * 92
        label(s, x, y, cw, name, c["muted"])
        lines = fit(words.scrub(value), cw, 12, body, 4)
        s.text(x, y + 16, cw, len(lines) * 17 + 2, " ".join(lines), 12, c["ink2"], body, lead=17)
    slides.append(s)

    s.notes = [f"The brand lock for {brand_name or 'this brand'}: "
               + ", ".join(f"{p.get('role')} {p['hex']}" for p in palette) + "."] if palette else []
    s.notes += [f"{name} type: {board.css_family(spec) or spec}." for name, spec, _ in faces if spec]
    s.notes += [f"{name}: {words.scrub(value)}" for name, value in fields]

    out = dest / "storyboard.pptx"
    write_pptx(out, slides, title, str(data["rendered_at"]), theme_xml(c, display, body), master_xml(c))
    return {"file": str(out), "slides": len(slides), "with_text": True,
            "missing": [x["id"] for x in shots if not x["frames"]]}


# --------------------------------------------------------------------------
# Rough cut
# --------------------------------------------------------------------------

def make_cut(page: Page, dest: Path, scratch: Path, music: Path | None) -> dict:
    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        raise Stop("the rough cut needs ffmpeg, and it was not found. Install it (on a Mac: brew install ffmpeg) and run this again.")
    if music and not music.is_file():
        raise Stop(f"no music file at {music}")
    shots, missing = framed(page.shots)
    usable = [s for s in shots if isinstance(s.get("start"), (int, float)) and isinstance(s.get("end"), (int, float)) and s["end"] > s["start"]]
    if not usable:
        raise Stop("no shot has both a frame and a length, so there is nothing to cut together")
    size = SIZES[plan_size(page.data["project"].get("aspect"))]
    w, h = size
    work = scratch / "cut"
    work.mkdir(exist_ok=True)
    text_missing = False
    segments = []
    for shot in usable:
        length = round(float(shot["end"]) - float(shot["start"]), 3)
        source = shot.get("source") or {}
        clip = page.out_dir / shot["clips"][-1]["path"] if shot["clips"] else None
        cmd = [ffmpeg, "-v", "error", "-y"]
        if clip:
            if isinstance(source.get("in"), float) and source["in"] > 0:
                cmd += ["-ss", f"{source['in']:.3f}"]
            cmd += ["-t", f"{length:.3f}", "-i", str(clip)]
        else:
            cmd += ["-loop", "1", "-framerate", str(FPS), "-t", f"{length:.3f}", "-i", str(page.out_dir / shot["frames"][-1]["path"])]
        graph = [f"[0:v]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},setsar=1,fps={FPS},"
                 f"tpad=stop_mode=clone:stop_duration={length:.3f},trim=duration={length:.3f},format=yuv420p[v0]"]
        last, layers = "v0", []
        overlays = [o for o in shot["overlays"] if o.get("content")]
        if overlays and page.browser:
            spans = []
            for o in overlays:
                a = o.get("enter_at") if isinstance(o.get("enter_at"), (int, float)) else shot["start"]
                b = o.get("exit_at") if isinstance(o.get("exit_at"), (int, float)) else shot["end"]
                a, b = max(0.0, a - shot["start"]), min(length, b - shot["start"])
                if b <= a:
                    a, b = 0.0, length
                spans.append((o, a, b))
            shade = work / f"{shot['id']}-shade.png"
            if page.shoot(shot["id"], shade, size, layer="field"):
                layers.append((shade, min(a for _, a, _ in spans), max(b for _, _, b in spans), True, True))
            for o, a, b in spans:
                png = work / f"{shot['id']}-{o['id']}.png"
                if page.shoot(shot["id"], png, size, layer="text", only=o["id"]):
                    layers.append((png, a, b, "fade" in str(o.get("enter_animation") or ""), "fade" in str(o.get("exit_animation") or "")))
                else:
                    text_missing = True
        elif overlays:
            text_missing = True
        for i, (png, a, b, fade_in, fade_out) in enumerate(layers, 1):
            cmd += ["-loop", "1", "-framerate", str(FPS), "-t", f"{length:.3f}", "-i", str(png)]
            chain = f"[{i}:v]format=rgba"
            if fade_in:
                chain += f",fade=t=in:st={a:.3f}:d=0.2:alpha=1"
            if fade_out:
                chain += f",fade=t=out:st={max(a, b - 0.2):.3f}:d=0.2:alpha=1"
            graph.append(chain + f"[t{i}]")
            graph.append(f"[{last}][t{i}]overlay=0:0:enable='between(t,{a:.3f},{b:.3f})':format=auto[v{i}]")
            last = f"v{i}"
        seg = work / f"{shot['id']}.mp4"
        cmd += ["-filter_complex", ";".join(graph), "-map", f"[{last}]", "-an", "-r", str(FPS), "-c:v", "libx264",
                "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-t", f"{length:.3f}", str(seg)]
        done = subprocess.run(cmd, capture_output=True, text=True)
        if done.returncode != 0 or not seg.is_file():
            raise Stop(f"ffmpeg could not make {shot['id']}: " + (done.stderr.strip().splitlines() or ["no message"])[-1])
        segments.append((seg, length))
    listing = work / "list.txt"
    listing.write_text("".join(f"file '{seg.as_posix()}'\n" for seg, _ in segments), encoding="utf-8")
    total = round(sum(length for _, length in segments), 3)
    out = dest / "rough-cut.mp4"
    cmd = [ffmpeg, "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(listing)]
    if music:
        fade_at = max(0.0, total - 0.6)
        cmd += ["-stream_loop", "-1", "-i", str(music), "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                "-af", f"afade=t=out:st={fade_at:.3f}:d=0.6", "-t", f"{total:.3f}"]
    else:
        cmd += ["-map", "0:v", "-c:v", "copy", "-an"]
    cmd += ["-movflags", "+faststart", str(out)]
    done = subprocess.run(cmd, capture_output=True, text=True)
    if done.returncode != 0 or not out.is_file():
        raise Stop("ffmpeg could not join the shots: " + (done.stderr.strip().splitlines() or ["no message"])[-1])
    return {"file": str(out), "seconds": total, "shots": len(segments), "missing": missing,
            "clips": sum(1 for s in usable if s["clips"]), "text": not text_missing, "music": bool(music)}


# --------------------------------------------------------------------------
# The hand-off for a shoot and an edit
# --------------------------------------------------------------------------

# The plan stores a shot in short codes. A crew and an editor read the full words.
FRAMING_WORDS = {"ECU": "Extreme close-up", "CU": "Close-up", "MCU": "Medium close-up", "MS": "Medium shot",
                 "MLS": "Medium long shot", "WS": "Wide shot", "EWS": "Extreme wide shot"}
ANGLE_WORDS = {"eye-level": "Eye level", "high": "High angle", "low": "Low angle", "overhead": "Overhead", "dutch": "Dutch tilt"}
MOTION_WORDS = {"static": "Locked off", "push": "Push in", "pull": "Pull out", "pan-left": "Pan left", "pan-right": "Pan right",
                "tilt-up": "Tilt up", "tilt-down": "Tilt down", "handheld": "Handheld", "orbit": "Orbit", "whip": "Whip pan",
                "rack": "Rack focus"}
FOCUS_WORDS = {"shallow": "Shallow focus", "deep": "Deep focus", "rack": "Rack focus"}


def timecode(seconds_in: float, fps: int = FPS, hour: int = 0) -> str:
    frames = int(round(seconds_in * fps))
    s, f = divmod(frames, fps)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{h + hour:02d}:{m:02d}:{s:02d}:{f:02d}"


def srt_time(seconds_in: float) -> str:
    ms = int(round(seconds_in * 1000))
    s, ms = divmod(ms, 1000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def make_edit(page: Page, dest: Path) -> dict:
    import csv
    import io

    shots = [s for s in page.shots if isinstance(s.get("start"), (int, float)) and isinstance(s.get("end"), (int, float))]
    if not shots:
        raise Stop("there is no timed plan in this folder yet, so there is nothing to hand off")
    folder = dest / "edit"
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir(parents=True)
    title = page.data["project"].get("title") or "Storyboard"

    # 1. The shot list, in a crew's words.
    out = io.StringIO()
    rows = csv.writer(out, lineterminator="\n")
    rows.writerow(["Shot", "Beat", "In", "Out", "Seconds", "Size", "Angle", "Move", "Focus", "What we see", "On screen", "Voice", "Sound", "Picture", "File"])
    for s in shots:
        source = s.get("source") or {}
        picture = {"own": "Your footage", "design": "Drawn in code", "generate": "To generate", "missing": "To shoot"}.get(source.get("type"), "To generate")
        file = (s["clips"][-1]["path"] if s["clips"] else s["frames"][-1]["path"] if s["frames"] else "")
        rows.writerow([
            s["n"], s.get("beat") or "", timecode(s["start"]), timecode(s["end"]), f"{s['end'] - s['start']:g}",
            FRAMING_WORDS.get(s.get("framing"), s.get("framing") or ""), ANGLE_WORDS.get(s.get("angle"), s.get("angle") or ""),
            MOTION_WORDS.get(s.get("motion"), s.get("motion") or ""), FOCUS_WORDS.get(s.get("depth_of_field"), s.get("depth_of_field") or ""),
            s.get("subject") or "", " / ".join(o["content"] for o in s["overlays"] if o.get("content")), s.get("vo") or "", s.get("sfx") or "",
            picture, file,
        ])
    (folder / "shot-list.csv").write_text(out.getvalue(), encoding="utf-8")

    # 2. Every on-screen line at its planned time, as subtitles an editor can import.
    cues = []
    for s in shots:
        for o in s["overlays"]:
            if not o.get("content"):
                continue
            a = o.get("enter_at") if isinstance(o.get("enter_at"), (int, float)) else s["start"]
            b = o.get("exit_at") if isinstance(o.get("exit_at"), (int, float)) else s["end"]
            if b > a:
                cues.append((a, b, str(o["content"])))
    cues.sort()
    (folder / "text.srt").write_text(
        "".join(f"{i}\n{srt_time(a)} --> {srt_time(b)}\n{text}\n\n" for i, (a, b, text) in enumerate(cues, 1)), encoding="utf-8")

    # 3. The cut as an edit decision list (CMX 3600). The record side starts at hour one.
    lines = [f"TITLE: {title[:60]}", "FCM: NON-DROP FRAME", ""]
    events = [s for s in shots if s["end"] > s["start"]]   # an optional shot with no length is listed, not cut
    for i, s in enumerate(events, 1):
        length = s["end"] - s["start"]
        source = s.get("source") or {}
        src_in = float(source["in"]) if s["clips"] and isinstance(source.get("in"), float) else 0.0
        name = Path(s["clips"][-1]["path"] if s["clips"] else s["frames"][-1]["path"] if s["frames"] else f"{s['id']} (to make)").name
        lines.append(f"{i:03d}  AX       V     C        {timecode(src_in)} {timecode(src_in + length)} "
                     f"{timecode(s['start'], hour=1)} {timecode(s['end'], hour=1)}")
        lines.append(f"* FROM CLIP NAME: {name}")
        lines.append(f"* COMMENT: {s['id']} {s.get('beat') or ''}".rstrip())
        lines.append("")
    (folder / "cut.edl").write_text("\n".join(lines), encoding="utf-8")

    archive = dest / "edit.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(folder.iterdir()):
            zf.write(path, f"edit/{path.name}")
    return {"files": [str(p) for p in sorted(folder.iterdir())], "archive": str(archive), "shots": len(shots), "lines": len(cues),
            "missing": [s["id"] for s in shots if not s["frames"] and not s["clips"]]}


# --------------------------------------------------------------------------
# Run
# --------------------------------------------------------------------------

def default_sizes(aspect: str | None) -> list[str]:
    own = plan_size(aspect)
    w, h = SIZES[own]
    return [own, "4x5"] if w / h < 0.8 else [own]


def export(out_dir: Path, what: list[str], sizes: list[str] | None = None, music: Path | None = None,
           browser: str | None = "find") -> dict:
    """Make the asked-for files. Returns what was made, and `skipped` for what could not be."""
    out_dir = out_dir.resolve()
    if not (out_dir / "shots.json").is_file():
        raise Stop(f"no shots.json in {out_dir}")
    dest = out_dir / "export"
    dest.mkdir(exist_ok=True)
    asked = what or list(WHAT)
    report: dict = {"folder": str(dest), "skipped": []}
    with tempfile.TemporaryDirectory() as tmp:
        scratch = Path(tmp)
        page = Page(out_dir, scratch, find_browser() if browser == "find" else browser)
        for kind in asked:
            try:
                if kind == "stills":
                    report["stills"] = make_stills(page, dest, sizes or default_sizes(page.data["project"].get("aspect")))
                elif kind == "deck":
                    report["deck"] = make_deck(page, dest, scratch)
                elif kind == "cut":
                    report["cut"] = make_cut(page, dest, scratch, music)
                elif kind == "edit":
                    report["edit"] = make_edit(page, dest)
            except Stop as stop:
                if what:  # asked for by name: it is an error, not something to skip
                    raise
                report["skipped"].append(f"{kind}: {stop}")
    return report


def say(report: dict, out_dir: Path) -> None:
    def rel(path: str) -> str:
        try:
            return str(Path(path).relative_to(out_dir.resolve()))
        except ValueError:
            return path

    if "stills" in report:
        r = report["stills"]
        per = len(r["files"]) // len(r["sizes"])
        print(f"  stills   {per} shots at {', '.join(r['sizes'])}. {rel(r['archive'])}")
        if r["missing"]:
            print(f"           left out, no frame yet: {', '.join(r['missing'])}")
    if "deck" in report:
        r = report["deck"]
        print(f"  deck     {r['slides']} slides. {rel(r['file'])}")
        if r["missing"]:
            print(f"           no frame yet, so the slide shows a panel that says what is still to make: {', '.join(r['missing'])}")
    if "cut" in report:
        r = report["cut"]
        print(f"  cut      {r['seconds']:g} seconds, {r['shots']} shots, {r['clips']} of them clips. {rel(r['file'])}")
        if r["missing"]:
            print(f"           left out, no frame yet: {', '.join(r['missing'])}")
        if not r["text"]:
            print("           without the on-screen text, which needs Chrome installed.")
    if "edit" in report:
        r = report["edit"]
        print(f"  edit     a shot list of {r['shots']} shots, {r['lines']} lines of text as subtitles, and an edit decision list. {rel(r['archive'])}")
        if r["missing"]:
            print(f"           no picture yet, named in the list as to make: {', '.join(r['missing'])}")
    for line in report["skipped"]:
        print(f"  skipped  {line}")


# --------------------------------------------------------------------------
# Selftest
# --------------------------------------------------------------------------

def selftest() -> int:
    import json
    import xml.dom.minidom

    worked = Path(__file__).resolve().parent.parent / "skills" / "visual-asset-critic" / "examples" / "worked-run"
    checks: list[tuple[str, bool]] = []
    notes: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        run = Path(tmp) / "run"
        shutil.copytree(worked, run)
        before = {str(p.relative_to(run)) for p in run.rglob("*") if p.is_file()}

        # The deck needs nothing but Python, so it is checked with no browser at all.
        report = export(run, ["deck"], browser=None)
        deck = Path(report["deck"]["file"])
        with zipfile.ZipFile(deck) as zf:
            names = set(zf.namelist())
            parsed = True
            for name in names:
                if name.endswith((".xml", ".rels")):
                    try:
                        xml.dom.minidom.parseString(zf.read(name))
                    except Exception:
                        parsed = False
            targets_ok = True
            for name in names:
                if not name.endswith(".rels") or name == "_rels/.rels":
                    continue
                base = Path(name).parent.parent
                for target in re.findall(r'Target="([^"]+)"', zf.read(name).decode()):
                    resolved = os.path.normpath(str(base / target)).replace(os.sep, "/")
                    if resolved not in names:
                        targets_ok = False
            types = zf.read("[Content_Types].xml").decode()
            slide_count = len([n for n in names if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)])
            built = board.build(run)[0]
            shots_n = len(built["shots"])
            kinds = [re.search(r'<p:cSld name="([^"]*)"', zf.read(f"ppt/slides/slide{i}.xml").decode()).group(1)
                     for i in range(1, slide_count + 1)]
            first = zf.read(f"ppt/slides/slide{kinds.index('Shot 01') + 1}.xml").decode()
            spoken = [zf.read(f"ppt/notesSlides/notesSlide{i}.xml").decode() for i in range(1, slide_count + 1)
                      if f"ppt/notesSlides/notesSlide{i}.xml" in names]
        checks.append(("the deck is a zip whose every part is well-formed XML", parsed))
        checks.append(("every part the deck points to is in the deck", targets_ok))
        checks.append(("every slide is declared in the content types", all(f"/ppt/slides/slide{i}.xml" in types for i in range(1, slide_count + 1))))
        checks.append(("the deck has a cover, a scene breakdown, a slide per shot, a script sheet and the brand lock",
                       kinds == ["Cover", "Scenes"] + [f"Shot {s['n']}" for s in built["shots"]] + ["Script", "Brand lock"]))
        checks.append(("a shot's words are real text on its slide, in the brand's faces",
                       "<a:t>" in first and "Shot 01 of 02" in first and 'typeface="Inter"' in first))
        checks.append(("every slide has speaker notes, and a shot's notes carry its full plan",
                       len(spoken) == slide_count and all("<a:p>" in n for n in spoken)
                       and "What we see: founder seated" in spoken[kinds.index("Shot 01")]))

        # A run on the user's own media, with an optional shot that has no length: the
        # picture is named by its file, never by an internal id, and the optional shot is
        # on the script sheet but gets no slide of its own.
        own = Path(tmp) / "own"
        shutil.copytree(worked, own)
        plan = json.loads((own / "shots.json").read_text())
        plan["shots"][0]["source"] = {"type": "own", "media": "m22", "why": "It beat m23 on the light.", "considered": ["m23"]}
        plan["shots"].append({"id": "shot_03", "beat": "promise", "start": 8.0, "end": 8.0, "optional": True,
                              "framing": "CU", "angle": "eye-level", "motion": "static", "subject": "hands on the desk",
                              "rationale": "A close detail, if one is shot.", "vo": None,
                              "source": {"type": "missing", "why": "Nothing in m22 shows the hands."},
                              "flags": [{"level": "missing", "kind": "missing", "short": "not in the library",
                                         "note": "Hands on the desk, close. Not in m22 or m23."}]})
        (own / "shots.json").write_text(json.dumps(plan))
        (own / "media").mkdir()
        (own / "media" / "media.json").write_text(json.dumps({"items": [
            {"id": "m22", "name": "portrait-room_chocolate_back.jpg", "kind": "photo"},
            {"id": "m23", "name": "desk_wide.jpg", "kind": "photo"}]}))
        report = export(own, ["deck"], browser=None)
        with zipfile.ZipFile(report["deck"]["file"]) as zf:
            parts = sorted(n for n in zf.namelist() if re.fullmatch(r"ppt/(slides|notesSlides)/\w+?\d+\.xml", n))
            said = {n: " ".join(re.findall(r"<a:t>([^<]*)</a:t>", zf.read(n).decode())) for n in parts}
            panels = " ".join(zf.read(n).decode() for n in parts if "/slides/" in n)
            own_kinds = [re.search(r'<p:cSld name="([^"]*)"', zf.read(f"ppt/slides/slide{i}.xml").decode()).group(1)
                         for i in range(1, len([n for n in parts if "/slides/" in n]) + 1)]
        everything = " ".join(said.values())
        checks.append(("no slide or note names a picture by an internal id like m22", not MEDIA_ID.search(everything)))
        checks.append(("a picture of yours is named by its file", "Your photo \u00b7 portrait-room chocolate back" in everything))
        checks.append(("a timed shot gets a slide, an optional shot with no length does not",
                       "Shot 01" in own_kinds and "Shot 03" not in own_kinds))
        script = " ".join(v for k, v in said.items() if k == f"ppt/slides/slide{own_kinds.index('Script') + 1}.xml")
        checks.append(("the script sheet lists the optional shot, marked as optional",
                       "03" in script and "Optional, not in the cut" in script))
        checks.append(("a shot with no frame gets a drawn panel, never an empty hole", 'name="Shot 03 panel"' in panels))
        after = {str(p.relative_to(run)) for p in run.rglob("*") if p.is_file()}
        checks.append(("an export writes only inside export/", all(p.startswith("export/") for p in after - before) and before <= after))

        try:
            export(run, ["stills"], browser=None)
            refused = False
        except Stop as stop:
            refused = "Chrome" in str(stop)
        checks.append(("stills with no browser stop with the reason", refused))
        checks.append(("a text with markup in it cannot break a slide", "<b>" not in clean("<b>x</b> & y") and "&amp;" in clean("a & b")))
        checks.append(("a tall plan also gets the 4:5 carousel size, a wide plan does not",
                       default_sizes("9:16") == ["9x16", "4x5"] and default_sizes("16:9") == ["16x9"]))

        report = export(run, ["edit"], browser=None)
        folder = Path(report["edit"]["archive"]).parent / "edit"
        listing = (folder / "shot-list.csv").read_text().splitlines()
        edl = (folder / "cut.edl").read_text()
        checks.append(("the shot list has a row per shot, in a crew's words", len(listing) == shots_n + 1 and "Close-up" in FRAMING_WORDS.values()))
        checks.append(("the edit decision list has an event per shot and starts at hour one", edl.count("* FROM CLIP NAME") == shots_n and "01:00:00:00" in edl))
        checks.append(("the on-screen text is a subtitle file with planned times", "-->" in (folder / "text.srt").read_text()))
        checks.append(("timecode counts frames", timecode(3.5) == "00:00:03:15" and srt_time(3.5) == "00:00:03,500"))

        browser = find_browser()
        if browser:
            try:
                report = export(run, ["stills"], sizes=["4x5"])
            except Stop:
                browser, report = None, None
                notes.append("the browser here did not answer, so the stills were not photographed")
        if browser:
            files = [Path(f) for f in report["stills"]["files"]]
            checks.append(("a still is exactly the size asked for", bool(files) and all(png_size(f) == SIZES["4x5"] for f in files)))
            with zipfile.ZipFile(report["stills"]["archive"]) as zf:
                checks.append(("the stills are also in one zip", len(zf.namelist()) == len(files)))
        elif not notes:
            notes.append("no browser here, so the stills were not photographed")
        if browser and find_ffmpeg():
            report = export(run, ["cut"])
            probe = subprocess.run([shutil.which("ffprobe") or "ffprobe", "-v", "error", "-show_entries", "format=duration",
                                    "-of", "csv=p=0", report["cut"]["file"]], capture_output=True, text=True)
            try:
                length = float(probe.stdout.strip())
            except ValueError:
                length = -1
            checks.append(("the rough cut runs as long as its shots", abs(length - report["cut"]["seconds"]) < 0.2))
        else:
            notes.append("no ffmpeg or no browser here, so the rough cut was not made")

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
    p = argparse.ArgumentParser(description="Turn a run into stills, a deck and a rough cut.")
    p.add_argument("output_dir", nargs="?", type=Path, help="Folder that holds shots.json")
    p.add_argument("what", nargs="*", help="stills, deck, cut. Leave out for everything this computer can make")
    p.add_argument("--size", action="append", choices=sorted(SIZES), help="A still size. Repeat for more. Default: the plan's own, and 4x5 for a tall plan")
    p.add_argument("--music", type=Path, help="A music file to lay under the rough cut")
    p.add_argument("--selftest", action="store_true", help="Prove the tool's guarantees")
    args = p.parse_args()
    if args.selftest:
        return selftest()
    if not args.output_dir:
        p.print_usage()
        return 2
    unknown = [w for w in args.what if w not in WHAT]
    if unknown:
        print(f"shotkit: '{unknown[0]}' is not something to export. Use: {', '.join(WHAT)}", file=sys.stderr)
        return 2
    try:
        report = export(args.output_dir, list(args.what), args.size, args.music)
    except Stop as stop:
        print(f"shotkit: {stop}", file=sys.stderr)
        return 1
    print(f"Exported to {report['folder']}")
    say(report, args.output_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
