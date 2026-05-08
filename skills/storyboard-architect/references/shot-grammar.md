# Shot Grammar

Controlled vocabulary. Use these exact terms in `shots.json`. Generators interpret loose language inconsistently, locked vocabulary survives translation.

## Framing (subject size in frame)

| Code | Name | What it shows |
|---|---|---|
| `ECU` | Extreme close-up | Eyes, hands, single detail |
| `CU` | Close-up | Head, or full hand-on-object |
| `MCU` | Medium close-up | Head and shoulders |
| `MS` | Medium shot | Waist up |
| `MLS` | Medium long shot | Full body, environment minimal |
| `WS` | Wide shot | Full body, environment present |
| `EWS` | Extreme wide shot | Subject small in environment |

Default to MCU and MS for talking-head founder content. ECU and CU for product detail and emotion. WS and EWS for context-setting.

## Angle (camera vertical position)

| Code | Effect |
|---|---|
| `eye-level` | Neutral, default |
| `high` | Subject feels smaller, vulnerable |
| `low` | Subject feels powerful, dominant |
| `overhead` | Detached, schematic, instructional |
| `dutch` | Tilted, tension, unease |

Default to eye-level. Use the others deliberately, not for variety.

## Motion (camera movement)

| Code | Effect | Use when |
|---|---|---|
| `static` | No movement | Default. Static is not boring. |
| `push` | Camera moves toward subject | Building intensity, revealing |
| `pull` | Camera moves away | Releasing, contextualizing |
| `pan-left` / `pan-right` | Camera rotates horizontally | Surveying environment |
| `tilt-up` / `tilt-down` | Camera rotates vertically | Reveal scale or detail |
| `handheld` | Subtle organic shake | Documentary feel, urgency |
| `orbit` | Camera circles subject | Hero shots, product reveal |
| `whip` | Fast pan as transition | Beat-cuts in fast-paced content |

For AI-generated still frames, motion is mostly intent for the editor. For Runway/Sora prompts, motion translates directly.

## Depth of field

| Code | Effect |
|---|---|
| `shallow` | Subject sharp, background blurred |
| `deep` | Everything in focus |
| `rack` | Focus shifts mid-shot |

Default to shallow for talking-head, deep for environmental and schematic.

## Lighting style (referenced from series_lock)

Don't redefine per shot. Define once in `series_lock.lighting`. Examples:

- `soft natural side-light, large window left, warm afternoon`
- `hard top-light, single source, deep shadows, studio black`
- `practical mixed sources, neon accents, urban night`

The series_lock string flows into every prompt automatically.

## Subject description

Structured, not poetic. Pattern:

```
[who/what], [doing what], [emotional or compositional note]
```

Good:
```
"Founder, mid-thirties, leaning forward at laptop, face partially turned to window light"
```

Bad:
```
"A determined entrepreneur conquering the digital frontier with passion"
```

Generators reward precision. Adjectives describing emotion ("determined", "passionate") produce stock-photo aesthetics. Describe what the camera actually sees.

## What goes in `subject` vs `series_lock` vs `brand_lock`

This trips people up. The rule:

- **brand_lock**, locked across the entire project. Palette, type, "never" list.
- **series_lock**, locked across this storyboard. Character anchor, environment, lighting style, color grade.
- **subject (per shot)**, what's different about *this* shot. Action, expression, framing-specific composition notes.

If you find yourself repeating the same lighting description across shots, it belongs in series_lock. If you find yourself repeating the same color description across storyboards, it belongs in brand_lock.
