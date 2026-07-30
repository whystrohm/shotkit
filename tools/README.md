# Tools

Python helpers that keep the repo honest, gate a real project's output, and render previews
without invoking Claude.

## Requirements

```bash
pip install pyyaml jsonschema
```

Standard library otherwise. No pandas, no numpy.

## Run everything

```bash
./tools/check.sh            # every check, with output
./tools/check.sh --quiet    # pass/fail lines only
PYTHON=python3.12 ./tools/check.sh
```

This is exactly what CI runs, so a green local run means a green PR.

Every validator below also ships a `--selftest` that constructs failing fixtures and fails if
the check does not catch them. A validator that silently stops catching things is worse than
no validator, and the selftests are how that gets noticed.

## Repo checks

### `validate_skills.py`

Checks every `SKILL.md` in `skills/` has the required YAML frontmatter, a `name` that matches
its directory and a substantive `description`.

```bash
python tools/validate_skills.py
```

### `validate_schemas.py`

Checks every `*.schema.json` file is itself valid JSON Schema (Draft 2020-12) and carries
`$id`, `title`, and `description`.

```bash
python tools/validate_schemas.py
```

It validates schemas, not instances. For instances, see `validate_shots.py`.

### `validate_capabilities.py`

Checks the generator capability matrix
(`skills/visual-prompt-forge/adapters/_capabilities.json`) against
`capabilities.schema.json`, then checks it against the adapter prose that defers to it:

- every generator id has an adapter `.md` and every adapter `.md` has an entry
- no adapter advertises more words than its own `max_prompt_words` ceiling
- every adapter documents the `aspect_param` the matrix says to send
- no `notes` field cites a word count above its own ceiling
- warns when the matrix or an entry is past its 120-day freshness window

```bash
python tools/validate_capabilities.py
python tools/validate_capabilities.py --selftest
```

The prose checks exist because the matrix and the adapters had drifted in three places while
every file repeated the rule that the JSON wins.

### `validate_brand_lock.py`

Checks a brand-lock has all required sections and Identity fields, that its palette declares
the five roles the HTML preview maps onto CSS variables, and that its fonts are in the
backticked form the tools read.

```bash
python tools/validate_brand_lock.py brand-packs/whystrohm.md
python tools/validate_brand_lock.py --require-configured brand-packs/whystrohm.md
python tools/validate_brand_lock.py --snapshot output/brand-lock.snapshot.md
python tools/validate_brand_lock.py --snapshots     # every snapshot in the repo
python tools/validate_brand_lock.py --selftest
```

A brand-pack may be an unfilled template; that is what a template is. A snapshot may not, and
`--snapshot` additionally requires the `<!-- snapshot taken: ... -->` and
`<!-- source: ... -->` header, with a full UTC instant preferred over a bare date.

## Project checks

These run against a project's output directory, not the repo.

### `validate_shots.py`

Validates `shots.json` and `text-overlays.json` as instances, plus every cross-field and
cross-file rule JSON Schema cannot express: `end` after `start`, no gaps or overlaps, span
matching `project.duration_s`, overlay references resolving in both directions, every overlay
reachable from some shot, overlay timing inside its shot window, and every overlay color
present in the brand-lock palette.

```bash
python tools/validate_shots.py output/
python tools/validate_shots.py path/to/shots.json
python tools/validate_shots.py --examples     # every bundled example
python tools/validate_shots.py --selftest
```

Warnings cover the judgement calls: overlay copy repeated in a shot subject, a raw hex in a
subject, shot ids out of chronological order, a font the brand-lock does not declare.

### `validate_critique.py`

Validates a critique against `critique.schema.json` **and** the two invariants the schema
cannot hold.

The gate: any `blocking` issue forces `REJECT`, three or more `major` issues force `REJECT`,
one or two `major` forbid `ACCEPT`.

