---
name: storyboard-architect
description: Turn a creative brief into a production-grade storyboard with structured shots, on-screen text, timing, and per-shot rationale. Use this whenever the user describes a video brief, mentions a storyboard, asks to plan a video, references shot lists or beats, wants to script a social video, or hands over a creative concept that needs to be broken into scenes, even if they don't explicitly say "storyboard." This produces files (storyboard.md, shots.json, text-overlays.json, brand-lock.snapshot.md), not panels in a UI. Pairs with visual-prompt-forge for image prompts, visual-asset-critic for QA, storyboard-html-preview for shareable output.
---

# Storyboard Architect

You are turning a creative brief into a deterministic storyboard. The output is a set of files an editor, agency, or developer can act on without asking follow-up questions.

This is not a creative-writing exercise. The output is a spec.

## When to use

Trigger this skill when the user:

- Describes a video they want to make ("30-second explainer for...", "TikTok ad about...")
- Asks to storyboard, plan shots, break out beats, write a shot list
- Hands over a script, brief, or concept document expecting structured pre-production output
- Mentions a beat framework by name (Hero Trilogy, Pain-Proof-Promise, etc.)
- References an existing brand-lock file or pack

If the user only wants prompts for an image generator (no narrative structure), use `visual-prompt-forge` directly instead.

## What you produce

For every storyboard run, create this exact set of files in the working output directory:

```
output/
├── storyboard.md              # Human-readable, structured per shot
├── shots.json                 # Machine-readable, schema in templates/shots.schema.json
├── text-overlays.json         # On-screen text + timing
└── brand-lock.snapshot.md     # Frozen copy of the brand-lock used (audit trail)
```

If the user asks for image prompts or HTML preview, hand off to `visual-prompt-forge` or `storyboard-html-preview`, those skills consume `shots.json` directly. Don't try to do their job here.

## Inputs

You need these. If any are missing, ask before drafting.

| Input | Required? | Default if absent |
|---|---|---|
| Brief (problem, audience, goal) | Yes | Ask |
| Total duration | Yes | Ask |
| Aspect ratio | Yes | Ask (16:9, 9:16, 1:1) |
| Beat framework | No | Suggest based on brief |
| Brand-lock file path | No | Use `brand-packs/_template.md` and flag the gap |
| Voiceover style (VO present, on-screen only, captions) | No | Ask if unclear |
| Target generator(s) for downstream prompts | No | Note as "to be specified" |

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

If no brand-lock is provided, copy `brand-packs/_template.md` into the output as `brand-lock.snapshot.md` with a note: `# UNCONFIGURED, using template defaults. Recommend providing a real brand-lock for production work.`

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
- Pain/setup: 2–6 seconds (for 30s) or 2–10 seconds (for 60s)
- Proof/reframe: middle third
- Promise/CTA: final 4–6 seconds

Don't fight the framework. If the brief and the duration disagree, surface the disagreement before drafting.

### Step 4. Draft the shot list

Read `references/shot-grammar.md` for controlled vocabulary. Every shot has:

- `id`, sequential, zero-padded (`shot_01`, `shot_02`...)
- `beat`, which beat this shot serves
- `start` / `end`, timestamps in seconds, decimal allowed
- `framing`, ECU / CU / MCU / MS / MLS / WS / EWS
- `angle`, eye-level / high / low / overhead / dutch
- `motion`, static / push / pull / pan-left / pan-right / handheld / orbit
- `subject`, what's in frame, structured
- `environment`, references series-lock language
- `lighting`, references series-lock language
- `on_screen_text`, null OR a text-overlay reference
- `vo`, voiceover line, or null
- `rationale`, one sentence explaining *why this shot at this moment*

### Step 5. Separate the text layer

Every piece of on-screen text becomes an entry in `text-overlays.json`. Never bake text into the visual description. Each overlay has:

- `id`, `text_01`, `text_02`...
- `shot_id`, which shot this overlays on
- `content`, the actual text
- `font`, references brand-lock typography
- `position`, `center`, `lower-third`, `upper-third`, `left-third`, `right-third`, or `{x, y}` percentages
- `size`, `display`, `headline`, `body`, `caption`
- `weight`, `regular`, `medium`, `bold`, `black`
- `color`, hex (must come from brand-lock palette)
- `enter`, `{ at: seconds, animation: fade-in | slide-up | type-on | hard-cut }`
- `exit`, `{ at: seconds, animation: fade-out | slide-down | hard-cut }`

### Step 6. Lock the series

Define environment, lighting, and character anchors that apply across every shot. These go at the top of `shots.json` under `series_lock`. Without these, image generation will produce incoherent frames.

### Step 7. Write rationale

Every shot has a one-sentence rationale. Why this beat. Why this framing. Why this on-screen text. This is the audit trail. Do not skip it.

### Step 8. Snapshot the brand-lock

Copy the brand-lock file (or template) into the output as `brand-lock.snapshot.md`. Add a header line at the top:

```
<!-- snapshot taken: ISO-8601 timestamp -->
<!-- source: original path or "template default" -->
```

This is what makes the storyboard reproducible later.

## Output formats

### `storyboard.md`

Use the template at `templates/storyboard.md.tpl`. Read it before writing.

### `shots.json`

Must validate against `templates/shots.schema.json`. Read it before writing. The structure is:

```json
{
  "version": "1.0",
  "project": { "title": "...", "duration_s": 30, "aspect": "9:16" },
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

### `text-overlays.json`

Must validate against `templates/text-overlays.schema.json`. Read it before writing.

## Quality bar

Before declaring the storyboard complete, verify:

- [ ] Every shot has a rationale
- [ ] Total of `(end - start)` across shots equals project duration (within 0.1s)
- [ ] Every `on_screen_text` reference resolves to an entry in `text-overlays.json`
- [ ] Every text overlay color appears in the brand-lock palette
- [ ] `series_lock` is populated (not empty strings)
- [ ] `brand-lock.snapshot.md` exists in output
- [ ] No on-screen text is described inside a shot's `subject` field
- [ ] No specific brand colors are described in shot subjects (those live in series_lock and brand-lock)

If any check fails, fix before declaring done.

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

## Handoff

After producing the four files, tell the user what's in `output/` and offer the obvious next steps:

- "Want image prompts? I'll run `visual-prompt-forge` on `shots.json`."
- "Want a shareable HTML preview? I'll run `storyboard-html-preview`."
- "Want to QA a generated image against this storyboard? I'll run `visual-asset-critic`."

Don't run those automatically. The user picks.
