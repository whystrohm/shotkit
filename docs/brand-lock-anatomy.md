# Brand-Lock Anatomy

A brand-lock is a single Markdown file that codifies how a brand looks, sounds, and behaves across every shot, every prompt, every render. Get it right and every storyboard the pack produces inherits coherence for free. Get it wrong and the pack produces fluent, professional, off-brand output. There is no middle ground.

## What a brand-lock is

A brand-lock is a frozen specification. It captures the brand's parameters at a point in time so that downstream artifacts can be produced deterministically against that state. Two operators reading the same brand-lock should produce visually compatible work without coordinating.

Concretely, it is a Markdown file with required sections, a small set of fields per section, and a versioning footer. The file lives in `brand-packs/`. The pack reads it at storyboard-creation time and snapshots it into `brand-lock.snapshot.md` alongside every output run.

## What a brand-lock is not

It is not a brand book. Brand books are 60-page documents written for a human design team. They include rationale, history, voice exercises, do-not-do galleries, brand-anniversary milestones. Useful for a designer onboarding to a brand, useless to a generator producing per-shot prompts.

It is not a style guide. Style guides specify how to write headlines and how to crop logos. They focus on a small slice of brand expression. The brand-lock is broader, covering palette, type, motion, voice, and posture in one file.

It is not a configuration file. The brand-lock is human-readable, human-editable Markdown by design. A YAML or JSON config would be faster to parse but harder to author. Authoring quality matters more than parse speed for a file that updates twice a year.

## The required fields

Every brand-lock has nine sections. Each is required. Missing sections fail validation in `tools/validate_brand_lock.py`.

### Identity

Brand name. One-line description. Archetype. Voice posture.

The one-line description is the most important sentence in the file. It is what a generator implicitly references when producing prompts. "Managed content infrastructure for founder-led brands. 30 minutes a week of founder time, 48-hour content cycles" reads differently than "Content agency for entrepreneurs." The former produces operator-coded shots. The latter produces hustle-coded shots. Same brand, different output.

### Palette

A table mapping color roles to hex values. Roles include Background, Ink, Accent, Muted, Rule, and any brand-specific roles (Success, Warning, etc.). Every hex listed is allowed. Anything outside the list is not.

Hex precision matters because the schema validates it. The `shots.schema.json` and `text-overlays.schema.json` accept color values as a regex match against `^#[0-9A-Fa-f]{6}$`. Approximations like "navy blue" or "warm cream" do not pass schema validation. They also do not survive composition. Eight different "warm creams" land in eight different shots and the brand fragments.

### Typography

Display font, body font, optional mono font. Each with explicit weight (e.g. `Inter Black 900`, not `Inter Bold`).

Two fonts is the production maximum. Three only if one is reserved for code or data (mono). Past three, the brand stops being recognizable. This is not aesthetic preference, it is a perception fact across all serious brand systems.

### Mood adjectives

Three to five adjectives that describe the brand's emotional posture. Specific, not generic.

"Professional, trustworthy, innovative" is generic. Every brand on Earth could claim it. "Operator (not creator), considered (not reactive), deterministic (not vibes-based)" is specific. The contrast clauses do real work, they tell the generator what to lean toward and what to lean away from.

### Never list

What this brand never does. The most undervalued field in the file.

Most brand documentation lists what a brand should be. The brand-lock inverts the emphasis. "Never use stock photo aesthetic" rules out an entire visual category. "Never use em dashes in copy" disables a specific punctuation pattern. "Never animate text with bouncing or wobbling" eliminates a class of motion.

Generators are pattern-completion engines. They produce whatever is statistically average for the prompt. The never-list is how you remove the average from the search space. Every "never" is a constraint that sharpens output.

The "always" fields establish identity. The "never" fields enforce it.

### Aspect ratios

The ratios this brand renders for. Default 9:16, 16:9, 1:1, 4:5. Brand-specific ratios go here.

This field looks redundant. It is not. It tells the prompt-forge skill what aspect ratio to inject into adapter outputs (`--ar 9:16` for Midjourney, `aspect_ratio: "9:16"` for Flux, etc.) and signals the storyboard-architect skill which framings work at which ratios.

### Color grade direction

One paragraph describing how footage and generated images should be graded. Reference points (Kodak Portra 400, Apple keynote photography, Wong Kar-wai, etc.) are encouraged.

The grade is what makes generated images sit next to brand photography. Without it, AI output looks like AI output. With it, the same generator can produce work that looks like it shares a colorist with the brand's existing library.

### Motion language

How motion behaves. Camera moves, cut style, text animation, transition vocabulary, pacing rules.

This field flows into the shot-grammar reference (it constrains what `motion` values are allowed per shot) and the video-pipeline bridge (it parameterizes spring physics, transition lengths, easing curves). Without it, every shot defaults to the global average. With it, shots earn their motion choice.

