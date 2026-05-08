# Tools

Python helpers that keep the repo honest and let you render previews without invoking Claude.

## Requirements

```bash
pip install pyyaml jsonschema
```

## `validate_skills.py`

Checks every `SKILL.md` in `skills/` has the required YAML frontmatter, a `name` that matches its directory and a substantive `description`.

```bash
python tools/validate_skills.py
```

Run by CI on every PR. Use locally before opening a PR.

## `validate_schemas.py`

Checks every `*.schema.json` file is itself valid JSON Schema (Draft 2020-12).

```bash
python tools/validate_schemas.py
```

Run by CI on every PR.

## `validate_brand_lock.py`

Checks a brand-lock Markdown file has all required sections and Identity fields.

```bash
python tools/validate_brand_lock.py brand-packs/whystrohm.md
python tools/validate_brand_lock.py brand-packs/_template.md brand-packs/whystrohm.md
```

Run before committing new brand-pack examples.

## `shots-to-html.py`

Standalone CLI version of the `storyboard-html-preview` skill. Renders an `output/` folder into a single `preview.html`.

```bash
python tools/shots-to-html.py path/to/output-folder
python tools/shots-to-html.py path/to/output-folder --inline-images
python tools/shots-to-html.py path/to/output-folder --out review.html
```

Useful when you want to render a preview without running the skill, e.g. in CI, in a deploy pipeline, or when sharing the helper with someone who isn't a Claude user.

The output is identical to what the skill produces. Same template, same CSS, same JavaScript.

## `copy-prompt.py`

Pipe a single shot's prompt from a generated prompts file straight to the system clipboard. Lets the user paste into a generator UI without hunting for the right block in the .txt file.

```bash
python tools/copy-prompt.py output/prompts/midjourney.txt
python tools/copy-prompt.py output/prompts/midjourney.txt --shot shot_03
python tools/copy-prompt.py output/prompts/midjourney.txt --list
```

No flags: lists shots and prompts for a numeric selection.
`--shot shot_NN`: copies that shot's prompt directly.
`--list`: prints the shot index and exits without copying.

Pure standard library. Uses `pbcopy` on macOS, `xclip` or `xsel` on Linux, `clip` on Windows. The header comment line is stripped, only the prompt body lands in the clipboard.

## Adding new tools

If you add a new tool here:

- Make it executable (`chmod +x`)
- Add a usage docstring at the top of the file
- Document it in this README
- If it's part of CI, wire it into `.github/workflows/validate-skills.yml`

Keep tools dependency-light. PyYAML, jsonschema, and the standard library are the baseline. Don't pull in pandas or numpy for these.
