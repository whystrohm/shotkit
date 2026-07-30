# AUDIT-v2

Audit of shotkit v2.0.0 as it stands in the tree. Read-only pass. Findings only.

> **Status.** This is a point-in-time record of v2.0.0 and is left unedited on purpose. The
> work addressing it shipped in v3.0.0; see `CHANGELOG.md`, which maps each change back to the
> defect it fixes. Line numbers below refer to the v2.0.0 tree, so read them against
> `git show v2.0.0:<path>` rather than the current files.

Tree state at audit time:

- branch `main` at `673ee99`, level with `origin/main`, working tree clean
- tag `v2.0.0` exists locally and on `origin`, pointing at `39c2227`, one commit behind `main`
- 5 skills, 10 generator adapters, 5 validator scripts in `tools/` (4 named in the brief, plus `validate_brand_lock.py`)

Severity vocabulary matches the critic (`skills/visual-asset-critic/templates/critique.schema.json:51`): `blocking`, `major`, `minor`.

Finding IDs are stable within this document. Each blocking and major finding is scoped to one issue.

---

## 1. Validator run

`python3` on this machine is 3.14.5 with neither `pyyaml` nor `jsonschema` installed. All four named validators exit 1 on a dependency guard before doing any work:

```
$ python3 tools/validate_skills.py
ERROR: PyYAML not installed. Run: pip install pyyaml
EXIT=1

$ python3 tools/validate_schemas.py
ERROR: jsonschema not installed. Run: pip install jsonschema
EXIT=1

$ python3 tools/validate_capabilities.py
ERROR: jsonschema not installed. Run: pip install jsonschema
EXIT=1

$ python3 tools/validate_critique.py --selftest
ERROR: jsonschema not installed. Run: pip install jsonschema
EXIT=1
```

Re-run under `~/.claude/media-tools-venv/bin/python` (yaml 6.0.3, jsonschema 4.26.0). Verbatim output:

```
======== validate_skills ========
Validating 5 skill(s) in skills/

  ok    skills/brand-lock-extractor
  ok    skills/storyboard-architect
  ok    skills/storyboard-html-preview
  ok    skills/visual-asset-critic
  ok    skills/visual-prompt-forge

All skills valid.
EXIT=0

======== validate_schemas ========
Validating 4 schema file(s)

  ok    skills/storyboard-architect/templates/shots.schema.json
  ok    skills/storyboard-architect/templates/text-overlays.schema.json
  ok    skills/visual-asset-critic/templates/critique.schema.json
  ok    skills/visual-prompt-forge/adapters/capabilities.schema.json

All schemas valid.
EXIT=0

======== validate_capabilities ========
Validating capability matrix: skills/visual-prompt-forge/adapters/_capabilities.json

Capability matrix valid (10 generators, 0 warning(s)).
EXIT=0

======== validate_critique --selftest ========
  ok    selftest: clean REVISE doc passes
  ok    selftest: ACCEPT-with-blocking is rejected by the gate

Selftest passed.
EXIT=0
```

Also run, because CI runs them and the brief named four:

```
======== validate_critique on example fixtures (CI step) ========
Validating 2 critique file(s)

  ok    skills/visual-asset-critic/examples/critique.accept.json
  ok    skills/visual-asset-critic/examples/critique.revise.json

All critiques valid.
EXIT=0

======== validate_brand_lock (CI args) ========
Validating 2 brand-lock file(s)

  ok    brand-packs/_template.md
  ok    skills/brand-lock-extractor/examples/brand-lock.md

All brand-locks valid.
EXIT=0
```

Coverage of that green result, for the record:

- `validate_skills.py` reads frontmatter `name` and `description` only (`tools/validate_skills.py:43-76`).
- `validate_schemas.py` checks that each `*.schema.json` is itself a valid schema and carries `$id`/`title`/`description` (`tools/validate_schemas.py:30-51`). It validates zero instances.
- `validate_capabilities.py` checks the matrix against its schema, checks that generator ids and adapter filenames match, and warns on staleness (`tools/validate_capabilities.py:67-99`).
- `validate_critique.py` checks two constructed in-memory documents under `--selftest`, and the two checked-in fixtures in CI.

No validator in the repo reads a `shots.json` or a `text-overlays.json` instance.

### F-01 `blocking` No instance validator exists for the two schemas the pipeline runs on

`skills/storyboard-architect/templates/shots.schema.json` and `templates/text-overlays.schema.json` have no runnable validator anywhere in the repo. `tools/validate_schemas.py:25-27` globs `*.schema.json` and only calls `Draft202012Validator.check_schema` on each (`:39-42`). `.github/workflows/validate-skills.yml:22-45` has no instance step.

Every "must validate against the schema" instruction is therefore model self-report: `skills/storyboard-architect/SKILL.md:151`, `skills/visual-prompt-forge/SKILL.md:65`, `skills/storyboard-html-preview/SKILL.md:53`.

Failure: an operator produces a `shots.json` with a misspelled key, a bad `framing` value, or a missing `rationale`. Every documented gate passes. The break surfaces downstream as a `KeyError` in `tools/shots-to-html.py:152-160` or as silently absent content, at whatever point someone happens to run the preview.

I wrote a one-off validator for this audit and confirmed all three bundled `shots.json` and all three `text-overlays.json` currently pass. Nothing in the repo will notice when they stop.

### F-02 `major` The critique gate is repo-only and never runs on a real critique

`tools/validate_critique.py` is the artifact that makes the verdict trustworthy (`docs/the-qa-loop.md:53`, `CHANGELOG.md:13`). It is not installed and not invoked:

- `install.sh:38-44` copies only the five directories under `skills/`. `tools/` is never installed.
- No skill workflow step runs it. `skills/visual-asset-critic/SKILL.md:147` and `:149` mention it in the passive voice ("will reject it", "is validated by") inside Step 6, and Step 6 ends there. The critic writes `critique.json` and hands off (`:200-206`) without ever gating.
- CI runs it against `--selftest` plus two checked-in fixtures (`.github/workflows/validate-skills.yml:41-46`).

Failure: a client project runs 36 critiques. Zero pass through the gate. The invariant is enforced only over two files that ship in the repo and never change.

### F-03 `minor` `validate_critique.py` has no directory or glob mode

`tools/validate_critique.py:121-135` requires explicit paths. `docs/the-qa-loop.md:75` shows `python tools/validate_critique.py output/critique.json`, a single file. `docs/the-qa-loop.md:88` describes the stop condition as "no critique.json has a verdict other than ACCEPT", plural. There is no command that checks a project's critiques.

### F-04 `minor` `validate_capabilities.py` parity check globs all markdown in `adapters/`

`tools/validate_capabilities.py:77` builds `md_ids` from `ADAPTERS_DIR.glob("*.md")`. Any non-adapter markdown placed in that directory (a README, a template, a note) fails parity at `:80-81` with "adapter 'X.md' has no entry in _capabilities.json".

### F-05 `minor` `validate_skills.py` does not check that referenced files exist

