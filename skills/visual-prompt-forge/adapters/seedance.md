# Adapter: Seedance 2.0 (motion-aware video, multi-shot)

> Capability data (length ceiling, text/motion support, aspect param) is canonical in `_capabilities.json`. This file is the how-to-prompt guidance. `max_prompt_words` there is a ceiling; the range below is the recommended target and has to sit inside it. Where a fact here and a fact in the JSON disagree, the JSON wins, and `tools/validate_capabilities.py` fails the build instead of letting the two drift.

Seedance 2.0 is the multi-shot model. It can generate a **short sequence of cuts in a single generation** while holding subject and environment consistency across them. Reach for it when several consecutive storyboard beats share one subject and you want them to feel like one continuous take, it beats stitching four independent Kling clips that drift apart. For a single isolated shot, Kling is the simpler default.

With video the **camera motion is load-bearing**, and with Seedance the **cut structure is also load-bearing**, you describe the sequence of shots, not just one frame.

## Syntax pattern

Single shot:
```
{Camera motion sentence, leading.} {Subject and action.} {Environment and lighting from series_lock.} {Color grade and mood from brand_lock.}
```

Multi-shot sequence (Seedance's strength):
```
Shot 1: {camera + action}. Shot 2: {camera + action}. Shot 3: {camera + action}. Consistent subject throughout: {series_lock character anchor, verbatim}. {Environment and lighting from series_lock.} {Color grade and mood from brand_lock.}
```

## Parameters

| Parameter | Default | Notes |
|---|---|---|
| `duration` | `5s` per shot block | Multi-shot sequences run longer; check the current fal.ai ceiling |
| `aspect_ratio` | from `project.aspect` | |
| `start_image` | optional | Image-to-video reference for the opening frame |
| `shots` | 1 | Number of cuts in the sequence when using multi-shot mode |

```
# shot_02-shot_04. Seedance 2.0: ar=9:16, shots=3, multi-shot sequence
{prompt}
```

## Length

Seedance handles **80–150 words**. In multi-shot mode, keep each shot clause short, one camera move and one action per cut.

## When to use multi-shot vs single

| Situation | Mode |
|---|---|
| One beat, one frame | Single shot (or use Kling) |
| 2–4 consecutive beats, same subject, want continuity | Multi-shot sequence |
| Beats with different subjects/locations | Separate generations, assemble in edit |

Map consecutive `shots.json` entries that share a subject into one Seedance multi-shot prompt; reference them by id range in the comment.

## Motion vocabulary

The shot grammar `motion` field maps directly. One move per cut.

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

## Example

**Three consecutive beats of the same founder, mapped to one sequence.**

```
Shot 1: static eye-level, the founder closes his laptop and exhales. Shot 2: slow push toward his face as he looks toward the window. Shot 3: handheld over-the-shoulder as he stands and crosses the room. Consistent subject throughout: a founder in his mid-thirties with salt-and-pepper hair, navy crewneck. Minimalist home office, white walls, oak desk, soft natural side-light from a large window on the left, warm afternoon golden hour. Warm filmic color grade with muted teal shadows. Calm, considered, operator mood.
```

## Pitfalls to avoid

- **Don't force unrelated beats into one sequence.** Multi-shot is for shots that genuinely belong to one take.
- **Don't write more than ~4 cuts per generation.** Consistency degrades past that; split and assemble in edit.
- **Don't vary the character anchor between cuts.** Restate it once for the whole sequence, verbatim.
- **Don't include text content.** Composite captions from `text-overlays.json` in post.
- **Don't stack two camera moves inside one cut.** One move per cut.

## Output handoff

Seedance returns a sequence as a single clip (or a small set). It still needs: editorial trimming to exact storyboard timing, text-overlay compositing, a color-grade pass, and audio. Multi-shot output usually needs *less* assembly than stitched single clips, which is the point. Say so in handoff.
