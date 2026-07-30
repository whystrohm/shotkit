#!/usr/bin/env python3
"""
Shared helpers for the shotkit tools. Standard library only.

Everything here exists because more than one tool needs it. Hashing, brand-lock
parsing, and the capability-id list were duplicated or absent before; keeping one
copy is what stops the tools from disagreeing about what a brand-lock palette is
or which generator ids are real.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

CAPABILITIES_PATH = (
    REPO_ROOT / "skills" / "visual-prompt-forge" / "adapters" / "_capabilities.json"
)

# Roles tools/shots-to-html.py maps onto CSS variables. Documented in
# docs/brand-lock-anatomy.md so a brand-lock author knows the names are load-bearing.
PALETTE_ROLES = ("background", "ink", "accent", "muted", "rule")

RUN_ID_RE = re.compile(r"^([0-9]{8}T[0-9]{6}Z)-[0-9a-f]{8}$")
ISO_INSTANT_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SHOT_ID_RE = re.compile(r"^shot_[0-9]{2,3}$")
TEXT_ID_RE = re.compile(r"^text_[0-9]{2,3}$")

HEX_RE = re.compile(r"#[0-9A-Fa-f]{6}")
PLACEHOLDER_HEX_RE = re.compile(r"#_{6}")

# | Role | `#RRGGBB` | Use | rows in a brand-lock Palette table.
PALETTE_ROW_RE = re.compile(
    r"^\|\s*([A-Za-z][A-Za-z0-9\s()/-]*?)\s*\|\s*`?(#(?:[0-9A-Fa-f]{6}|_{6}))`?\s*\|"
)

SNAPSHOT_TAKEN_RE = re.compile(r"<!--\s*snapshot taken:\s*(.+?)\s*-->")
SNAPSHOT_SOURCE_RE = re.compile(r"<!--\s*source:\s*(.+?)\s*-->")

IMAGE_EXTS = ("png", "jpg", "jpeg", "webp")


# --------------------------------------------------------------------------
# Hashing
# --------------------------------------------------------------------------

def sha256_file(path: Path) -> str:
    """SHA-256 of a file's bytes, read in chunks so large frames do not load whole."""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    """SHA-256 of a string, UTF-8 encoded."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------
# Run identity
# --------------------------------------------------------------------------

def make_run_id(now: datetime | None = None, nonce: str | None = None) -> str:
    """Build a run_id. Pass `now` and `nonce` to make it reproducible in tests."""
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    if nonce is None:
        nonce = sha256_text(now.isoformat() + str(id(now)))[:8]
    return f"{stamp}-{nonce}"


def iso_instant(now: datetime | None = None) -> str:
    """UTC ISO-8601 to second precision with a trailing Z."""
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%SZ")


def run_id_timestamp(run_id: str) -> str | None:
    """Extract the compact timestamp from a run_id, or None if malformed."""
    m = RUN_ID_RE.match(run_id or "")
    return m.group(1) if m else None


# --------------------------------------------------------------------------
# JSON loading
# --------------------------------------------------------------------------

def load_json(path: Path) -> tuple[dict | list | None, str | None]:
    """Return (data, error). Exactly one of the two is None."""
    if not path.exists():
        return (None, f"file does not exist: {path}")
    try:
        return (json.loads(path.read_text(encoding="utf-8")), None)
    except json.JSONDecodeError as e:
        return (None, f"invalid JSON: {e}")
    except OSError as e:
        return (None, f"cannot read: {e}")


# --------------------------------------------------------------------------
# Capability matrix
# --------------------------------------------------------------------------

def capability_ids(caps_path: Path | None = None) -> set[str]:
    """Generator ids from the capability matrix. Empty set if it cannot be read."""
    data, err = load_json(caps_path or CAPABILITIES_PATH)
    if err or not isinstance(data, dict):
        return set()
    return {
        g["id"]
        for g in data.get("generators", [])
        if isinstance(g, dict) and isinstance(g.get("id"), str)
    }


def capability_map(caps_path: Path | None = None) -> dict[str, dict]:
    """Generator id to its full capability entry."""
    data, err = load_json(caps_path or CAPABILITIES_PATH)
    if err or not isinstance(data, dict):
        return {}
    return {
        g["id"]: g
        for g in data.get("generators", [])
        if isinstance(g, dict) and isinstance(g.get("id"), str)
    }


# --------------------------------------------------------------------------
# Brand-lock parsing
# --------------------------------------------------------------------------

def parse_palette(text: str) -> dict[str, str]:
    """Role (lowercased) to hex value, from a brand-lock Palette table."""
    palette: dict[str, str] = {}
    for line in text.splitlines():
        m = PALETTE_ROW_RE.match(line)
        if m:
            palette[m.group(1).strip().lower()] = m.group(2).strip()
    return palette


