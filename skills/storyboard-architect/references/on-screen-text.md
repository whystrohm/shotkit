# On-Screen Text

Text on screen is a load-bearing decision. Most storyboards over-text. The default should be: **does this shot need text to land?** If the visual carries the meaning, text dilutes.

## When on-screen text earns its keep

1. **Auto-play-mute environments.** Social feeds. Text replaces VO.
2. **Concept compression.** A short phrase lands harder than 4 seconds of narration.
3. **Stat or proof point.** Numbers stick visually in a way they don't audibly.
4. **Beat punctuation.** A single word or phrase that lands on a music hit.
5. **CTA.** The action you want the viewer to take.

## When on-screen text doesn't earn its keep

1. **Restating the VO.** If the voice says it, the text is noise.
2. **Decorative copy.** "Moments matter" floating over b-roll. Cut it.
3. **Brand vibing.** Product names everywhere. Logo lockup in the CTA covers this.
4. **Filler beats.** If the shot doesn't need text, leave it clean.

## Composition rules

These flow into the `position` field of each text overlay.

### Negative-space-aware composition

When a shot has on-screen text, the **shot subject must reserve space for it**. This is enforced at storyboard time, not generation time.

If text is in the right third → subject composition leaves the right third clear.
If text is lower third → subject upper two-thirds.
If text is centered → subject framed to negative space around center.

This goes into the shot's rationale: "MCU left-third subject, reserves right-third for `text_03`."

### Positions

| Position | Use when |
|---|---|
| `center` | Display headline, single concept, hard cut in/out |
| `lower-third` | Caption / VO substitute, persistent across shots |
| `upper-third` | Stat callout, secondary information |
| `left-third` | Subject is right-weighted in frame |
| `right-third` | Subject is left-weighted in frame |
| `{x: %, y: %}` | Custom, only when the standard positions don't fit |

### Sizes

| Size | Pixel approx (1080p) | Use for |
|---|---|---|
| `display` | 96–144 px | Hero/hook beats |
| `headline` | 56–80 px | Reframe beats |
| `body` | 32–48 px | Caption-style, persistent |
| `caption` | 20–28 px | Disclaimers, attribution |

### Animation

Default to clean, not flashy:

- Hook beats → `hard-cut` in, `hard-cut` out (no fade)
- Reframe beats → `fade-in` 0.2s, `fade-out` 0.2s
- Persistent captions → `slide-up` in, `slide-down` out
- CTA → `type-on` for a typewriter effect, or `slide-up`

Avoid stacking animations. Pick one per overlay.

## Color rules

The `color` field of every text overlay must be a hex value that exists in the brand-lock palette. If you find yourself wanting a color that's not in the palette, the answer is not to add it, the answer is to pick a different overlay style or shot composition.

## Typography rules

Same: every `font` field must reference a font defined in brand-lock typography. Two fonts max per project (display + body). More than that and the brand stops being recognizable.

## The "read twice" rule

Already covered in timing-rules.md but worth repeating: text needs to be on screen long enough for someone to read it twice. Calculate, then verify. Don't eyeball.

## Stacking text across shots

Text can persist across consecutive shots. This is useful when:

- The text takes longer to read than a single shot's duration
- You want text to feel anchored while visuals change underneath

To stack, both shots reference the same `on_screen_text` ID. The overlay's `enter.at` aligns to the first shot's start, `exit.at` aligns to the second shot's end.

In `shots.json`:

```json
{ "id": "shot_03", "on_screen_text": "text_02", ... },
{ "id": "shot_04", "on_screen_text": "text_02", ... }
```

In `text-overlays.json`:

```json
{
  "id": "text_02",
  "shot_id": ["shot_03", "shot_04"],
  ...
}
```

Document this in rationale: "text persists across shot 3-4 to give 4.8s read-time for 16-word reframe."

## Type treatment

A line set in one weight and one colour over a photo reads as a caption. These optional
fields in `text-overlays.json` make it read as the brand's own. Use them on purpose and
sparingly: one accent element per frame.

| Field | What it does | Use it when |
|---|---|---|
| `emphasis` | Marks the words that carry the line. Copy them exactly from `content`. | Almost every headline has two or three words doing the work. Mark those, never the whole line. |
| `emphasis_style` | `bar` (default) keeps the words' colour and puts a bar in the accent under them. `color` sets the words in the accent. | `bar` reads over any picture. Use `color` only where the frame behind the type is dark and flat. |
| `kicker` | A small label in spaced capitals above the line, after a short rule in the accent. | To name the brand, the product or the step once, early. A fact from the brief. Never a slogan. |
| `treatment: "lockup"` | Sets a brand or product name as small spaced capitals after a square in the accent. | The sign-off on the last shot. Put it on the same side as the call to action so the two stack. |
| `treatment: "plate"` + `plate` | Sets each line on a solid plate in a palette colour. | The frame behind the type is busy or bright and the subject cannot move. |
| `case: "upper"` | Capitals with wider spacing. | Four words or fewer. |
| `accent` | The colour of the rule, the bar and the lockup mark. | Leave it out. It defaults to the palette's accent. |

### How lines break

Two or three short sentences are set one per line: "New panel. Neat wiring. Permit
handled." becomes three lines. Write to that. A line of two short sentences reads better
than one long one, and the last sentence is usually the one to mark.

### How long a line can be

| Size | Words | Above that |
|---|---|---|
| `display` | 6 | The type shrinks to fit and stops being a headline |
| `headline` | 9 | Same |
| `body` | 16 | Split it across two shots |
| `caption` | 12 | It is a paragraph, and nobody reads a paragraph in a video |

`validate_shots.py` warns past these.

### Where type goes

- Put type where the picture is quiet: a wall, sky, a dark table, out-of-focus ground.
  Say in the shot's `subject` which part of the frame is left clear, so the generator
  and the check both know.
- A side third is a narrow column. Keep lines there to four or five words.
- Never put type over a face, a hand doing the work, or a product.
- Two overlays on the same side stack by themselves. Two on different sides compete:
  one of them should go.

## Safe zones

A vertical video plays inside an app that draws its own buttons over it. On a 9:16 frame
keep type out of:

- the top 12% (account name, search),
- the bottom 21% (caption, sound, progress bar),
- the right 13% (like, comment and share buttons).

The named positions already stay clear: on a vertical frame `upper-third` starts 14%
down, `lower-third` ends 23% up, and both stop short of the right edge. A custom
`{x, y}` position is yours to keep safe, and `validate_shots.py` warns when it is not.

The same applies to the picture. Do not put a face, a product or the hand doing the work
in those bands. Say so in the shot's `subject`: "bag in the centre, clear of the lower
fifth".

On a 16:9 frame keep type inside a 5% margin. The board's **Safe zones** switch draws
both.
