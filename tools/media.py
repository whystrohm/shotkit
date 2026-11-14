#!/usr/bin/env python3
"""
Start a storyboard from photos and clips you already have.

    sk media scan  ~/Desktop/shoot --out output/     list every photo and clip, make thumbnails
    sk media list  output/                           what was found, what Claude saw, where it went
    sk media place output/                           put each file on the shot the plan gave it
    sk media --selftest

`scan` never changes or moves your files. It writes output/media/media.json and small
thumbnails under output/media/thumbs/, which is what Claude looks at, one by one, before
it plans a shot. A clip gets three thumbnails: its first, middle and last frame.

`place` reads shots.json. A shot whose "source" says {"type": "own", "media": "m03"}
gets that file copied to frames/round-1/ (a photo) or clips/round-1/ (a clip, with its
first frame as the shot's frame and its last frame kept for the shot that follows).
A shot whose source says {"type": "generate"} is a gap, and is left for `sk generate`.

Standard library only. ffmpeg and ffprobe are used when they are installed: they are
what reads a clip. Without them photos still work, and clips are listed by name and
size only.
"""

from __future__ import annotations

import argparse
import json
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _shotkit import IMAGE_EXTS, SHOT_ID_RE, iso_instant, load_json, sha256_file  # noqa: E402

PHOTO_EXTS = IMAGE_EXTS + ("heic", "heif", "tif", "tiff")
CLIP_EXTS = ("mp4", "mov", "m4v", "webm")
# What a browser can show without converting.
WEB_PHOTO = IMAGE_EXTS
WEB_CLIP = ("mp4", "mov", "m4v", "webm")
THUMB_EDGE = 1024
MEDIA_DIR = "media"
INBOX = "inbox"


class Stop(Exception):
    """A problem to print as one line and exit on, not a traceback."""


def have(tool: str) -> str | None:
    return shutil.which(tool)


def run(cmd: list[str], timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, timeout=timeout)


# --------------------------------------------------------------------------
# reading a file
# --------------------------------------------------------------------------
def image_size(path: Path) -> tuple[int, int] | None:
    """Width and height of a PNG, JPEG or WebP from its header. None if unreadable."""
    try:
        with path.open("rb") as fh:
            head = fh.read(32)
            if head[:8] == b"\x89PNG\r\n\x1a\n":
                return struct.unpack(">II", head[16:24])
            if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
                chunk = head[12:16]
                if chunk == b"VP8X":
                    w = int.from_bytes(head[24:27], "little") + 1
                    h = int.from_bytes(head[27:30], "little") + 1
                    return (w, h)
                if chunk == b"VP8 ":
                    w, h = struct.unpack("<HH", head[26:30])
                    return (w & 0x3FFF, h & 0x3FFF)
                if chunk == b"VP8L":
                    bits = int.from_bytes(head[21:25], "little")
                    return ((bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1)
                return None
            if head[:2] == b"\xff\xd8":
                fh.seek(2)
                while True:
                    marker = fh.read(4)
                    if len(marker) < 4 or marker[0] != 0xFF:
                        return None
                    kind, length = marker[1], struct.unpack(">H", marker[2:4])[0]
                    if 0xC0 <= kind <= 0xCF and kind not in (0xC4, 0xC8, 0xCC):
                        data = fh.read(5)
                        h, w = struct.unpack(">HH", data[1:5])
                        return (w, h)
                    fh.seek(length - 2, 1)
    except (OSError, struct.error):
        return None
    return None


def probe(path: Path, kind: str) -> dict:
    """Size, and for a clip its length and frame rate. Missing values stay None."""
    info: dict = {"width": None, "height": None, "duration_s": None, "fps": None}
    if have("ffprobe"):
        out = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                   "stream=width,height,r_frame_rate,duration:stream_side_data=rotation:format=duration",
                   "-of", "json", str(path)])
        try:
            doc = json.loads(out.stdout or b"{}")
            stream = (doc.get("streams") or [{}])[0]
            w, h = stream.get("width"), stream.get("height")
            rotation = next((abs(int(float(s["rotation"]))) for s in stream.get("side_data_list") or []
                             if "rotation" in s), 0)
            if rotation in (90, 270) and w and h:
                w, h = h, w
            info["width"], info["height"] = w, h
            if kind == "clip":
                length = stream.get("duration") or (doc.get("format") or {}).get("duration")
                info["duration_s"] = round(float(length), 2) if length else None
                num, _, den = (stream.get("r_frame_rate") or "").partition("/")
                if num and den and float(den):
                    info["fps"] = round(float(num) / float(den), 2)
        except (ValueError, KeyError, IndexError, TypeError):
            pass
    if kind == "photo" and not info["width"]:
        size = image_size(path)
        if size:
            info["width"], info["height"] = size
    return info