The provenance rules, from schema version `1.1`: a hash without its path is not a reference,
`image_ref` may not be null, `HIGH` confidence requires the shot, brand-lock, and prompt all
to be identified, and a named generator has to exist in the capability matrix.

```bash
python tools/validate_critique.py output/critiques/round-1/shot_03.critique.json
python tools/validate_critique.py output/          # every critique in the tree
python tools/validate_critique.py --examples
python tools/validate_critique.py --selftest
```

Version `1.0` critiques still pass, with a warning: they carry a verdict and no way to tie it
to the bytes it reviewed.

### `validate_provenance.py`

Walks an output tree and recomputes every recorded hash. This is the tool that answers "does
this verdict still describe the file it reviewed."

```bash
python tools/validate_provenance.py output/
python tools/validate_provenance.py output/ --require-accept
python tools/validate_provenance.py output/ --json
python tools/validate_provenance.py --selftest
```

It catches, with a selftest for each:

- a frame regenerated after its critique (`image_sha256` no longer matches)
- a brand-lock edited mid-project (`brand_lock_sha256` no longer matches `run.json`)
- a frame on disk with no critique for its round, never reviewed at all
- two critiques for the same shot in the same round, two operators colliding
- rounds that skip a number, or a critique whose `run_id` belongs to another run

`--require-accept` makes it the pipeline stop condition: exit 0 only when the chain is intact
*and* every shot's latest verdict is ACCEPT.

## Rendering

### `shots-to-html.py`

Renders an output folder into a single `preview.html`.

```bash
python tools/shots-to-html.py output/
python tools/shots-to-html.py output/ --inline-images
python tools/shots-to-html.py output/ --out review.html
python tools/shots-to-html.py output/ --rendered-at 2026-07-30T00:00:00Z
python tools/shots-to-html.py --selftest
```

It renders `skills/storyboard-html-preview/templates/preview.html.tpl`, the same structural
template the skill uses, through the small engine in `_template.py`. It did not always: the
CLI used to build its HTML inline while claiming to share the template, so the two could and
did diverge.

Everything interpolated is HTML-escaped. Shot subjects and rationales are model-generated
prose, and one angle bracket used to be enough to break the page.

`--rendered-at` pins the render timestamp, which makes output reproducible. CI re-renders
every bundled preview with a pinned value and fails if a byte moves.

The page shows two dates, deliberately: the **run** date from `run.json`, and the **render**
date. A single "Generated" date meant re-rendering a preview restamped the run as today.

### `copy-prompt.py`

Pipes one shot's prompt to the clipboard so you can paste into a generator UI without hunting
through the file.

```bash
python tools/copy-prompt.py output/prompts/round-1/flux.txt
python tools/copy-prompt.py output/prompts/round-2/revised-flux.txt --shot shot_02
python tools/copy-prompt.py output/prompts/round-1/flux.txt --list
python tools/copy-prompt.py --selftest
```

Reads both file shapes the forge writes. Comment lines inside a shot block are annotations and
never land in the clipboard, so a revision file's `# fix [...]` notes are shown but not
copied. Revision files used to be unreadable to this tool entirely, which was awkward given
they are the files an operator pastes from most.

Pure standard library. `pbcopy` on macOS, `xclip` or `xsel` on Linux, `clip` on Windows.

## Internal modules

Not entry points. Imported by the tools above.

- `_shotkit.py`, hashing, run ids, brand-lock parsing, and the output-tree path conventions.
  One copy, so no two tools can disagree about what a palette or a frame path is.
- `_template.py`, the template engine: `{{var}}`, `{{{raw}}}`, `{{#each}}`, `{{#if}}`. Only
  the subset `preview.html.tpl` uses, deliberately.

## Adding new tools

- Make it executable (`chmod +x`)
- Add a usage docstring at the top of the file
- Give it a `--selftest` that proves the check fires
- Document it in this README
- Wire it into `tools/check.sh`, which is what CI calls

Keep tools dependency-light. PyYAML, jsonschema, and the standard library are the baseline.
