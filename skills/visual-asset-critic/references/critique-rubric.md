# Critique Rubric

The structured layer-by-layer pass. Use this as the checklist when reviewing a generated image.

## Layer 1. Brand Lock check

| Check | Pass | Soft fail | Hard fail |
|---|---|---|---|
| Palette | Image colors come from brand-lock palette | Colors close but slightly off | Colors not in palette at all |
| Mood adjectives | Image reads as the brand mood | Mood reads as adjacent (e.g. "calm" vs "neutral") | Image reads as a different mood (e.g. "energetic" when brief was "calm") |
| "Never" list | None of the items in the never list are present | One item in the never list shows softly | Multiple never-list violations |
| Aspect ratio | Matches `project.aspect` |, | Wrong aspect |

Hard fail on Brand Lock = REJECT or REVISE depending on whether prompt fix exists.

## Layer 2. Series Lock check

| Check | Pass | Soft fail | Hard fail |
|---|---|---|---|
| Character anchor | All described features visible | One minor feature off (e.g. wrong shirt color) | Wrong person (different age/race/build than anchor) |
| Environment | Matches series_lock | Slight environment drift | Different environment entirely |
| Lighting direction | Matches series_lock | Lighting is right but slightly different angle | Lighting from wrong direction (continuity break) |
| Color grade | Matches series_lock | Slight tonal drift | Different color grade |

Hard fail on Series Lock = REJECT (continuity break) or REVISE if specific fix available.

## Layer 3. Shot Spec check

| Check | Pass | Soft fail | Hard fail |
|---|---|---|---|
| Framing | Matches spec (ECU/CU/MS/etc.) | One step off (e.g. MS instead of MCU) | Two+ steps off |
| Angle | Matches spec | Slight angle variation | Wrong angle (low when spec was eye-level) |
| Subject action | Matches `subject` description | Subject doing similar but slightly different action | Subject doing wrong action |
| Depth of field | Matches if specified | Slight DOF variation | Deep when shallow was specified |

Soft fail = post-level fix or accept. Hard fail = revise.

## Layer 4. Composition check

| Check | Pass | Soft fail | Hard fail |
|---|---|---|---|
| Negative space for text | Reserved per spec | Reserved but tight | No reserved space, overlay won't fit |
| Subject placement | Matches rationale | Slightly off (subject in left-third vs right-third) | Subject blocks where text was meant to go |
| Eye-line | Looks where intended | Slight gaze direction off | Looking the wrong way |
| Headroom | Appropriate | Slightly tight or loose | Cropped at hairline / huge headroom |

Composition fails are usually prompt-level fixable. Re-roll with explicit composition language.

## Layer 5. Technical check

| Check | Pass | Soft fail | Hard fail |
|---|---|---|---|
| Hands | Anatomically correct | Slight finger weirdness | Six fingers, fused fingers, wrong joints |
| Eyes | Symmetrical, focused | Slight asymmetry | Wonky eyes, wrong reflections |
| Skin texture | Natural | Slightly plastic | Heavy AI plastic |
| Anatomy | Correct | Minor weirdness | Major anatomy errors |
| Background artifacts | Clean | Minor weirdness | Distorted text, melted objects, impossible geometry |

Technical hard fails are almost always **re-roll required**. The prompt was probably fine; the generator just produced a bad sample. Budget 2–3 re-rolls.

## Layer 6. Continuity check (if previous shots available)

| Check | Pass | Soft fail | Hard fail |
|---|---|---|---|
| Character match | Same person, same look | Slight drift | Clearly different person |
| Lighting continuity | Same direction, time of day | Subtle shift | Direction reversed, time of day jumped |
| Environment continuity | Same space | Slight environment drift | Different space |
| Color grade match | Identical | Subtle shift | Visibly different |

Continuity hard fails break the storyboard. REVISE with verbatim-anchor checks on the prompt.

## Aggregating verdict

Count hard fails across layers:

| Hard fails | Verdict |
|---|---|
| 0 | ACCEPT |
| 1 (with clear prompt fix) | REVISE |
| 1 (Brand Lock or Series Lock with no prompt fix) | REJECT |
| 2 | REVISE if both have prompt fixes; REJECT otherwise |
| 3+ | REJECT |

Soft fails are noted but don't change verdict unless they cluster (3+ soft fails = REVISE).

## Speed bumps to remember

- **Don't critique what wasn't asked**, if the spec didn't call for cinematic mood, don't say "could be more cinematic"
- **Don't pile-on once verdict is set**, if you're rejecting, list the issues that drive the rejection; don't list every cosmetic concern
- **Be specific, always**, "lighting is off" is not a critique; "key light is camera-right but series_lock says camera-left" is
- **Cite the layer**, every issue gets tagged with which layer it falls under. This makes the fix path obvious
- **Distinguish prompt failure from generator failure**, if the prompt was fine and the generator produced garbage hands, that's "re-roll required", not "fix the prompt"