def palette_hexes(text: str) -> set[str]:
    """Every real (non-placeholder) hex in a brand-lock, lowercased."""
    return {h.lower() for h in HEX_RE.findall(text)}


def is_unconfigured(text: str) -> bool:
    """True when the brand-lock still carries template placeholders in its palette."""
    return bool(PLACEHOLDER_HEX_RE.search(text))


def parse_typography(text: str) -> dict[str, str | None]:
    """
    Pull font names out of a brand-lock Typography section.

    Matches the documented format:
        **Display font:** `Inter Black 900`, headline weight, ...
        **Body font:** `Inter Medium 500`, body copy, ...
        **Mono font:** `JetBrains Mono Regular`, code, data, ...

    Mono is optional. A brand-lock that declares one has three legal overlay fonts,
    not two, which is why the font check reads all three rather than assuming a pair.
    """
    out: dict[str, str | None] = {
        "display_font": None,
        "body_font": None,
        "mono_font": None,
    }
    # The value has to be backticked and sit immediately after the label. That is what
    # separates a real declaration from the template's instructional prose
    # ("**Display font:** font name, weights used (e.g. `Inter Black 900`)"), which
    # would otherwise resolve to the example font.
    for key, label in (
        ("display_font", "Display"),
        ("body_font", "Body"),
        ("mono_font", "Mono"),
    ):
        pattern = re.compile(
            r"^\*\*" + label + r"\s+font[^:*]*:?\*\*[ \t]*`([^`\n]+)`",
            re.IGNORECASE | re.MULTILINE,
        )
        m = pattern.search(text)
        if m:
            value = m.group(1).strip()
            if value and not value.startswith("_"):
                out[key] = value
    return out


def parse_snapshot_header(text: str) -> dict[str, str | None]:
    """The two provenance comments storyboard-architect writes at the top of a snapshot."""
    taken = SNAPSHOT_TAKEN_RE.search(text)
    source = SNAPSHOT_SOURCE_RE.search(text)
    return {
        "snapshot_taken": taken.group(1).strip() if taken else None,
        "source": source.group(1).strip() if source else None,
    }


# --------------------------------------------------------------------------
# Output-tree conventions
# --------------------------------------------------------------------------

def round_dirs(output_dir: Path, kind: str) -> list[tuple[int, Path]]:
    """
    Sorted (round_number, path) for output_dir/<kind>/round-N directories.

    `kind` is 'frames', 'critiques', or 'prompts'.
    """
    base = output_dir / kind
    if not base.is_dir():
        return []
    found: list[tuple[int, Path]] = []
    for child in base.iterdir():
        if child.is_dir() and child.name.startswith("round-"):
            suffix = child.name[len("round-"):]
            if suffix.isdigit():
                found.append((int(suffix), child))
    return sorted(found)


def find_frame(output_dir: Path, shot_id: str, round_no: int | None = None) -> Path | None:
    """
    Locate a frame for a shot by the path convention.

    Prefers the highest-numbered round under frames/, then falls back to the
    legacy flat generated/ directory so pre-3.0.0 projects still render.
    """
    candidates = round_dirs(output_dir, "frames")
    if round_no is not None:
        candidates = [(n, p) for n, p in candidates if n == round_no]
    for _, directory in reversed(candidates):
        for ext in IMAGE_EXTS:
            candidate = directory / f"{shot_id}.{ext}"
            if candidate.exists():
                return candidate
    legacy = output_dir / "generated"
    if legacy.is_dir():
        for ext in IMAGE_EXTS:
            candidate = legacy / f"{shot_id}.{ext}"
            if candidate.exists():
                return candidate
    return None


def critique_paths(output_dir: Path) -> list[Path]:
    """
    Every critique file in an output tree, newest layout first.

    New layout: critiques/round-N/shot_NN.critique.json
    Legacy:     critique.json at the output root
    """
    found: list[Path] = []
    for _, directory in round_dirs(output_dir, "critiques"):
        found.extend(sorted(directory.glob("*.critique.json")))
        found.extend(sorted(directory.glob("*.json")))
    legacy = output_dir / "critique.json"
    if legacy.exists():
        found.append(legacy)
    # Preserve order, drop duplicates from the two globs above.
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in found:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(path)
    return unique


def as_overlay_ids(value) -> list[str]:
    """Normalise shots.json on_screen_text (null, string, or array) to a list."""
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [v for v in value if isinstance(v, str)]
    return []


def as_shot_ids(value) -> list[str]:
    """Normalise text-overlays.json shot_id (string or array) to a list."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [v for v in value if isinstance(v, str)]
    return []
