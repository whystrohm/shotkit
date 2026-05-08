# Prompt Anatomy: The Five Layers

Every image prompt this skill produces is composed from five layers. Four are inputs, one is applied at compose-time. Understanding the layers is the difference between bulletproof prompts and lottery tickets.

## Layer 1. Brand Lock

**What:** the locked brand parameters for the entire project.
**Source:** `brand-lock.snapshot.md` referenced in `shots.json`.
**Constant across:** every storyboard, every shot.

Contains:

- Palette (hex values)
- Typography (font names, weights)
- Mood descriptors (3–5 adjectives that describe the brand's emotional posture)
- "Never" list (things this brand never does, e.g. "no stock photo aesthetic", "no AI uncanny", "no over-saturated", "no shouting copy")
- Aspect ratios used
- Color grade direction

This layer answers: **what does the brand always look and feel like?**

## Layer 2. Series Lock

**What:** the locked anchors for this specific storyboard.
**Source:** `shots.json` → `series_lock`.
**Constant across:** every shot in this one storyboard.

Contains:

- Character anchor (who's in frame, described identically every shot)
- Environment description (where the action takes place, identical every shot)
- Lighting setup (direction, source, color temperature, identical every shot)
- Color grade (filmic look, identical every shot)

This layer answers: **what stays the same across this storyboard?**

The series_lock is what makes shot 1 and shot 7 feel like the same piece. Without it, every generated frame looks like a different production.

## Layer 3. Shot Spec

**What:** the per-shot variables.
**Source:** `shots.json` → `shots[i]`.
**Variable across:** every shot.

Contains:

- Framing (ECU, CU, MS, etc.)
- Angle (eye-level, high, low, etc.)
- Motion (static, push, pull, etc.)
- Subject (what's happening in this specific shot)
- Depth of field
- Rationale (audit trail, why this shot, this beat, this moment)

This layer answers: **what's different about this specific shot?**

## Layer 4. Text Layer

**What:** on-screen text composited after generation.
**Source:** `text-overlays.json`.
**Never appears in image prompts** (except Ideogram Mode 2 with explicit override).

Why text is a separate layer:

1. **Editability.** Composited text can be revised without re-generating images.
2. **Quality.** Even Ideogram and GPT Image (the best at text) produce typography that lags professional design tools.
3. **Animation.** Animated text needs After Effects / Remotion / CapCut. Static rendered text is dead-on-arrival for motion content.
4. **Brand control.** Composited text uses exact brand fonts and exact brand colors. Generated text approximates.

## Layer 5. Generator Adapter

**What:** model-specific syntax wrapper.
**Source:** the relevant `adapters/{generator}.md` file.
**Variable across:** every target generator.

This is the only layer the skill *applies* (vs. reads). Layers 1–4 are inputs; Layer 5 is the renderer that turns inputs into a generator-specific string.

The adapter handles:

- Word order (Midjourney leads with subject; Runway leads with camera motion)
- Length conventions (Seedream short, GPT Image long)
- Parameter syntax (`--ar 9:16` vs `aspect_ratio: "9:16"`)
- Idiosyncratic strengths (Ideogram for text, Flux for photoreal, etc.)

## How layers compose

For a single shot's prompt:

```
Layer 1 (brand) ───┐
                   │
Layer 2 (series) ──┼──> Layer 5 (adapter) ──> {generator-specific prompt}
                   │
Layer 3 (shot) ────┘

Layer 4 (text) ────> separate compositing pipeline
```

The adapter pulls from Layers 1–3 and produces a string. Layer 4 lives parallel and never enters the prompt.

## Why this matters operationally

**Change the brand color** → edit brand-lock.md. Every prompt across every storyboard updates. No find-and-replace across files.

**Change the character** → edit series_lock in shots.json. Every shot in this storyboard updates. Other storyboards untouched.

**Change one shot** → edit just that shot's spec. Other shots unaffected.

**Change the generator** → swap adapters. Same shot data, different output file. Zero edits to brand-lock or series_lock.

**Audit a render** → check brand-lock.snapshot.md to see what version the storyboard was built against.

This is why guardrails-in-code beat guardrails-in-vibes. Each layer has one job. Changes are surgical. Outputs are reproducible.
