# Adapter: Kling 3.0 (motion-aware video)

> Capability data (length ceiling, text/motion support, aspect param) is canonical in `_capabilities.json`. This file is the how-to-prompt guidance. `max_prompt_words` there is a ceiling; the range below is the recommended target and has to sit inside it. Where a fact here and a fact in the JSON disagree, the JSON wins, and `tools/validate_capabilities.py` fails the build instead of letting the two drift.

Kling 3.0 generates short video clips, not still frames. It is the default motion model: the best camera-motion realism per dollar on fal.ai, and the strongest image-to-video of the four. Reach for it first. Escalate to Veo (dialogue/lipsync), Seedance (multi-shot), or Hailuo (cheap iteration) only when the shot needs what Kling does not do.

With video the **camera motion becomes load-bearing** instead of optional. The same shot generates differently when `motion` is `static` versus `push` versus `handheld`. Use this adapter when the storyboard is destined for video generation rather than still-frame compositing.

## Syntax pattern

```
{Camera motion sentence, explicit, leading.} {Subject and action over the duration.} {Environment and lighting from series_lock.} {Photographic spec.} {Color grade and mood from brand_lock.}
```

Camera motion goes **first**. This is the inverse of image generators where camera is implied. With video the camera's behaviour is the first thing the model must understand.

## Parameters

| Parameter | Default | Notes |
|---|---|---|
| `duration` | `5s` for shots, `10s` for hero | 5s and 10s are the supported lengths |
| `aspect_ratio` | from `project.aspect` | |
| `cfg_scale` | `0.5` | Lower = looser/more dynamic, higher = closer to prompt |
| `start_image` | optional | Image-to-video. Pass an accepted still from `shots.json` assets to lock the opening frame |
| `tail_image` | optional | End-frame target for controlled moves |
| `negative_prompt` | per series | Supported. Use to suppress drift, e.g. `extra fingers, warped face` |

Document parameters as a comment line above each prompt:

```
# shot_01. Kling 3.0: duration=5s, ar=9:16, cfg=0.5, start_image=frames/round-1/shot_01.png
{prompt}
```

## Length

Kling handles **80–150 words** comfortably. Motion description adds a beat over a still prompt; do not pad past it.

## Motion vocabulary

The shot grammar `motion` field maps directly. One move per shot.

| `motion` | Video prompt phrase |
|---|---|
| `static` | "Static camera, locked off." |
| `push` | "Camera dollies forward slowly at a steady pace." |
| `pull` | "Camera dollies backward, pulling away from the subject." |
| `pan-left` / `pan-right` | "Camera pans smoothly to the left / right." |
| `tilt-up` / `tilt-down` | "Camera tilts upward / downward." |
| `handheld` | "Handheld camera, subtle organic movement, documentary feel." |
| `orbit` | "Camera orbits the subject in a slow circle." |
| `whip` | "Fast whip pan with motion blur." |
| `rack` | "Rack focus shifts from foreground to background mid-shot." |

## Subject motion

Beyond the camera, describe what the subject does over the duration:

> "Over the course of the shot the founder leans slightly forward and turns his face toward the window light off-camera left."

Static composition is not enough for video. This is what separates a video prompt from an image prompt.

## Example

**Same shot data as the image-adapter examples, with `motion = "push"`.**

```
Camera dollies forward slowly into the scene at a steady pace. A founder in his mid-thirties with salt-and-pepper hair, wearing a navy crewneck, sits at his laptop in a minimalist home office; over the shot he leans slightly forward and his face turns toward window light off-camera left, holding negative space on the right of frame throughout. Soft natural side-light from a large window, warm afternoon golden hour. Shot on a 50mm prime equivalent, shallow depth of field. Warm filmic color grade with muted teal shadows. Calm, considered, operator mood.
```

## Continuity across shots

- Use `start_image` from the previous shot's accepted final frame to chain a sequence.
- Repeat the series_lock character anchor verbatim in every prompt.
- Do not flip lighting direction between consecutive shots (window-left stays window-left).
- Even with start-frame locking, each clip is a fresh generation. Plan for an editorial pass.

## Pitfalls to avoid

- **Don't put camera motion at the end.** Kling parses motion best as the leading instruction.
- **Don't request multiple camera moves in one shot.** Pick one; compound moves break.
- **Don't describe motion faster than the duration allows.** A slow dolly over 5s is plausible; over 1s it is jitter.
- **Don't include text content.** Video text rendering is unreliable; composite or animate text in post.
- **Don't expect frame-perfect character match between clips.** Budget editorial cleanup.

## Output handoff

Generated clips are raw material, not deliverable. After generation they still need: editorial assembly to storyboard timing, text-overlay compositing from `text-overlays.json`, a color-grade pass, and audio (VO, music, sound design). Say this in handoff.
