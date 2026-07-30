---
name: visual-prompt-forge
description: Generate model-specific prompts from shots.json. Outputs copy-paste-ready prompts for stills (Midjourney, Flux, Ideogram, GPT Image, Nano Banana, Seedream) and motion video (Kling, Veo, Seedance, Hailuo). Also runs a revision mode that reads a critique.json and re-emits prompts for only the failed shots, closing the QA loop. Use when the user asks for image or video prompts, mentions any of those generators, wants AI-generated frames for a storyboard, or hands over shots.json. The prompt half of the pipeline. Composes with storyboard-architect upstream, visual-asset-critic downstream.
---

# Visual Prompt Forge

You are turning structured shot data into prompts that work in production. Each image generator rewards a different prompting style, short and high-signal for Midjourney, natural-language for Flux, paragraph-form for GPT Image, text-aware for Ideogram. A prompt that crushes in one will produce slop in another.

This skill adapts. Same shot, different syntax.

## When to use

Trigger when the user:

- Hands over a `shots.json` (or any structured shot list) and asks for prompts
- Names a specific generator (Midjourney, Flux, Ideogram, GPT Image, Nano Banana, Seedream, Kling, Veo, Seedance, Hailuo)
- Asks for "image prompts," "Midjourney prompts," "AI prompts," "generation prompts" for a storyboard
- Wants the same shot adapted to multiple generators

If the user wants to build a storyboard from scratch (no shots.json yet), use `storyboard-architect` first, then chain into this skill.

## What you produce

For a given `shots.json` and a list of target generators, produce one file per generator,
inside a directory named for the round:

```
output/prompts/round-1/
├── midjourney.txt          # If targeted
├── flux.txt
├── ideogram.txt
├── gpt-image.txt
├── nano-banana.txt
├── seedream.txt
├── kling.txt               # Motion-aware video, default
├── veo.txt                 # Motion, dialogue/lipsync + native audio
├── seedance.txt            # Motion, multi-shot sequences
└── hailuo.txt              # Motion, budget iteration
```

Round 1 is the first pass. Revision mode writes `output/prompts/round-2/`, and so on.
The round in the path is not decoration: prompt files used to be written to one fixed
path per generator, so round 2 destroyed round 1 and the prompt that actually produced
most of the surviving frames was gone.

Each file is plain text, one prompt per shot, separated by a blank line and a `# shot_NN` comment. Designed for copy-paste workflows, drop into the generator's UI or pipe into an API.

## The five-layer prompt anatomy

Every prompt is composed from these layers. Read `references/prompt-anatomy.md` for the full theory. Quick version:

1. **Brand Lock**, palette, type, mood, "never" list (constant across project)
2. **Series Lock**, character/environment/lighting anchors (constant across storyboard)
3. **Shot Spec**, framing, angle, motion, subject (per shot)
4. **Text Layer**, **never in the prompt**, composited separately
5. **Generator Adapter**, model-specific syntax wrapper

The first four come from `shots.json` and the brand-lock. The fifth is what this skill applies.

## Workflow

### Step 1. Read inputs

You need:

- `shots.json` (required), the structured shot list
- `brand-lock.snapshot.md` (required), referenced from shots.json
- Target generators (required), ask if not specified

Validate before composing:

```bash
python tools/validate_shots.py output/
```

If the brand-lock is missing or `shots.json` does not validate, stop and tell the user.
Don't try to forge prompts from incomplete data.

If `tools/` is not on hand (a Claude.ai upload, or a single-skill install), read the
schema from `../storyboard-architect/templates/shots.schema.json` and check by hand. That
relative path only resolves when the skills sit side by side; when they don't, ask the
user for the schema rather than composing from memory of it.

### Step 2. Pick the adapters

For each target generator, read the matching adapter file:

- `adapters/midjourney.md`
- `adapters/flux.md`
- `adapters/ideogram.md`
- `adapters/gpt-image.md`
- `adapters/nano-banana.md`
- `adapters/seedream.md`
- `adapters/kling.md`      (motion video, default)
- `adapters/veo.md`        (motion video, dialogue/lipsync + native audio)
- `adapters/seedance.md`   (motion video, multi-shot sequences)
- `adapters/hailuo.md`     (motion video, budget iteration)

Each adapter file documents the prompting style, parameter syntax, and known pitfalls for that generator. You **must** read the adapter before writing prompts for it. Don't guess from training data, image-gen syntax has churned multiple times.

**`adapters/_capabilities.json` is the single source of truth for per-generator limits** (`max_prompt_words`, `supports_text_render`, `supports_motion`, `aspect_param`, and so on). Read it once at the start and respect those values when composing, and do not target motion on a stills-only generator.

`max_prompt_words` is a ceiling. The range in an adapter `.md` is the recommended target
and always sits inside that ceiling, so a `.md` saying "40 to 70 words" under a ceiling of
120 is guidance, not a conflict. Where a fact in a `.md` and a fact in the JSON genuinely
disagree, **the JSON wins**.

