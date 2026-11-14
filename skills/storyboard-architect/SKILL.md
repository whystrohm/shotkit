---
name: storyboard-architect
description: Turn a video brief into a storyboard and shot list with shot specs, timing, on-screen text and per-shot rationale. Use when the user asks for a storyboard, a shot list, shot-by-shot beats or structured pre-production for a video, or hands over a script or concept to break into shots. Produces run.json, storyboard.md, shots.json, text-overlays.json and brand-lock.snapshot.md. It plans the video; it does not render it. Pairs with visual-prompt-forge, visual-asset-critic and storyboard-html-preview.
---

# Storyboard Architect

You are turning a creative brief into a deterministic storyboard. The output is a set of files an editor, agency, or developer can act on without asking follow-up questions.

This is not a creative-writing exercise. The output is a spec.

## When to use

Trigger this skill when the user:

- Asks for a storyboard or shot list for a video ("storyboard a 30-second explainer for...", "shot list for a TikTok ad about...")
- Asks to plan shots, break out beats, or write a shot list
- Hands over a script, brief, or concept document expecting structured pre-production output
- Mentions a beat framework by name (Hero Trilogy, Pain-Proof-Promise, etc.)
- References an existing brand-lock file or pack

If the user only wants prompts for an image generator (no narrative structure), use `visual-prompt-forge` directly instead.

## What you produce

For every storyboard run, create this exact set of files in the working output directory:

```
output/
├── run.json                   # Run identity + every input pinned by content hash
├── storyboard.md              # Human-readable, structured per shot
├── shots.json                 # Machine-readable, schema in templates/shots.schema.json
├── text-overlays.json         # On-screen text + timing
└── brand-lock.snapshot.md     # Frozen copy of the brand-lock used (audit trail)
```

`run.json` is what makes the rest of the tree auditable later. A filename says nothing
about the bytes behind it, so the snapshot sitting next to a set of frames is not proof
that it is the snapshot they were built from. The hashes in `run.json` are that proof.
Write it once, as the last step, after the other four files are final. Everything in `run.json` except `rounds` is written once and never edited. `rounds` is append-only: `visual-prompt-forge` adds one entry per prompt round and never changes an earlier one.

If the user asks for image prompts or HTML preview, hand off to `visual-prompt-forge` or `storyboard-html-preview`, those skills consume `shots.json` directly. Don't try to do their job here.

## Where the tools and packs are

After `./install.sh`, the validators and helpers are in `~/.claude/shotkit-tools/` and the
brand packs are in `~/.claude/shotkit-brand-packs/`. A `--project` install puts both
under `./.claude/` instead. From a repo clone they are `tools/` and `brand-packs/`. The
commands below give the installed path first and the clone path second. They need no
setup: `sk` runs each tool and supplies the two Python packages the validators use.

## Inputs

You need these. If any are missing, ask before drafting.

| Input | Required? | Default if absent |
|---|---|---|
| Brief (problem, audience, goal) | Yes | Ask |
| Total duration | Yes | Ask |
| Aspect ratio | Yes | Ask (16:9, 9:16, 1:1) |
| Beat framework | No | Suggest based on brief |
| Brand-lock file path | No | Use `~/.claude/shotkit-brand-packs/_starter.md` (clone: `brand-packs/_starter.md`) and flag the gap |
| Voiceover style (VO present, on-screen only, captions) | No | Ask if unclear |
| Target generator(s) for downstream prompts | No | Note as "to be specified" |
| Audit findings, `brand/audit-findings.json` from whystrohm-audit | No | Skip Step 1b |

## Reading budget

This file carries what a normal run needs: the fields, the vocabularies and the file
shapes. Do not read the references, the templates and the examples up front. That costs
the user minutes before the first file is written.

- Always read: the brand-lock.
- Read when the decision needs it: `references/beat-frameworks.md` for a framework you
  do not know cold, `references/timing-rules.md` when the brief and the length disagree,
  `references/on-screen-text.md` when you are unsure a line belongs on screen.
- Read when the validator says so: the schemas in `templates/`. Its messages name the
  field and the rule, so fix from the message first.
- Read last, if at all: the examples.

## Workflow

Follow this sequence. Don't skip steps even if the brief seems simple.

### Step 1. Read the brand-lock

If a brand-lock file path is provided, read it first. Extract:

- Palette (hex)
- Typography
- Mood descriptors
- "Never" list (what this brand will never do visually)
- Motion language
- Voice tone
- Aspect-ratio preferences

If no brand-lock is provided, copy `~/.claude/shotkit-brand-packs/_starter.md` (from a
clone, `brand-packs/_starter.md`) into the output as `brand-lock.snapshot.md`. The
starter is a neutral, filled-in lock, so the snapshot passes its check and the overlays
have real colours to use. Set `brand_lock_configured: false` in `run.json`, and tell the
user the run used the starter brand and how to replace it: ask for a brand lock from
their site, or fill in `_template.md`.

