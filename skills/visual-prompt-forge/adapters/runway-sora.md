# Adapter: Runway / Sora (motion-aware video)

Runway Gen-4 and OpenAI Sora generate short video clips, not still frames. The prompt anatomy is similar to image generators but **motion description becomes load-bearing** instead of optional. The same shot generates differently when "motion" is "static" versus "push" versus "handheld."

Use this adapter when the storyboard is destined for video generation rather than still-frame compositing.

## Syntax pattern

```
{Camera motion sentence, explicit, leading.} {Subject and action sentence.} {Environment and lighting sentence.} {Style and mood closing.}
```

Camera motion goes **first**. This is the inverse of image generators where camera is implied. With video, the camera's behavior is the first thing the model needs to understand.

## Parameters

Runway and Sora have different parameter surfaces:

### Runway Gen-4

| Parameter | Default | Notes |
|---|---|---|
| `duration` | `5s` for short, `10s` for hero | Max 10s per generation in Gen-4 |
| `aspect_ratio` | from `project.aspect` | |
| `motion_strength` | `5` (1–10 scale) | Lower for subtle moves, higher for dynamic |
| `seed` | per-storyboard | |

### OpenAI Sora

| Parameter | Default | Notes |
|---|---|---|
| `duration` | `5s` (or `10s`, `20s` depending on tier) | |
| `resolution` | `720p` for drafts, `1080p` for finals | |
| `aspect_ratio` | from `project.aspect` | |

Document:
```
# shot_01. Runway: duration=5s, ar=9:16, motion=4, seed=2840193
# shot_01. Sora: duration=5s, ar=9:16, resolution=1080p
{prompt}
```

Output one combined `runway-sora.txt` with both parameter blocks per shot.

## Length

**80–150 words per prompt**. Slightly longer than image generators because motion description adds a beat.

## Motion vocabulary

The shot grammar's motion field maps directly:

| shot_grammar.motion | Video prompt phrase |
|---|---|
| `static` | "Static camera, locked off." |
| `push` | "Camera dollies forward into the scene at a slow, steady pace." |
| `pull` | "Camera dollies backward, pulling away from the subject." |
| `pan-left` | "Camera pans smoothly to the left." |
| `pan-right` | "Camera pans smoothly to the right." |
| `tilt-up` | "Camera tilts upward, revealing more of the scene above." |
| `tilt-down` | "Camera tilts downward." |
| `handheld` | "Handheld camera with subtle organic movement, documentary feel." |
| `orbit` | "Camera orbits around the subject in a slow circle." |
| `whip` | "Fast whip pan, motion blur." |
| `rack` | "Rack focus shifts from foreground to background mid-shot." |

## Subject motion

Beyond camera, describe what the subject does over the duration:

- "The founder begins by looking at the laptop, then slowly turns his head toward the camera over the course of the shot."
- "The product rests on the surface for the first second, then the hand enters frame and lifts it."
- "The text reveals letter by letter from left to right."

This is what differentiates video prompts from image prompts. Static composition isn't enough.

## Composition pattern

```
{Camera motion sentence, first.} {Subject and action over duration sentence.} {Environment and lighting from series_lock.} {Photographic spec, lens, depth of field.} {Color grade and mood from brand_lock.}
```

## Example

**Same shot data as previous examples, with motion = "push".**

**Output prompt:**
```
Camera dollies forward slowly into the scene at a steady pace. A founder in his mid-thirties with salt-and-pepper hair, wearing a navy crewneck, sits at his laptop in a minimalist home office. Over the course of the shot, he leans slightly more forward and his face turns gradually toward the window light off-camera left. Composition holds negative space on the right side of the frame throughout. Soft natural side-light from a large window, warm afternoon golden hour. Shot on a 50mm prime equivalent, shallow depth of field. Warm filmic color grade with muted teal shadows. Calm, considered, operator mood.
```

## Continuity across shots

Video shots in a sequence need to feel continuous. Bake this into the prompt:

- Use `seed` consistency where supported
- Repeat the character anchor verbatim
- Match lighting direction across consecutive shots (don't flip from window-left to window-right)
- For Runway, use the "image-to-video" feature with a still from a previous shot as the reference frame

## Pitfalls to avoid

- **Don't put camera motion at the end**, the model parses motion best when it's the leading instruction
- **Don't describe motion that's faster than the duration allows**, a "slow dolly forward" over 5 seconds is plausible; over 1 second is jitter
- **Don't include text content**, video text rendering is unreliable; composite or animate the text in post (After Effects, Remotion, CapCut)
- **Don't request multiple camera moves in one shot**, pick one. Compound moves break.
- **Don't expect frame-perfect character consistency between shots**, even with seed locking, each clip is a fresh generation. Plan for editorial work in post.

## When to use Runway vs Sora

| Use case | Pick |
|---|---|
| Cinematic style, hero shots | Sora |
| B-roll and lifestyle | Runway Gen-4 |
| Image-to-video from existing stills | Runway (better feature) |
| Long-form (>10s clips) | Sora (longer duration tiers) |
| Cost efficiency | Runway |
| Best motion quality | Sora |

## Output handoff

After the video clips are generated, they still need:

1. **Editorial assembly**, cut into the storyboard timing
2. **Text overlay compositing**, from `text-overlays.json`
3. **Color grade pass**, even with brand-lock prompts, video gen output needs grading
4. **Audio**. VO, music, sound design

Mention these to the user in handoff. Generated video is raw material, not deliverable.