`tools/validate_skills.py:43-76` validates frontmatter only. `skills/storyboard-html-preview/SKILL.md:220` states that `examples/` contains generated `preview.html` files. `skills/storyboard-html-preview/examples/` is an empty, untracked directory. CI is green.

---

## 2. QA loop trace: conventions the chain depends on with no schema or validator behind them

Trace: `shots.schema.json` to the forge adapters to `critique.schema.json` to revision-mode `fix_type` branching. Each item below is a load-bearing convention with nothing enforcing it.

### F-06 `major` `storyboard-architect` documents field names the schema rejects

`skills/storyboard-architect/SKILL.md:103-104` instructs:

```
- `environment`, references series-lock language
- `lighting`, references series-lock language
```

The schema requires `environment_ref` and `lighting_ref` (`shots.schema.json:93-100`) and sets `additionalProperties: false` on the shot object (`shots.schema.json:62`). A model following Step 4 literally emits a file that fails the schema on two counts: unknown keys `environment` and `lighting`.

The example block later in the same file uses the correct `_ref` names (`SKILL.md:174-175`), and all three bundled examples use `_ref`. The instruction and the example contradict each other inside one file, and F-01 means nothing catches whichever one the model followed.

### F-07 `major` The documented motion vocabulary is missing four of eleven enum values

`skills/storyboard-architect/SKILL.md:101` lists `static / push / pull / pan-left / pan-right / handheld / orbit`.

`shots.schema.json:81-86` allows eleven: those seven plus `tilt-up`, `tilt-down`, `whip`, `rack`. `references/shot-grammar.md:39,42,52` documents all four missing ones.

Failure: a model composing from SKILL.md never selects `tilt-up`, `tilt-down`, `whip`, or `rack`. Four documented camera moves are unreachable through the primary instruction path.

### F-08 `major` Timing invariants are stated as a checklist and enforced nowhere

`shots.schema.json:69-70` constrains `start >= 0` and `end > 0`. It does not constrain `end > start`, does not require shots to tile or order, and does not relate any shot to `project.duration_s` (`:26`).

`skills/storyboard-architect/SKILL.md:193` states the invariant as a quality-bar checkbox: "Total of `(end - start)` across shots equals project duration (within 0.1s)". No tool computes it. The stated invariant is also the wrong one for a shot list: summed durations and timeline span only coincide when there are no gaps and no overlaps, which is itself unchecked.

I verified all three bundled examples currently satisfy `end > start`, zero gaps, zero overlaps, and sum equal to `duration_s`. A `shots.json` with `start: 5.0, end: 3.0` validates.

### F-09 `major` Cross-file reference integrity between `shots.json` and `text-overlays.json` is unenforced, and the two schemas disagree on cardinality

`shots.schema.json:101-106` gives each shot one optional `on_screen_text` string. `text-overlays.schema.json:29-39` lets each overlay name one shot or an array of shots. Nothing checks that a `shot.on_screen_text` resolves to an overlay id, that an `overlay.shot_id` resolves to a shot, or that every overlay is reachable from some shot. `skills/storyboard-architect/SKILL.md:194` states the first of those three as a checkbox.

The cardinality mismatch has already produced a defect in the repo's own flagship example:

- `skills/storyboard-architect/examples/shotkit-explainer/text-overlays.json:77-88` defines `text_07` on `shot_06`.
- `skills/storyboard-architect/examples/shotkit-explainer/shots.json:109` sets `shot_06`'s `on_screen_text` to `text_06`.
- `text_07` is therefore unreachable from the shot side. Both renderers resolve exactly one overlay per shot (`tools/shots-to-html.py:227`, `skills/storyboard-html-preview/templates/preview.html.tpl:77-81,112-118`), so it is silently dropped.

Verified: `text_07`'s content string "Pre-production for founder-led video at scale." appears zero times in the checked-in `skills/storyboard-architect/examples/shotkit-explainer/preview.html`. `skills/storyboard-html-preview/SKILL.md:214` asserts the opposite as a quality-bar item: "Every text overlay from `text-overlays.json` is rendered".

### F-10 `major` Palette membership is claimed as schema-enforced and is not

`docs/brand-lock-anatomy.md:87`: "The brand-lock file enforces this at the source. The schema enforces it at the output. The two together produce deterministic color across every run."

`text-overlays.schema.json:53-57` validates hex format only, with a description that states the rule in prose: "Must come from brand-lock palette." `skills/storyboard-architect/SKILL.md:195` restates it as a checkbox. Nothing reads the brand-lock.

Counterexample in tree: `skills/storyboard-architect/examples/shotkit-explainer/text-overlays.json:85` uses `#6B6B73`, which does not appear in `skills/storyboard-architect/examples/shotkit-explainer/brand-lock.snapshot.md`. The file validates.

### F-11 `major` The `.md` versus `_capabilities.json` precedence rule is a convention with no check, and three entries currently disagree

`skills/visual-prompt-forge/SKILL.md:84` establishes the rule: "Where a number in an adapter `.md` and in `_capabilities.json` disagree, the JSON wins." Every adapter repeats it on line 3. `tools/validate_capabilities.py:76-81` compares filenames to ids and never reads a number out of any `.md`.

Live disagreements:

- `adapters/gpt-image.md:38` states "150-300 words"; `_capabilities.json:60` caps `max_prompt_words` at 250. The upper half of the documented range is over the cap.
- `adapters/seedream.md:38` states "40-70 words per prompt. Shorter than most."; `_capabilities.json:92` sets 120. The prose is 40 percent of the cap.
- `_capabilities.json:12` sets midjourney `max_prompt_words` to 80 while `_capabilities.json:20` notes "Over 100 words underperforms." The single source of truth contradicts itself in adjacent lines.
- `adapters/ideogram.md` states no word budget at all; `_capabilities.json:44` sets 120.

### F-12 `major` The nano-banana aspect parameter name is wrong in the file that wins

`_capabilities.json:82` sets `aspect_param` to `aspect_ratio`. `adapters/nano-banana.md:30` documents the parameter as `aspectRatio`, and `:101` states it explicitly: "Nano Banana ignores `--ar`, expects `aspectRatio` parameter."

Under the precedence rule at `skills/visual-prompt-forge/SKILL.md:84`, the JSON wins and the forge emits `aspect_ratio`. `capabilities.schema.json:52` types `aspect_param` as any non-empty string, so no validator can catch it.

Failure: every nano-banana prompt file carries a parameter name the API does not recognize, and the adapter file that says so is the one the rule tells the model to disregard.

### F-13 `major` Revision mode treats REJECT identically to REVISE

`skills/visual-prompt-forge/SKILL.md:143-144` branches on one thing: "Skip any with `verdict: ACCEPT`, those are done. For every non-ACCEPT shot, walk its `issues[]`".

`skills/visual-asset-critic/SKILL.md:106` defines REJECT as "Three+ layers fail or one critical layer (Brand Lock, Series Lock) hard-fails with no clear fix". `:139` defines `blocking` as "hard-fail on a critical layer with no clear fix, or a defect that makes the asset unusable". `tools/validate_critique.py:47-50` forces REJECT whenever any issue is `blocking`.

