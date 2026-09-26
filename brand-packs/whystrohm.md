# Brand Lock: WhyStrohm

## Identity

**Brand:** WhyStrohm
**One-line description:** A media studio for founder-led companies. WhyStrohm researches the market, builds the site at the center of it, and keeps the media around it moving.
**Archetype:** Operator
**Voice posture:** Calm, considered, confident without shouting

## Palette

The ground is dark and the ink is warm off-white. The site and the install film set the ink
steps as alpha over the ground. The tools need flat hex, so each step below is that alpha
composited over the ground.

| Role | Hex | Use |
|---|---|---|
| Background | `#07080A` | Ground, the canvas under everything |
| Ink | `#F6F5F2` | Headlines and primary text |
| Accent (Signal) | `#E4552A` | One word per step, plus live states. Never a fill or a flood |
| Ink secondary | `#B3B3B1` | Support lines. Ink at 0.72 over the ground |
| Muted | `#757575` | Eyebrows, captions, labels. Ink at 0.46 over the ground |
| Ink faint | `#2D2E2F` | The grid, inactive states. Ink at 0.16 over the ground |
| Rule | `#242426` | Borders and dividers. Ink at 0.12 over the ground |

## Typography

**Display font:** `Archivo Bold 700 wdth 80`, headlines, tracking -0.022em, line height 1.04
**Body font:** `Archivo Medium 500 wdth 104`, support lines and UI body, line height 1.3
**Mono font:** `IBM Plex Mono Regular 400`, eyebrows, labels, numbers, uppercase with 0.18em tracking

Archivo is one variable family used on its width axis: narrow and heavy for headlines, wide
and lighter for support lines. IBM Plex Mono carries every eyebrow, label and number.
Eyebrows read as `01 / The brief`.

## Mood adjectives

- operator (not creator)
- considered (not reactive)
- shown (not described)
- one object (not a montage)
- confident (without volume)

## Never list

- never a light or cream ground; the ground is `#07080A`
- never use Signal `#E4552A` as a fill or a flood; one word per step, plus live states
- never more than one accent color
- never bounce, wobble or overshoot; two easings only
- never let text ride on a moving object; text appears once its object has landed
- never show an empty frame or a dead hold
- never put labels on tilted 3D planes; they go in a flat legend
- never use stock photo aesthetic
- never use AI uncanny faces
- never use clip-art or generic icon sets
- never use em dashes, emojis, or exclamation points in headlines
- never use hype words ("game-changing", "revolutionary", "next-level", "comprehensive")
- never show a number, price, client name or client count that is not true and on screen

## Aspect ratios

- 16:9, primary, films and web embeds (1920x1080)
- 9:16, short-form social
- 4:5, feed
- 1:1, feed posts and covers

## Color grade direction

Dark ground `#07080A` with a faint 80px grid that drifts slowly, a radial vignette, and film grain as fractal noise at 6 percent overlay. Highlights sit in the warm off-white of the ink, never pure white. Footage runs graded low and defocused behind type, so the copy always reads. Signal orange appears only on the one accent word or a live state.

## Motion language

One object carries the whole film, and each step turns it into the next thing. There are no cuts between unrelated shots. A morph moves one rectangle into the next (position, size, corner radius) over 40 to 52 frames, and the next step's copy arrives while the morph is still moving, so no frame is empty. Two easings only: enter `cubic-bezier(0.16, 1, 0.3, 1)`, morph `cubic-bezier(0.65, 0, 0.35, 1)`. Nothing bounces. Headline words rise in one at a time, 4 frames apart, with a short de-blur, then fade out. The camera makes one slow push across the whole film, from scale 1 to 1.035, with copy held outside the push. Diagrams draw on, and nodes fade in with a stagger. A still gives way to live footage at the moment its step completes.

## Voice rules

- a setup line, then a payoff line
- short plain sentences
- one accent word per step, set in Signal
- every step is shown happening, never only described; if a line says "checked", something on screen gets checked
- no em dashes
- no emojis
- no exclamation points in headlines
- no hype words ("game-changing", "revolutionary", "comprehensive", "next-level", "leverage")
- no qualifiers in declarative copy ("perhaps", "maybe", "kind of")
- no invented numbers, prices, client names or client counts; any count on screen is the count of things on screen
- prefer present tense over future tense
- prefer "operator" over "creator", "system" over "service"

## Reference materials

- Site: https://whystrohm.com
- The install film on the site's homepage is the style reference for motion and type

---

**Last updated:** 2026-09-26
**Owner:** Yuri Strohm
**Version:** 2.0 (2026-09-26: dark ground `#07080A`, ink `#F6F5F2`, Signal `#E4552A`, Archivo on its width axis and IBM Plex Mono. Replaces 1.0: cream ground, coral accent, Inter and JetBrains Mono.)
