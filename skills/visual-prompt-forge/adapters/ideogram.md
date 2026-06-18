# Adapter: Ideogram (v3)

> Capability data (length limits, text/motion support, aspect param) is canonical in `_capabilities.json`. This file is the how-to-prompt guidance. If a number here and in `_capabilities.json` disagree, the JSON wins.

Ideogram is the only generator that reliably renders text inside images. Use it for cases where text-as-image is the deliverable, posters, branded social tiles, signage, packaging mockups. For everything else, default to Flux or Midjourney and composite text separately.

This adapter has **two modes**: composited (default) and text-in-image (override).

## Mode 1: Composited (default)

Same as Flux, generate the image clean, composite text in post. Use when Ideogram is being chosen for general image quality, not text rendering. Syntax matches Flux conventions.

## Mode 2: Text-in-image (override)

Use when the on-screen text is meant to appear as part of the image itself, a poster headline, a sign in the scene, a packaging label. This is the only case where a generator prompt contains the text content.

**To trigger Mode 2, the shot must have an explicit override flag in rationale**, e.g.:
```
"rationale": "Text-in-image override: poster shot, headline must render as part of composition"
```

If you don't see that override flag, default to Mode 1.

## Syntax pattern (Mode 2)

```
{Subject and composition}. {Environment and lighting}. The text "{exact text}" appears {position description}, in {font style description}. {Brand mood and color closing.}
```

The exact text must be in straight double-quotes. Ideogram parses these as the text-render target.

## Parameters

| Parameter | Where | Default |
|---|---|---|
| `aspect_ratio` | API field | from `project.aspect` |
| `model` | API field | `V_3` |
| `magic_prompt` | API field | `OFF` for series work, kills consistency |
| `style_type` | API field | `DESIGN` for posters, `REALISTIC` for scenes |
| `seed` | API field | set per-storyboard |

Document in comment block:
```
# shot_01, params: ar=9:16, model=V_3, magic_prompt=OFF, style=DESIGN, seed=2840193
{prompt}
```

## Composition pattern (Mode 1, composited)

Same as Flux pattern, no text in prompt:

```
{Framing description with character and action}. {Environment from series_lock}. {Lighting from series_lock}. {Photographic spec}. {Brand mood and color}. Clean composition with negative space for text overlay placement.
```

## Composition pattern (Mode 2, text-in-image)

```
{Subject/composition sentence}. {Environment/lighting sentence}. The text "{exact content}" appears {center / top-third / bottom-third / etc.}, in {font style, bold sans-serif / elegant serif / handwritten script / etc.}, color {hex or named color from brand-lock}. {Brand mood closing}.
```

## Example (Mode 2)

**Shot:** poster-style hero frame, brand launch
**Brand-lock:** display font is `Inter Black`, headline color `#0F1F3A` on `#F5F0E8` cream background
**Text content:** `built different`

**Output prompt:**
```
Editorial poster composition, dense cream background, single bold composition. Minimalist studio environment, even diffused lighting. The text "built different" appears center of the frame, in heavy sans-serif typography (Inter Black style), color deep navy #0F1F3A on cream #F5F0E8 background. Calm, considered, operator brand mood, confident without shouting.
```

## When NOT to use Ideogram

- **Photorealistic scenes with people**. Flux is better
- **Cinematic mood/aesthetic**. Midjourney is better
- **Product photography**. Flux 2 Pro is better
- **Series work where consistency matters**. Midjourney with `--cref` or Flux with seed-locking handles consistency better

Ideogram's specialty is text. If the brief doesn't need text-in-image, picking Ideogram is choosing the wrong tool.

## Pitfalls to avoid

- **Don't use Mode 2 without the rationale override**, defaults to text-in-image cause double-text (composited + generated) which destroys the comp
- **Don't trust magic_prompt**, it auto-rewrites and produces inconsistent shots across a series
- **Don't pile multiple text elements in one prompt**. Ideogram handles one text element well, two becomes lottery, three is broken
- **Don't use cursive/decorative fonts**, even Ideogram fails on these. Sans-serif and clean serif are reliable
- **Don't forget seed**, for any series work, lock the seed at the storyboard level