So the loop takes a verdict that means "no fix path exists" and re-emits a prompt with the fix applied. `docs/the-qa-loop.md:24` routes REVISE and REJECT down the same arrow. There is no escalation branch, no human gate, no round cap in any file. The only stop conditions documented are "every shot is ACCEPT" or "you decide a shot is good enough" (`docs/the-qa-loop.md:37`).

### F-14 `major` `fix_type: post-level` produces no artifact and no record

`skills/visual-prompt-forge/SKILL.md:148`: "A shot that has only `post-level` issues needs no new prompt, leave it out of the revised file." `:162` says to tell the user which shots need only post work.

That instruction is a chat message. Nothing is written. The compositing obligation exists only in the surviving `critique.json`, and per F-16 that file is overwritten on the next review. A shot whose only defect is post-level therefore exits the loop as an ACCEPT-equivalent with no on-disk record that post work is owed.

### F-15 `major` The prompt-file format is defined only by a regex in a helper

The forge writes prompt files whose structure is documented in prose at `skills/visual-prompt-forge/SKILL.md:99-117` (header comment block, then `# shot_NN` comment, then prompt body). There is no schema and no validator. The only executable definition is `tools/copy-prompt.py:20`:

```python
SHOT_HEADER = re.compile(r'^#\s*(shot_\d+)\b(.*)$')
```

`tools/copy-prompt.py:54-55` treats every line after a shot header as prompt body, including further comment lines. See F-21 for the concrete break this produces on revision-mode output.

### F-16 `blocking` Every loop artifact is written to a fixed path, so each write destroys the previous state

- `output/critique.json`: `skills/visual-asset-critic/SKILL.md:24`, `:120`, `:149`; `docs/the-qa-loop.md:20`, `:40`, `:75`.
- `output/prompts/{generator}.txt`: `skills/visual-prompt-forge/SKILL.md:27-39`.
- `output/prompts/revised-{generator}.txt`: `skills/visual-prompt-forge/SKILL.md:153`; `docs/the-qa-loop.md:78`, `:87`.
- `output/generated/shot_NN.{png,jpg}`: `skills/storyboard-html-preview/SKILL.md:34`, `:51`, `:130-134`; `tools/shots-to-html.py:76-83`.

One critique is one shot's verdict (`skills/visual-prompt-forge/SKILL.md:143`). A 12-shot project produces 12 critiques per round, all at the same path. No filename carries a shot id, a round number, an operator, or a run id. No schema has a field for any of those (see F-18).

Failure: reviewing shot_02 destroys shot_01's verdict. The forge in revision mode then reads whatever single file survived and re-emits prompts for that one shot, reporting completion. `docs/the-qa-loop.md:41` describes revision mode as taking "one or more `critique.json` files"; nothing in the repo names or produces more than one.

### F-17 `major` `assets.generated[].accepted` has no writer, no consumer, and no link to a verdict

`shots.schema.json:114-137` adds the v1.1 asset block: `path`, `generator`, `accepted`. `shots.schema.json:116` states its purpose: "Lets visual-asset-critic and the HTML preview find images without a schema bump."

- No skill writes it. Neither the critic's Step 6 output mapping (`skills/visual-asset-critic/SKILL.md:122-131`) nor revision mode (`skills/visual-prompt-forge/SKILL.md:141-162`) touches `shots.json`.
- No tool reads it. `tools/shots-to-html.py:76-83` finds images by filename convention and ignores `assets` entirely.
- No bundled example contains it.
- `README.md:221` states the wiring is unfinished: "The `shot.assets` field landed in shots schema v1.1; wiring the HTML preview and critic to consume it is the remaining work."

`accepted: true` has no reference to the critique that produced the acceptance, no timestamp, and no approver. `generator` is an unconstrained string (`shots.schema.json:131`) with no relation to the ids in `_capabilities.json`.

### F-18 `major` `critique.schema.json` forbids adding provenance in band

`critique.schema.json:8` sets `additionalProperties: false` on the root. There is no `meta` passthrough, unlike `shots.schema.json:15-19`.

Consequence: a content hash, run id, round number, prompt reference, generator id, model version, or seed cannot be added to a critique without a schema version bump. The one schema that records a decision is the one schema that cannot be extended by a downstream operator.

### F-19 `minor` The `rack` token means two different things in one schema

`shots.schema.json:85` lists `rack` in the `motion` enum. `shots.schema.json:90` lists `rack` in the `depth_of_field` enum. `references/shot-grammar.md:52` documents it only as a focus behavior. Disambiguation depends entirely on which field it appears in.

### F-20 `minor` `depth_of_field` is in the schema and all three examples but absent from the architect instructions

`shots.schema.json:88-91` defines it. All three bundled `shots.json` set it on every shot. `skills/storyboard-architect/SKILL.md:96-107` does not list it in the per-shot field set, and the example block at `:153-182` omits it.

### F-21 `major` `copy-prompt.py` cannot read revision-mode output

Verified empirically. Constructed the revision file exactly as documented at `skills/visual-prompt-forge/SKILL.md:155-160`:

```
# Revision of shot_03 (was REVISE)
# fix [Series Lock, major]: added 'salt-and-pepper hair' to the character anchor (was missing)
# fix [Shot Spec, minor]: medium shot -> medium close-up
medium close-up of founder mid-thirties, salt-and-pepper hair --ar 9:16 --style raw --s 50
```

Result:

```
$ python tools/copy-prompt.py /tmp/revised-midjourney.txt --list
No shot blocks found in /tmp/revised-midjourney.txt.
Expected lines like: # shot_03, beat, timing, framing
EXIT=1

$ python tools/copy-prompt.py /tmp/revised-midjourney.txt --shot shot_03
No shot blocks found in /tmp/revised-midjourney.txt.
EXIT=1
```

`tools/copy-prompt.py:20` requires the shot id immediately after `#`. The documented revision header puts "Revision of" in front of it. The same command run against `skills/visual-prompt-forge/examples/one-shot-all-adapters/midjourney.txt` succeeds.

`README.md:112` places `tools/copy-prompt.py` at step 4 of the round-trip workflow. It works on round one and fails on every revision round.

### F-22 `major` Two renderers, no shared template, and a README that claims otherwise

`tools/README.md` on `shots-to-html.py`: "The output is identical to what the skill produces. Same template, same CSS, same JavaScript."

`tools/shots-to-html.py:210-211` reads `styles.css.tpl` and `print.css.tpl` only. `tools/shots-to-html.py:239-240` states in a comment: "using a simpler direct render rather than the templated one, to avoid full handlebars dependency. Output is equivalent." `skills/storyboard-html-preview/templates/preview.html.tpl` is never opened.

`skills/storyboard-html-preview/SKILL.md:142-149` defines a template-flag convention (`has_image`, `has_no_image`, `on_screen_text`, plus nine resolved `overlay_*` fields) for a template the CLI does not use. Nothing compares the two renderers' output.

