#!/usr/bin/env python3
"""Turn a run into files you can post, present and play.

  export.py output/                  everything this computer can make
  export.py output/ stills           one image per shot, with its text on it
  export.py output/ stills --size 4x5 --size 9x16
  export.py output/ deck             a PowerPoint deck, one slide per shot
  export.py output/ cut              a rough cut: the shots in order, as one video
  export.py output/ cut --music track.wav
  export.py output/ edit             the hand-off for a shoot and an edit
  export.py --selftest

Everything is written to output/export/. Nothing else in the folder is changed.

  stills   export/stills-<size>/shot_NN.png and export/stills.zip. The text is drawn by
           the board's own page, so a still looks like the board. Needs Chrome, Edge,
           Brave or Chromium on this computer.
  deck     export/storyboard.pptx. Opens in PowerPoint, Keynote and Google Slides. The
           words on each slide are real text you can edit. Needs nothing. With a
           browser the pictures carry the on-screen text. Without one they are the
           plain frames.
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

EMU = 914400
SLIDE_W, SLIDE_H = 13.333, 7.5
NS = ('xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
      'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"')
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
XML = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'


def emu(inches: float) -> int:
    return int(round(inches * EMU))


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


def deck_colours(brand: dict) -> dict:
    """The deck's ground, ink and accent: the brand's own when they read, plain dark when not."""
    found = {}
    for row in brand.get("palette") or []:
        role = str(row.get("role") or "").lower()
        hex_val = str(row.get("hex") or "")
        if not HEX_RE.fullmatch(hex_val):
            continue
        for key in ("background", "ink", "accent"):
            if role.startswith(key) and key not in found:
                found[key] = hex_val.lstrip("#").upper()
    bg, ink = found.get("background", "0E0F12"), found.get("ink", "F3F2EE")
    if contrast(bg, ink) < 4.5:
        bg, ink = "0E0F12", "F3F2EE"
    accent = found.get("accent", "FF5A2B")
    if contrast(bg, accent) < 2:
        accent = ink
    return {"bg": bg, "ink": ink, "accent": accent, "muted": mix(ink, bg, 0.62), "line": mix(ink, bg, 0.22)}


def clean(text) -> str:
    """Text that is safe inside XML: no control characters, and escaped."""
    return escape(re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", str(text if text is not None else "")))


def lines_for(text: str, width_in: float, pt: float, factor: float = 0.5) -> int:
    """About how many lines a text takes in a box. `factor` is a glyph's width over its size."""
    per_line = max(int(width_in * 72 / (pt * factor)), 8)
    total = 0
    for para in str(text).split("\n"):
        total += max(1, math.ceil(len(para) / per_line))
    return total


def shorten(text: str, width_in: float, pt: float, max_lines: int) -> str:
    text = " ".join(str(text or "").split())
    per_line = max(int(width_in * 72 / (pt * 0.5)), 8)
    limit = per_line * max_lines - 2
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip(",;:. ")
    return cut + "..."


