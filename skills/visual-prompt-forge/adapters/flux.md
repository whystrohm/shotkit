# Adapter: Flux (Flux 2 Pro / Flux 1.1 Pro / Flux Dev)

Flux rewards natural-language prompts that read like a competent photographer briefing themselves. It interprets full sentences accurately and handles spatial relationships better than Midjourney. It's the photorealism leader as of Q2 2026, choose Flux over Midjourney when the brief calls for "looks like a real photograph" rather than "looks designed."

## Syntax pattern

```
{One or two natural-language sentences describing the subject and action}. {Sentence describing environment and lighting}. {Sentence describing technical/photographic specs}. {Brand mood line.}
```

Periods separate beats. Each sentence does one job. No bracket weights, no `--` flags. Flux is parameterless on most APIs (fal.ai, Replicate, BFL direct).

## Where parameters go

Flux parameters are typically passed alongside the prompt, not inside it:

| Parameter | Where | Default |
|---|---|---|
| `aspect_ratio` | API call field | from `project.aspect` |
| `output_format` | API call field | `png` for compositing |
| `safety_tolerance` | API call field | `2` (default) |
| `prompt_upsampling` | API call field | `false` for series work, auto-rewrites kill consistency |
| `seed` | API call field | set per-storyboard for series consistency |

In the `flux.txt` output, document parameters as a comment line above each prompt:

```
# shot_01, params: ar=9:16, seed=2840193, upsampling=false
{prompt}
```

## Length

Flux handles **80–150 words** comfortably. Don't pad, but you have headroom Midjourney doesn't.

## Composition mapping

Translate shot grammar into descriptive language:

| shot_grammar | Flux phrasing |
|---|---|
| `MCU eye-level` | `Medium close-up framing, camera at eye level.` |
| `WS overhead` | `Wide overhead shot, looking straight down.` |
| `push` | `Camera pushing slowly toward the subject.` |
| `handheld` | `Handheld camera with slight natural movement.` |
| `shallow DOF` | `Shot at f/1.8 with shallow depth of field, background softly out of focus.` |
| `deep DOF` | `Shot at f/8, everything in sharp focus front to back.` |

## Photographic specifics

Flux rewards camera/lens vocabulary. Add when relevant:

- `Shot on Hasselblad, 80mm lens, f/2.8`
- `Sony FX6, 35mm prime, natural light only`
- `Documentary 16mm film aesthetic, slight grain`
- `Editorial fashion lighting, large softbox key`

## Composition pattern

```
{Framing description with character anchor and action}. {Environment description from series_lock}. {Lighting sentence from series_lock}. {Photographic spec, camera, lens, depth of field}. {Color grade and mood from brand_lock}. Photorealistic, natural skin texture, no AI artifacts.
```

The closing "Photorealistic, natural skin texture, no AI artifacts" line meaningfully reduces the AI-look in Flux output. Include in every prompt.

## Example

**Same shot data as Midjourney example.**

**Output prompt:**
```
Medium shot of a founder in his mid-thirties with salt-and-pepper hair, wearing a navy crewneck, leaning forward at his laptop with his face partially turned toward window light. Composition leaves negative space on the right side of the frame. The setting is a minimalist home office with white walls and an oak desk. Soft natural side-light from a large window on the left, warm afternoon golden hour. Shot on a 50mm prime at f/2.0, shallow depth of field. Warm filmic color grade with muted teal shadows. Calm, considered mood, operator, not creator. Photorealistic, natural skin texture, no AI artifacts.
```

## Flux variant selection

| Variant | When | Cost ratio |
|---|---|---|
| Flux 2 Pro | Hero shots, final assets | 1× (highest) |
| Flux 1.1 Pro | Series work, balanced | ~0.6× |
| Flux Schnell | Quick iteration, drafts | ~0.1× |
| Flux Dev | Self-hosted, scale | ~0× per image, GPU cost |

Default to Flux 2 Pro for storyboard previews. The `flux.txt` file works for any variant, same prompt syntax.

## Pitfalls to avoid

- **Don't write "highly detailed, 4k, masterpiece"**, these are Stable Diffusion crutches. Flux ignores them and the line burns tokens
- **Don't use weight syntax `(thing:1.4)`**. Flux 2 doesn't support it; Flux 1.1 partially does. Stick to natural language
- **Don't enable prompt upsampling for series work**, fal.ai's auto-rewrite produces inconsistent shots
- **Don't include text content**, even if Flux 2 handles text better than Flux 1.1, composite separately for editability
- **Don't omit the photoreal closing line**, the "no AI artifacts" anchor measurably reduces the AI-look

## API access

Flux has multiple API surfaces:

- **fal.ai**, fastest, most stable, supports all variants
- **Replicate**, broader model selection, slightly slower
- **BFL direct API**, official, requires their key
- **WaveSpeedAI**, unified interface across many models

Same prompt syntax across all four. The `flux.txt` file is portable.