### F-23 `major` The brand-lock snapshot header is required by the architect and checked by nothing

`skills/storyboard-architect/SKILL.md:134-141` requires two HTML comments at the top of every snapshot, "ISO-8601 timestamp" and source path, and states: "This is what makes the storyboard reproducible later." `docs/audit-trail-pattern.md:59-66` repeats it as the mechanism.

`tools/validate_brand_lock.py:89-115` checks section headings, four Identity fields, and the presence of a hex-shaped string. It never looks at the header. CI runs it against `brand-packs/_template.md` and `skills/brand-lock-extractor/examples/brand-lock.md` only (`.github/workflows/validate-skills.yml:32-33`), neither of which is a snapshot.

The three snapshots in the tree already diverge:

- `examples/30s-pain-proof-promise/brand-lock.snapshot.md:1-2` and `examples/60s-founder-explainer/brand-lock.snapshot.md:1-2`: `2026-05-07T14:23:00Z`, two comments.
- `examples/shotkit-explainer/brand-lock.snapshot.md:1-3`: `2026-05-08`, date only, no time, no zone, plus a third `<!-- storyboard: -->` comment the others do not have.

All three pass `validate_brand_lock.py`. So does a snapshot with no header at all.

### F-24 `major` An unfilled template passes as a valid brand-lock

`tools/validate_brand_lock.py:112` accepts template placeholders:

```python
if not re.search(r"#[0-9A-Fa-f]{6}|#[_]{6}", palette_body):
```

`brand-packs/_template.md:19-23` supplies five rows of `#______`. `skills/storyboard-architect/SKILL.md:68` instructs the architect to copy that template into the output as `brand-lock.snapshot.md` when no brand-lock is provided, with an `UNCONFIGURED` note in a comment.

The validator cannot distinguish a real brand-lock from a blank one. Downstream, `tools/shots-to-html.py:47-52` will not match `#______` with its hex regex and falls back to the hardcoded generic defaults at `:37-43` (`#3B82F6` accent) with no warning.

### F-25 `major` A cross-skill relative path breaks under the repo's own documented packaging

`skills/visual-prompt-forge/SKILL.md:65` refers to `../storyboard-architect/templates/shots.schema.json`.

`docs/claude-ai-workflow.md:12-20` documents the Claude.ai path as zipping each skill directory individually and uploading five separate `.skill` artifacts. In that surface the parent directory does not exist. The same break occurs for any single-skill install, and `install.sh:93-96` allows skipping individual skills at the overwrite prompt, so a partial install produces the same result on Claude Code.

### F-26 `major` `tools/` is not installed, so every tool path in a SKILL.md is unresolvable after install

`install.sh:38-44` defines the install set as five skill directories. `install.sh:104` copies `skills/<name>` to `<target>/<name>`. `tools/` is never copied, and no skill carries its own copy.

Paths that do not resolve after `./install.sh`:

- `python tools/copy-prompt.py output/prompts/midjourney.txt` (`skills/visual-prompt-forge/SKILL.md:128`)
- `python tools/validate_brand_lock.py path/to/file.md`, inside the handoff message the extractor is told to send the user (`skills/brand-lock-extractor/SKILL.md:88`)
- `tools/validate_critique.py` (`skills/visual-asset-critic/SKILL.md:147`, `:149`)

`tools/shots-to-html.py:25-26` compounds this: `TEMPLATE_DIR` is derived from the script's own parent, so the CLI only functions from inside a repo checkout.

### F-27 `minor` `install.sh` copies working-tree junk into the skills directory

`install.sh:104` uses `cp -R "${src}" "${dst}"`. `.DS_Store` files exist at `skills/.DS_Store`, `skills/visual-prompt-forge/.DS_Store`, and `skills/visual-prompt-forge/examples/.DS_Store`. They are gitignored, so they do not ship over git, but they are copied into `~/.claude/skills/` on any local install and into any `.skill` zip built per `docs/claude-ai-workflow.md:16`.

---

## 3. Provenance: what identifies each artifact the pipeline writes

Confirmed as stated in the brief. `image_ref` and `brand_lock_ref` are filenames. No content hash, no timestamp, no run id, no prompt hash, no generator id, anywhere in any schema.

| Artifact | Written by | What identifies it |
|---|---|---|
| `storyboard.md` | architect (`SKILL.md:29`) | filename. No version field, no run id. |
| `shots.json` | architect (`SKILL.md:30`) | `version` (schema version, not run version), `project.title`. No run id, no timestamp, no hash. |
| `text-overlays.json` | architect (`SKILL.md:31`) | `version` const `1.0`. Nothing else. No reference back to the `shots.json` it belongs to. |
| `brand-lock.snapshot.md` | architect (`SKILL.md:132-139`) | two HTML comments, unchecked (F-23). No hash of the source brand-pack. |
| `prompts/{generator}.txt` | forge (`SKILL.md:99-117`) | free-text comment header including `# Generated: {timestamp}` and `# Brand-lock: brand-lock.snapshot.md`. Not machine-parsed by anything; `copy-prompt.py:20` reads only `# shot_NN` lines. |
| `prompts/revised-{generator}.txt` | forge (`SKILL.md:153`) | filename plus per-shot prose annotations. No round number. |
| `generated/shot_NN.png` | the operator or their generator | filename equal to the shot id. Nothing else. No sidecar. |
| `critique.json` | critic (`SKILL.md:118-131`) | optional `shot_id`, optional `image_ref`, optional `brand_lock_ref`, all bare paths. |
| `preview.html` | preview skill / `shots-to-html.py` | render-time timestamp, hardcoded brand-lock link. |

### F-28 `blocking` `critique.json` can be schema-valid, gate-passing, and identify nothing

`critique.schema.json:7`: `"required": ["version", "verdict", "confidence", "issues"]`.

`shot_id` (`:11-17`), `brand_lock_ref` (`:18-21`), and `image_ref` (`:22-25`) are all optional. `tools/validate_critique.py:41-55` reads only `verdict` and `issues[].severity`.

A document consisting of `version`, `verdict: ACCEPT`, `confidence: HIGH`, `issues: []` passes both the schema and the gate. It is a signed approval of nothing in particular. The `--selftest` fixtures at `tools/validate_critique.py:83-100` are themselves exactly this shape: neither carries `shot_id`, `image_ref`, or `brand_lock_ref`, and both pass.

### F-29 `blocking` No artifact binds an image to the prompt, generator, or brand-lock that produced it

`critique.schema.json:22-25` records `image_ref` as a path. There is no field for the prompt text, prompt file, prompt hash, generator id, model version, seed, or generation timestamp, and `additionalProperties: false` (`:8`) prevents adding one (F-18).

`docs/audit-trail-pattern.md:137-143` claims the trail already supports pointing to "The prompt that drove the generation" and "The image that was approved". `docs/audit-trail-pattern.md:106` contradicts that on the same page, listing the mechanism as an unshipped extension: "Render manifests. When images are generated, log which prompt produced which image, with which seed, on which date. A `renders.json` alongside the four files completes the loop from spec to artifact. These are extensions."