class Slide:
    """One slide: a ground colour and the shapes on it."""

    def __init__(self, colours: dict):
        self.c = colours
        self.shapes: list[str] = []
        self.media: list[tuple[str, Path]] = []
        self.next_id = 2

    def _id(self) -> int:
        self.next_id += 1
        return self.next_id - 1

    def text(self, x: float, y: float, w: float, h: float, runs, pt: float, colour: str | None = None,
             bold: bool = False, font: str | None = None, spacing: int = 0, align: str = "l",
             line: int = 100, anchor: str = "t", caps: bool = False) -> None:
        """`runs` is one string, or a list of paragraphs."""
        paras = runs if isinstance(runs, list) else [runs]
        colour = colour or self.c["ink"]
        face = f'<a:latin typeface="{clean(font)}"/><a:cs typeface="{clean(font)}"/>' if font else ""
        cap = ' cap="all"' if caps else ""
        body = ""
        for para in paras:
            rpr = (f'<a:rPr lang="en-US" sz="{int(pt * 100)}" b="{1 if bold else 0}" spc="{spacing}"{cap} dirty="0">'
                   f'<a:solidFill><a:srgbClr val="{colour}"/></a:solidFill>{face}</a:rPr>')
            body += (f'<a:p><a:pPr algn="{align}"><a:lnSpc><a:spcPct val="{line * 1000}"/></a:lnSpc></a:pPr>'
                     f'<a:r>{rpr}<a:t>{clean(para)}</a:t></a:r></a:p>')
        n = self._id()
        self.shapes.append(
            f'<p:sp><p:nvSpPr><p:cNvPr id="{n}" name="Text {n}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr>'
            f'<p:txBody><a:bodyPr wrap="square" lIns="0" tIns="0" rIns="0" bIns="0" anchor="{anchor}"><a:noAutofit/></a:bodyPr>'
            f'<a:lstStyle/>{body}</p:txBody></p:sp>')

    def rect(self, x: float, y: float, w: float, h: float, fill: str | None, outline: str | None = None) -> None:
        n = self._id()
        paint = f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>' if fill else "<a:noFill/>"
        edge = (f'<a:ln w="9525"><a:solidFill><a:srgbClr val="{outline}"/></a:solidFill></a:ln>' if outline
                else "<a:ln><a:noFill/></a:ln>")
        self.shapes.append(
            f'<p:sp><p:nvSpPr><p:cNvPr id="{n}" name="Shape {n}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>{paint}{edge}</p:spPr>'
            f'<p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:endParaRPr lang="en-US"/></a:p></p:txBody></p:sp>')

    def picture(self, x: float, y: float, w: float, h: float, path: Path, name: str) -> None:
        n = self._id()
        rid = f"rId{len(self.media) + 2}"
        self.media.append((rid, path))
        self.shapes.append(
            f'<p:pic><p:nvPicPr><p:cNvPr id="{n}" name="{clean(name)}" descr="{clean(name)}"/>'
            f'<p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr>'
            f'<p:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>'
            f'<p:spPr><a:xfrm><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic>')

    def xml(self) -> str:
        return (XML + f'<p:sld {NS}><p:cSld><p:bg><p:bgPr><a:solidFill><a:srgbClr val="{self.c["bg"]}"/></a:solidFill>'
                '<a:effectLst/></p:bgPr></p:bg><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/>'
                '</p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/>'
                '<a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>' + "".join(self.shapes)
                + '</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>')


THEME = (XML + '<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Shotkit">'
         '<a:themeElements><a:clrScheme name="Shotkit"><a:dk1><a:srgbClr val="000000"/></a:dk1><a:lt1><a:srgbClr val="FFFFFF"/></a:lt1>'
         '<a:dk2><a:srgbClr val="1F2328"/></a:dk2><a:lt2><a:srgbClr val="F3F2EE"/></a:lt2>'
         '<a:accent1><a:srgbClr val="FF5A2B"/></a:accent1><a:accent2><a:srgbClr val="2F6FED"/></a:accent2>'
         '<a:accent3><a:srgbClr val="2EB67D"/></a:accent3><a:accent4><a:srgbClr val="E0A100"/></a:accent4>'
         '<a:accent5><a:srgbClr val="8A63D2"/></a:accent5><a:accent6><a:srgbClr val="6B7280"/></a:accent6>'
         '<a:hlink><a:srgbClr val="2F6FED"/></a:hlink><a:folHlink><a:srgbClr val="8A63D2"/></a:folHlink></a:clrScheme>'
         '<a:fontScheme name="Shotkit"><a:majorFont><a:latin typeface="Arial"/><a:ea typeface=""/><a:cs typeface=""/></a:majorFont>'
         '<a:minorFont><a:latin typeface="Arial"/><a:ea typeface=""/><a:cs typeface=""/></a:minorFont></a:fontScheme>'
         '<a:fmtScheme name="Shotkit"><a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
         '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst>'
         '<a:lnStyleLst><a:ln w="6350"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>'
         '<a:ln w="12700"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>'
         '<a:ln w="19050"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst>'
         '<a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst/></a:effectStyle>'
         '<a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst>'
         '<a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
         '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst></a:fmtScheme></a:themeElements></a:theme>')

EMPTY_TREE = ('<p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm>'
              '<a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree>')