That rule is now enforced rather than trusted. `tools/validate_capabilities.py` fails the
build when an adapter advertises more words than its ceiling, or when an adapter never
documents the `aspect_param` the JSON tells you to send. The second check exists because
nano-banana's matrix entry said `aspect_ratio` while its adapter said the API expects
`aspectRatio`; the precedence rule meant the wrong one won, silently, on every prompt.

### Step 3. Compose per shot

For each shot in `shots.json`, for each target generator:

1. Pull brand-lock palette, mood, "never" list
2. Pull series_lock character/environment/lighting
3. Pull shot framing/angle/motion/subject
4. **Strip any on_screen_text reference**, text never goes in the prompt
5. Apply the generator adapter's syntax wrapper
6. Append generator-specific parameters (aspect ratio, style flags, seed if applicable)

### Step 4. Write output files

One file per generator, into `output/prompts/round-{N}/`. Format:

```
# Storyboard: {project title}
# Generator: midjourney
# Model: {model_version from _capabilities.json}
# Aspect: 9:16
# Brand-lock: brand-lock.snapshot.md
# Run: {run_id from run.json}
# Round: 1

# shot_01, hook, 0.0-2.0s, MCU eye-level static
{the prompt}

# shot_02, pain, 2.0-6.0s, MS eye-level push
{the prompt}

...
```

The `#` lines are comments; the user copies just the prompt body. `tools/copy-prompt.py`
parses this format, treating a comment line that names a shot as a block header and any
other comment inside a block as an annotation it will not copy.

Record the run and round in the header, not a wall-clock "Generated" line. A timestamp in
the header made every file differ between two otherwise identical runs, which is a strange
thing to put in an artifact whose selling point is determinism.

### Step 4b. Append the round to run.json

After writing the files, append an entry to `run.json`'s `rounds` array: the round number,
`started_at`, a `reason`, and for each file its generator, path, SHA-256, and the shot ids
it covers.

```bash
shasum -a 256 output/prompts/round-1/*.txt
```

This is the only writeable part of `run.json`. Everything else was fixed when the
architect wrote it.

### Step 5. Hand off

Tell the user where the files are. Offer the next step:

> "Want me to QA the generated images against the storyboard? Use `visual-asset-critic` once you have the renders."

For paste-into-generator workflows, the user can pipe individual shots to the clipboard with the bundled helper:

```bash
python tools/copy-prompt.py output/prompts/round-1/midjourney.txt
python tools/copy-prompt.py output/prompts/round-2/revised-midjourney.txt --shot shot_03
```

This is optional. The `.txt` files are also directly readable, and the user can copy any block by hand. The helper exists for the case where the operator is bouncing between the terminal and a generator UI repeatedly.

## Revision mode (closing the QA loop)

This is what `visual-asset-critic`'s structured output is for. When the user hands you `shots.json` plus one or more `critique.json` files (the machine-readable verdict the critic writes), don't re-forge the whole storyboard, re-emit prompts for **only the shots that failed**, with the fix already applied.

### Trigger

The user says "apply the critique", "revise the failed shots", "re-roll what didn't pass", or hands over an output tree containing `critiques/`.

### Workflow

1. Read every critique under `output/critiques/round-{N}/`, where N is the highest round
   present. Each file is one shot's verdict (`shot_id`, `verdict`, `issues[]`).
2. Skip any with `verdict: ACCEPT`. Those are done.
3. **Stop on `REJECT`.** A REJECT means the critic found a blocking issue, or three or more
   major ones: a failure with no clear fix path. Re-emitting a prompt for it pretends
   otherwise. List the rejected shots, say what the critic said about them, and ask the
   user how to proceed. Common answers are a change to the shot spec, a change to the
   brand-lock, or a different generator, and all three are decisions above this skill's
   pay grade.
4. For every `REVISE` shot, walk its `issues[]` and branch on `fix_type`:
   - **`prompt-level`**, recompose that shot's prompt with the change in `fix` applied
     (e.g. add the missing series_lock anchor). Re-emit it.
   - **`re-roll`**, keep the prompt identical; the generation was just a bad sample.
     Re-emit it with a `# fix [Technical, re-roll]` annotation saying to take 2-3 samples
     and pick the cleanest.
   - **`post-level`**, do **not** re-emit. The fix happens in compositing, not a new
     generation.
5. A shot whose issues are all `post-level` needs no new prompt. Leave it out of the
   revised file and add its id to `post_only_shots` on the new round entry in `run.json`.
   Saying it in chat is not recording it: that obligation has to exist on disk or the
   compositing step is a memory.
6. Re-apply the five-layer anatomy and the same adapter as the original run.

### Output

Write `output/prompts/round-{N+1}/revised-{generator}.txt` containing only the revised
shots, then append the round to `run.json`. Annotate each shot with what changed and why,
citing the issue:

```
# shot_03, reframe, 11.0-16.0s, MCU eye-level push, revision (was REVISE)
# fix [Series Lock, major]: added 'salt-and-pepper hair' to the character anchor (was missing)
# fix [Shot Spec, minor]: medium shot -> medium close-up
{the revised prompt}
```