`docs/audit-trail-pattern.md:108` does the same for approvals: `approvals.json` is an extension, not shipped. `README.md:86` states the outcome as delivered: "Six months later, you can still answer 'what brand version was this approved against.'"

### F-30 `major` Everything in the chain references state by name, and the base of those names is inconsistent

Name-based references, all unhashed:

- `shots.schema.json:37-40` `brand_lock_ref`, described as relative "within the output directory".
- `critique.schema.json:18-21` `brand_lock_ref`, base unspecified.
- `critique.schema.json:22-25` `image_ref`, base unspecified.
- `shots.schema.json:128-134` `assets.generated[].path`, base unspecified.
- `shots.schema.json:101-106` `on_screen_text`, an id reference into a separate file with no file reference.
- `text-overlays.schema.json:29-39` `shot_id`, an id reference into a separate file with no file reference.
- `text-overlays.schema.json:41-44` `font`, described as "Must reference a font defined in brand-lock typography", by name, unchecked.
- `shots.schema.json:93-100` `environment_ref` / `lighting_ref`, whose documented default value is the literal string `series_lock.environment`, a hand-written path into the same document.
- `tools/shots-to-html.py:293` hardcodes the link text and href `brand-lock.snapshot.md`, ignoring `shots_data['brand_lock_ref']` entirely.

The two shipped critique fixtures mix bases inside a single file: `skills/visual-asset-critic/examples/critique.accept.json` sets `brand_lock_ref` to `brand-lock.snapshot.md` (output-relative) and `image_ref` to `output/generated/shot_01.png` (project-root-relative). Both fields pass.

### F-31 `major` Images are resolved by filename convention that no schema describes

`tools/shots-to-html.py:76-83`:

```python
def find_image(generated_dir: Path, shot_id: str) -> Path | None:
    for ext in ("png", "jpg", "jpeg", "webp"):
        p = generated_dir / f"{shot_id}.{ext}"
```

The convention `output/generated/{shot_id}.{ext}` appears in `skills/storyboard-html-preview/SKILL.md:34`, `:51`, `:130-134` and in the two critique fixtures. It is not in any schema. It competes with `shot.assets.generated[].path` (F-17), which is in the schema and has no reader.

Nothing distinguishes a first draft from a fifth re-roll at that path, and nothing records which of the two conventions a given project used.

---

## 4. State after a 12-shot project through three revision rounds

Assumes the operator follows the documented conventions exactly: `docs/the-qa-loop.md:69-80` for the by-hand loop, one target generator, the critic writing `output/critique.json` per `skills/visual-asset-critic/SKILL.md:120`, frames landing at `output/generated/shot_NN.png` per `skills/storyboard-html-preview/SKILL.md:130`.

### What exists on disk

```
output/
├── storyboard.md                      1 file, from the architect run
├── shots.json                         1 file, 12 shots, no assets block
├── text-overlays.json                 1 file
├── brand-lock.snapshot.md             1 file, header unchecked
├── prompts/
│   ├── {generator}.txt                1 file, round-1 prompts for all 12 shots
│   └── revised-{generator}.txt        1 file, round-3 revisions only
├── generated/
│   └── shot_01.png … shot_12.png      up to 12 files, last surviving frame per shot
├── critique.json                      1 file
└── preview.html                       optional, stamped with the date last rendered
```

36 critiques were produced. One file remains: the last one written in round 3. 35 verdicts are gone (F-16). Two revised prompt sets were produced in rounds 1 and 2; both were overwritten by round 3 (F-16). If the operator re-generated a shot in place, earlier frames are gone as well.

### What a person can reconstruct six months later

- The storyboard intent: beats, timing, framing, angle, motion, subject, per-shot rationale. `shots.json` and `storyboard.md` are written once and not touched by the loop.
- The on-screen text spec, minus any overlay unreachable from a shot (F-09).
- The brand-lock text the project claims to have been built against, as a document.
- The round-1 prompt set for all 12 shots, including which generator it targeted, from the file name and the `# Generator:` header line.
- The round-3 revised prompt set for whichever shots failed in round 3, and, from the prose annotations at `skills/visual-prompt-forge/SKILL.md:157-159`, what changed and which layer and severity drove it.
- One critique in full: one shot, one verdict, its issues, its severities, its fixes.
- The 12 surviving image files.

### What is lost

- 35 of 36 verdicts. Which shots ever failed, on which layer, at what severity, in which round, and why.
- Round 1 and round 2 revised prompts. The prompt that actually produced 11 of the 12 surviving frames is not on disk.
- Which round any given frame came from, and how many attempts it took.
- Whether any frame was ever ACCEPTed. `assets.generated[].accepted` exists (`shots.schema.json:133`) and has no writer (F-17). The surviving `critique.json` covers one shot and may not name it (F-28).
- Which prompt produced which frame. There is no link in either direction. If more than one generator was targeted, `generated/shot_03.png` does not say which one made it.
- Which generator, model version, seed, or settings produced any frame. `_capabilities.json:9` records `model_version` for the matrix as of `matrix_last_reviewed` (`:4`), not per run, and nothing copies it into the output.
- Whether the `brand-lock.snapshot.md` on disk is the one the prompts and frames were built from. `brand_lock_ref` is a name (F-30). Re-running the architect overwrites the snapshot in place at the same path, and `shots.json` still resolves.
- Any post-level compositing obligation. Recorded only in critiques that no longer exist (F-14).
- The original render date of `preview.html`. `tools/shots-to-html.py:241` stamps `datetime.now()`, and `:267` and `:293` write it into the header and the footer. Re-rendering silently replaces the run date with today's.
- Who approved anything, and when. `docs/audit-trail-pattern.md:108` lists `approvals.json` as an unshipped extension.

### F-32 `major` Re-rendering the preview overwrites the only date on the artifact with a false one

Verified. Copied `skills/storyboard-architect/examples/shotkit-explainer/` out of the repo and re-ran `tools/shots-to-html.py` against it. The regenerated file is byte-identical to the checked-in `preview.html` except for the timestamp, which appears twice: 8 diff lines total, both hunks timestamp-only. Same byte count, 25904.

`tools/shots-to-html.py:293` then asserts: "Generated against `brand-lock.snapshot.md` on {timestamp}". The statement is false whenever the preview is regenerated after the run, which is the normal case for a shareable review artifact.

### F-33 `minor` The preview's version marker is hardcoded and does not track anything

`tools/shots-to-html.py:261` writes `Storyboard · v1.0` into the header regardless of the `shots.json` `version` field (which may be `1.1`) and regardless of the shotkit version. The template does the same at `skills/storyboard-html-preview/templates/preview.html.tpl:15-16`.

### F-34 `major` `shots-to-html.py` interpolates model-generated strings into HTML with no escaping