MASTER = (XML + f'<p:sldMaster {NS}><p:cSld><p:bg><p:bgRef idx="1001"><a:schemeClr val="bg1"/></p:bgRef></p:bg>{EMPTY_TREE}</p:cSld>'
          '<p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" '
          'accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>'
          '<p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>'
          '<p:txStyles><p:titleStyle><a:lvl1pPr><a:defRPr sz="4400"/></a:lvl1pPr></p:titleStyle>'
          '<p:bodyStyle><a:lvl1pPr><a:defRPr sz="1800"/></a:lvl1pPr></p:bodyStyle>'
          '<p:otherStyle><a:lvl1pPr><a:defRPr sz="1800"/></a:lvl1pPr></p:otherStyle></p:txStyles></p:sldMaster>')
LAYOUT = (XML + f'<p:sldLayout {NS} type="blank" preserve="1"><p:cSld name="Blank">{EMPTY_TREE}</p:cSld>'
          '<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>')


def rels(entries: list[tuple[str, str, str]]) -> str:
    rows = "".join(f'<Relationship Id="{rid}" Type="{REL}/{kind}" Target="{target}"/>' for rid, kind, target in entries)
    return XML + f'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{rows}</Relationships>'


def write_pptx(dest: Path, slides: list[Slide], title: str, created: str) -> None:
    media_names: dict[Path, str] = {}
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
            zf.writestr(f"ppt/slides/slide{i}.xml", slide.xml())
            zf.writestr(f"ppt/slides/_rels/slide{i}.xml.rels", rels(entries))
            overrides += (f'<Override PartName="/ppt/slides/slide{i}.xml" '
                          'ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>')
            slide_rels.append((f"rId{i + 2}", "slide", f"slides/slide{i}.xml"))
        ids = "".join(f'<p:sldId id="{255 + i}" r:id="rId{i + 2}"/>' for i in range(1, len(slides) + 1))
        zf.writestr("ppt/presentation.xml", XML + (
            f'<p:presentation {NS} saveSubsetFonts="1"><p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>'
            f'<p:sldIdLst>{ids}</p:sldIdLst><p:sldSz cx="{emu(SLIDE_W)}" cy="{emu(SLIDE_H)}"/>'
            '<p:notesSz cx="6858000" cy="9144000"/></p:presentation>'))
        zf.writestr("ppt/_rels/presentation.xml.rels", rels(
            [("rId1", "slideMaster", "slideMasters/slideMaster1.xml"), ("rId2", "theme", "theme/theme1.xml")] + slide_rels))
        zf.writestr("ppt/theme/theme1.xml", THEME)
        zf.writestr("ppt/slideMasters/slideMaster1.xml", MASTER)
        zf.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", rels(
            [("rId1", "slideLayout", "../slideLayouts/slideLayout1.xml"), ("rId2", "theme", "../theme/theme1.xml")]))
        zf.writestr("ppt/slideLayouts/slideLayout1.xml", LAYOUT)
        zf.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", rels([("rId1", "slideMaster", "../slideMasters/slideMaster1.xml")]))
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
            '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>'
            '<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>'
            '<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>'
            '<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>'
            '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
            + overrides + '</Types>'))


STATUS_WORDS = {"plan": "Needs a prompt", "frame": "Needs a frame", "check": "Not checked yet", "revise": "Sent back to revise", "accept": "Accepted"}


def seconds(value) -> str:
    if not isinstance(value, (int, float)):
        return "?"
    return str(int(value)) if float(value).is_integer() else f"{value:.1f}"


