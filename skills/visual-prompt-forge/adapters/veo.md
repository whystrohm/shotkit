# Adapter: Veo 3 (motion-aware video, native audio)

> Capability data (length ceiling, text/motion support, aspect param) is canonical in `_capabilities.json`. This file is the how-to-prompt guidance. `max_prompt_words` there is a ceiling; the range below is the recommended target and has to sit inside it. Where a fact here and a fact in the JSON disagree, the JSON wins, and `tools/validate_capabilities.py` fails the build instead of letting the two drift.

Veo 3 is the dialogue and lipsync model. It is the only adapter that generates **synchronised native audio**, speech, ambience, and sound effects, in the same pass as the video. It also has the strongest prompt adherence and physical realism of the four motion models. It is the most expensive, so reserve it for shots that actually need spoken dialogue, lipsync, or audio baked in. For silent B-roll and camera moves, Kling is the cheaper default.

With video the **camera motion is load-bearing**. When the shot has dialogue, the **spoken line is also load-bearing** and is written into the prompt (this is the one place where text belongs in a prompt, it is audio, not on-screen text).

## Syntax pattern

```
{Camera motion sentence, leading.} {Subject and action over the duration.} {Dialogue line, in quotes, if any.} {Environment and lighting from series_lock.} {Audio direction.} {Color grade and mood from brand_lock.}
```

## Parameters

| Parameter | Default | Notes |
|---|---|---|
| `duration` | `8s` | Veo's native clip length |
| `aspect_ratio` | from `project.aspect` | |
| `generate_audio` | `true` | The reason to choose Veo. Set `false` only for silent shots |
| `start_image` | optional | Image-to-video from an accepted still |

```
# shot_04. Veo 3: duration=8s, ar=9:16, generate_audio=true
{prompt}
```

## Length

Veo handles **80–150 words**. Spend the headroom on action timing and audio direction, not adjective stacks.

## Dialogue and lipsync

When the shot calls for the subject to speak, put the exact line in quotes:

> The founder looks directly into the lens and says, "I built the system once, and it runs without me."

Keep spoken lines to what fits the duration, roughly 12–18 words for an 8s clip. Direct the delivery ("calm, unhurried"). Veo lipsyncs the quoted line.

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

## Audio direction

Even on silent shots Veo can place ambience. Be explicit and brief:

- "Audio: quiet room tone, faint keyboard, no music."
- "Audio: soft afternoon ambience, distant street."

If the brand-lock or storyboard owns the audio bed (VO recorded separately, music added in post), set `generate_audio=false` and skip this section so Veo does not invent a competing track.

## Example

**Shot with `motion = "static"` and a spoken line.**

```
Static camera, locked off, eye level. A founder in his mid-thirties with salt-and-pepper hair in a navy crewneck sits at his laptop in a minimalist home office and looks directly into the lens. He says, "I built the system once, and it runs without me," calm and unhurried. Soft natural side-light from a large window on the left, warm afternoon golden hour. Audio: quiet room tone, faint keyboard, no music. Warm filmic color grade with muted teal shadows. Calm, considered, operator mood.
```

## Pitfalls to avoid

- **Don't use Veo for silent B-roll.** You are paying for an audio engine you turned off; use Kling.
- **Don't overrun the duration with dialogue.** A line that needs 12s of speech will clip or rush at 8s.
- **Don't put on-screen text in the prompt.** Spoken lines are fine; rendered captions still come from `text-overlays.json` in post.
- **Don't stack two camera moves.** One move per shot.
- **Don't let Veo's auto-audio fight a post audio bed.** Pick one owner of sound per shot.

## Output handoff

Veo clips arrive with audio attached. They still need: editorial assembly to timing, on-screen text compositing from `text-overlays.json`, a color-grade pass, and an audio decision, keep Veo's native track, or mute it and use the storyboard's recorded VO and music. State which in handoff.