`tools/shots-to-html.py` builds output with f-strings throughout: `:98` (alt text), `:115` (a `style` attribute delimited by single quotes, taking `overlay["font"]`, `overlay["weight"]`, `overlay["color"]`), `:126` (overlay content inside literal double quotes), `:133` (VO line inside literal double quotes), `:157` (subject), `:160` (rationale), `:279-282` (all four `series_lock` values).

`font` is an unconstrained string (`text-overlays.schema.json:41-44`). Subject, rationale, and VO are free prose generated by a model. There is no `html.escape` call in the file.

Failure: a rationale containing `<` or a VO line containing a double quote produces broken markup in the artifact handed to a client. A `font` value containing `'` closes the style attribute. F-01 means no instance validation runs first.

### F-35 `major` `shots-to-html.py` discards brand typography and depends on undocumented palette role names

`tools/shots-to-html.py:67-68` hardcodes `display_font` and `body_font` to `"Inter"` in both the parsed and the fallback path. `skills/storyboard-html-preview/SKILL.md:59` requires extracting "Display font and body font names" from the snapshot, and `:212` lists brand appearance in the quality bar.

`tools/shots-to-html.py:47-58` extracts colors by matching table rows and then substring-matching role names against the literal list `background`, `ink`, `accent (warm)`, `accent`, `muted`, `rule`. Those words match `brand-packs/whystrohm.md:14-19` and `brand-packs/examples/saas-clean.md:16-20`. Nothing documents them as a requirement, no schema constrains a brand-lock palette table, and `tools/validate_brand_lock.py:110-113` only checks that some hex-shaped string exists. Any brand-lock using different role words falls back silently to `#3B82F6` and friends (`:37-43`).

---

## 5. Failure modes

### F-36 `blocking` Two operators on one project silently destroy each other's verdicts

All four loop artifacts are fixed paths (F-16), and no schema has a run id, round number, or author field.

- Operator A critiques shot_03, writes `output/critique.json` with `verdict: REVISE`. Operator B critiques shot_07 thirty seconds later and writes the same path. A's verdict no longer exists. Neither file contained a shot list, so nothing indicates a loss occurred.
- Either operator then runs revision mode. `skills/visual-prompt-forge/SKILL.md:143` reads the surviving critique, re-emits prompts for that one shot, and reports which shots were revised. The report is accurate about the file it read and wrong about the project.
- Both operators write `output/prompts/{generator}.txt` and `output/prompts/revised-{generator}.txt`. Last writer wins. The only distinguishing mark is the `# Generated: {timestamp}` comment (`skills/visual-prompt-forge/SKILL.md:106`), which no tool reads.
- Both write `output/generated/shot_NN.png`. Operator A's accepted frame is replaced by B's re-roll. `tools/shots-to-html.py:76-83` picks up the new file on the next preview with no change to `shots.json` and no change to any critique.
- `docs/audit-trail-pattern.md:118` instructs teams to "Commit all four output files to Git per major revision". Concurrent work therefore lands as merge conflicts on binary PNGs and on a `critique.json` whose content carries no shot identity, so the conflict cannot be resolved by reading it.

There is no lock file, no per-run output directory, and no `run_id` field in `shots.schema.json`, `text-overlays.schema.json`, or `critique.schema.json`.

### F-37 `blocking` A frame regenerated without re-running the critic terminates the loop on an unreviewed image

Replace `output/generated/shot_03.png`. Nothing else changes:

- `shots.json` is untouched; the architect owns it and the loop never writes it.
- `output/critique.json` still holds whatever verdict was last written, describing the file that used to be at that path. `image_ref` is a name (`critique.schema.json:22-25`), so it still "resolves".
- No content hash exists anywhere, so no tool can detect that the bytes changed.
- `tools/shots-to-html.py:76-83` embeds the new frame under the old rationale, and `:293` stamps it "Generated against brand-lock.snapshot.md on {today}".
- `docs/the-qa-loop.md:88` defines the pipeline stop condition as "no critique.json has a verdict other than ACCEPT". A stale ACCEPT survives the swap, so the loop reports done on a frame no critic has seen.
- `assets.generated[].accepted` would be the field that goes stale here. It has no writer (F-17), so there is not even a stale value to catch.

The gate that `docs/the-qa-loop.md:55` says you can "branch on `critique.json.verdict` and trust" is trustworthy about severity arithmetic (`tools/validate_critique.py:47-53`) and says nothing about whether the verdict still describes the file on disk.

### F-38 `blocking` A mid-project brand-lock change silently repoints history

The one thing that works: editing `brand-packs/whystrohm.md` does not alter an existing `output/brand-lock.snapshot.md`. Everything downstream of that breaks.

- Re-running the architect re-snapshots to the same path (`skills/storyboard-architect/SKILL.md:132-139`, output set at `:29-33`). The file is overwritten in place. Round-1 prompts and frames now sit beside a snapshot they were not built from. `shots.json:brand_lock_ref` still resolves, so no tool reports a mismatch (F-30).
- The critic is then handed the new snapshot (`skills/visual-asset-critic/SKILL.md:56` lists brand-lock as a recommended input) and judges round-1 frames against rules that did not exist when they were generated. A `blocking` Brand Lock issue forces REJECT (`tools/validate_critique.py:47-50`), so frames get rejected for retroactive violations. The critique records `brand_lock_ref: "brand-lock.snapshot.md"`, a string that is now ambiguous across the project's history.
- Revision mode re-forges those shots against the new brand-lock while reusing the same fixed output paths (F-16), so the round-1 prompt set built against the old brand state is gone.
- A color removed from the brand pack keeps validating in `text-overlays.json` forever, because palette membership is unenforced (F-10). The overlay renders in the retired color, and `docs/brand-lock-anatomy.md:87` says the schema prevents exactly this.
- `tools/shots-to-html.py:293` continues to assert the preview was "Generated against brand-lock.snapshot.md" with today's date, for both the pre-change and post-change frames in the same document.

### F-39 `major` Determinism is asserted repeatedly and tested nowhere

`docs/why-this-exists.md:33`: "Determinism, same inputs, same outputs. If two team members run the same brief, they should produce the same storyboard."
`skills/visual-prompt-forge/SKILL.md:186`: "If two consecutive runs produce different prompts for the same shot, the skill is broken. Determinism is the whole point."
`skills/visual-prompt-forge/SKILL.md:149`: "same inputs plus the same critique produce the same revised prompt."
`docs/audit-trail-pattern.md:85`: "Regeneration on demand. Same inputs, same outputs."

There is no `tests/` directory, no golden-output fixture, and no CI step that runs a skill twice and diffs. Every composition step is model judgment: the five-layer assembly (`skills/visual-prompt-forge/SKILL.md:86-96`), the severity mapping (`skills/visual-asset-critic/SKILL.md:133-139`), and the application of a free-prose `fix` string (`critique.schema.json:60`) to a prompt.

The forge's own output format defeats byte-level determinism regardless: `skills/visual-prompt-forge/SKILL.md:106` puts `# Generated: {timestamp}` in every prompt file header.