def deck_pictures(page: Page, scratch: Path, size: tuple[int, int]) -> tuple[dict[str, Path], bool]:
    """
    A picture for each shot. With a browser it is the still with its text, and a shot with
    no frame yet gets its planned text on the brand's ground. Without one it is the plain
    frame, for the shots that have one.
    """
    shots, _ = framed(page.shots)
    pictures: dict[str, Path] = {}
    with_text = False
    if page.browser:
        folder = scratch / "deck"
        folder.mkdir(exist_ok=True)
        jobs = [(s["id"], folder / f"{s['id']}.png", size) for s in page.shots]
        done = page.shoot_all(jobs)
        with_text = bool(done) and all(done)
        if with_text:
            pictures = {job[0]: job[1] for job in jobs}
    if not pictures:
        for shot in shots:
            path = page.out_dir / shot["frames"][-1]["path"]
            if path.suffix.lower() in (".png", ".jpg", ".jpeg"):
                pictures[shot["id"]] = path
    ffmpeg = find_ffmpeg()
    if ffmpeg and with_text:
        # A photograph of a page is a large PNG. A JPEG keeps the deck small enough to email.
        for shot_id, path in list(pictures.items()):
            small = path.with_suffix(".jpg")
            done = subprocess.run([ffmpeg, "-v", "error", "-y", "-i", str(path), "-q:v", "3", str(small)], capture_output=True)
            if done.returncode == 0 and small.is_file():
                pictures[shot_id] = small
    return pictures, with_text