Do not snapshot `_template.md`. It is blank on purpose, and a blank palette fails the
snapshot check. Do not invent a palette for a real company either: an invented brand
lock looks like a decision the company made.

### Step 1b. Read the audit findings, if there are any

If the user points at `brand/audit-findings.json`, or it sits in the project's `brand/` folder
and the brief is for the same company, read it. Its format is
`contracts/audit-findings.v1.schema.json` in this repo. Check `contract` is `audit-findings`
and `version` is `"1"` before using it.

- The first of `top_gaps` is a candidate for the pain or world beat: the problem the film
  answers.
- `rewrite.after` is a candidate overlay line. Use it only as written. A bracketed
  placeholder in it means the proof is missing, so leave that line out rather than filling it.
- Name the file and its `audited_at` in the Brief section of `storyboard.md`.

The brief still decides. Findings inform the beats; they never replace what the user asked for.

### Step 2. Pick the beat framework

Read `references/beat-frameworks.md`. Pick the one that matches the brief. Common cases:

- Pain-reframe-promise → conversion content
- Hero Trilogy → product hero films
- Founder Explainer → personal-brand content
- Content Spiral → kinetic typography / opinion pieces

If none fit cleanly, build a custom beat structure but document why in `storyboard.md` rationale section.

### Step 3. Block out timing

Read `references/timing-rules.md` for the math. Default cadence:

- Hook beat: 0–2 seconds
- Pain/setup: 2–4 seconds (for 15s), 2–6 seconds (for 30s) or 2–10 seconds (for 60s)
- Proof/reframe: middle third
- Promise/CTA: final 3–4 seconds (for 15s), 4–6 seconds (for 30s), 6–10 seconds (for 60s)

Don't fight the framework. If the brief and the duration disagree, surface the disagreement before drafting.

### Step 4. Draft the shot list

