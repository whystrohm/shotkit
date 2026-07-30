#!/usr/bin/env python3
"""Copy a shot prompt from a shotkit prompts file to the system clipboard.

Handles both file shapes the forge writes: a full pass, and a revision file where each
shot block carries `# fix [...]` annotations above the prompt. Comment lines inside a
block are treated as annotations and never land in the clipboard, so what you paste
into a generator is the prompt and nothing else.

Usage:
  python tools/copy-prompt.py output/prompts/round-1/flux.txt
  python tools/copy-prompt.py output/prompts/round-2/revised-flux.txt --shot shot_02
  python tools/copy-prompt.py output/prompts/round-1/flux.txt --list
  python tools/copy-prompt.py --selftest
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

# A shot block opens with the shot id near the start of a comment line. The forge's
# revision format prefixes it, so both of these are headers:
#   # shot_03, reframe, 11.0-16.0s, MCU eye-level push
#   # shot_03, promise, 3.0-8.0s, MCU eye-level push, revision (was REVISE)
#   # Revision of shot_03 (was REVISE)
SHOT_HEADER = re.compile(
    r"^#\s*(?:revision\s+of\s+)?(shot_\d{2,3})\b(.*)$", re.IGNORECASE
)
COMMENT_LINE = re.compile(r"^\s*#")


class Block:
    __slots__ = ("shot_id", "header", "annotations", "body")

    def __init__(self, shot_id: str, header: str) -> None:
        self.shot_id = shot_id
        self.header = header
        self.annotations: list[str] = []
        self.body: list[str] = []

    def prompt(self) -> str:
        return "\n".join(self.body).strip()

    def label(self) -> str:
        note = f"  [{len(self.annotations)} fix note(s)]" if self.annotations else ""
        return f"{self.header}{note}  ({len(self.prompt())} chars)"


def get_clipboard_command() -> list[str] | None:
    """Return the platform-appropriate clipboard command, or None if unavailable."""
    if sys.platform == "darwin":
        return ["pbcopy"]
    if sys.platform.startswith("linux"):
        if shutil.which("xclip"):
            return ["xclip", "-selection", "clipboard"]
        if shutil.which("xsel"):
            return ["xsel", "--clipboard", "--input"]
        return None
    if sys.platform == "win32":
        return ["clip"]
    return None


def parse_prompt_text(text: str) -> list[Block]:
    """Split a prompt file into shot blocks, separating annotations from prompt body."""
    blocks: list[Block] = []
    current: Block | None = None

    for line in text.splitlines():
        match = SHOT_HEADER.match(line)
        if match:
            current = Block(match.group(1), line.strip())
            blocks.append(current)
            continue
        if current is None:
            continue  # file-level header comments, before the first shot block
        if COMMENT_LINE.match(line):
            current.annotations.append(line.strip())
        else:
            current.body.append(line)

    return [b for b in blocks if b.prompt()]


def parse_prompt_file(path: Path) -> list[Block]:
    return parse_prompt_text(path.read_text(encoding="utf-8"))


def copy_to_clipboard(text: str) -> bool:
    cmd = get_clipboard_command()
    if not cmd:
        return False
    proc = subprocess.run(cmd, input=text.encode("utf-8"))
    return proc.returncode == 0


def print_clipboard_help() -> None:
    if sys.platform.startswith("linux"):
        print("No clipboard utility found. Install xclip or xsel.", file=sys.stderr)
    else:
        print("No clipboard utility found on this platform.", file=sys.stderr)


def list_blocks(blocks: list[Block]) -> None:
    for i, block in enumerate(blocks, 1):
        print(f"{i}. {block.label()}")
        for note in block.annotations:
            print(f"     {note}")


def select_interactively(blocks: list[Block]) -> Block | None:
    list_blocks(blocks)
    try:
        raw = input(f"\nWhich shot? (1-{len(blocks)}): ").strip()
        idx = int(raw) - 1
    except (ValueError, EOFError):
        print("Invalid selection.", file=sys.stderr)
        return None
    if not (0 <= idx < len(blocks)):
        print("Selection out of range.", file=sys.stderr)
        return None
    return blocks[idx]


STANDARD_FIXTURE = """\
# Storyboard: Fixture
# Generator: flux
# Aspect: 9:16

# shot_01, hook, 0.0-2.0s, MCU eye-level static
first prompt body

# shot_02, pain, 2.0-6.0s, MS eye-level push
second prompt body
"""

REVISION_FIXTURE = """\
# Storyboard: Fixture
# Generator: flux
# Round: 2
# Revision of round 1. Shots not listed here already passed.

