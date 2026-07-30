# Adapter: Hailuo 02 Pro (motion-aware video, budget iteration)

> Capability data (length ceiling, text/motion support, aspect param) is canonical in `_capabilities.json`. This file is the how-to-prompt guidance. `max_prompt_words` there is a ceiling; the range below is the recommended target and has to sit inside it. Where a fact here and a fact in the JSON disagree, the JSON wins, and `tools/validate_capabilities.py` fails the build instead of letting the two drift.

Hailuo 02 Pro is the cheap, fast iteration model. Strong motion response and prompt-following for the price, on fal.ai. Use it to **find the shot**, block out camera move, framing, and timing across many quick drafts, then re-generate the keeper on Kling (motion finals), Veo (dialogue), or Seedance (sequences). Treat Hailuo output as a working draft, not a final asset.

With video the **camera motion is load-bearing**. The prompt anatomy matches Kling; the difference is cost and intent: iterate freely here.

## Syntax pattern

```
{Camera motion sentence, leading.} {Subject and action over the duration.} {Environment and lighting from series_lock.} {Color grade and mood from brand_lock.}
```

## Parameters

| Parameter | Default | Notes |
|---|---|---|
| `duration` | `6s` | Check the current fal.ai ceiling for the Pro tier |
| `aspect_ratio` | from `project.aspect` | |
| `start_image` | optional | Image-to-video from an accepted still |
| `prompt_optimizer` | `false` for series | Auto-rewrite helps one-offs but breaks shot-to-shot consistency |

```
# shot_01 (draft). Hailuo 02 Pro: duration=6s, ar=9:16, optimizer=false
{prompt}
```

## Length

Hailuo handles **60–120 words** efficiently. Shorter than Kling/Veo. Keep drafts lean, you are testing motion and framing, not final polish.

## Motion vocabulary

The shot grammar `motion` field maps directly. One move per shot.

| `motion` | Video prompt phrase |
|---|---|
| `static` | "Static camera, locked off." |
| `push` / `pull` | "Camera dollies forward / backward slowly." |
| `pan-left` / `pan-right` | "Camera pans smoothly left / right." |
| `tilt-up` / `tilt-down` | "Camera tilts up / down." |
| `handheld` | "Handheld camera, subtle organic movement." |
| `orbit` | "Camera orbits the subject slowly." |
| `whip` | "Fast whip pan with motion blur." |
| `rack` | "Rack focus from foreground to background." |

## Iteration workflow

1. Draft the shot on Hailuo with `prompt_optimizer=false`. Cheap, fast.
2. Lock the camera move, framing, and timing that read best.
3. Re-generate the keeper on the right final-tier model: **Kling** for motion finals, **Veo** for dialogue/lipsync, **Seedance** for multi-shot sequences.
4. Carry the exact prompt forward, the adapters share the same five-layer anatomy, so the prompt body ports with only parameter changes.

## Example

**Draft of the `motion = "push"` shot.**

```
Camera dollies forward slowly at a steady pace. A founder in his mid-thirties with salt-and-pepper hair in a navy crewneck sits at his laptop in a minimalist home office and leans slightly forward toward window light off-camera left. Soft natural side-light, warm afternoon. Warm filmic color grade, muted teal shadows. Calm operator mood.
```

## Pitfalls to avoid

- **Don't ship Hailuo drafts as finals.** Re-roll the keeper on a final-tier model.
- **Don't enable the prompt optimizer for series work.** Auto-rewrite breaks shot-to-shot consistency.
- **Don't stack two camera moves.** One move per shot.
- **Don't include text content.** Composite captions in post.
- **Don't over-polish the draft prompt.** Spend words on motion and framing; save the photographic detail for the final-tier re-roll.

## Output handoff

Hailuo output is a draft used to choose the shot. The deliverable comes from the final-tier re-roll. If a Hailuo take is genuinely good enough to keep, treat it like any other clip: editorial assembly, text-overlay compositing, color grade, audio.