def aspect_name(w: int | None, h: int | None) -> str | None:
    if not w or not h:
        return None
    ratio = w / h
    named = {"16:9": 16 / 9, "9:16": 9 / 16, "1:1": 1.0, "4:5": 0.8, "4:3": 4 / 3, "3:4": 0.75, "3:2": 1.5, "2:3": 2 / 3}
    best = min(named, key=lambda k: abs(named[k] - ratio))
    return best if abs(named[best] - ratio) < 0.04 else f"{ratio:.2f}:1"


def still(src: Path, dest: Path, at: float | None = None, edge: int | None = THUMB_EDGE) -> bool:
    """One JPEG from a photo or from a moment in a clip. False if nothing here can make it."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if have("ffmpeg"):
        cmd = ["ffmpeg", "-v", "error", "-y"]
        if at is not None:
            cmd += ["-ss", f"{max(at, 0):.2f}"]
        cmd += ["-i", str(src), "-frames:v", "1"]
        if edge:
            cmd += ["-vf", f"scale='min({edge},iw)':'min({edge},ih)':force_original_aspect_ratio=decrease"]
        cmd += ["-q:v", "3", str(dest)]
        if run(cmd).returncode == 0 and dest.exists() and dest.stat().st_size:
            return True
    if at is None and have("sips"):
        cmd = ["sips", "-s", "format", "jpeg"]
        if edge:
            cmd += ["-Z", str(edge)]
        cmd += [str(src), "--out", str(dest)]
        if run(cmd).returncode == 0 and dest.exists() and dest.stat().st_size:
            return True
    return False


# --------------------------------------------------------------------------
# scan
# --------------------------------------------------------------------------
def kind_of(path: Path) -> str | None:
    ext = path.suffix.lstrip(".").lower()
    return "photo" if ext in PHOTO_EXTS else "clip" if ext in CLIP_EXTS else None


def load_media(out_dir: Path) -> dict:
    doc, err = load_json(out_dir / MEDIA_DIR / "media.json")
    if err or not isinstance(doc, dict):
        return {"version": 1, "sources": [], "items": []}
    doc.setdefault("items", [])
    doc.setdefault("sources", [])
    return doc


def save_media(out_dir: Path, doc: dict) -> None:
    path = out_dir / MEDIA_DIR / "media.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")


def scan(folder: Path, out_dir: Path) -> tuple[dict, list[dict]]:
    """
    Add every photo and clip under folder to media.json. Returns (doc, new items).

    A file already listed (same bytes) keeps its id, its note and its placement, so
    scanning again after adding files only adds the new ones.
    """
    folder = folder.resolve()
    if not folder.is_dir():
        raise Stop(f"{folder} is not a folder")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_resolved = out_dir.resolve()
    doc = load_media(out_dir)
    by_hash = {item["sha256"]: item for item in doc["items"]}
    if str(folder) not in doc["sources"]:
        doc["sources"].append(str(folder))
    used = {int(item["id"][1:]) for item in doc["items"] if item["id"][1:].isdigit()}
    next_id = max(used | {0}) + 1
    new: list[dict] = []
    files = sorted(p for p in folder.rglob("*") if p.is_file() and not p.name.startswith(".") and kind_of(p))
    for path in files:
        resolved = path.resolve()
        # Never list the thumbnails, or the frames and clips already placed on shots.
        if out_resolved in resolved.parents and resolved.parent != (out_resolved / MEDIA_DIR / INBOX):
            continue
        digest = sha256_file(path)
        if digest in by_hash:
            by_hash[digest]["file"] = str(resolved)
            continue
        kind = kind_of(path)
        info = probe(path, kind)
        item = {
            "id": f"m{next_id:02d}", "file": str(resolved), "name": path.name, "kind": kind,
            "bytes": path.stat().st_size, "sha256": digest, **info,
            "aspect": aspect_name(info["width"], info["height"]),
            "thumbs": [], "note": None, "shots": [],
        }
        next_id += 1
        thumbs = out_dir / MEDIA_DIR / "thumbs"
        if kind == "photo":
            if still(path, thumbs / f"{item['id']}.jpg"):
                item["thumbs"] = [f"{MEDIA_DIR}/thumbs/{item['id']}.jpg"]
        else:
            length = info["duration_s"] or 0
            moments = [("a", 0.0), ("b", length / 2), ("c", max(length - 0.15, 0))] if length else [("a", 0.0)]
            for tag, at in moments:
                if still(path, thumbs / f"{item['id']}_{tag}.jpg", at=at):
                    item["thumbs"].append(f"{MEDIA_DIR}/thumbs/{item['id']}_{tag}.jpg")
        doc["items"].append(item)
        by_hash[digest] = item
        new.append(item)
    doc["scanned_at"] = iso_instant()
    save_media(out_dir, doc)
    return (doc, new)


def describe(item: dict) -> str:
    size = f"{item['width']}x{item['height']}" if item.get("width") else "size unknown"
    length = f", {item['duration_s']}s" if item.get("duration_s") else ""
    where = ", ".join(item.get("shots") or []) or "not placed"
    return f"{item['id']}  {item['kind']:5}  {size}{length}  {item.get('aspect') or ''}  {item['name']}  -> {where}"


# --------------------------------------------------------------------------
# place
# --------------------------------------------------------------------------
def place(out_dir: Path, replace: bool = False) -> tuple[list[str], list[str]]:
    """
    Copy each shot's own photo or clip to where the board and the checks look.

    Returns (done, problems). A frame the critic has reviewed is never replaced.
    """
    shots_doc, err = load_json(out_dir / "shots.json")
    if err or not isinstance(shots_doc, dict):
        raise Stop(err or "shots.json is not readable")
    doc = load_media(out_dir)
    items = {item["id"]: item for item in doc["items"]}
    for item in doc["items"]:
        item["shots"] = []
    done: list[str] = []
    problems: list[str] = []
    for shot in shots_doc.get("shots") or []:
        shot_id, source = shot.get("id"), shot.get("source")
        if not isinstance(shot_id, str) or not SHOT_ID_RE.match(shot_id) or not isinstance(source, dict):
            continue
        if source.get("type") != "own":
            continue
        item = items.get(source.get("media"))
        if item is None:
            problems.append(f"{shot_id}: media '{source.get('media')}' is not in media.json")
            continue
        src = Path(item["file"])
        if not src.is_file():
            problems.append(f"{shot_id}: {src} is gone. Scan the folder again.")
            continue
        item["shots"].append(shot_id)
        frames = out_dir / "frames" / "round-1"
        reviewed = (out_dir / "critiques" / "round-1" / f"{shot_id}.critique.json").exists()
        have_frame = next((frames / f"{shot_id}.{e}" for e in IMAGE_EXTS if (frames / f"{shot_id}.{e}").exists()), None)
        ext = src.suffix.lstrip(".").lower()
        if item["kind"] == "photo":
            if have_frame and (reviewed or not replace):
                done.append(f"{shot_id}: keeps {have_frame.relative_to(out_dir)}")
                continue
            frames.mkdir(parents=True, exist_ok=True)
            if have_frame:
                have_frame.unlink()
            if ext in WEB_PHOTO:
                dest = frames / f"{shot_id}.{'jpg' if ext == 'jpeg' else ext}"
                shutil.copyfile(src, dest)
            else:
                dest = frames / f"{shot_id}.jpg"
                if not still(src, dest, edge=None):
                    problems.append(f"{shot_id}: {src.name} needs converting to JPEG, and neither ffmpeg nor sips is here")
                    continue
            done.append(f"{shot_id}: {item['id']} {src.name} -> {dest.relative_to(out_dir)}")
            continue
        # a clip
        clips = out_dir / "clips" / "round-1"
        clips.mkdir(parents=True, exist_ok=True)
        dest = clips / f"{shot_id}.{ext}"
        old = [clips / f"{shot_id}.{e}" for e in CLIP_EXTS if (clips / f"{shot_id}.{e}").exists()]
        if old and not replace:
            done.append(f"{shot_id}: keeps {old[0].relative_to(out_dir)}")
        else:
            for path in old:
                path.unlink()
            shutil.copyfile(src, dest)
            done.append(f"{shot_id}: {item['id']} {src.name} -> {dest.relative_to(out_dir)}")
        start = float(source.get("in") or 0)
        length = item.get("duration_s") or 0
        end = float(source.get("out") or length or 0)
        if not have_frame or (replace and not reviewed):
            frames.mkdir(parents=True, exist_ok=True)
            if have_frame:
                have_frame.unlink()
            if not still(src, frames / f"{shot_id}.jpg", at=start, edge=None):
                problems.append(f"{shot_id}: no ffmpeg here, so the clip has no still for the board or the check")
        if end:
            still(src, out_dir / MEDIA_DIR / "ends" / f"{shot_id}.jpg", at=max(end - 0.15, 0), edge=None)
    save_media(out_dir, doc)
    return (done, problems)


# --------------------------------------------------------------------------
# the board's upload
# --------------------------------------------------------------------------
def safe_name(name: str) -> str | None:
    """A bare file name with a known extension, or None."""
    name = Path(name.replace("\\", "/")).name.strip()
    cleaned = "".join(c if c.isalnum() or c in "._- " else "_" for c in name).strip(" .")
    if not cleaned or kind_of(Path(cleaned)) is None:
        return None
    return cleaned[:120]


def inbox_path(out_dir: Path, name: str) -> Path | None:
    cleaned = safe_name(name)
    if cleaned is None:
        return None
    inbox = out_dir / MEDIA_DIR / INBOX
    inbox.mkdir(parents=True, exist_ok=True)
    dest = inbox / cleaned
    stem, suffix, n = dest.stem, dest.suffix, 2
    while dest.exists():
        dest = inbox / f"{stem}-{n}{suffix}"
        n += 1
    return dest


# --------------------------------------------------------------------------
# selftest
# --------------------------------------------------------------------------
def tiny_png(path: Path, w: int, h: int, rgb: tuple[int, int, int]) -> None:
    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    raw = b"".join(b"\x00" + bytes(rgb) * w for _ in range(h))
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def selftest() -> int:
    checks: list[tuple[str, bool]] = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        shoot, out = root / "shoot", root / "output"
        (shoot / "day one").mkdir(parents=True)
        tiny_png(shoot / "wide.png", 160, 90, (40, 80, 120))
        tiny_png(shoot / "day one" / "tall.png", 90, 160, (120, 80, 40))
        (shoot / "notes.txt").write_text("not media")
        (shoot / ".hidden.png").write_bytes(b"x")
        clip = None
        if have("ffmpeg") and have("ffprobe"):
            clip = shoot / "pan.mp4"
            made = run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc=size=160x90:rate=10:duration=2",
                        "-pix_fmt", "yuv420p", str(clip)])
            if made.returncode != 0 or not clip.exists():
                clip = None

        doc, new = scan(shoot, out)
        expected = 3 if clip else 2
        checks.append(("scan lists photos and clips and nothing else", len(new) == expected))
        by_name = {i["name"]: i for i in doc["items"]}
        checks.append(("a photo's size is read", (by_name["wide.png"]["width"], by_name["wide.png"]["height"]) == (160, 90)))
        checks.append(("its shape is named", by_name["wide.png"]["aspect"] == "16:9" and by_name["tall.png"]["aspect"] == "9:16"))
        if have("ffmpeg") or have("sips"):
            checks.append(("a photo gets a thumbnail", bool(by_name["wide.png"]["thumbs"])
                           and (out / by_name["wide.png"]["thumbs"][0]).exists()))
        if clip:
            item = by_name["pan.mp4"]
            checks.append(("a clip's length is read", item["duration_s"] is not None and 1.8 <= item["duration_s"] <= 2.2))
            checks.append(("a clip gets its first, middle and last frame", len(item["thumbs"]) == 3))

        # a note and a second scan
        by_name["wide.png"]["note"] = "a wide of the shop front"
        save_media(out, doc)
        tiny_png(shoot / "extra.png", 100, 100, (9, 9, 9))
        doc2, new2 = scan(shoot, out)
        checks.append(("a second scan adds only the new file", [i["name"] for i in new2] == ["extra.png"]))
        kept = {i["name"]: i for i in doc2["items"]}["wide.png"]
        checks.append(("and keeps ids and notes", kept["id"] == by_name["wide.png"]["id"] and kept["note"] == "a wide of the shop front"))
        _, new3 = scan(shoot, out)
        checks.append(("the output folder's own files are never listed", new3 == []))

        # place
        wide, tall = by_name["wide.png"]["id"], by_name["tall.png"]["id"]
        shots = [
            {"id": "shot_01", "source": {"type": "own", "media": wide}},
            {"id": "shot_02", "source": {"type": "generate", "why": "nothing shows the finished job"}},
            {"id": "shot_03", "source": {"type": "own", "media": "m99"}},
        ]
        if clip:
            shots.append({"id": "shot_04", "source": {"type": "own", "media": by_name["pan.mp4"]["id"], "in": 0.5, "out": 1.5}})
        (out / "shots.json").write_text(json.dumps({"shots": shots}))
        done, problems = place(out)
        checks.append(("place copies a photo to its shot", (out / "frames/round-1/shot_01.png").exists()))
        checks.append(("a gap is left alone", not list((out / "frames/round-1").glob("shot_02.*"))))
        checks.append(("a wrong media id is reported", any("m99" in p for p in problems)))
        checks.append(("the original is untouched", (shoot / "wide.png").exists()))
        placed = {i["id"]: i for i in load_media(out)["items"]}
        checks.append(("media.json records where a file went", placed[wide]["shots"] == ["shot_01"]))
        if clip:
            checks.append(("place copies a clip, its first frame and its last", (out / "clips/round-1/shot_04.mp4").exists()
                           and (out / "frames/round-1/shot_04.jpg").exists() and (out / "media/ends/shot_04.jpg").exists()))

        # a reviewed frame stays
        (out / "critiques/round-1").mkdir(parents=True)
        (out / "critiques/round-1/shot_01.critique.json").write_text("{}")
        shots[0]["source"]["media"] = tall
        (out / "shots.json").write_text(json.dumps({"shots": shots}))
        before = (out / "frames/round-1/shot_01.png").read_bytes()
        place(out, replace=True)
        checks.append(("a reviewed frame is never replaced", (out / "frames/round-1/shot_01.png").read_bytes() == before))

        # upload names
        checks.append(("an upload name cannot leave the inbox", inbox_path(out, "../../etc/passwd.png").parent == out / "media/inbox"))
        checks.append(("an upload that is not a photo or clip is refused", inbox_path(out, "run.sh") is None and safe_name(".png") is None))
        first = inbox_path(out, "a.jpg")
        first.write_bytes(b"x")
        checks.append(("an upload never overwrites another", inbox_path(out, "a.jpg").name == "a-2.jpg"))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(("  ok   " if ok else "  FAIL ") + name)
    if not (have("ffmpeg") and have("ffprobe")):
        print("  note: ffmpeg or ffprobe is not installed, so the clip checks did not run")
    print(f"media selftest: {len(checks) - len(failed)}/{len(checks)} passed")
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Start a storyboard from photos and clips you already have.")
    parser.add_argument("--selftest", action="store_true")
    sub = parser.add_subparsers(dest="cmd")
    p_scan = sub.add_parser("scan", help="list every photo and clip in a folder")
    p_scan.add_argument("folder", type=Path)
    p_scan.add_argument("--out", type=Path, default=Path("output"))
    p_list = sub.add_parser("list", help="what was found and where it went")
    p_list.add_argument("out", type=Path, nargs="?", default=Path("output"))
    p_place = sub.add_parser("place", help="put each file on the shot the plan gave it")
    p_place.add_argument("out", type=Path, nargs="?", default=Path("output"))
    p_place.add_argument("--replace", action="store_true", help="replace frames and clips that are already there, unless reviewed")
    args = parser.parse_args()
    if args.selftest:
        return selftest()
    try:
        if args.cmd == "scan":
            doc, new = scan(args.folder, args.out)
            for item in new:
                print(describe(item))
            photos = sum(1 for i in doc["items"] if i["kind"] == "photo")
            print(f"{len(new)} new, {len(doc['items'])} in all ({photos} photos, {len(doc['items']) - photos} clips). "
                  f"Listed in {args.out / MEDIA_DIR / 'media.json'}")
            if not have("ffmpeg"):
                print("ffmpeg is not installed, so clips have no thumbnails. Photos still work.")
            return 0
        if args.cmd == "list":
            doc = load_media(args.out)
            for item in doc["items"]:
                print(describe(item))
                if item.get("note"):
                    print(f"      {item['note']}")
            if not doc["items"]:
                print("No media listed yet. Run: sk media scan <folder> --out " + str(args.out))
            return 0
        if args.cmd == "place":
            done, problems = place(args.out, args.replace)
            for line in done:
                print(line)
            for line in problems:
                print("PROBLEM " + line, file=sys.stderr)
            return 1 if problems else 0
    except Stop as stop:
        print(f"shotkit: {stop}", file=sys.stderr)
        return 2
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
