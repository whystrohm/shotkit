# Adapter: Nano Banana (Gemini 2.5 Flash Image)

> Capability data (length ceiling, text/motion support, aspect param) is canonical in `_capabilities.json`. This file is the how-to-prompt guidance. `max_prompt_words` there is a ceiling; the range below is the recommended target and has to sit inside it. Where a fact here and a fact in the JSON disagree, the JSON wins, and `tools/validate_capabilities.py` fails the build instead of letting the two drift.

Google's Nano Banana model (`gemini-2.5-flash-image`) is the edit-and-iterate champion. Where other generators are best for first-frame creation, Nano Banana excels at variations, inpainting, and reference-based modification. The 2026 production pattern is to generate hero frames in Midjourney or Flux, then use Nano Banana for variants.

For storyboard work, Nano Banana is the right choice when you need **many variations of a single concept** or you're feeding generated images back through for refinement.

## Syntax pattern

Nano Banana takes natural-language prompts plus optional reference images. For text-to-image:

```
{Subject and action}. {Environment and lighting}. {Photographic specs and mood}.
```

For image-to-image (the strength), the prompt describes the modification:

```
{Modification description}. Keep {what to preserve}. Change {what to vary}.
```

## Parameters

Nano Banana goes through the Gemini API:

| Parameter | Default | Notes |
|---|---|---|
| `model` | `gemini-2.5-flash-image` | |
| `aspectRatio` | from `project.aspect` | Native support for `9:16`, `16:9`, `1:1`, `4:5`, `3:4`, `21:9` |
| `numberOfImages` | `1` for series, `4` for variant exploration | |
| `referenceImages` | array of base64 images | Optional |

Document:
```
# shot_01, params: ar=9:16, n=1, ref=none (or list of refs)
{prompt}
```

## Length

Nano Banana handles **60–120 words** efficiently. Shorter than GPT Image, longer than Midjourney.

## Composition pattern (text-to-image)

```
{Framing and subject sentence with character anchor}. {Environment and lighting from series_lock}. {Photographic spec, lens, depth of field, mood}. {Brand color grade closing}.
```

## Composition pattern (image-to-image, the strength)

When refining a hero shot generated elsewhere:

```
Reference: {description of input image}. Modify the image to {specific change}. Preserve the character's {face/clothing/pose}, the {environment elements}, and the lighting direction. Change {specific element} to {target state}.
```

## Example (text-to-image)

**Same shot data as previous examples.**

**Output prompt:**
```
Medium shot of a founder, mid-thirties, salt-and-pepper hair, navy crewneck sweater, leaning forward at his laptop with face turned partially toward window light. Composition leaves negative space on the right side. Minimalist home office, white walls, oak desk. Soft natural side-light from large window left, warm afternoon golden hour. Shot on 50mm prime, f/2.0, shallow depth of field, warm filmic color grade with muted teal shadows. Calm, considered, operator mood.
```

## Example (image-to-image variant)

**Use case:** generated `shot_03` in Flux, want a variant where the founder is looking directly at camera

**Output prompt:**
```
Reference: medium shot of founder at laptop in home office, leaning forward, face partially turned to window. Modify the image so the founder looks directly into the camera lens with a calm, neutral expression. Preserve the character's face, salt-and-pepper hair, navy crewneck, body posture, the home office environment, the desk and laptop, and the warm afternoon side-lighting. Change only the head angle and gaze direction.
```

## Variant-generation workflow

The pattern Nano Banana enables, and the reason it's worth including in storyboard work:

1. Generate hero shot in Midjourney or Flux (one prompt → one image)
2. Feed that image to Nano Banana with variation prompts
3. Get 4–8 variants of the same shot for editorial selection
4. Composite text on the chosen variant

When generating prompts for Nano Banana in `nano-banana.txt`, include both:

- The text-to-image prompt (for first-pass generation)
- A modification template comment showing how to use the result for variants:

```
# shot_01, text-to-image prompt:
{prompt}

# shot_01, variant template (after generating once):
# Reference: [the generated image]. Modify the image to {your change}.
# Preserve {anchors}. Change {target}.
```

## Pitfalls to avoid

- **Don't use Midjourney-style flag syntax**. Nano Banana ignores `--ar`, expects `aspectRatio` parameter
- **Don't expect Midjourney-level aesthetic by default**. Nano Banana is a workhorse, not a stylist. Stack mood adjectives explicitly
- **Don't pile multiple modifications in one image-to-image prompt**, one change per pass produces cleaner results
- **Don't forget the "preserve" clause in image-to-image**, without it, Nano Banana treats the reference as loose inspiration and drifts
- **Don't include text content in image prompts**, composite separately; text rendering is mediocre

## API access

Through Google Gemini API (`gemini-2.5-flash-image` model endpoint). Available via:

- Gemini API direct
- Vertex AI
- Replicate
- fal.ai (under "google/nano-banana")

Same prompt syntax across all four.