def make_deck(page: Page, dest: Path, scratch: Path) -> dict:
    data = page.data
    shots = data["shots"]
    if not shots:
        raise Stop("there is no plan in this folder yet, so there is nothing to put in a deck")
    c = deck_colours(data["brand"])
    fonts = data["brand"].get("fonts") or {}
    display = board.css_family(fonts.get("display_font")) or "Arial"
    body = board.css_family(fonts.get("body_font")) or "Arial"
    project = data["project"]
    size_key = plan_size(project.get("aspect"))
    px = SIZES[size_key]
    ratio = px[0] / px[1]
    pictures, with_text = deck_pictures(page, scratch, px)
    title = project.get("title") or "Storyboard"
    total = len(shots)
    slides: list[Slide] = []
    m = 0.6

    def label(slide: Slide, x: float, y: float, w: float, text: str, colour: str | None = None) -> None:
        slide.text(x, y, w, 0.25, text, 11, colour or c["muted"], bold=True, font=body, spacing=140, caps=True)

    def footer(slide: Slide, n: int) -> None:
        slide.text(m, SLIDE_H - 0.45, 8, 0.2, title, 9, c["muted"], font=body)
        slide.text(SLIDE_W - m - 2, SLIDE_H - 0.45, 2, 0.2, f"{n} / {total + 3}", 9, c["muted"], font=body, align="r")

    def place(slide: Slide, shot: dict, x: float, y: float, w: float, h: float) -> None:
        path = pictures.get(shot["id"])
        if path:
            slide.picture(x, y, w, h, path, f"{shot['id']} frame")
        else:
            slide.rect(x, y, w, h, None, c["line"])
            slide.text(x, y + h / 2 - 0.15, w, 0.3, "No frame yet", 10, c["muted"], font=body, align="c")

    # 1. Title
    s = Slide(c)
    first = next((x for x in shots if x["id"] in pictures), None)
    hero_h = SLIDE_H - 2 * m
    hero_w = min(hero_h * ratio, 6.2)
    hero_h = hero_w / ratio
    text_w = SLIDE_W - 2 * m - (hero_w + 0.8 if first else 0)
    s.rect(m, m + 0.02, 0.5, 0.07, c["accent"])
    label(s, m, m + 0.3, text_w, "Storyboard", c["accent"])
    title_pt = 46 if len(title) <= 34 else 36 if len(title) <= 60 else 28
    title_lines = lines_for(title, text_w, title_pt, 0.52)
    s.text(m, m + 0.75, text_w, title_lines * title_pt * 1.08 / 72 + 0.1, title, title_pt, bold=True, font=display, spacing=-60, line=98)
    y = m + 0.95 + title_lines * title_pt * 1.08 / 72
    facts = [f"{seconds(project.get('duration_s'))} seconds" if project.get("duration_s") else None,
             project.get("aspect"), f"{total} shots"]
    s.text(m, y, text_w, 0.3, "   ·   ".join(f for f in facts if f), 14, c["muted"], font=body)
    y += 0.55
    for approval in data.get("approvals") or []:
        if approval.get("holds"):
            s.text(m, y, text_w, 0.3, f"Approved: the {approval['what']}, by {approval['by']}, {str(approval['at'])[:10]}", 12, c["ink"], font=body)
            y += 0.32
    s.text(m, SLIDE_H - m - 0.2, text_w, 0.2, str(data["rendered_at"])[:10], 10, c["muted"], font=body)
    if first:
        place(s, first, SLIDE_W - m - hero_w, (SLIDE_H - hero_h) / 2, hero_w, hero_h)
    slides.append(s)

    # 2. The whole story on one slide
    s = Slide(c)
    label(s, m, m, 6, "The story, shot by shot", c["accent"])
    rows = 1 if total <= 8 else 2
    per_row = math.ceil(total / rows)
    gap = 0.18
    avail_w = SLIDE_W - 2 * m
    row_h = (SLIDE_H - m - 1.15 - 0.55) / rows
    tile_h = row_h - 0.95
    tile_w = min((avail_w - gap * (per_row - 1)) / per_row, tile_h * ratio)
    tile_h = tile_w / ratio
    for i, shot in enumerate(shots):
        row, col = divmod(i, per_row)
        in_row = min(per_row, total - row * per_row)
        x0 = m + (avail_w - (tile_w * in_row + gap * (in_row - 1))) / 2 if rows == 1 else m
        x = x0 + col * (tile_w + gap)
        y = m + 0.55 + row * row_h
        place(s, shot, x, y, tile_w, tile_h)
        s.text(x, y + tile_h + 0.12, tile_w, 0.2, f"{shot['n']}  {shot.get('beat') or ''}".strip(), 9, c["ink"], bold=True, font=body, spacing=80, caps=True)
        said = shot["overlays"][0]["content"] if shot["overlays"] else ""
        if said and tile_w >= 1.1:
            s.text(x, y + tile_h + 0.36, tile_w, 0.45, shorten(said, tile_w, 9, 2), 9, c["muted"], font=body)
    footer(s, 2)
    slides.append(s)

    # 3. One slide per shot
    for n, shot in enumerate(shots, 3):
        s = Slide(c)
        if ratio < 0.9:
            img_h = SLIDE_H - 2 * m - 0.35
            img_w = img_h * ratio
        elif ratio > 1.2:
            img_w = 7.3
            img_h = img_w / ratio
        else:
            img_h = 5.4
            img_w = img_h * ratio
        place(s, shot, m, m, img_w, img_h)
        x = m + img_w + 0.7
        w = SLIDE_W - m - x
        y = m
        when = f"{seconds(shot.get('start'))} to {seconds(shot.get('end'))} s"
        label(s, x, y, w, "   ·   ".join(v for v in (f"Shot {shot['n']}", shot.get("beat"), when) if v), c["accent"])
        y += 0.45
        said = [o["content"] for o in shot["overlays"] if o.get("content") and o.get("treatment") != "lockup"]
        head = "\n".join(said) if said else shorten(shot.get("subject") or "", w, 26, 3)
        head_pt = 40 if said and max(len(t) for t in said) <= 26 else 32 if said and max(len(t) for t in said) <= 40 else 26
        # A heavy display face can run wide, and the deck may open with a fallback font,
        # so the headline is given room for the widest likely setting.
        head_lines = lines_for(head, w, head_pt, 0.66)
        if head_lines > 3:
            head_pt = 26
            head_lines = lines_for(head, w, head_pt, 0.66)
        head_h = head_lines * head_pt * 1.1 / 72
        s.text(x, y, w, head_h + 0.1, head.split("\n"), head_pt, bold=True, font=display, spacing=-40, line=100)
        y += head_h + 0.55
        s.rect(x, y - 0.25, w, 0.01, c["line"])
        fields = []
        if said:
            fields.append(("In the frame", shot.get("subject")))
        camera = ", ".join(str(v) for v in (shot.get("framing"), shot.get("angle"), shot.get("motion")) if v)
        fields.append(("Camera", camera))
        if shot.get("vo"):
            fields.append(("Voice", shot["vo"]))
        fields.append(("Why this shot", shot.get("rationale")))
        source = shot.get("source") or {}
        if source.get("type") == "design":
            fields.append(("Picture", f"Drawn in code from the brand lock, a {source.get('card') or 'card'}"))
        if source.get("type") == "own":
            fields.append(("Picture", "Your own media" + (f", {source['media']}" if source.get("media") else "")))
        status = STATUS_WORDS.get(shot.get("status"), "")
        if shot["critiques"]:
            status += f", round {shot['critiques'][-1].get('round')}"
        fields.append(("Check", status))
        floor = SLIDE_H - m - 0.35
        for name, value in fields:
            if not value:
                continue
            room = int((floor - y - 0.28) / (15 * 1.35 / 72))
            if room < 1:
                break
            value = shorten(value, w, 15, min(room, 4))
            label(s, x, y, w, name)
            height = lines_for(value, w, 15) * 15 * 1.35 / 72
            s.text(x, y + 0.28, w, height + 0.05, value, 15, c["ink"], font=body, line=118)
            y += 0.28 + height + 0.3
        footer(s, n)
        slides.append(s)

    # 4. The brand and the things that hold in every shot
    s = Slide(c)
    label(s, m, m, 6, "Brand lock", c["accent"])
    s.text(m, m + 0.4, 8, 0.6, data["brand"].get("name") or "Brand", 30, bold=True, font=display, spacing=-40)
    palette = [p for p in data["brand"].get("palette") or [] if HEX_RE.fullmatch(str(p.get("hex") or ""))][:7]
    sw = 1.35
    for i, row in enumerate(palette):
        x = m + i * (sw + 0.2)
        s.rect(x, m + 1.35, sw, sw, row["hex"].lstrip("#").upper(), c["line"])
        s.text(x, m + 1.35 + sw + 0.1, sw, 0.2, row["hex"].upper(), 10, c["ink"], bold=True, font=body)
        s.text(x, m + 1.35 + sw + 0.32, sw, 0.2, str(row.get("role") or ""), 10, c["muted"], font=body)
    y = m + 1.35 + sw + 0.95
    col_w = (SLIDE_W - 2 * m - 0.6) / 2
    left = [("Display type", fonts.get("display_font")), ("Body type", fonts.get("body_font"))]
    lock = data.get("series_lock") or {}
    right = [(k.replace("_", " ").capitalize(), lock.get(k)) for k in ("character", "environment", "lighting", "color_grade")]
    def column(rows, x: float, top: float) -> float:
        for name, value in rows:
            if not value:
                continue
            value = shorten(value, col_w, 12, 2)
            label(s, x, top, col_w, name)
            s.text(x, top + 0.24, col_w, 0.5, value, 12, c["ink"], font=body, line=118)
            top += 0.24 + lines_for(value, col_w, 12) * 12 * 1.35 / 72 + 0.2
        return top

    column(left[:1], m, y)
    y = column(left[1:], m + col_w + 0.6, y) + 0.05
    column(right[:2], m, y)
    column(right[2:], m + col_w + 0.6, y)
    footer(s, total + 3)
    slides.append(s)

    out = dest / "storyboard.pptx"
    write_pptx(out, slides, title, str(data["rendered_at"]))
    return {"file": str(out), "slides": len(slides), "with_text": with_text,
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
        picture = {"own": "Your footage", "design": "Drawn in code", "generate": "To generate"}.get(source.get("type"), "To generate")
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
    for i, s in enumerate(shots, 1):
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
        if r["missing"] and r["with_text"]:
            print(f"           no frame yet, so the slide shows the planned text on the brand's ground: {', '.join(r['missing'])}")
        elif r["missing"]:
            print(f"           no frame yet, so the slide has no picture: {', '.join(r['missing'])}")
        if not r["with_text"]:
            print("           the pictures are the plain frames. With Chrome installed they carry the on-screen text.")
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
            shots_n = len(board.build(run)[0]["shots"])
            first = zf.read("ppt/slides/slide3.xml").decode()
        checks.append(("the deck is a zip whose every part is well-formed XML", parsed))
        checks.append(("every part the deck points to is in the deck", targets_ok))
        checks.append(("every slide is declared in the content types", all(f"/ppt/slides/slide{i}.xml" in types for i in range(1, slide_count + 1))))
        checks.append(("the deck has a title, an overview, one slide per shot and a brand slide", slide_count == shots_n + 3))
        checks.append(("a shot's words are real text on its slide", "<a:t>" in first and "Shot 01" in first))
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
