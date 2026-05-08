# Adapter: Seedream (4.5 / 4.0)

ByteDance's Seedream models are the high-volume cost-efficient choice. Quality is below Flux 2 Pro and Midjourney v7 but above older mid-tier models, and the cost-per-image is roughly 5–10× lower. Choose Seedream when you're producing **many variations or doing rapid concept iteration**, not for hero/final assets.

For storyboard work, Seedream is useful for the storyboard preview pass: render every shot quickly to validate composition before committing to higher-cost generation for finals.

## Syntax pattern

Seedream rewards **short, precise prompts**. Long descriptive prompts underperform, the model interprets them as competing weights and produces mush. Closer to Midjourney's style than Flux's.

```
{Subject phrase}, {action}, {environment}, {lighting}, {mood/style}, {aspect note}
```

Comma-separated, no full sentences.

## Parameters

Seedream is API-driven through fal.ai, Replicate, or BytePlus direct:

| Parameter | Default | Notes |
|---|---|---|
| `aspect_ratio` | from `project.aspect` | |
| `seed` | per-storyboard | Critical for series consistency |
| `guidance_scale` | `4.5` | Lower = more creative, higher = more literal |
| `steps` | `28` | Default. Increase to 50 for higher quality at cost |

Document:
```
# shot_01, params: ar=9:16, seed=2840193, guidance=4.5, steps=28
{prompt}
```

## Length

**40–70 words per prompt**. Shorter than most. Don't pad.

## Composition pattern

```
{Framing} of {character anchor}, {action}, {environment from series_lock}, {lighting from series_lock}, {color grade from brand_lock}, {one mood adjective}, photorealistic
```

## Example

**Same shot data as previous examples.**

**Output prompt:**
```
Medium shot of founder mid-thirties, salt-and-pepper hair, navy crewneck, leaning forward at laptop, face turned to window light, minimalist home office, oak desk, soft natural side-light from large window, warm afternoon, warm filmic color grade, muted teal shadows, calm operator mood, photorealistic
```

## When Seedream is the right choice

- **Storyboard preview pass**, render all shots quickly at low cost to validate composition before final pass
- **High-volume social content**, when you need 50+ images per day and the quality bar allows it
- **Concept exploration**, quick iteration on shot ideas before committing to a final generator
- **Placeholder content**, assets that will be replaced once the brand-lock is finalized

## When Seedream is the wrong choice

- **Hero shots / final deliverables**. Flux 2 Pro or Midjourney v7 produce noticeably better output
- **Photorealistic product shots**. Flux is meaningfully better for product fidelity
- **Text-heavy designs**. Ideogram or GPT Image
- **Cinematic mood pieces**. Midjourney is the move

## Series consistency

Seedream's character consistency is weaker than Midjourney `--cref` or Ideogram omni-reference. To compensate:

- **Lock the seed** at the storyboard level (same seed across all shots in a series)
- **Verbatim repeat** the character anchor string from series_lock in every prompt
- **Don't vary** the lighting language between shots, series_lock string in, no paraphrasing
- **Accept** that some shots will need re-rolls; budget for it

## Pitfalls to avoid

- **Don't write paragraphs**. Seedream wants comma-separated phrases
- **Don't use `--ar` syntax**, pass aspect_ratio as a parameter
- **Don't include text content**, text rendering is poor; composite separately
- **Don't expect Midjourney aesthetic**. Seedream produces clean but less art-directed output
- **Don't skip the seed lock for series work**, without it, character consistency breaks

## API access

- **fal.ai**, `bytedance/seedream-4.5` and `bytedance/seedream-4.0`
- **Replicate**, `bytedance/seedream-4.5`
- **BytePlus**, direct API, requires their account

Same prompt syntax across surfaces.
