#!/usr/bin/env python3
"""
The Shotkit board: one page that shows a whole run.

preview.html is the page you send to a client. It is quiet, takes the brand's own
colours and prints cleanly. The board is the page you work from. It shows every shot on
a contact sheet and a timeline, the newest frame for each one, the critic's verdict and
its fixes, every prompt with a copy button, the brand lock, and whether the files still
match the hashes run.json recorded. It also carries the whole storyboard as Markdown,
so one click copies it for another model.

It needs Python 3 and nothing else. No pyyaml, no jsonschema. A storyboard with no
prompts and no frames still renders, and the board says what to do next.

Usage:
    python tools/board.py output/                 # write output/board.html
    python tools/board.py output/ --open          # write it and open it in a browser
    python tools/board.py output/ --serve         # live board on localhost: it reloads
                                                  # when files change, and a frame
                                                  # dropped on a shot is saved to
                                                  # frames/round-N/ for you
    python tools/board.py output/ --inline-images # one portable file, frames embedded
    python tools/board.py --example               # open the bundled finished run
    python tools/board.py output/ --rendered-at 2026-07-30T00:00:00Z
    python tools/board.py --selftest
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import sys
import webbrowser
from pathlib import Path

from _shotkit import (
    INSTALLED,
    IMAGE_EXTS,
    OVERLAY_WEIGHTS,
    PALETTE_ROW_RE,
    REPO_ROOT,
    SHOT_ID_RE,
    as_overlay_ids,
    capability_map,
    is_unconfigured,
    iso_instant,
    load_json,
    parse_font_spec,
    parse_snapshot_header,
    parse_typography,
    round_dirs,
    sha256_file,
)

TEMPLATE = REPO_ROOT / "skills" / "storyboard-html-preview" / "templates" / "board.html.tpl"

# A finished run that ships with the kit, so a new user can see a board with frames on
# it before they have made any.
EXAMPLE_DIR = (
    Path(__file__).resolve().parent / "example" if INSTALLED
    else REPO_ROOT / "examples" / "harbor-roast"
)

SHOT_HEADER = re.compile(r"^#\s*(?:revision\s+of\s+)?(shot_\d{2,3})\b(.*)$", re.IGNORECASE)
FILE_HEADER = re.compile(r"^#\s*([A-Za-z][A-Za-z -]*?):\s*(.+)$")
_UNSAFE_FAMILY_CHARS = re.compile(r"[^A-Za-z0-9 _-]")

MIME = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"}
MAX_FRAME_BYTES = 40 * 1024 * 1024

# What the board counts as the files of a run, in the order it lists them.
TOP_FILES = (
    "run.json",
    "storyboard.md",
    "shots.json",
    "text-overlays.json",
    "brand-lock.snapshot.md",
)


# --------------------------------------------------------------------------
# Reading the tree
# --------------------------------------------------------------------------

def parse_prompt_file(path: Path) -> dict:
    """
    Split a prompts file into its header lines and one block per shot.

    The forge writes two shapes: a full pass, and a revision file whose blocks carry
    `# fix [...]` lines. Comment lines inside a block are annotations and never part of
    the prompt, which is the same rule copy-prompt.py applies.
    """
    meta: dict[str, str] = {}
    blocks: list[dict] = []
    current: dict | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        header = SHOT_HEADER.match(line)
        if header:
            current = {
                "shot_id": header.group(1).lower(),
                "header": line.lstrip("# ").strip(),
                "params": [],
                "fixes": [],
                "notes": [],
                "body": [],
            }
            blocks.append(current)
            continue
        if line.lstrip().startswith("#"):
            text = line.lstrip().lstrip("#").strip()
            if current is None:
                found = FILE_HEADER.match(line)
                if found:
                    meta[found.group(1).strip().lower()] = found.group(2).strip()
                continue
            lowered = text.lower()
            if lowered.startswith("params"):
                current["params"].append(text.split(":", 1)[-1].strip())
            elif lowered.startswith("fix"):
                current["fixes"].append(text)
            elif text:
                current["notes"].append(text)
            continue
        if current is not None:
            current["body"].append(line)
    for block in blocks:
        block["body"] = "\n".join(block["body"]).strip()
    return {"meta": meta, "blocks": [b for b in blocks if b["body"]]}


def generator_of(path: Path) -> tuple[str, bool]:
    """('flux', False) for flux.txt and ('flux', True) for revised-flux.txt."""
    stem = path.stem
    if stem.startswith("revised-"):
        return (stem[len("revised-"):], True)
    return (stem, False)


def read_prompts(out_dir: Path) -> tuple[dict[str, dict[str, list]], list[str]]:
    """
    Prompts by shot, then by generator, oldest round first.

    Also returns the generators seen, in the order the capability matrix lists them, so
    the tabs read the same on every board.
    """
    by_shot: dict[str, dict[str, list]] = {}
    seen: list[str] = []
    for round_no, directory in round_dirs(out_dir, "prompts"):
        for path in sorted(directory.glob("*.txt")):
            generator, revised = generator_of(path)
            parsed = parse_prompt_file(path)
            if not parsed["blocks"]:
                continue
            if generator not in seen:
                seen.append(generator)
            rel = str(path.relative_to(out_dir))
            for block in parsed["blocks"]:
                by_shot.setdefault(block["shot_id"], {}).setdefault(generator, []).append(
                    {
                        "round": round_no,
                        "revised": revised,
                        "file": rel,
                        "model": parsed["meta"].get("model"),
                        "header": block["header"],
                        "params": block["params"],
                        "fixes": block["fixes"],
                        "notes": block["notes"],
                        "body": block["body"],
                    }
                )
    return (by_shot, seen)


def read_critiques(out_dir: Path) -> dict[str, list[dict]]:
    """Every critique per shot, oldest round first."""
    by_shot: dict[str, list[dict]] = {}
    for round_no, directory in round_dirs(out_dir, "critiques"):
        for path in sorted(directory.glob("*.json")):
            data, err = load_json(path)
            if err or not isinstance(data, dict) or not data.get("shot_id"):
                continue
            image_ref = data.get("image_ref")
            # True: the reviewed frame is on disk and unchanged. False: it has changed.
            # "missing": the file the critic reviewed is not in this folder, which is
            # the case when a run is shared with smaller copies of its frames.
            image_ok = None
            if image_ref and data.get("image_sha256"):
                image = out_dir / image_ref
                if not image.exists():
                    image_ok = "missing"
                else:
                    image_ok = sha256_file(image) == data["image_sha256"]
            by_shot.setdefault(data["shot_id"], []).append(
                {
                    "round": data.get("round") or round_no,
                    "file": str(path.relative_to(out_dir)),
                    "verdict": str(data.get("verdict") or "").upper() or None,
                    "confidence": data.get("confidence"),
                    "generator": data.get("generator"),
                    "model": data.get("model_version"),
                    "seed": data.get("seed"),
                    "image_ref": image_ref,
                    "image_ok": image_ok,
                    "working": [w for w in data.get("working") or [] if isinstance(w, str)],
                    "issues": [
                        {
                            "layer": i.get("layer"),
                            "severity": i.get("severity"),
                            "note": i.get("note"),
                            "fix_type": i.get("fix_type"),
                            "fix": i.get("fix"),
                        }
                        for i in data.get("issues") or []
                        if isinstance(i, dict)
                    ],
                    "post_notes": [n for n in data.get("post_notes") or [] if isinstance(n, str)],
                }
            )
    for entries in by_shot.values():
        entries.sort(key=lambda c: c["round"])
    return by_shot


def read_frames(out_dir: Path, shot_id: str, inline: bool) -> list[dict]:
    """Every frame on disk for a shot, oldest round first."""
    frames: list[dict] = []
    for round_no, directory in round_dirs(out_dir, "frames"):
        for ext in IMAGE_EXTS:
            path = directory / f"{shot_id}.{ext}"
            if path.exists():
                frames.append(frame_entry(out_dir, path, round_no, inline))
                break
    if not frames:
        legacy = out_dir / "generated"
        for ext in IMAGE_EXTS:
            path = legacy / f"{shot_id}.{ext}"
            if path.exists():
                frames.append(frame_entry(out_dir, path, 1, inline))
                break
    return frames


def read_clips(out_dir: Path, shot_id: str) -> list[dict]:
    """Every clip on disk for a shot, oldest round first. Clips are never inlined."""
    clips: list[dict] = []
    for round_no, directory in round_dirs(out_dir, "clips"):
        path = directory / f"{shot_id}.mp4"
        if path.exists():
            rel = str(path.relative_to(out_dir))
            clips.append({"round": round_no, "path": rel, "src": rel, "bytes": path.stat().st_size})
    return clips


def frame_entry(out_dir: Path, path: Path, round_no: int, inline: bool) -> dict:
    rel = str(path.relative_to(out_dir))
    if inline:
        mime = MIME.get(path.suffix.lstrip(".").lower(), "image/png")
        src = f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")
    else:
        src = rel
    return {"round": round_no, "path": rel, "src": src, "bytes": path.stat().st_size}


def read_brand(path: Path) -> dict:
    """Palette rows, fonts and the snapshot header from a brand lock."""
    if not path.exists():
        return {"found": False, "palette": [], "fonts": {}, "name": None}
    text = path.read_text(encoding="utf-8")
    palette = []
    for line in text.splitlines():
        row = PALETTE_ROW_RE.match(line)
        if not row:
            continue
        role, hex_val = row.group(1).strip(), row.group(2).strip()
        if hex_val.startswith("#_"):
            continue
        cells = [c.strip() for c in line[row.end():].split("|") if c.strip()]
        palette.append({"role": role, "hex": hex_val.upper(), "use": cells[0] if cells else ""})
    fonts = {k: v for k, v in parse_typography(text).items() if v}
    name = None
    found = re.search(r"^\*\*Brand:\*\*\s*(.+)$", text, re.MULTILINE)
    if found:
        name = found.group(1).strip()
    header = parse_snapshot_header(text)
    return {
        "found": True,
        "name": name,
        "palette": palette,
        "fonts": fonts,
        "source": header.get("source"),
        "snapshot_taken": header.get("snapshot_taken"),
        "unconfigured": is_unconfigured(text),
        "markdown": text,
    }


def css_family(value: str | None) -> str | None:
    family = parse_font_spec(value)["family"]
    clean = _UNSAFE_FAMILY_CHARS.sub("", family or "").strip()
    return clean or None


def font_links(families: list[tuple[str, int]]) -> list[str]:
    """One Google Fonts stylesheet per family the overlays use."""
    weights: dict[str, set[int]] = {}
    for family, weight in families:
        weights.setdefault(family, set()).update({weight, 400})
    links = []
    for family in sorted(weights):
        axis = ";".join(str(w) for w in sorted(weights[family]))
        links.append(
            "https://fonts.googleapis.com/css2?family="
            + family.replace(" ", "+")
            + f":wght@{axis}&display=swap"
        )
    return links


def check_inputs(out_dir: Path, run_doc: dict) -> list[dict]:
    """The files of the run, each with its hash and whether run.json still agrees."""
    inputs = run_doc.get("inputs") or {}
    pinned = {}
    for key in ("shots", "text_overlays", "brand_lock"):
        ref, sha = inputs.get(f"{key}_ref"), inputs.get(f"{key}_sha256")
        if ref and sha:
            pinned[ref] = sha
    for entry in run_doc.get("rounds") or []:
        for prompt in entry.get("prompts") or []:
            if prompt.get("ref") and prompt.get("sha256"):
                pinned[prompt["ref"]] = prompt["sha256"]

    files: list[dict] = []
    listed: set[str] = set()

    def add(rel: str) -> None:
        path = out_dir / rel
        if rel in listed or not path.is_file():
            return
        listed.add(rel)
        sha = sha256_file(path)
        state = "unpinned"
        if rel in pinned:
            state = "match" if pinned[rel] == sha else "changed"
        files.append({"path": rel, "bytes": path.stat().st_size, "sha": sha[:12], "state": state})

    for name in TOP_FILES:
        add(name)
    for kind in ("prompts", "frames", "clips", "critiques"):
        for _, directory in round_dirs(out_dir, kind):
            for path in sorted(directory.iterdir()):
                if path.is_file() and not path.name.startswith("."):
                    add(str(path.relative_to(out_dir)))
    for rel, _ in pinned.items():
        if rel not in listed and not (out_dir / rel).exists():
            files.append({"path": rel, "bytes": 0, "sha": "", "state": "missing"})
    return files


# --------------------------------------------------------------------------
# Status, next step, Markdown
# --------------------------------------------------------------------------

def shot_status(shot: dict) -> str:
    """
    One word for where a shot stands.

    plan     no prompt has been written for it
    frame    it has a prompt and no frame
    check    its newest frame has not been reviewed
    revise   its newest frame came back REVISE, or REJECT
    accept   its newest frame is ACCEPT
    """
    frames, critiques = shot["frames"], shot["critiques"]
    if not frames:
        return "frame" if shot["prompts"] else "plan"
    newest = frames[-1]["round"]
    reviewed = [c for c in critiques if c["round"] == newest]
    if not reviewed:
        return "check"
    verdict = reviewed[-1]["verdict"]
    if verdict == "ACCEPT":
        return "accept"
    return "revise"


def count(n: int, word: str = "shot") -> str:
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def next_step(shots: list[dict], generators: list[str], rounds: int) -> dict:
    """What to do next, and the line to type in Claude to do it."""
    by = {}
    for shot in shots:
        by.setdefault(shot["status"], []).append(shot["id"])
    total = len(shots)

    def ids(key: str) -> str:
        return ", ".join(by.get(key, []))

    if by.get("plan"):
        return {
            "title": "Write the prompts",
            "body": f"{len(by['plan'])} of {count(total)} have no prompt yet. Name the "
                    "generator you use and Shotkit writes one prompt per shot for it.",
            "say": "Write Flux and Kling prompts for output/shots.json, then update the board.",
        }
    if by.get("frame"):
        target = f"frames/round-{max(rounds, 1)}/"
        return {
            "title": "Make the frames",
            "body": f"Waiting for a frame: {ids('frame')}. "
                    "Copy each prompt into your generator and save the result as "
                    f"{target}shot_NN.png, or drop it on the shot on a live board. With a "
                    "fal.ai key, Shotkit can make them for you.",
            "say": "Make the frames with Flux on fal, then update the board.",
        }
    if by.get("check"):
        return {
            "title": "Check the frames",
            "body": f"Not reviewed yet: {ids('check')}. "
                    "The critic compares each one with its shot and the brand lock.",
            "say": "Check the new frames in output/frames against the storyboard, then update the board.",
        }
    if by.get("revise"):
        open_ids = []
        for shot in shots:
            if shot["status"] != "revise":
                continue
            newest_frame = shot["frames"][-1]["round"]
            newest_prompt = max(
                (p["round"] for runs in shot["prompts"].values() for p in runs), default=0
            )
            if newest_prompt <= newest_frame:
                open_ids.append(shot["id"])
        if open_ids:
            return {
                "title": "Revise the prompts",
                "body": f"{count(len(open_ids))} came back for another pass: "
                        f"{', '.join(open_ids)}. Shotkit rewrites only those prompts, "
                        "using the critic's fixes.",
                "say": "Revise the prompts for the shots marked REVISE, then update the board.",
            }
        return {
            "title": "Make the revised frames",
            "body": f"Revised prompts are written for {ids('revise')}. Make the new "
                    f"frames and save them to frames/round-{rounds}/.",
            "say": None,
        }
    return {
        "title": "Every shot is accepted",
        "body": f"Each of the {count(total)} has an accepted frame. Send preview.html for review, "
                "make a clip from each frame, or hand shots.json and text-overlays.json to the edit.",
        "say": "Render the client preview for output/ and open it.",
    }


def storyboard_markdown(data: dict) -> str:
    """The whole run as Markdown, written to be pasted into another model."""
    project, series = data["project"], data["series_lock"]
    lines = [
        f"# {project['title']}",
        "",
        f"Storyboard made with Shotkit. {project['duration_s']} seconds, {project['aspect']}, "
        f"{len(data['shots'])} shots, framework: {project.get('framework') or 'not specified'}.",
        f"Run {data['run']['id']}, started {data['run']['created_at']}.",
        "",
        "## Series lock",
        "",
        "These hold for every shot.",
        "",
        f"- Character: {series.get('character')}",
        f"- Environment: {series.get('environment')}",
        f"- Lighting: {series.get('lighting')}",
        f"- Color grade: {series.get('color_grade')}",
        "",
    ]
    brand = data["brand"]
    if brand.get("palette"):
        lines += ["## Brand", ""]
        if brand.get("name"):
            lines.append(f"- Brand: {brand['name']}")
        for row in brand["palette"]:
            use = f" ({row['use']})" if row.get("use") else ""
            lines.append(f"- {row['role']}: {row['hex']}{use}")
        for key, label in (("display_font", "Display font"), ("body_font", "Body font"), ("mono_font", "Mono font")):
            if brand["fonts"].get(key):
                lines.append(f"- {label}: {brand['fonts'][key]}")
        lines.append("")
    lines += ["## Shots", ""]
    for shot in data["shots"]:
        lines += shot_markdown(shot, heading="###")
    return "\n".join(lines).rstrip() + "\n"


def shot_markdown(shot: dict, heading: str = "##") -> list[str]:
    spec = ", ".join(
        str(v) for v in (shot["framing"], shot["angle"], shot["motion"]) if v
    )
    if shot.get("depth_of_field"):
        spec += f", {shot['depth_of_field']} depth of field"
    lines = [
        f"{heading} {shot['id']} · {shot['beat']} · {shot['start']}s to {shot['end']}s",
        "",
        f"- Camera: {spec}",
        f"- Subject: {shot['subject']}",
    ]
    if shot.get("vo"):
        lines.append(f"- Voiceover: \"{shot['vo']}\"")
    for overlay in shot["overlays"]:
        lines.append(
            f"- On-screen text: \"{overlay['content']}\" ({overlay['position_label']}, "
            f"{overlay['size']}, in at {overlay['enter_at']}s, out at {overlay['exit_at']}s)"
        )
    lines.append(f"- Why: {shot['rationale']}")
    if shot["critiques"]:
        last = shot["critiques"][-1]
        lines.append(f"- Latest check: {last['verdict']}, round {last['round']}")
        for issue in last["issues"]:
            lines.append(f"  - {issue['layer']} ({issue['severity']}): {issue['note']} Fix: {issue['fix']}")
    lines.append("")
    return lines


# --------------------------------------------------------------------------
# Build
# --------------------------------------------------------------------------

def build(out_dir: Path, inline_images: bool = False, rendered_at: str | None = None,
          live: bool = False, web_fonts: bool = True) -> tuple[dict, list[str]]:
    warnings: list[str] = []
    shots_doc, err = load_json(out_dir / "shots.json")
    if err or not isinstance(shots_doc, dict):
        raise SystemExit(f"ERROR: {err or 'shots.json is not an object'}")

    overlays_doc, ov_err = load_json(out_dir / "text-overlays.json")
    overlays_by_id = {}
    if not ov_err and isinstance(overlays_doc, dict):
        overlays_by_id = {o["id"]: o for o in overlays_doc.get("overlays", []) if o.get("id")}

    run_doc, run_err = load_json(out_dir / "run.json")
    if run_err or not isinstance(run_doc, dict):
        run_doc = {}
        warnings.append("no run.json in this folder, so the board cannot check the files against it")

    project = shots_doc.get("project") or {}
    brand_ref = shots_doc.get("brand_lock_ref") or "brand-lock.snapshot.md"
    brand = read_brand(out_dir / brand_ref)
    brand["ref"] = brand_ref
    if not brand["found"]:
        warnings.append(f"brand lock {brand_ref} is missing")

    prompts_by_shot, generators_seen = read_prompts(out_dir)
    critiques_by_shot = read_critiques(out_dir)
    caps = capability_map()
    order = list(caps)
    generators_seen.sort(key=lambda g: order.index(g) if g in order else len(order))
    generators = [
        {
            "id": g,
            "name": (caps.get(g) or {}).get("display_name") or g,
            "model": (caps.get(g) or {}).get("model_version"),
            "motion": bool((caps.get(g) or {}).get("supports_motion")),
        }
        for g in generators_seen
    ]

    overlay_families: list[tuple[str, int]] = []
    shots: list[dict] = []
    for raw in shots_doc.get("shots") or []:
        shot_id = raw.get("id")
        if not isinstance(shot_id, str) or not SHOT_ID_RE.match(shot_id):
            warnings.append(f"skipped a shot with an unusable id: {shot_id!r}")
            continue
        overlays = []
        for oid in as_overlay_ids(raw.get("on_screen_text")):
            overlay = overlays_by_id.get(oid)
            if overlay is None:
                warnings.append(f"{shot_id} names overlay {oid}, which is not in text-overlays.json")
                continue
            spec = parse_font_spec(overlay.get("font"))
            weight = OVERLAY_WEIGHTS.get(str(overlay.get("weight") or "").lower(), spec["weight"] or 400)
            family = css_family(overlay.get("font"))
            if family:
                overlay_families.append((family, weight))
            position = overlay.get("position")
            overlays.append(
                {
                    "id": oid,
                    "content": overlay.get("content"),
                    "font": overlay.get("font"),
                    "family": family,
                    "weight": weight,
                    "color": overlay.get("color"),
                    "size": overlay.get("size"),
                    "position": position if isinstance(position, str) else "custom",
                    "xy": position if isinstance(position, dict) else None,
                    "position_label": position if isinstance(position, str)
                    else f"x{(position or {}).get('x')}% y{(position or {}).get('y')}%",
                    "enter_at": (overlay.get("enter") or {}).get("at"),
                    "enter_animation": (overlay.get("enter") or {}).get("animation"),
                    "exit_at": (overlay.get("exit") or {}).get("at"),
                    "exit_animation": (overlay.get("exit") or {}).get("animation"),
                }
            )
        shot = {
            "id": shot_id,
            "n": shot_id.replace("shot_", ""),
            "beat": raw.get("beat"),
            "start": raw.get("start"),
            "end": raw.get("end"),
            "framing": raw.get("framing"),
            "angle": raw.get("angle"),
            "motion": raw.get("motion"),
            "depth_of_field": raw.get("depth_of_field"),
            "subject": raw.get("subject"),
            "vo": raw.get("vo"),
            "rationale": raw.get("rationale"),
            "overlays": overlays,
            "frames": read_frames(out_dir, shot_id, inline_images),
            "clips": read_clips(out_dir, shot_id),
            "critiques": critiques_by_shot.get(shot_id, []),
            "prompts": prompts_by_shot.get(shot_id, {}),
        }
        shot["status"] = shot_status(shot)
        shots.append(shot)

    rounds = max(
        [n for n, _ in round_dirs(out_dir, "prompts")]
        + [n for n, _ in round_dirs(out_dir, "frames")]
        + [0]
    )
    files = check_inputs(out_dir, run_doc)
    changed = [f["path"] for f in files if f["state"] in ("changed", "missing")]
    if changed:
        warnings.append("changed since run.json recorded them: " + ", ".join(changed))

    inputs = run_doc.get("inputs") or {}
    data = {
        "shotkit_version": run_doc.get("shotkit_version"),
        "project": {
            "title": project.get("title") or "Untitled storyboard",
            "duration_s": project.get("duration_s"),
            "aspect": project.get("aspect") or "16:9",
            "framework": project.get("framework"),
        },
        "run": {
            "id": run_doc.get("run_id") or "not recorded",
            "created_at": run_doc.get("created_at") or "not recorded",
            "brand_source": inputs.get("brand_lock_source") or brand.get("source"),
            "brand_configured": inputs.get("brand_lock_configured"),
            "rounds": [
                {"round": r.get("round"), "started_at": r.get("started_at"), "reason": r.get("reason")}
                for r in run_doc.get("rounds") or []
                if isinstance(r, dict)
            ],
        },
        "rendered_at": rendered_at or iso_instant(),
        "live": live,
        "rounds": rounds,
        "series_lock": shots_doc.get("series_lock") or {},
        "brand": brand,
        "generators": generators,
        "shots": shots,
        "files": files,
        "warnings": warnings,
        "font_links": font_links(overlay_families) if web_fonts else [],
    }
    data["next"] = next_step(shots, [g["id"] for g in generators], rounds)
    data["markdown"] = storyboard_markdown(data)
    return (data, warnings)


def render(data: dict) -> str:
    template = TEMPLATE.read_text(encoding="utf-8")
    # The blob sits inside a script element. Escaping "<" keeps any string in it from
    # closing that element, whatever a subject line or a prompt contains.
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    links = "".join(f'<link rel="stylesheet" href="{href}">\n' for href in data["font_links"])
    title = (
        str(data["project"]["title"])
        .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )
    return (
        template.replace("<!--__FONT_LINKS__-->", links)
        .replace("__TITLE__", title)
        .replace("/*__DATA__*/null", blob)
    )


# --------------------------------------------------------------------------
# Live board
# --------------------------------------------------------------------------

def tree_stamp(out_dir: Path) -> str:
    """Changes whenever a file the board reads is added, removed or rewritten."""
    parts = []
    for path in sorted(out_dir.rglob("*")):
        if path.is_file() and path.name not in ("board.html", "preview.html") and not path.name.startswith("."):
            stat = path.stat()
            parts.append(f"{path.relative_to(out_dir)}:{stat.st_size}:{stat.st_mtime_ns}")
    import hashlib

    return hashlib.sha256("\n".join(parts).encode()).hexdigest()[:16]


def save_frame(out_dir: Path, shot_id: str, content_type: str, body: bytes) -> tuple[int, dict]:
    """
    Save a dropped frame to frames/round-N/shot_NN.ext.

    N is the round the shot is in. A frame the critic has already reviewed is never
    replaced: its hash is recorded in the critique, so a new image goes to the next
    round, which only exists once the forge has written revised prompts.
    """
    if not SHOT_ID_RE.match(shot_id):
        return (400, {"error": "not a shot id"})
    ext = {v: k for k, v in MIME.items() if k != "jpeg"}.get(content_type.split(";")[0].strip())
    if ext is None:
        return (415, {"error": "use a PNG, JPEG or WebP image"})
    if not body or len(body) > MAX_FRAME_BYTES:
        return (413, {"error": "image is empty or over 40 MB"})
    shots_doc, err = load_json(out_dir / "shots.json")
    if err or shot_id not in {s.get("id") for s in (shots_doc or {}).get("shots", [])}:
        return (404, {"error": f"{shot_id} is not in shots.json"})

    prompt_rounds = [n for n, _ in round_dirs(out_dir, "prompts")]
    target = max(prompt_rounds + [1])
    # Use the newest round that has a prompt for this shot, so a shot that passed in
    # round 1 is not handed a round-2 frame nobody asked for.
    for round_no, directory in reversed(round_dirs(out_dir, "prompts")):
        if any(
            block["shot_id"] == shot_id
            for path in directory.glob("*.txt")
            for block in parse_prompt_file(path)["blocks"]
        ):
            target = round_no
            break
    reviewed = out_dir / "critiques" / f"round-{target}" / f"{shot_id}.critique.json"
    if reviewed.exists():
        return (409, {
            "error": f"The round {target} frame for {shot_id} has been reviewed, so it "
                     "stays as it is. Ask Claude to revise the prompt, then drop the new "
                     f"frame for round {target + 1}."
        })
    directory = out_dir / "frames" / f"round-{target}"
    directory.mkdir(parents=True, exist_ok=True)
    for old in IMAGE_EXTS:
        stale = directory / f"{shot_id}.{old}"
        if stale.exists():
            stale.unlink()
    path = directory / f"{shot_id}.{ext}"
    path.write_bytes(body)
    return (200, {"saved": str(path.relative_to(out_dir))})


def serve(out_dir: Path, port: int, open_browser: bool) -> int:
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from urllib.parse import parse_qs, unquote, urlparse

    root = out_dir.resolve()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):  # the terminal stays readable
            pass

        def send(self, status: int, body: bytes, kind: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def local(self) -> bool:
            # Only a page this server sent may write a frame. A request from any other
            # site carries that site's Origin and is refused.
            origin = self.headers.get("Origin")
            host = self.headers.get("Host", "")
            return origin is None or origin in (f"http://{host}",)

        def do_GET(self):
            url = urlparse(self.path)
            if url.path in ("/", "/board.html"):
                data, _ = build(root, live=True)
                self.send(200, render(data).encode("utf-8"), "text/html; charset=utf-8")
                return
            if url.path == "/__stamp":
                self.send(200, tree_stamp(root).encode(), "text/plain")
                return
            target = (root / unquote(url.path).lstrip("/")).resolve()
            if root not in target.parents or not target.is_file():
                self.send(404, b"not found", "text/plain")
                return
            ext = target.suffix.lstrip(".").lower()
            kind = MIME.get(ext) or {
                "json": "application/json", "md": "text/plain; charset=utf-8",
                "txt": "text/plain; charset=utf-8", "html": "text/html; charset=utf-8",
                "mp4": "video/mp4", "jsonl": "text/plain; charset=utf-8",
            }.get(ext, "application/octet-stream")
            self.send(200, target.read_bytes(), kind)

        def do_POST(self):
            url = urlparse(self.path)
            if url.path != "/__frame" or not self.local():
                self.send(403, b'{"error":"refused"}', "application/json")
                return
            shot_id = (parse_qs(url.query).get("shot") or [""])[0]
            length = int(self.headers.get("Content-Length") or 0)
            if length > MAX_FRAME_BYTES:
                self.send(413, b'{"error":"image is over 40 MB"}', "application/json")
                return
            status, payload = save_frame(
                root, shot_id, self.headers.get("Content-Type", ""), self.rfile.read(length)
            )
            self.send(status, json.dumps(payload).encode(), "application/json")

    server = None
    for candidate in range(port, port + 20):
        try:
            server = ThreadingHTTPServer(("127.0.0.1", candidate), Handler)
            break
        except OSError:
            continue
    if server is None:
        print(f"ERROR: no free port between {port} and {port + 19}")
        return 1
    address = f"http://127.0.0.1:{server.server_address[1]}/"
    print(f"  live board at {address}")
    print("  it reloads when files in the folder change. Ctrl-C stops it.")
    if open_browser:
        webbrowser.open(address)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print()
    finally:
        server.server_close()
    return 0


# --------------------------------------------------------------------------
# Selftest
# --------------------------------------------------------------------------

def selftest() -> int:
    import shutil
    import tempfile

    worked = REPO_ROOT / "skills" / "visual-asset-critic" / "examples" / "worked-run"
    pinned = "2026-07-30T00:00:00Z"
    data, _ = build(worked, rendered_at=pinned)
    html_a = render(data)
    html_b = render(build(worked, rendered_at=pinned)[0])
    by_id = {s["id"]: s for s in data["shots"]}

    with tempfile.TemporaryDirectory() as tmp:
        bare = Path(tmp) / "bare"
        bare.mkdir()
        for name in ("shots.json", "text-overlays.json", "brand-lock.snapshot.md"):
            shutil.copy(worked / name, bare / name)
        bare_data, _ = build(bare, rendered_at=pinned)

        hostile = Path(tmp) / "hostile"
        shutil.copytree(worked, hostile)
        doc = json.loads((hostile / "shots.json").read_text())
        doc["shots"][0]["subject"] = "</script><script>alert(1)</script>"
        (hostile / "shots.json").write_text(json.dumps(doc))
        hostile_html = render(build(hostile, rendered_at=pinned)[0])

        drop = Path(tmp) / "drop"
        shutil.copytree(worked, drop)
        png = (worked / "frames" / "round-1" / "shot_01.png").read_bytes()
        reviewed = save_frame(drop, "shot_02", "image/png", png)
        outside = save_frame(drop, "../shot_01", "image/png", png)
        wrong_type = save_frame(drop, "shot_01", "text/html", b"<html>")
        shutil.rmtree(drop / "critiques")
        fresh = save_frame(drop, "shot_02", "image/jpeg", png)

        edited = Path(tmp) / "edited"
        shutil.copytree(worked, edited)
        with (edited / "shots.json").open("a") as handle:
            handle.write("\n")
        edited_files = {f["path"]: f["state"] for f in build(edited, rendered_at=pinned)[0]["files"]}

    checks = [
        ("two renders with a pinned timestamp are identical", html_a == html_b),
        ("reads every shot", len(data["shots"]) == 2),
        ("a shot accepted in round 1 is accept", by_id["shot_01"]["status"] == "accept"),
        ("a shot revised and passed in round 2 is accept", by_id["shot_02"]["status"] == "accept"),
        ("keeps both rounds of a revised shot's frames", len(by_id["shot_02"]["frames"]) == 2),
        ("keeps both rounds of its critiques", [c["verdict"] for c in by_id["shot_02"]["critiques"]] == ["REVISE", "ACCEPT"]),
        ("reads the revision prompt and its fix lines",
         by_id["shot_02"]["prompts"]["flux"][-1]["revised"] and len(by_id["shot_02"]["prompts"]["flux"][-1]["fixes"]) == 2),
        ("a prompt body carries no comment line",
         all(not line.startswith("#") for runs in by_id["shot_01"]["prompts"].values() for p in runs for line in p["body"].splitlines())),
        ("names the generator from the capability matrix", data["generators"][0]["name"] == "Flux"),
        ("files that match run.json are marked match",
         {f["path"]: f["state"] for f in data["files"]}["shots.json"] == "match"),
        ("a file edited after the run is marked changed", edited_files["shots.json"] == "changed"),
        ("a storyboard with no run.json, prompts or frames still builds",
         [s["status"] for s in bare_data["shots"]] == ["plan", "plan"]),
        ("and its next step is to write prompts", bare_data["next"]["title"] == "Write the prompts"),
        ("a finished run says so", data["next"]["title"] == "Every shot is accepted"),
        ("the Markdown copy names every shot",
         all(s["id"] in data["markdown"] for s in data["shots"])),
        ("a subject cannot close the data element",
         "</script><script>alert(1)" not in hostile_html),
        ("a reviewed frame is never replaced", reviewed[0] == 409),
        ("a shot id cannot leave the frames folder", outside[0] == 400),
        ("only images are saved", wrong_type[0] == 415),
        ("a dropped frame is saved to the shot's round", fresh == (200, {"saved": "frames/round-2/shot_02.jpg"})),
        ("carries no unfilled placeholder", "__TITLE__" not in html_a and "/*__DATA__*/" not in html_a),
    ]
    ok = True
    for label, passed in checks:
        print(f"  {'ok  ' if passed else 'FAIL'}  selftest: {label}")
        ok = ok and passed
    print()
    print("Selftest passed." if ok else "Selftest FAILED.")
    return 0 if ok else 1


def main() -> int:
    p = argparse.ArgumentParser(description="Render a shotkit output folder into board.html.")
    p.add_argument("output_dir", nargs="?", type=Path, help="Folder that holds shots.json")
    p.add_argument("--out", default="board.html", help="Output filename, relative to output_dir")
    p.add_argument("--open", action="store_true", help="Open the board in a browser")
    p.add_argument("--serve", action="store_true", help="Serve a live board on localhost")
    p.add_argument("--port", type=int, default=4173, help="Port for --serve (default 4173)")
    p.add_argument("--inline-images", action="store_true", help="Embed frames so the file is portable on its own")
    p.add_argument("--no-web-fonts", action="store_true", help="Do not link overlay fonts from Google Fonts")
    p.add_argument("--rendered-at", help="Pin the render timestamp (UTC ISO-8601)")
    p.add_argument("--selftest", action="store_true", help="Prove the board's guarantees")
    p.add_argument("--example", action="store_true", help="Open the board of the bundled finished run")
    args = p.parse_args()

    if args.selftest:
        return selftest()
    if args.example:
        if not (EXAMPLE_DIR / "shots.json").exists():
            print(f"ERROR: the example run is not at {EXAMPLE_DIR}")
            return 1
        args.output_dir, args.open = EXAMPLE_DIR, True
    if args.output_dir is None:
        p.error("output_dir is required unless --selftest is given")
    out_dir: Path = args.output_dir
    if not (out_dir / "shots.json").exists():
        print(f"ERROR: shots.json not found in {out_dir}")
        return 1

    data, warnings = build(
        out_dir, inline_images=args.inline_images, rendered_at=args.rendered_at,
        web_fonts=not args.no_web_fonts,
    )
    out_path = out_dir / args.out
    out_path.write_text(render(data), encoding="utf-8")
    print(f"  wrote {out_path}")
    for warn in warnings:
        print(f"  warn  {warn}")
    counts = {}
    for shot in data["shots"]:
        counts[shot["status"]] = counts.get(shot["status"], 0) + 1
    print("  " + ", ".join(f"{n} {k}" for k, n in counts.items()) + f". Next: {data['next']['title']}.")
    if args.serve:
        return serve(out_dir, args.port, args.open)
    if args.open:
        webbrowser.open(out_path.resolve().as_uri())
    return 0


if __name__ == "__main__":
    sys.exit(main())