The block header leads with the shot id, same as a full pass. `tools/copy-prompt.py`
identifies a block by the shot id near the start of the line, so a header that led with
"Revision of" produced a file the paste helper could not read at all, which is
inconvenient in the one file the operator is about to paste from repeatedly.

Tell the user which shots were revised, which need only post work, which were rejected,
and which were already ACCEPT. Then they generate the revised shots and run
`visual-asset-critic` again.

### Determinism, and its limits

Given the same `shots.json`, the same brand-lock, and the same critique, this should
produce the same revised prompt. Nothing in the file format fights that any more: no
wall-clock stamps, no random ordering.

What the format cannot guarantee is the judgement in between. Applying a `fix` field means
reading a sentence of English and editing prose, so hold yourself to the narrowest edit
that satisfies the fix and leave every other layer byte-identical. If you find yourself
rewriting a prompt the critique did not ask you to touch, stop: that is drift, and it will
read as a mystery six shots later.

## Hard rules

These are non-negotiable. Violating them produces broken output even if the prompt looks fine.

### Rule 1. Text is never in the prompt

If the shot has `on_screen_text: "text_03"`, the prompt does NOT contain the text content. Text is composited separately. The only exception: Ideogram, where text-in-image is the reason you'd choose it, but even then, treat it as an explicit override flagged in rationale.

### Rule 2. Brand colors never in shot subject prose

Colors come from the series_lock color_grade and the brand_lock palette. They get rendered into the prompt by the adapter. Don't write "deep navy blazer" in the shot subject if "deep navy" is already in the palette, that's a duplicated description and produces oversaturation.

### Rule 3. Series_lock anchors are verbatim

The series_lock environment / lighting / character strings flow into every prompt **verbatim**. This is what produces visual consistency across shots. If you paraphrase or vary, shots stop matching each other.

### Rule 4. Adapters are the source of truth on syntax

If your training data says Midjourney uses `--style 4a` and the adapter file says `--style raw`, the adapter wins. Image-gen syntax changes monthly. The adapter is current; your training is not.

### Rule 5. Prompts must be reproducible

Every prompt is composed from the same inputs the same way. If two consecutive runs produce different prompts for the same shot, the skill is broken. Determinism is the whole point.

## Reference files

- `references/prompt-anatomy.md`, the five-layer model in depth
- `references/consistency-locks.md`, how series_lock prevents shot drift
- `references/failure-modes.md`, common image-gen failures and their prompt-side fixes

## Adapters

One file per generator. Read these on demand, only for the generators being targeted.

| File | Generator | Strength |
|---|---|---|
| `adapters/midjourney.md` | Midjourney v7+ | Aesthetic, cinematic |
| `adapters/flux.md` | Flux 2 / Flux 1.1 Pro | Photorealism |
| `adapters/ideogram.md` | Ideogram v3 | Text in image (override only) |
| `adapters/gpt-image.md` | GPT Image 1.5 / 2 | Prompt accuracy, spatial reasoning |
| `adapters/nano-banana.md` | Gemini 2.5 Flash Image | Edit fidelity, inpainting |
| `adapters/seedream.md` | Seedream 4.5 | High-volume, cost-efficient |
| `adapters/kling.md` | Kling 3.0 | Motion video, default (best camera motion per dollar) |
| `adapters/veo.md` | Veo 3 | Motion video, dialogue/lipsync + native audio |
| `adapters/seedance.md` | Seedance 2.0 | Motion video, multi-shot sequences |
| `adapters/hailuo.md` | Hailuo 02 Pro | Motion video, budget iteration |

## Quality bar

Before declaring done, verify:

- [ ] One output file per requested generator, under `output/prompts/round-{N}/`
- [ ] On a full pass, every shot in shots.json appears in every output file. On a revision
      pass, only the revised shots appear, and the rest are accounted for as ACCEPT,
      post-only, or rejected
- [ ] No on-screen text content appears in any image prompt (except Ideogram-with-override)
- [ ] Series_lock strings appear verbatim in every prompt
- [ ] Aspect ratio matches `project.aspect`, sent under the `aspect_param` named in
      `_capabilities.json`
- [ ] No prompt exceeds its generator's `max_prompt_words`
- [ ] Header comment block at the top of each file, naming the run and round
- [ ] The round is appended to `run.json` with a hash per prompt file

Then confirm the files are readable by the tool that consumes them:

```bash
python tools/copy-prompt.py output/prompts/round-1/flux.txt --list
```

## Examples

`examples/one-shot-all-adapters/` contains a single shot rendered across seven adapters
side-by-side: the six stills generators plus Kling. Use it to calibrate output quality.
The three remaining motion adapters (Veo, Seedance, Hailuo) have no worked example yet;
their `.md` files carry a worked prompt each in the meantime.

For a complete two-round output tree, prompts and frames and critiques together, see
`../visual-asset-critic/examples/worked-run/`.