The one component that is demonstrably deterministic is `tools/shots-to-html.py`, and only modulo its timestamp (F-32).

---

## 6. Drift: CHANGELOG v2.0.0 against the tree

### Claimed and present

Verified in the tree: `brand-lock-extractor` (`CHANGELOG.md:11`), `critique.json` output and schema (`:12`), `validate_critique.py` with `--selftest` (`:13`), `_capabilities.json` plus `capabilities.schema.json` (`:14`), `validate_capabilities.py` (`:15`), revision mode (`:16`), the four fal.ai motion adapters (`:17`), the two critique fixtures (`:18`), shots schema v1.1 (`:19`), `docs/the-qa-loop.md` (`:20`), the `install.sh` hardening (`:26`, matching `install.sh:46-54`), the two new CI steps (`:27`), and the `SocialPreview` composition (`:28`, `remotion/src/SocialPreview.tsx:22` reads `v2.0.0`). The `runway-sora` adapter and its capability entry are gone (`:32`).

### F-40 `major` The v2.0.0 tag is published, the CHANGELOG says Unreleased, and the tag is not what is on main

`CHANGELOG.md:5`: `## [2.0.0] - Unreleased`, with no date.

Actual state: `git tag -l` returns `v2.0.0`. `git ls-remote --tags origin` returns it on the remote. The tag object is `1d806fa`, dereferencing to commit `39c2227` ("chore: brand this release v2.0.0"). `main` is at `673ee99`, one commit ahead. `git merge-base --is-ancestor v2.0.0 main` succeeds.

The commit the tag excludes is `673ee99`, which changed three files: `LICENSE` (+184 lines), `docs/images/demo.gif`, and `remotion/src/ShotkitDemo.tsx`.

Consequence: `git show v2.0.0:LICENSE` is 17 lines, the Apache short-form notice only. `LICENSE` on main is 201 lines, the full Apache-2.0 text with appendix. Anyone fetching the published v2.0.0 tag gets the pre-LICENSE-completion tree. `README.md:253` and `CHANGELOG.md` both state Apache 2.0.

Also: `CHANGELOG.md:34` records `[0.1.0], 2026-05-08` and no `v0.1.0` tag exists.

### F-41 `major` `README.md` lists the release's headline feature as still on the roadmap

`README.md:219`, under "Still on the roadmap": "**`brand-lock-extractor`**. Upload a brand book (PDF, screenshots, URL), get a `brand-lock.md` back. The cold-start killer."

The same file ships it at `:50` ("The five skills"), `:54` (table row), `:14` ("all five skills"). `CHANGELOG.md:11` announces it as added in this release. `install.sh:39` installs it.

### F-42 `major` The schema description claims a consumer that `README.md` says does not exist

`shots.schema.json:116`: the `assets` block "Lets visual-asset-critic and the HTML preview find images without a schema bump."

`README.md:221`: "The `shot.assets` field landed in shots schema v1.1; wiring the HTML preview and critic to consume it is the remaining work."

`CHANGELOG.md:19` states v1.1 was "verified against all bundled examples". No bundled example contains an `assets` block, and no CI step validates any instance (F-01). See also F-17.

### F-43 `minor` `docs/the-qa-loop.md` describes a four-skill kit

`docs/the-qa-loop.md:5`: "shotkit's four skills already give you the pieces of a review."

There are five. `README.md:50`, `docs/claude-code-workflow.md:7`, `:16`, `:86`, and `install.sh:38-44` all say five.

### F-44 `minor` Adapter count is seven in three places and ten in two

Ten adapters exist in `skills/visual-prompt-forge/adapters/` and ten entries in `_capabilities.json`.

- `docs/connecting-to-generators.md:47`: "The seven adapters in `visual-prompt-forge`".
- `skills/visual-prompt-forge/SKILL.md:225`: "`examples/one-shot-all-adapters/` contains a single shot rendered to all seven adapters side-by-side."
- `CHANGELOG.md:70`: "One shot rendered across all 7 generator adapters".

Against `README.md:56` ("10 generators (6 stills, 4 motion)") and `README.md:87` ("Ten generators, one spec").

`skills/visual-prompt-forge/examples/one-shot-all-adapters/` contains seven `.txt` files: flux, gpt-image, ideogram, kling, midjourney, nano-banana, seedream. There is no worked example for veo, seedance, or hailuo, the three adapters added in this release.

### F-45 `minor` Sora survives in the flagship demo the README points visitors to

`CHANGELOG.md:32` records the `runway-sora` removal. `CHANGELOG.md:28` discloses the exception: "The demo.gif and explainer videos are unchanged."

`README.md:18` presents that unchanged asset as the primary demo: "**Watch shotkit explain itself.** The 90-second explainer was made *by* shotkit."

Surviving references:

- `skills/storyboard-architect/examples/shotkit-explainer/shots.json:90`: subject text listing "runway sora" as one of seven adapters.
- `skills/storyboard-architect/examples/shotkit-explainer/storyboard.md:51-53`: "Midjourney, Flux, Ideogram, GPT Image, Nano Banana, Seedream, Runway/Sora", plus on-screen text "One shot. Seven generators. One spec."
- `skills/storyboard-architect/examples/shotkit-explainer/storyboard.md:39`: "prompts/ directory with seven adapter files".
- `remotion/src/ShotkitExplainer.tsx:238`, `:393`, `:642`: Sora in the adapter list, the file tree, and the radial diagram.
- `remotion/src/ShotkitExplainer.tsx:977`: version string reads `v0.1.0`.

`docs/why-this-exists.md:22` and `docs/connecting-to-generators.md:39` both cite the Sora removal as evidence of model agnosticism, in the same repo where the demo still shows it.

### F-46 `minor` `remotion/package.json` version is 0.1.0

`remotion/package.json:3`: `"version": "0.1.0"`. `remotion/src/SocialPreview.tsx:22` and `remotion/src/ShotkitDemo.tsx:393,410` read `v2.0.0`.

### F-47 `minor` CHANGELOG 0.1.0 entries are stale against the current tree

- `CHANGELOG.md:54`: "Three validation scripts (frontmatter, JSON schemas, brand-lock structure)". There are five.
- `CHANGELOG.md:83-89`, "Known v2.0.0 work", lists four items. One shipped (`brand-lock-extractor`). The other three are absent from the tree and absent from the 2.0.0 Added list: PDF and PPTX exporters, user-supplied asset folder convention, duration-rescale workflow with beat-aware redistribution. `README.md:220-222` still lists all three as roadmap.

### F-48 `minor` `tools/README.md` overstates what CI and the tools cover

- On `shots-to-html.py`: "The output is identical to what the skill produces. Same template, same CSS, same JavaScript." False on the template (F-22).
- On `validate_brand_lock.py`: "Run before committing new brand-pack examples." CI runs it against two fixed paths, neither of which is a brand-pack example or a snapshot (F-23).
- `README.md:236-247` lists five validator commands as the local pre-PR set and states "CI runs all of these on every PR". CI also runs `validate_critique.py` against the two example fixtures, which the README list omits.