### Voice rules

Copy-level constraints that apply to VO and on-screen text.

Same logic as the never-list. "No em dashes" is more useful than "good copy." "Prefer specific numbers over vague claims" is more useful than "be precise." Voice rules turn into prompt constraints in the storyboard-architect skill and into validators in commercial pipelines.

## Why hex precision matters

The shots.schema.json defines text overlay colors as a regex match against `^#[0-9A-Fa-f]{6}$`. An overlay color of "navy" fails validation. An overlay color of `#0F1F3A` passes.

This is not pedantry. It is what makes the brand-lock load-bearing. If color was a freeform string, the pack would produce one shot with `color: "deep blue"`, the next with `color: "navy blue"`, the next with `color: "midnight blue"`. Three shots, three slightly different blues, none of which match the brand. Hex precision forces every reference to compose against the same value.

The brand-lock file enforces this at the source. The schema enforces it at the output. The two together produce deterministic color across every run.

## Why archetype is the most undervalued field

Archetype is one word. Operator. Sage. Caregiver. Rebel. Creator. It feels like marketing-deck filler. It is not.

The archetype is the implicit narrator of every shot the pack produces. An Operator brand frames problems as systems to engineer. A Sage brand frames problems as questions to investigate. A Caregiver brand frames problems as people to support. The framing changes everything. Same brief, different archetype, different storyboard.

Skipping the archetype field produces output with no implicit narrator. The generator picks one for you, and the pick varies per shot. The result reads as four different brands stitched together.

## Why the "never" list is more valuable than the "always" list

This is the single most counterintuitive part of the brand-lock methodology.

A brand's identity is defined more by what it refuses than by what it claims. Every brand claims "credible, innovative, customer-obsessed." Few brands hold a coherent line on what they will not do. The hold is the brand.

In production, the never-list translates directly into prompt negative-conditioning, schema rejection, and editorial filtering. "Never use stock photo aesthetic" feeds into Midjourney as `--no stock photo`, into Flux as a negative prompt, into the visual-asset-critic as a hard-fail rubric line. One field, three downstream constraints.

The "always" fields anchor what the brand is. The "never" fields make the brand recognizable when reduced to a single shot.

## How brand-locks compose with series-locks and shot specs

The five-layer prompt anatomy (see [`docs/the-five-layer-prompt.md`](./the-five-layer-prompt.md)) places the brand-lock at the top of the layer stack:

```
brand-lock                  -->  constant across project
  ↓
series-lock                 -->  constant across one storyboard
  ↓
shot-spec                   -->  variable per shot
  ↓
text-overlay                -->  composited separately
  ↓
generator-adapter           -->  applied at compose time
```

Each layer constrains the layers below it. The brand-lock locks palette and motion and voice across every shot in every storyboard. The series-lock locks character and environment across one storyboard. The shot-spec locks framing and motion within a shot. The text-overlay handles on-screen copy as a separate compositing pass.

This is the architectural reason the pack composes. Change the brand-lock once, every storyboard inherits. Change the series-lock once, every shot in that storyboard inherits. Change a shot once, only that shot updates. No cross-contamination. No partial updates.

## Common mistakes

Five patterns show up repeatedly in first-draft brand-locks.

**Vague mood adjectives.** "Professional, modern, friendly" describes 90% of brands. Replace with contrast clauses ("operator not creator", "considered not reactive") that do real work.

**Paraphrased palette.** "Warm cream", "deep navy", "coral pop." Replace with hex values. The schema requires them anyway.

**Missing never list.** First drafts often skip the never list because nothing about the brand "feels constrained." This is the section that makes the brand recognizable. Do not skip it. If it feels hard, that means it is doing its job.

**Two motion languages in one paragraph.** "Camera moves are minimal and deliberate. Default to static. When motion is used, slow push or slow pull only" is one motion language. "Camera moves are minimal. Also we use whip pans and dolly zooms for energetic moments" is two. Pick one. Tonal split-decisions confuse generators.

**Reference materials missing.** Past hero films, mood boards, related brand books. Optional, but valuable for the human reading the brand-lock for the first time.

## How to write one that actually works in production

Three rules.

**Write it with the pack in mind.** Every field flows into a downstream operation. Specificity at this layer compounds. Vagueness at this layer compounds the other direction.

**Test it on one storyboard before committing to a brand-pack.** Run the storyboard-architect skill against the new brand-lock. Open the preview. If the output looks generic, the brand-lock is not specific enough. If it looks off, the brand-lock contradicts itself.

**Treat it as living.** Update the brand-lock when palette, type, or voice evolve. The snapshot pattern means past storyboards stay valid against past brand-lock versions. New work targets the current version. Both are explicit, neither is overwritten.

The brand-lock is the file where the smallest edits have the biggest downstream effect. A 90-line Markdown file that constrains every output across every storyboard. Worth the time it takes to get right.
