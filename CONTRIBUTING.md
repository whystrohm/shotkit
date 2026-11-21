# Contributing

Thanks for looking. Small, focused pull requests are the easiest to review.

## What is welcome

- **A new generator adapter** in `skills/visual-prompt-forge/adapters/`, with its entry
  in `_capabilities.json`.
- **A new beat framework** in `skills/storyboard-architect/references/beat-frameworks.md`.
- **A brand pack example** in `brand-packs/examples/`.
- **A fix**, with a test that fails without it.

Open an issue first for anything that changes a file format (`shots.json`,
`text-overlays.json`, `run.json`, `critique.json`). Other tools read those files.

## Run the checks

```bash
tools/sk check
```

CI runs the same suite on Python 3.11 and checks that the bundled previews
can be reproduced. The launcher sets up the validator dependencies in a private
environment.

## Rules the checks enforce

- **Every check proves itself.** A new validator ships a `--selftest` that builds a
  failing case and shows the check catches it.
- **Bundled previews are reproducible.** If you change the preview renderer or its
  templates, re-render the three bundled `preview.html` files with their pinned
  timestamps (the commands are in `.github/workflows/validate-skills.yml`).
- **No keys in the repo.** `tools/validate_no_secrets.py` fails the build on one.
- **Share fixtures that can be published.** Use generated test data or
  approved example media. Keep private run folders, project state, and account
  files out of the repository and release assets.
- **The tools that ship to users need no install.** `board.py`, `generate.py`,
  `shots-to-html.py` and `copy-prompt.py` use the Python standard library only.

## Writing

Plain words and short sentences. Say what the thing does. No hype. Docs and skill files
are read by people and by models, and both do better with literal text.

## Licence

By contributing you agree that your work is released under the repo's Apache 2.0 licence.