# shot_02, pain, 2.0-6.0s, MCU eye-level push, revision (was REVISE)
# fix [Shot Spec, major]: framing MS -> MCU
# fix [Technical, re-roll]: hand was malformed
revised prompt body
"""

LEGACY_REVISION_FIXTURE = """\
# Revision of shot_03 (was REVISE)
# fix [Series Lock, major]: added 'salt-and-pepper hair' to the character anchor
legacy revised prompt body
"""


def selftest() -> int:
    ok = True

    cases = [
        ("standard file yields both shots", STANDARD_FIXTURE, ["shot_01", "shot_02"]),
        ("revision file yields its shot", REVISION_FIXTURE, ["shot_02"]),
        ("legacy revision header is tolerated", LEGACY_REVISION_FIXTURE, ["shot_03"]),
    ]
    for label, fixture, expected in cases:
        got = [b.shot_id for b in parse_prompt_text(fixture)]
        if got == expected:
            print(f"  ok    selftest: {label}")
        else:
            print(f"  FAIL  selftest: {label} -> expected {expected}, got {got}")
            ok = False

    blocks = parse_prompt_text(REVISION_FIXTURE)
    body = blocks[0].prompt()
    if body == "revised prompt body":
        print("  ok    selftest: fix annotations stay out of the copied prompt")
    else:
        print(f"  FAIL  selftest: prompt body was {body!r}")
        ok = False
    if len(blocks[0].annotations) == 2:
        print("  ok    selftest: fix annotations are captured for display")
    else:
        print(f"  FAIL  selftest: expected 2 annotations, got {blocks[0].annotations}")
        ok = False

    header_only = parse_prompt_text("# Storyboard: x\n# Generator: flux\n")
    if header_only == []:
        print("  ok    selftest: a file with no shot blocks yields nothing")
    else:
        print(f"  FAIL  selftest: expected no blocks, got {header_only}")
        ok = False

    # The shipped worked run must be readable by this tool, both rounds.
    repo_root = Path(__file__).resolve().parent.parent
    worked = repo_root / "skills" / "visual-asset-critic" / "examples" / "worked-run"
    for rel, expected in (
        ("prompts/round-1/flux.txt", ["shot_01", "shot_02"]),
        ("prompts/round-2/revised-flux.txt", ["shot_02"]),
    ):
        path = worked / rel
        if not path.exists():
            print(f"  FAIL  selftest: bundled fixture missing: {rel}")
            ok = False
            continue
        got = [b.shot_id for b in parse_prompt_file(path)]
        if got == expected:
            print(f"  ok    selftest: bundled {rel} parses")
        else:
            print(f"  FAIL  selftest: bundled {rel} -> expected {expected}, got {got}")
            ok = False

    print()
    print("Selftest passed." if ok else "Selftest FAILED.")
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Copy a shot prompt from a shotkit prompts file to the clipboard."
    )
    parser.add_argument(
        "file",
        nargs="?",
        type=Path,
        help="Path to a prompt file (e.g. output/prompts/round-1/flux.txt)",
    )
    parser.add_argument(
        "--shot", help="Shot ID to copy (e.g. shot_03). If omitted, prompts interactively."
    )
    parser.add_argument(
        "--list", action="store_true", help="List shots and exit. Does not copy."
    )
    parser.add_argument(
        "--selftest", action="store_true", help="Prove both file shapes parse"
    )
    args = parser.parse_args()

    if args.selftest:
        return selftest()
    if args.file is None:
        parser.error("file is required unless --selftest is given")

    if not args.file.exists():
        print(f"File not found: {args.file}", file=sys.stderr)
        return 1

    blocks = parse_prompt_file(args.file)
    if not blocks:
        print(f"No shot blocks found in {args.file}.", file=sys.stderr)
        print(
            "Expected a comment line naming a shot, e.g. "
            "'# shot_03, beat, timing, framing'.",
            file=sys.stderr,
        )
        return 1

    if args.list:
        list_blocks(blocks)
        return 0

    if args.shot:
        matches = [b for b in blocks if b.shot_id == args.shot]
        if not matches:
            print(f'Shot "{args.shot}" not found in {args.file}.', file=sys.stderr)
            print("Available shots:", file=sys.stderr)
            for block in blocks:
                print(f"  {block.shot_id}", file=sys.stderr)
            return 1
        if len(matches) > 1:
            print(
                f'Shot "{args.shot}" appears {len(matches)} times in {args.file}; '
                f"copying the last block.",
                file=sys.stderr,
            )
        selection = matches[-1]
    else:
        result = select_interactively(blocks)
        if result is None:
            return 1
        selection = result

    body = selection.prompt()
    if copy_to_clipboard(body):
        print(f"Copied {selection.shot_id} prompt to clipboard ({len(body)} chars).")
        for note in selection.annotations:
            print(f"  {note}")
        return 0

    print_clipboard_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
