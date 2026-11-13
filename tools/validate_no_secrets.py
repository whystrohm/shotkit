#!/usr/bin/env python3
"""
Fail if a key or a secret is in the repo.

Shotkit is bring-your-own-key: a fal key lives in the user's environment or in a .env
file that git ignores. This check is what stops one from being committed by accident,
in this repo or in a project that uses it. It needs Python 3 and nothing else.

    python tools/validate_no_secrets.py            # every file git tracks, or would add
    python tools/validate_no_secrets.py path ...   # these files or folders
    python tools/validate_no_secrets.py --selftest

It looks for key shapes (fal, OpenAI, Anthropic, AWS, GitHub, Google, Slack, private
key blocks), for NAME=value lines whose name says KEY, SECRET, TOKEN or PASSWORD, and for
files that should never be tracked, such as .env. A value that is plainly a placeholder
passes. A finding is printed as file and line with the value cut to four characters.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SHAPES = [
    ("fal key", re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}:[0-9a-f]{32}\b")),
    ("Anthropic key", re.compile(r"\bsk-ant-[A-Za-z0-9_\-]{20,}")),
    ("OpenAI key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_\-]{32,}")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}|\bgithub_pat_[A-Za-z0-9_]{40,}")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9\-]{20,}")),
    ("private key", re.compile(r"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----")),
]
ASSIGN = re.compile(
    r"""\b([A-Z][A-Z0-9_]*(?:KEY|SECRET|TOKEN|PASSWORD|PASSWD)[A-Z0-9_]*)\s*[:=]\s*['"]?([^\s'"#,;]{12,})"""
)
PLACEHOLDER = re.compile(
    r"your|example|placeholder|changeme|xxxx|\.\.\.|<|>|\$\{|\$\(|\$[A-Z_]|test-key|redacted|dummy|sample|none|null|true|false",
    re.IGNORECASE,
)
NEVER_TRACK = re.compile(r"(^|/)\.env(\.(?!example$|sample$|template$)[^/]*)?$|\.pem$|(^|/)id_(rsa|ed25519)$")
SKIP_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".mp4", ".mov", ".pdf", ".zip", ".woff", ".woff2", ".ico"}


def scan_text(text: str) -> list[tuple[int, str, str]]:
    """(line number, what, the first four characters) for every finding."""
    found = []
    for number, line in enumerate(text.splitlines(), 1):
        if len(line) > 4000:
            continue
        for label, shape in SHAPES:
            hit = shape.search(line)
            if hit and not PLACEHOLDER.search(hit.group(0)):
                found.append((number, label, hit.group(0)[:4]))
        for hit in ASSIGN.finditer(line):
            value = hit.group(2)
            # A real secret is long and mixes character kinds. Code that reads a key
            # (os.environ[...], find_key(...)) and prose are not.
            if PLACEHOLDER.search(value) or re.search(r"[()\[\]{}.]", value):
                continue
            if not (re.search(r"[0-9]", value) and re.search(r"[A-Za-z]", value)):
                continue
            found.append((number, f"{hit.group(1)} has a value", value[:4]))
    return found


def tracked_files() -> list[Path]:
    try:
        out = subprocess.run(
            ["git", "-C", str(ROOT), "ls-files", "--cached", "--others", "--exclude-standard"],
            capture_output=True, text=True, check=True,
        ).stdout
        return [ROOT / line for line in out.splitlines() if line]
    except (OSError, subprocess.CalledProcessError):
        return [p for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.parts and ".venv" not in p.parts]


def scan(paths: list[Path]) -> list[str]:
    problems = []
    for path in paths:
        if path.is_dir():
            problems.extend(scan([p for p in path.rglob("*") if p.is_file() and ".venv" not in p.parts and ".git" not in p.parts]))
            continue
        try:
            shown = path.resolve().relative_to(ROOT)
        except ValueError:
            shown = path
        if NEVER_TRACK.search(str(shown).replace("\\", "/")):
            problems.append(f"{shown}: this file should not be in git. Add it to .gitignore.")
            continue
        if path.suffix.lower() in SKIP_EXT or not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for number, label, start in scan_text(text):
            problems.append(f"{shown}:{number}: {label} (starts {start}...)")
    return problems


def selftest() -> int:
    # Fixtures are built in pieces so this file does not trip its own check.
    fal = "0a1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d:" + "0123456789abcdef" * 2
    cases = [
        ("catches a fal key", bool(scan_text(f"FAL_KEY={fal}"))),
        ("catches a fal key with no name beside it", bool(scan_text(f"key is {fal} ok"))),
        ("catches an OpenAI-shaped key", bool(scan_text("sk-" + "aB3" * 14))),
        ("catches a GitHub token", bool(scan_text("ghp_" + "aB3" * 12))),
        ("catches a private key block", bool(scan_text("-----BEGIN RSA " + "PRIVATE KEY-----"))),
        ("catches a named secret with a real-looking value", bool(scan_text("API_" + 'SECRET="q8Zp2Lm9' + 'Xc4Vb7Nn"'))),
        ("passes the placeholder the guide prints", not scan_text('export FAL_KEY="your-key"')),
        ("passes FAL_KEY=... in prose", not scan_text("put FAL_KEY=... in a .env file")),
        ("passes code that reads a key", not scan_text('key = os.environ["FAL_KEY"].strip()')),
        ("passes a SHA-256 in run.json", not scan_text('"shots_sha256": "' + "ab12" * 16 + '"')),
        ("flags a tracked .env", bool(NEVER_TRACK.search(".env")) and bool(NEVER_TRACK.search("app/.env.local"))),
        ("allows .env.example", not NEVER_TRACK.search(".env.example")),
        ("never prints more than four characters of a finding", scan_text(f"FAL_KEY={fal}")[0][2] == fal[:4]),
    ]
    ok = True
    for label, passed in cases:
        print(f"  {'ok  ' if passed else 'FAIL'}  selftest: {label}")
        ok = ok and passed
    print()
    print("Selftest passed." if ok else "Selftest FAILED.")
    return 0 if ok else 1


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        return selftest()
    paths = [Path(a) for a in args] or tracked_files()
    problems = scan(paths)
    if problems:
        for line in problems:
            print(f"  FAIL  {line}")
        print(f"\nFAILED: {len(problems)} possible secret(s). Remove them, and rotate any key that was real.")
        return 1
    print(f"  ok    no keys or secrets in {len(paths)} path(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
