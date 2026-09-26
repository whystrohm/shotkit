# Tools

Python helpers that keep the repo honest, gate a real project's output, and render previews
without invoking Claude.

## Requirements

```bash
pip install pyyaml jsonschema
```

Standard library otherwise. No pandas, no numpy.

## Where the tools are

In a repo clone they are in `tools/`. `./install.sh` copies them to
`~/.claude/shotkit-tools/` (or `./.claude/shotkit-tools/` with `--project`), and the
brand packs to `~/.claude/shotkit-brand-packs/`. Every command below works from either
place. The examples use the repo path; after an install, swap `tools/` for
`~/.claude/shotkit-tools/`.

The installed tools find the skills in `~/.claude/skills/`, but they only look at the
five shotkit skills. Other skills in that folder are never checked.

`install.sh` also writes `~/.claude/shotkit-tools/VERSION`. Line 1 is the shotkit
version from the repo's `VERSION` file. Line 2, when the install came from a git clone,
names the exact checkout.

## Run everything

```bash
./tools/check.sh                          # every check, with output
./tools/check.sh --quiet                  # pass/fail lines only
~/.claude/shotkit-tools/check.sh --quiet  # the same checks, run against an install
PYTHON=python3.12 ./tools/check.sh
```

This is exactly what CI runs, so a green local run means a green PR. `check.sh` finds
its own folder, so it runs from a clone or from an install, from any working directory.

Every validator below also ships a `--selftest` that constructs failing fixtures and fails if
the check does not catch them. A validator that silently stops catching things is worse than
no validator, and the selftests are how that gets noticed.

## Repo checks

### `validate_skills.py`

Checks each of the five shotkit `SKILL.md` files has the required YAML frontmatter, a
`name` that matches its directory and a substantive `description`. Other skills in the
same folder are not checked. In a repo clone, a directory under `skills/` that is not one
of the five is an error, because `install.sh` would skip it.

```bash
python tools/validate_skills.py
python tools/validate_skills.py --selftest
```

### `validate_schemas.py`

Checks every `*.schema.json` file in the five shotkit skills is itself valid JSON Schema
(Draft 2020-12) and carries `$id`, `title`, and `description`.

```bash
python tools/validate_schemas.py
python tools/validate_schemas.py --selftest
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

The prose checks keep the matrix and the adapter files in step, so the rule that the JSON
wins is checked rather than trusted.

### `validate_brand_lock.py`

Checks a brand-lock has all required sections and Identity fields, that its palette declares
the five roles the HTML preview maps onto CSS variables, and that its fonts are in the
backticked form the tools read.

```bash
python tools/validate_brand_lock.py brand-packs/whystrohm.md
python tools/validate_brand_lock.py --require-configured brand-packs/whystrohm.md
python tools/validate_brand_lock.py --snapshot output/brand-lock.snapshot.md
python tools/validate_brand_lock.py --snapshots     # every snapshot in the five skills
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

### `validate_prompts.py`

Validates the prompt files `visual-prompt-forge` writes, against `shots.json` and the
capability matrix. Header completeness, generator id, aspect agreement, the
`max_prompt_words` ceiling, shot coverage, duplicate blocks, and the forge's two hard
rules: no on-screen text copy inside a prompt, and `environment` / `lighting` /
`color_grade` appearing verbatim.

```bash
python tools/validate_prompts.py output/
python tools/validate_prompts.py output/prompts/round-1/flux.txt
python tools/validate_prompts.py --examples
python tools/validate_prompts.py --selftest
```

The verbatim check is the reason this file exists. Series consistency depends on the
series_lock anchors landing unedited in every prompt, and that is the easiest rule in the
kit to break, because paraphrasing an anchor is what writing good prose feels like.

The character anchor is a warning rather than an error: a shot with no person in it can
legitimately omit it, and the message says so, so you can confirm rather than guess.

A shot that overrides `environment_ref` or `lighting_ref` is checked for its override text
instead of the series anchor. Comment lines inside a block are never prompt text:
`# params:`, `# fix`, `# variant:`, and `# covers:`, which names the other shots a
multi-shot sequence renders. A parameters line written as a second `# shot_NN, ...` header
fails as a duplicate block, and the error names the `# params:` form.

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

`--require-accept` makes it the pipeline stop condition: exit 0 only when the chain is intact,
every shot in `shots.json` has at least one critique, *and* every shot's latest verdict is
ACCEPT. A shot with no critique is reported as "no critique" and keeps the gate shut, with a
selftest for an unreviewed tree, a partly reviewed tree, and an all-ACCEPT tree.

## Rendering

### `shots-to-html.py`

Renders an output folder into a single `preview.html`.

```bash
python tools/shots-to-html.py output/
python tools/shots-to-html.py output/ --inline-images
python tools/shots-to-html.py output/ --out review.html
python tools/shots-to-html.py output/ --rendered-at 2026-07-30T00:00:00Z
python tools/shots-to-html.py output/ --no-web-fonts
python tools/shots-to-html.py --selftest
```

Fonts come from the brand-lock. A value such as `Archivo Bold 700 wdth 80` is split into a
quoted family, a weight and a width, and each is set as its own CSS property. The mono font
comes from the brand-lock's Mono line, with the system mono stack when there is none. The
page links each brand font from Google Fonts, one stylesheet per family, and falls back to
the system stack offline. `--no-web-fonts` leaves the links out.

It renders `skills/storyboard-html-preview/templates/preview.html.tpl`, the same structural
template the skill uses, through the small engine in `_template.py`, so the CLI and the skill
cannot drift apart.

Everything interpolated is HTML-escaped. Shot subjects and rationales are model-generated
prose, and an unescaped angle bracket would change the page structure.

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
never land in the clipboard, so a revision file's `# fix [...]` notes and every `# params:`
line are shown but not copied. `--list` counts each kind by name: params lines, fix notes,
variant lines, covers lines, and other notes.

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
