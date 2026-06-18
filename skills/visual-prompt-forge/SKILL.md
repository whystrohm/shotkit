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

For a given `shots.json` and a list of target generators, produce one file per generator:

```
output/prompts/
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

If brand-lock is missing or shots.json doesn't validate against `../storyboard-architect/templates/shots.schema.json`, stop and tell the user. Don't try to forge prompts from incomplete data.

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

**`adapters/_capabilities.json` is the single source of truth for per-generator limits** (`max_prompt_words`, `supports_text_render`, `supports_motion`, `aspect_param`, and so on). Read it once at the start and respect those values when composing, do not exceed a generator's `max_prompt_words`, and do not target motion on a stills-only generator. Where a number in an adapter `.md` and in `_capabilities.json` disagree, **the JSON wins**; the `.md` files are how-to-prompt guidance, the JSON owns the numbers.

### Step 3. Compose per shot

For each shot in `shots.json`, for each target generator:

1. Pull brand-lock palette, mood, "never" list
2. Pull series_lock character/environment/lighting
3. Pull shot framing/angle/motion/subject
4. **Strip any on_screen_text reference**, text never goes in the prompt
5. Apply the generator adapter's syntax wrapper
6. Append generator-specific parameters (aspect ratio, style flags, seed if applicable)

### Step 4. Write output files

One file per generator. Format:

```
# Storyboard: {project title}
# Generator: midjourney
# Aspect: 9:16
# Brand-lock: brand-lock.snapshot.md
# Generated: {timestamp}

# shot_01, hook, 0.0-2.0s. MCU eye-level static
{the prompt}

# shot_02, pain, 2.0-6.0s. MS eye-level push
{the prompt}

...
```

The `#` lines are comments; the user copies just the prompt body. The header gives them context if they paste the file into a script.

### Step 5. Hand off

Tell the user where the files are. Offer the next step:

> "Want me to QA the generated images against the storyboard? Use `visual-asset-critic` once you have the renders."

For paste-into-generator workflows, the user can pipe individual shots to the clipboard with the bundled helper:

```bash
python tools/copy-prompt.py output/prompts/midjourney.txt
```

This is optional. The `.txt` files are also directly readable, and the user can copy any block by hand. The helper exists for the case where the operator is bouncing between the terminal and a generator UI repeatedly.

## Revision mode (closing the QA loop)

This is what `visual-asset-critic`'s structured output is for. When the user hands you `shots.json` plus one or more `critique.json` files (the machine-readable verdict the critic writes), don't re-forge the whole storyboard, re-emit prompts for **only the shots that failed**, with the fix already applied.

### Trigger

The user says "apply the critique", "revise the failed shots", "re-roll what didn't pass", or hands over `critique.json` alongside `shots.json` and the original prompt files.

### Workflow

1. Read each `critique.json`. Each one is one shot's verdict (`shot_id`, `verdict`, `issues[]`). Skip any with `verdict: ACCEPT`, those are done.
2. For every non-ACCEPT shot, walk its `issues[]` and branch on `fix_type`:
   - **`prompt-level`**, recompose that shot's prompt with the change in `fix` applied (e.g. add the missing series_lock anchor). Re-emit it.
   - **`re-roll`**, keep the prompt identical; the generation was just a bad sample. Re-emit it with a `# re-roll 2-3x, pick the cleanest` note.
   - **`post-level`**, do **not** re-emit. The fix happens in compositing, not in a new generation. Note it in the handoff instead.
3. A shot that has only `post-level` issues needs no new prompt, leave it out of the revised file.
4. Re-apply the five-layer anatomy and the same adapter as the original run. Determinism still holds: same inputs plus the same critique produce the same revised prompt.

### Output

Write `output/prompts/revised-{generator}.txt` containing only the revised shots. Annotate each with what changed and why, citing the issue:

```
# Revision of shot_03 (was REVISE)
# fix [Series Lock, major]: added 'salt-and-pepper hair' to the character anchor (was missing)
# fix [Shot Spec, minor]: medium shot -> medium close-up
{the revised prompt}
```

Tell the user which shots were revised, which need only post work, and which were already ACCEPT. Then they generate the revised shots and run `visual-asset-critic` again, the loop runs until every shot is ACCEPT or the user calls it.

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

- [ ] One output file per requested generator
- [ ] Every shot in shots.json appears in every output file
- [ ] No on-screen text content appears in any image prompt (except Ideogram-with-override)
- [ ] Series_lock strings appear verbatim in every prompt
- [ ] Aspect ratio matches `project.aspect`
- [ ] Generator-specific parameters present (--ar for Midjourney, etc.)
- [ ] Header comment block at top of each file

## Examples

`examples/one-shot-all-adapters/` contains a single shot rendered to all seven adapters side-by-side. Use this to calibrate output quality.