Read `references/shot-grammar.md` for controlled vocabulary. The field names below are
the schema's field names. `templates/shots.schema.json` sets `additionalProperties:
false`, so a near-miss like `environment` instead of `environment_ref` is a validation
failure, not a synonym.

- `id`, sequential, zero-padded (`shot_01`, `shot_02`...)
- `beat`, which beat this shot serves
- `start` / `end`, timestamps in seconds, decimal allowed. `end` must be after `start`
- `framing`, ECU / CU / MCU / MS / MLS / WS / EWS
- `angle`, eye-level / high / low / overhead / dutch
- `motion`, static / push / pull / pan-left / pan-right / tilt-up / tilt-down /
  handheld / orbit / whip / rack. All eleven are legal; the schema enum is the
  authority and `references/shot-grammar.md` explains when each earns its keep
- `depth_of_field`, optional, shallow / deep / rack
- `subject`, what's in frame, structured
- `environment_ref`, references series-lock language, default `series_lock.environment`
- `lighting_ref`, references series-lock language, default `series_lock.lighting`
- `on_screen_text`, null, one text-overlay id, OR an array of ids when a shot carries
  more than one overlay
- `vo`, voiceover line, or null
- `rationale`, one sentence explaining *why this shot at this moment*

Note on `rack`: as a `motion` value it means the rack focus is the shot's movement; as a
`depth_of_field` value it means focus shifts mid-shot. Same word, two fields, two
meanings.

### Step 5. Separate the text layer

Every piece of on-screen text becomes an entry in `text-overlays.json`. Never bake text into the visual description. Each overlay has:

- `id`, `text_01`, `text_02`...
- `shot_id`, which shot this overlays on
- `content`, the actual text
- `font`, references brand-lock typography
- `position`, `center`, `lower-third`, `upper-third`, `left-third`, `right-third`, or `{x, y}` percentages
- `size`, `display`, `headline`, `body`, `caption`
- `weight`, `regular` (400), `medium` (500), `semibold` (600), `bold` (700), `black` (900)
- `color`, hex (must come from brand-lock palette)
- `enter`, `{ at: seconds, animation: fade-in | slide-up | slide-down | type-on | hard-cut }`
- `exit`, `{ at: seconds, animation: fade-out | slide-up | slide-down | hard-cut }`

Then set the type and check the words:

- **Type treatment.** Mark the two or three words that carry each headline with
  `emphasis`, name the brand once with a `kicker` or a `lockup`, and use a `plate` where
  the frame is busy. The fields and when to use each are in
  `references/on-screen-text.md`, under "Type treatment".
- **The language pass.** Before you write the file, run every line through
  `references/hooks-and-language.md`: a first line that is a hook and not a slogan,
  specific words, one idea per line, nothing the brief did not give.
- **A brand with no typeface.** Pick a pairing from the brand packs folder's
  `type-pairings.md` and write it into the brand lock. Do not default to Inter.

Enter and exit have different animation vocabularies, and `templates/text-overlays.schema.json`
is the authority on both. A shot may carry more than one overlay; list every id in that
shot's `on_screen_text` array, or the extra overlays render nowhere.

### Step 6. Lock the series

Define environment, lighting, and character anchors that apply across every shot. These go at the top of `shots.json` under `series_lock`. Without these, image generation will produce incoherent frames.

### Step 7. Write rationale

Every shot has a one-sentence rationale. Why this beat. Why this framing. Why this on-screen text. This is the audit trail. Do not skip it.

### Step 8. Snapshot the brand-lock

Copy the brand-lock file (or template) into the output as `brand-lock.snapshot.md`. Add
these two comments at the very top, in this order:

```
<!-- snapshot taken: 2026-05-07T14:23:00Z -->
<!-- source: brand-packs/whystrohm.md -->
```

The timestamp is a full UTC instant, `YYYY-MM-DDThh:mm:ssZ`. A bare date cannot
distinguish two runs made on the same day, which is the case that matters. The source is
the path it was copied from, or the literal string `template default` for an
unconfigured run. After an install, a pack path is
`~/.claude/shotkit-brand-packs/whystrohm.md`; from a repo clone it is
`brand-packs/whystrohm.md`. Either passes the validator. Extra comments after these two are fine.

`validate_brand_lock.py --snapshot <path>` checks both lines. Run it:

```bash
~/.claude/shotkit-tools/sk validate_brand_lock.py --snapshot output/brand-lock.snapshot.md
# from a repo clone:
# tools/sk validate_brand_lock.py --snapshot output/brand-lock.snapshot.md
```

### Step 9. Write run.json

Last step, after the other four files are final. Fill in `templates/run.schema.json`.
These fields are required:

| Field | Value |
|---|---|
| `version` | `"1.0"`, the run.json format |
| `run_id` | compact UTC timestamp, a dash, 8 hex characters (below) |
| `created_at` | the same instant as `YYYY-MM-DDThh:mm:ssZ` |
| `shotkit_version` | line 1 of `~/.claude/shotkit-tools/VERSION`; in a repo clone, `VERSION` at the root |
| `project` | `title`, `duration_s` and `aspect` from `shots.json`, plus `framework` and `seed` if set |
| `inputs.shots_ref`, `inputs.shots_sha256` | `shots.json` and its SHA-256 |
| `inputs.text_overlays_ref`, `inputs.text_overlays_sha256` | `text-overlays.json` and its SHA-256, or both `null` with no on-screen text |
| `inputs.brand_lock_ref`, `inputs.brand_lock_sha256` | `brand-lock.snapshot.md` and its SHA-256 |
| `inputs.brand_lock_source` | the pack it was copied from, or `template default` |

Optional: `operator`, `inputs.brand_lock_configured`, `generators`, `rounds`, `meta`.

```bash
head -n 1 ~/.claude/shotkit-tools/VERSION     # from a repo clone: head -n 1 VERSION
shasum -a 256 output/shots.json output/text-overlays.json output/brand-lock.snapshot.md
```

`run_id` is the compact UTC timestamp, a dash, then 8 hex characters, e.g.
`20260730T142300Z-9f2c1ab4`. The hex suffix is what keeps two operators starting a run
in the same second from colliding. Set `brand_lock_configured: false` when the snapshot
is an unfilled template.

Leave `rounds` empty. Everything in `run.json` except `rounds` is written once and never edited. `rounds` is append-only: `visual-prompt-forge` adds one entry per prompt round and never changes an earlier one.

## Output formats

### `storyboard.md`

One heading per section, in this order: the brief as given, the assumptions you made,
the framework and why, the series lock, then one block per shot (id, beat, time,
camera, subject, on-screen text, VO, rationale), then the full VO script if there is
one. `templates/storyboard.md.tpl` has the exact layout if you want it.

### `shots.json`

Must validate against `templates/shots.schema.json`. The structure is:

```json
{
  "version": "1.2",
  "project": { "title": "...", "duration_s": 30, "aspect": "9:16", "framework": "..." },
  "brand_lock_ref": "brand-lock.snapshot.md",
  "series_lock": {
    "character": "...",
    "environment": "...",
    "lighting": "...",
    "color_grade": "..."
  },
  "shots": [
    {
      "id": "shot_01",
      "beat": "hook",
      "start": 0.0,
      "end": 2.0,
      "framing": "MCU",
      "angle": "eye-level",
      "motion": "static",
      "depth_of_field": "shallow",
      "subject": "...",
      "environment_ref": "series_lock.environment",
      "lighting_ref": "series_lock.lighting",
      "on_screen_text": "text_01",
      "vo": null,
      "rationale": "..."
    }
  ]
}
```

Write `1.2` for new storyboards. `1.0` and `1.1` files stay valid; the array form of
`on_screen_text` and the hashed `assets` block need `1.2`.

A shot may also carry a `source`, when the run starts from the user's own photos and
clips. `{"type": "own", "media": "m03", "in": 0.5, "out": 3.5}` puts their file on the
shot. `{"type": "generate", "why": "...", "model": "flux"}` marks a gap. Adding `"start"`
and `"end"` shot ids makes it a bridge clip between two of their shots. The `shotkit`
skill says when to use each. Leave `source` out for an ordinary generated storyboard.

### `text-overlays.json`

Must validate against `templates/text-overlays.schema.json`. The structure is:

```json
{
  "version": "1.0",
  "overlays": [
    {
      "id": "text_01",
      "shot_id": "shot_01",
      "content": "Your content feels random.",
      "font": "Inter Black 900",
      "position": "lower-third",
      "size": "display",
      "weight": "black",
      "color": "#F3F2EE",
      "enter": { "at": 0.4, "animation": "hard-cut" },
      "exit": { "at": 2.0, "animation": "hard-cut" }
    }
  ]
}
```

`enter.at` and `exit.at` are seconds from the start of the film, not of the shot, and
both sit inside the shot's window.

## Quality bar

Run the validator. Do not eyeball this list.

```bash
~/.claude/shotkit-tools/sk validate_shots.py output/
~/.claude/shotkit-tools/sk validate_brand_lock.py --snapshot output/brand-lock.snapshot.md
~/.claude/shotkit-tools/sk validate_provenance.py output/
# from a repo clone:
# tools/sk validate_shots.py output/
# tools/sk validate_brand_lock.py --snapshot output/brand-lock.snapshot.md
# tools/sk validate_provenance.py output/
```

`validate_shots.py` checks every mechanical rule, because a checkbox is a rule enforced by
remembering to look:

- shots.json and text-overlays.json validate against their schemas
- `end` is after `start`, no duplicate ids, no gaps, no overlaps, and the covered span
  matches `project.duration_s` within 0.1s
- every `on_screen_text` resolves to an overlay, every `overlay.shot_id` resolves to a
  shot, and every overlay is reachable from at least one shot
- every overlay's timing sits inside its shot window, and exit is after enter
- every overlay color appears in the brand-lock palette
- `brand_lock_ref` resolves on disk

It warns, rather than fails, on judgement calls worth a second look: overlay copy
repeated inside a shot subject, a raw hex in a subject, shot ids out of chronological
order, an overlay font the brand-lock does not declare.

What the validator cannot check, and you still have to:

- [ ] Every rationale says *why this shot at this moment*, not what the shot contains
- [ ] `series_lock` anchors are specific enough to reproduce (not "a person in a room")
- [ ] The beat structure actually matches the brief's argument
- [ ] `run.json` is written and its hashes are the files as shipped

If the validator fails, fix it before declaring done. A green validator plus an unread
rationale is not a finished storyboard.

## Reference files

Load these as needed:

- `references/beat-frameworks.md`, the beat structures
- `references/shot-grammar.md`, controlled vocabulary for framing/angle/motion
- `references/timing-rules.md`, pacing math
- `references/on-screen-text.md`, when on-screen text earns its keep

## Examples

- `examples/30s-pain-proof-promise/`, full output set for a 30-second conversion ad
- `examples/60s-founder-explainer/`, full output set for a founder explainer

Read these to understand the expected output quality, especially the rationale fields.
Both validate clean under `validate_shots.py --examples`, so they are also
the reference for what a passing file looks like.

For what the output tree looks like after generation and review, see
`../visual-asset-critic/examples/worked-run/`: two shots through two rounds, with real
hashes, per-round prompts and frames, and one critique per shot per round.

## Handoff

After the five files validate, put them on screen. Render the board and open it, without
waiting to be asked:

```bash
~/.claude/shotkit-tools/sk board output/ --open
# from a repo clone:
# tools/sk board output/ --open
```

The board shows every shot on a timeline and a contact sheet, and names the next step.
Then tell the user, in a few lines: what is in `output/`, what you assumed, and that the
board is open. Offer the next steps:

- "Want image prompts? Name your generator and I'll run `visual-prompt-forge`."
- "Have frames already? I'll check them with `visual-asset-critic`."
- "Need a page to send a client? I'll render `preview.html`."

Writing prompts and checking frames wait for the user's word. Opening the board does not.