### F-49 `minor` A monthly price is committed in the docs

`docs/connecting-to-generators.md:44`: "The operated pipeline (running generators, managing rendering, automated publishing) is what WhyStrohm offers commercially at $3,000/month."

`README.md:156` and `:200` route the same question to whystrohm.com without a figure. This also violates the standing no-prices-in-repo rule in `~/.claude/CLAUDE.md`.

### F-50 `minor` Internal handoff notes ship in the public repo and contradict the current tree

`.archive/HANDOFF.md` is tracked. `.archive/README.md:3` frames it as "Build documentation from prior shotkit construction sessions. Kept for transparency."

`.archive/HANDOFF.md:168-173` discusses an example directory named `one-shot-five-generators` containing two adapter files and debates renaming it, and `:78` describes a reference file by a state that no longer holds. The directory is now `one-shot-all-adapters` with seven files.

---

## Finding index

| ID | Severity | Title | Primary location |
|---|---|---|---|
| F-01 | blocking | No instance validator for `shots.json` or `text-overlays.json` | `tools/validate_schemas.py:25-51` |
| F-16 | blocking | Every loop artifact uses a fixed path; each write destroys prior state | `skills/visual-asset-critic/SKILL.md:120` |
| F-28 | blocking | A gate-passing `critique.json` can identify nothing | `critique.schema.json:7` |
| F-29 | blocking | No artifact binds an image to its prompt, generator, or brand-lock | `critique.schema.json:8,22-25` |
| F-36 | blocking | Concurrent operators silently destroy each other's verdicts | `skills/visual-asset-critic/SKILL.md:120` |
| F-37 | blocking | A regenerated frame terminates the loop on an unreviewed image | `docs/the-qa-loop.md:88` |
| F-38 | blocking | A mid-project brand-lock change silently repoints history | `skills/storyboard-architect/SKILL.md:132-139` |
| F-02 | major | The critique gate is repo-only and never runs on a real critique | `install.sh:38-44` |
| F-06 | major | Architect documents field names the schema rejects | `skills/storyboard-architect/SKILL.md:103-104` |
| F-07 | major | Documented motion vocabulary missing four of eleven enum values | `skills/storyboard-architect/SKILL.md:101` |
| F-08 | major | Timing invariants stated as a checklist, enforced nowhere | `shots.schema.json:69-70` |
| F-09 | major | Cross-file reference integrity unenforced; schemas disagree on cardinality | `shots.schema.json:101-106` |
| F-10 | major | Palette membership claimed as schema-enforced, is not | `docs/brand-lock-anatomy.md:87` |
| F-11 | major | `.md` versus JSON precedence unchecked; three entries disagree | `tools/validate_capabilities.py:76-81` |
| F-12 | major | nano-banana aspect parameter wrong in the file that wins | `_capabilities.json:82` |
| F-13 | major | Revision mode treats REJECT identically to REVISE | `skills/visual-prompt-forge/SKILL.md:143-144` |
| F-14 | major | `post-level` fixes produce no artifact and no record | `skills/visual-prompt-forge/SKILL.md:148` |
| F-15 | major | Prompt-file format defined only by a regex in a helper | `tools/copy-prompt.py:20` |
| F-17 | major | `assets.generated[].accepted` has no writer, reader, or verdict link | `shots.schema.json:114-137` |
| F-18 | major | `critique.schema.json` forbids adding provenance in band | `critique.schema.json:8` |
| F-21 | major | `copy-prompt.py` cannot read revision-mode output | `tools/copy-prompt.py:20` |
| F-22 | major | Two renderers, no shared template, README claims otherwise | `tools/shots-to-html.py:239-240` |
| F-23 | major | Snapshot header required by the architect, checked by nothing | `tools/validate_brand_lock.py:89-115` |
| F-24 | major | An unfilled template passes as a valid brand-lock | `tools/validate_brand_lock.py:112` |
| F-25 | major | Cross-skill relative path breaks under documented packaging | `skills/visual-prompt-forge/SKILL.md:65` |
| F-26 | major | `tools/` is not installed; tool paths in SKILL.md unresolvable | `install.sh:38-44` |
| F-30 | major | Chain references state by name with inconsistent path bases | `shots.schema.json:37-40` |
| F-31 | major | Images resolved by a filename convention no schema describes | `tools/shots-to-html.py:76-83` |
| F-32 | major | Re-rendering the preview overwrites the run date with a false one | `tools/shots-to-html.py:241,293` |
| F-34 | major | HTML built from model-generated strings with no escaping | `tools/shots-to-html.py:98-160` |
| F-35 | major | Preview discards brand typography, depends on undocumented role names | `tools/shots-to-html.py:47-68` |
| F-39 | major | Determinism asserted repeatedly, tested nowhere | `docs/why-this-exists.md:33` |
| F-40 | major | v2.0.0 tag published, CHANGELOG says Unreleased, tag behind main | `CHANGELOG.md:5` |
| F-41 | major | README lists the release's headline feature as roadmap | `README.md:219` |
| F-42 | major | Schema description claims a consumer README says is unbuilt | `shots.schema.json:116` |
| F-03 | minor | `validate_critique.py` has no directory or glob mode | `tools/validate_critique.py:121-135` |
| F-04 | minor | Parity check globs all markdown in `adapters/` | `tools/validate_capabilities.py:77` |
| F-05 | minor | `validate_skills.py` does not check referenced files exist | `skills/storyboard-html-preview/SKILL.md:220` |
| F-19 | minor | `rack` means two things in one schema | `shots.schema.json:85,90` |
| F-20 | minor | `depth_of_field` in schema and examples, absent from instructions | `skills/storyboard-architect/SKILL.md:96-107` |
| F-27 | minor | `install.sh` copies `.DS_Store` into the skills directory | `install.sh:104` |
| F-33 | minor | Preview version marker hardcoded to v1.0 | `tools/shots-to-html.py:261` |
| F-43 | minor | `docs/the-qa-loop.md` describes a four-skill kit | `docs/the-qa-loop.md:5` |
| F-44 | minor | Adapter count seven in three places, ten in two; three have no example | `docs/connecting-to-generators.md:47` |
| F-45 | minor | Sora survives in the flagship demo the README points to | `remotion/src/ShotkitExplainer.tsx:238` |
| F-46 | minor | `remotion/package.json` version is 0.1.0 | `remotion/package.json:3` |
| F-47 | minor | CHANGELOG 0.1.0 entries stale against the tree | `CHANGELOG.md:54,83-89` |
| F-48 | minor | `tools/README.md` overstates tool and CI coverage | `tools/README.md` |
| F-49 | minor | A monthly price is committed in the docs | `docs/connecting-to-generators.md:44` |
| F-50 | minor | Internal handoff notes ship publicly and contradict the tree | `.archive/HANDOFF.md:168-173` |

Totals: 7 blocking, 28 major, 15 minor.
