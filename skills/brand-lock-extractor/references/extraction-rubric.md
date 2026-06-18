# Extraction rubric

How to read each brand-lock section out of real assets. For every section: where the signal lives, how to read it, and how to assign confidence.

## Confidence levels

Apply one to every value.

- **extracted**, read directly from an asset. A hex in the brand book PDF. A `font-family` in the site CSS. A verbatim quote from the homepage. Ship it plainly.
- **inferred**, reasoned from evidence, not stated. Archetype from how the brand frames problems. Never-list from what the assets consistently avoid. Ship it, note the reasoning.
- **needs confirmation**, a best estimate where assets were silent, compressed, or contradictory. A color sampled from a low-quality JPEG. A font you could not positively identify. Fill it so the file is complete, then flag it in Extraction notes.

## Identity

**Brand:** the name. Extracted from the logo, the title tag, or the description.

**One-line description:** what the brand does and who for. This is the load-bearing sentence; a generator implicitly references it on every prompt. Pull it from the hero headline plus the about page. Prefer concrete over abstract: "Managed bookkeeping for solo law firms" beats "Financial services for professionals." If the site only offers a vague tagline, sharpen it from the services/about copy and flag it `needs confirmation`.

**Archetype:** one word, Operator, Sage, Caregiver, Rebel, Creator, Jester, Ruler, Everyman, etc. Almost always `inferred`. Read it from how the brand frames the customer's problem:
- frames problems as systems to engineer -> Operator
- frames problems as questions to investigate -> Sage
- frames problems as people to support -> Caregiver
- frames problems as a status quo to break -> Rebel

**Voice posture:** Confident / Warm / Sharp / Quiet / Playful / Authoritative. Read from sentence length, punctuation, and word choice in the body copy. Short declaratives -> Sharp/Confident. Long, soft, second-person -> Warm. Cite a representative sentence.

## Palette

A table of `#RRGGBB` by role: Background, Ink, Accent, Muted, Rule, plus any brand-specific roles. Up to 8; past that the brand stops being recognizable.

How to get real hex:
- **Brand book PDF:** read the swatches directly. Highest confidence.
- **Website:** the CSS holds exact values (`background`, `color`, CSS custom properties like `--accent`). Highest confidence after a brand book.
- **Screenshots:** sample the dominant background, the text color, and the one or two accent colors. Compression shifts color slightly, so flag screenshot-sampled values `needs confirmation` unless they are clearly flat brand colors.

**Never guess a hex.** If you cannot read or sample one, estimate, label it `needs confirmation`, and tell the user exactly which role to verify. (See SKILL.md Rule 1.)

## Typography

Display font, body font, optional mono, each with weight (`Inter Black 900`, not `Inter Bold`).

- **Website:** `font-family` declarations and loaded font files (`fonts.googleapis.com`, `@font-face`, `.woff2` names) name the fonts exactly. Weights come from `font-weight`.
- **Brand book:** named directly.
- **Screenshots:** identify by eye only if confident; otherwise flag `needs confirmation`. Do not invent a plausible name (Rule 2).

Two fonts max; three only if one is mono for code/data.

## Mood adjectives

3-5 adjectives, specific, contrast clauses preferred. Read tone from the body copy and the imagery together.

Reject generic fillers ("professional, modern, clean"), they describe everything and constrain nothing. Push to contrast clauses that do work: "operator not creator", "warm not precious", "plainspoken not corporate". If the assets only support generic adjectives, flag `needs confirmation`. Cite the copy or image that supports each adjective.

## Never list

The hardest and most valuable section. Brands document what they do; you infer what they avoid from consistency across the assets.

Method, look for what is conspicuously absent:
- Imagery: no stock-photo gloss? no people? no gradients? no clip-art icons? Each absence is a never.
- Copy: no exclamation points? no hype words ("revolutionary", "game-changing")? no emojis? no questions in headlines? Each pattern is a never.
- Color/layout: never full-bleed photography? never more than one accent? never centered body text?

Turn each observed constraint into a `never` line. Be specific: "never use stock-photo aesthetic" beats "keep it authentic". Aim for 5+. Never ship an empty list (Rule 4).

## Aspect ratios

The ratios the brand renders for. Default to `9:16, 16:9, 1:1, 4:5`. If the assets reveal a bias (a vertical-only social brand, a cinematic 21:9 site hero), reflect it and note the evidence.

## Color grade direction

One sentence on how footage and generated images should be graded, with a reference point where possible (Kodak Portra 400, Apple keynote photography, A24 film grade). Infer from the existing photography's warmth, contrast, and saturation. If there is no photography to read, base it on the palette and flag `needs confirmation`.

## Motion language

One paragraph: camera moves, cut style, text animation, pacing. Read from any existing video or motion on the site; if there is none, infer a conservative default consistent with the voice posture (a Quiet/Authoritative brand -> minimal, slow, deliberate) and flag `needs confirmation`. Keep it to one coherent motion language, do not blend "minimal and deliberate" with "energetic whip pans".

## Voice rules

Copy-level constraints for VO and on-screen text. Many overlap the never-list but are phrased as authoring rules: "no em dashes", "sentences under 14 words", "prefer specific numbers over vague claims", "no exclamation points in headlines". Extract from observed copy patterns. These become prompt constraints downstream, so make them enforceable, not aspirational.
