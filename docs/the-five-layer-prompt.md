# The Five-Layer Prompt

The architectural decision underneath every prompt this skill pack produces.

## The problem

A naïve "AI storyboard tool" generates an image prompt by taking a brief and stuffing it into a generator. The output is unreliable across shots, inconsistent across generators, and impossible to audit later.

The five-layer prompt is the discipline that fixes this.

## The five layers

### Layer 1. Brand Lock

Constant across the entire project.

Contains: palette, typography, mood adjectives, "never" list, aspect ratios, color grade direction, voice rules.

Source: `brand-pack.md` file → snapshotted into `brand-lock.snapshot.md` per storyboard run.

This is the slowest-changing layer. A brand-lock might update twice a year for a stable brand, monthly for a new one.

### Layer 2. Series Lock

Constant across one storyboard.

Contains: character anchor (who's in frame), environment, lighting setup, color grade specifics.

Source: `shots.json` → `series_lock` field.

This locks visual continuity across a single piece of content. Same person across every shot. Same environment. Same lighting direction. Same color grade.

### Layer 3. Shot Spec

Variable per shot.

Contains: framing, angle, motion, depth of field, subject (what's happening in this specific shot), rationale.

Source: `shots.json` → `shots[i]`.

This is where each shot earns its individual identity within the series-locked world.

### Layer 4. Text Layer

Composited separately. **Never in the image prompt.**

Contains: text content, font, color, position, animation, timing.

Source: `text-overlays.json`.

This layer flows to the editor or motion designer, not to the generator.

### Layer 5. Generator Adapter

Applied at compose time.

Contains: model-specific syntax, parameter mapping, length conventions, idiosyncratic strengths.

Source: `visual-prompt-forge/adapters/{generator}.md`.

This is the only layer the skill *applies*. Layers 1-4 are inputs.

## Why this matters operationally

**Change one layer, others unaffected.**

- Brand color updates → edit `brand-pack.md`. Every storyboard, every prompt, every shot inherits.
- Character outfit changes mid-project → edit `series_lock.character` once. Every shot in this storyboard updates.
- One shot's framing is wrong → edit just that shot's `framing` field. Other shots untouched.
- Switch from Midjourney to Flux → swap adapter. Same shot data, different output file. Brand-lock and series-lock untouched.

This is the architectural property that makes the pack maintainable at scale. WhyStrohm runs 11 brands and 800+ generated videos through this pattern. Without layer separation, that throughput is impossible.

## Why text never goes in the image prompt

Four reasons:

**1. Editability.** Composited text can be revised in 30 seconds without re-running the generator. Baked-in text requires a re-roll, which costs API credits and breaks consistency with neighboring shots.

**2. Quality.** Even Ideogram v3 and GPT Image 1.5, the best at text rendering, produce typography that lags professional design tools. Kerning is rough, weight is approximate, brand fonts are not honored.

**3. Animation.** Most production text needs animation. Type-on, fade-in, slide-up. None of this exists in a static rendered frame. Composited text gets handled in After Effects, Remotion, or CapCut.

**4. Brand control.** Composited text uses exact brand fonts at exact brand weights at exact brand colors. Generated text approximates. The approximation is uneven across runs.

The exception: text-as-image (poster work, signage in scene, packaging mockups) where the text *is* the artifact. For this case, Ideogram Mode 2 with explicit override flag. Documented in `adapters/ideogram.md`.

## How this differs from other approaches

**vs. monolithic prompts**, most AI image tools encourage stuffing every parameter into one prompt string. This is fast for one-off use, fragile across a series. The five-layer model trades simplicity for maintainability.

**vs. preset systems**, some tools offer "style presets" that bundle aesthetic decisions. This is closer to what brand-lock does but lacks the per-shot variability. Presets are too coarse for production work.

**vs. fine-tuned models**, some teams train a custom LoRA per brand. This works but locks you to one generator family and produces inconsistent results across model updates. The five-layer model is portable across generators because the layers are text, not weights.

## When this is overkill

- Single-shot generation (no series). Just write a prompt.
- Hobbyist exploration. The structure is overhead for play.
- Brand-agnostic work (e.g. abstract art generation). Without a brand-lock, layer 1 is empty.

When you're doing repeated, branded, multi-shot, production-bound work, the five layers earn their structure.

## How to apply this without the skill pack

The skill pack automates the composition. But the layers exist independently. You can apply them by hand:

1. Write a brand-lock file (use the template)
2. Write a series-lock per storyboard (one paragraph each: character / environment / lighting / color grade)
3. Write per-shot specs (framing, angle, motion, subject, rationale)
4. Keep text in a separate doc
5. For each generator, write an adapter (or use the ones in this repo)

The skill pack is a productivity layer over this discipline. The discipline works without it. The skill pack just makes it fast.
