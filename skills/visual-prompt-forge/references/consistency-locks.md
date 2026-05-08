# Consistency Locks

Visual consistency across a storyboard is the hardest problem in AI image generation. Generators are stateless, every prompt is interpreted fresh. Without consistency locks, shot 1 and shot 7 will look like different productions.

This document covers the techniques that actually work in 2026.

## Lock 1. Verbatim character anchors

The most effective single technique. The character is described in `series_lock.character` once, and that exact string appears in every shot's prompt verbatim. No paraphrasing, no synonyms, no "improvement."

**Good (consistent):**
```
shot_01: "founder, mid-thirties, salt-and-pepper hair, navy crewneck, stubble"
shot_02: "founder, mid-thirties, salt-and-pepper hair, navy crewneck, stubble"
shot_07: "founder, mid-thirties, salt-and-pepper hair, navy crewneck, stubble"
```

**Bad (inconsistent):**
```
shot_01: "a thoughtful entrepreneur in his thirties, dark hair, casual sweater"
shot_02: "founder, 35 years old, salt-pepper hair, blue knit top"
shot_07: "the man in the home office, navy shirt"
```

Even small variations compound. Lock the string. Repeat verbatim.

## Lock 2. Verbatim environment anchors

Same principle for `series_lock.environment`. The environment string is identical in every shot prompt. The shot's individual subject describes what changes within the environment, not the environment itself.

## Lock 3. Verbatim lighting anchors

Same principle for `series_lock.lighting`. Lighting direction in particular is critical, flipping window-left to window-right between shots produces obvious cuts where there shouldn't be any.

## Lock 4. Seed locking

For generators that support seeds (Flux, Seedream, Ideogram, Stable Diffusion), set the seed at the storyboard level. Same seed across every shot. This anchors the generator's randomness so character features carry.

In `shots.json`, you can document the seed at the project level:

```json
{
  "project": {
    "title": "...",
    "seed": 2840193
  }
}
```

The adapter reads this and applies to every prompt.

**Caveat:** Midjourney and Sora handle seeds differently (or not at all). Document seed-locking as best-effort, not guaranteed.

## Lock 5. Reference images (`--cref`, omni-reference, image-to-image)

For Midjourney v7, Ideogram v3, and Nano Banana, you can pass a reference image alongside the prompt to anchor character or style.

**Workflow:**

1. Generate the hero shot first (any shot, usually `shot_01` or whichever is most defining)
2. Use that image as the reference for every subsequent shot
3. Each subsequent prompt has the verbatim character anchor PLUS the reference image link

For Midjourney: `--cref {url} --cw 50` (character weight 50 = features only, not clothing).

For Ideogram: `omni-reference` parameter with the image.

For Nano Banana: `referenceImages` array.

**This is the most effective lock for character consistency** in 2026. Use it whenever the storyboard features the same person across multiple shots.

## Lock 6. Style references

When the storyboard has a distinctive visual style (specific film stock, specific lighting school, specific color theory), use a style reference image:

- Midjourney: `--sref {url}`
- Ideogram: style reference parameter
- Flux: not directly supported; bake style language into prompt instead

A consistent style reference across all shots produces aesthetic continuity even when characters or environments shift.

## Lock 7. Lighting direction continuity

A subtle one that breaks scenes when violated. If `series_lock.lighting` says "soft natural side-light, large window LEFT", then every shot's lighting must respect that direction.

When a shot reverses character orientation (e.g., over-the-shoulder reverse), update the rationale to acknowledge the lighting flip:

```
"rationale": "OTS reverse, light source now camera-right (matching scene continuity from window-left in master)"
```

If you find yourself flipping light direction without rationale, you're producing visual jump cuts.

## Lock 8. Color grade flow-through

The `series_lock.color_grade` string flows into every prompt verbatim. Same as character/environment/lighting. If shot 1 is "warm filmic, muted teal shadows" and shot 7 is "cinematic teal and orange", the audience will read it as different scenes.

## Failure modes when locks are missing

| Missing lock | Failure mode |
|---|---|
| Character | Different person every shot |
| Environment | Scene jumps |
| Lighting | Time-of-day jumps, eye-line breaks |
| Seed | Random feature drift |
| Reference image | Loose character interpretation |
| Color grade | Tonal whiplash |

Every one of these is a production problem editorial cannot fully fix. Lock at the prompt level. Save the editor's time.

## What doesn't work

A few things people try that don't actually fix consistency:

- **Adding "consistent character" or "same person" to the prompt**, generators don't read meta-instructions
- **Numbering shots in the prompt** ("shot 3 of 7, same as before"), generators don't have memory across calls
- **Long descriptive paragraphs of the character**, past 4–5 features, the generator starts dropping details randomly
- **Asking for "exactly the same"**, there is no such thing in stateless image gen; you reduce drift, you don't eliminate it

Accept that some shots will need re-rolls. Budget for it. The locks reduce the failure rate; they don't eliminate it.
