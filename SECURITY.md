# Security

## Reporting a problem

Write to [hello@whystrohm.com](mailto:hello@whystrohm.com) with "Shotkit security" in the
subject. Please do not open a public issue for a security problem. Say what you found,
how to reproduce it and which version you ran (`sk doctor` prints it). You will get a
reply within three working days.

The latest release is the supported version.

## What Shotkit touches

- **Your files.** Shotkit reads and writes inside the output folder you point it at, and
  installs into `~/.claude/` or `./.claude/`.
- **The network.** Nothing by default except Google Fonts links on the preview and the
  board, which `--no-web-fonts` turns off. `sk generate` talks to fal.ai, and only when
  you run it with `--yes`.
- **The live board.** `sk board --serve` listens on `127.0.0.1` only. It refuses writes
  from any other site, saves only image files, only into `frames/`, and does not serve
  hidden files such as `.env`.

## Keys

Shotkit ships with no keys. If you use `sk generate`, your fal.ai key stays in your
environment or in a `.env` file that git ignores. Shotkit sends it to fal and nowhere
else, and never prints or stores it.

- Never commit a key. `tools/validate_no_secrets.py` runs in CI and fails the build if
  one is found.
- If a key was ever committed or pasted somewhere public, delete it at
  fal.ai/dashboard/keys and make a new one. Removing it from the file is not enough.
