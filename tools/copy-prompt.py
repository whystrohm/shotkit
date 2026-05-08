#!/usr/bin/env python3
"""Copy a shot prompt from a shotkit prompts file to the system clipboard.

Usage:
  python tools/copy-prompt.py output/prompts/midjourney.txt
  python tools/copy-prompt.py output/prompts/midjourney.txt --shot shot_03
  python tools/copy-prompt.py output/prompts/midjourney.txt --list
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path


SHOT_HEADER = re.compile(r'^#\s*(shot_\d+)\b(.*)$')


def get_clipboard_command() -> list[str] | None:
    """Return the platform-appropriate clipboard command, or None if unavailable."""
    if sys.platform == 'darwin':
        return ['pbcopy']
    if sys.platform.startswith('linux'):
        if shutil.which('xclip'):
            return ['xclip', '-selection', 'clipboard']
        if shutil.which('xsel'):
            return ['xsel', '--clipboard', '--input']
        return None
    if sys.platform == 'win32':
        return ['clip']
    return None


def parse_prompt_file(path: Path) -> list[tuple[str, str, str]]:
    """Parse a prompt file into a list of (shot_id, header_line, prompt_body) tuples."""
    text = path.read_text(encoding='utf-8')
    shots: list[tuple[str, str, str]] = []
    current_id: str | None = None
    current_header: str = ''
    current_body: list[str] = []

    for line in text.splitlines():
        m = SHOT_HEADER.match(line)
        if m:
            if current_id is not None:
                shots.append((current_id, current_header, '\n'.join(current_body).strip()))
            current_id = m.group(1)
            current_header = line.strip()
            current_body = []
        elif current_id is not None:
            current_body.append(line)

    if current_id is not None:
        shots.append((current_id, current_header, '\n'.join(current_body).strip()))

    return shots


def copy_to_clipboard(text: str) -> bool:
    """Pipe text into the platform clipboard. Returns True on success."""
    cmd = get_clipboard_command()
    if not cmd:
        return False
    proc = subprocess.run(cmd, input=text.encode('utf-8'))
    return proc.returncode == 0


def print_clipboard_help() -> None:
    if sys.platform.startswith('linux'):
        print('No clipboard utility found. Install xclip or xsel.', file=sys.stderr)
    else:
        print('No clipboard utility found on this platform.', file=sys.stderr)


def list_shots(shots: list[tuple[str, str, str]]) -> None:
    for i, (sid, header, body) in enumerate(shots, 1):
        print(f'{i}. {header}  ({len(body)} chars)')


def select_interactively(shots: list[tuple[str, str, str]]) -> tuple[str, str, str] | None:
    list_shots(shots)
    try:
        raw = input(f'\nWhich shot? (1-{len(shots)}): ').strip()
        idx = int(raw) - 1
    except (ValueError, EOFError):
        print('Invalid selection.', file=sys.stderr)
        return None
    if not (0 <= idx < len(shots)):
        print('Selection out of range.', file=sys.stderr)
        return None
    return shots[idx]


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Copy a shot prompt from a shotkit prompts file to the clipboard.'
    )
    parser.add_argument(
        'file',
        type=Path,
        help='Path to a prompt file (e.g. output/prompts/midjourney.txt)',
    )
    parser.add_argument(
        '--shot',
        help='Shot ID to copy (e.g. shot_03). If omitted, prompts interactively.',
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List shots and exit. Does not copy.',
    )
    args = parser.parse_args()

    if not args.file.exists():
        print(f'File not found: {args.file}', file=sys.stderr)
        return 1

    shots = parse_prompt_file(args.file)
    if not shots:
        print(f'No shot blocks found in {args.file}.', file=sys.stderr)
        print('Expected lines like: # shot_03, beat, timing, framing', file=sys.stderr)
        return 1

    if args.list:
        list_shots(shots)
        return 0

    if args.shot:
        match = next((s for s in shots if s[0] == args.shot), None)
        if not match:
            print(f'Shot "{args.shot}" not found in {args.file}.', file=sys.stderr)
            print('Available shots:', file=sys.stderr)
            for sid, _, _ in shots:
                print(f'  {sid}', file=sys.stderr)
            return 1
        selection = match
    else:
        result = select_interactively(shots)
        if result is None:
            return 1
        selection = result

    sid, _, body = selection

    if not body:
        print(f'Shot {sid} has no prompt body to copy.', file=sys.stderr)
        return 1

    if copy_to_clipboard(body):
        print(f'Copied {sid} prompt to clipboard ({len(body)} chars).')
        return 0

    print_clipboard_help()
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
