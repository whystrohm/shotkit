# The Remotion Bridge

This is a pointer document. The skill pack stops at the `shots.json` spec. This doc explains how that spec maps to Remotion components for teams that want to build the bridge themselves.

The actual implementation is intentionally not included. WhyStrohm runs the implementation as part of its commercial offering. The methodology is open.

## Why Remotion

Remotion renders video from React components. Same shot data → same video output, every time. Deterministic, version-controlled, scriptable. It pairs naturally with the file-native, audit-rich approach in this skill pack.

For teams already using Remotion, the bridge is straightforward. For teams not using Remotion, it's a path worth considering for high-volume programmatic video.

## The mapping

`shots.json` maps to a Remotion Composition. Each shot maps to a Sequence inside the composition. Each text overlay maps to a layer above the shot's image.

```
shots.json                       Remotion structure
├── project                ─→    <Composition durationInFrames={duration_s * 30} fps={30} ...>
├── series_lock            ─→    Theme provider / context (character, environment, lighting passed down)
├── shots[]                ─→    <Sequence from={start * 30} durationInFrames={(end - start) * 30}>
│                                  <Img src={generatedImagePath} />
│                                </Sequence>
└── text-overlays[]        ─→    <Sequence from={enter.at * 30} durationInFrames={(exit.at - enter.at) * 30}>
                                   <TextOverlay
                                     content={...}
                                     font={...}
                                     position={...}
                                     enterAnimation={...}
                                   />
                                 </Sequence>
```

## Component conventions

A working Remotion bridge typically defines these components:

- **`<Storyboard />`**, the top-level composition. Reads shots.json, renders all sequences.
- **`<Shot />`**, single shot wrapper. Handles image loading, motion blur, transitions.
- **`<TextOverlay />`**, single text layer. Handles enter/exit animations, positioning.
- **`<BrandTheme />`**, context provider that exposes brand-lock palette, fonts, motion tokens.

Each component is a thin wrapper over Remotion's primitives. The complexity is in the data model, not the rendering.

## Animation mapping

The `enter.animation` and `exit.animation` fields in `text-overlays.json` map to Remotion animation patterns:

| animation | Remotion implementation |
|---|---|
| `fade-in` / `fade-out` | `interpolate(frame, [0, 12], [0, 1])` for opacity |
| `slide-up` / `slide-down` | `interpolate` on `translateY` |
| `type-on` | character-by-character reveal using `Math.floor(frame / charsPerFrame)` to slice content |
| `hard-cut` | conditional render based on frame |

Standard Remotion patterns. Nothing exotic.

## Series consistency

The series_lock fields don't render directly, they govern the rendering. A bridge implementation typically:

- Passes series_lock.character / environment / lighting through context
- Uses these for text overlay color selection (avoiding combinations that fail against the lighting)
- Uses color_grade for global filter/grading on top of all sequences
- Surfaces them as props for any custom shot components

## Brand-lock integration

Brand-lock palette and typography typically get loaded as design tokens at build time. A common pattern:

1. Read `brand-lock.snapshot.md` at composition mount
2. Parse palette table → CSS custom properties
3. Parse typography → loaded via `staticFile()` or `@font-face`
4. Expose to all child components via React context

This means the same Remotion build can render against different brand-locks, swap the snapshot, get a different brand's video.

## Audio integration

`shots.json` doesn't include audio. Most bridge implementations handle audio separately:

- VO comes from a separate `vo.json` or `vo/` directory of WAV/MP3 files keyed by shot_id
- Music comes from a single track with start/end timestamps
- Sound design is a per-shot field added in a downstream `audio.json`

A serious bridge merges these into the composition. The skill pack doesn't reach into audio because the audio production workflow varies too much across teams to encode into a methodology.

## Render orchestration

For programmatic rendering at scale:

- `npx remotion render` produces a single MP4
- `@remotion/lambda` produces parallel renders on AWS Lambda for speed
- Custom orchestration handles batch jobs across multiple storyboards

This is where the pipeline goes from "creative workflow" to "video infrastructure." The skill pack stops well before this layer. The methodology survives, but the operational tooling is yours to build.

## Why we're not including the implementation

Three reasons:

**1. Operational specifics vary.** Every team has different deployment targets, brand-loading strategies, audio workflows, render infrastructure. A reference implementation would need to be either too opinionated (constraining your choices) or too abstract (not actually useful).

**2. The methodology is what matters.** The architectural decisions, separating brand-lock from series-lock from shot-spec from text-layer, survive any implementation. The implementation is plumbing.

**3. Operating it well is part of the value WhyStrohm delivers.** The infrastructure that runs hundreds of rendered videos per month against the methodology is the product offering. Open-sourcing it would commoditize the operator role without commensurate value to the open-source community.

If you build a bridge yourself, the methodology in this repo is enough. If you want the operated version, [whystrohm.com](https://whystrohm.com).

## Worth building yourself if

- You render more than 10 videos per month
- You have 3+ active brands needing consistent output
- You have engineers comfortable with React and CI/CD
- Your output cadence is > 48 hours per video and you want it under
- You have specific custom rendering needs that no SaaS handles

## Not worth building yourself if

- You render fewer than 10 videos per month
- You have one brand, infrequent updates
- You don't have engineering capacity for a Node/React video pipeline
- You're happy with manual editorial assembly in Premiere or After Effects

The skill pack works without Remotion. The bridge is for teams scaling beyond manual assembly.
