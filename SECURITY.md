# Security

## Reporting a problem

Write to [hello@whystrohm.com](mailto:hello@whystrohm.com) with "Shotkit security" in the
subject. Please do not open a public issue for a security problem. Say what you found,
how to reproduce it and which version you ran (`sk doctor` prints it). You will get a
reply within three working days.

The latest release is the supported version.

## What Shotkit touches

- **Plugin and CLI.** The installer writes to `~/.claude/` or `./.claude/`.
  Board and export tools use the run folder you pass to them. The preview can
  load Google Fonts. Disable those links with `--no-web-fonts`.
- **Live board.** `sk board --serve` listens on `127.0.0.1`. Edits arrive through
  the board's local endpoints. Hidden files such as `.env` are excluded from
  asset requests.
- **Canvas.** The workspace also listens on `127.0.0.1`. It reads source runs
  in place and stores edits and exports locally. Use `--isolated` to open the
  public examples in a separate profile with local rules.
- **Connected providers.** Claude Code receives material it reads when it
  plans or reviews. With Claude enabled in Canvas, Home chat sends the request
  and relevant project context. `sk generate --yes` sends an approved
  generation request to fal.ai.
- **MCP.** A client you connect can read and change workspace state through
  the local API. Connect it only to a workspace whose contents it may use.

## Keys

Shotkit ships with no keys. The generation CLI reads your fal.ai key from
the environment or a git-ignored `.env` file. Canvas checks your Claude Console
key and stores it in macOS Keychain.

- Never commit a key. `tools/validate_no_secrets.py` runs in CI and fails the build if
  one is found.
- Revoke any exposed key with its provider and issue a replacement.
