# Connecting to Video Pipelines

This is a pointer document. The skill pack stops at the `shots.json` spec. This doc explains how that spec maps to a programmatic video framework for teams that want to build the bridge themselves.

The actual implementation is intentionally not included. WhyStrohm runs the implementation as part of its commercial offering. The methodology is open.

## Why a programmatic video framework

Programmatic video frameworks render video from declarative components. Same shot data, same output, every time. Deterministic, version-controlled, scriptable. They pair naturally with the file-native, audit-rich approach in this skill pack.

Several mature React-based options exist as of 2026 (Remotion, Motion Canvas, and similar). The pattern below applies to any of them. The API surface differs, the architecture does not.

For teams not already using one, this is a path worth considering for high-volume programmatic video. For teams using a different toolchain (After Effects, Premiere, Resolve), the same `shots.json` is still readable as a script. The pattern below is one of several valid bridges.

## The mapping

`shots.json` maps to a top-level Composition. Each shot maps to a Sequence inside the composition. Each text overlay maps to a layer above the shot's image.

```
shots.json                      Composition structure
├── project              -->    Composition root (duration, fps, dimensions)
├── series_lock          -->    Theme context (character, environment, lighting)
├── shots[]              -->    Sequence per shot (start frame, duration, image)
└── text-overlays[]      -->    Sequence per overlay above shot image
```

The components a working bridge typically defines:

- **Storyboard root**, the top-level composition. Reads `shots.json`, renders all sequences.
- **Shot wrapper**, single shot. Handles image loading, motion blur, transitions.
- **Text overlay**, single text layer. Handles enter/exit animations, positioning.
- **Brand theme**, context provider that exposes brand-lock palette, fonts, motion tokens.

Each is a thin wrapper over the framework's primitives. The complexity is in the data model, not the rendering.

## Animation patterns

The `enter.animation` and `exit.animation` fields in `text-overlays.json` map to standard easing patterns. Framework-agnostic:

| animation | Pattern |
|---|---|
| `fade-in` / `fade-out` | linear interpolate on opacity |
| `slide-up` / `slide-down` | linear interpolate on translateY |
| `type-on` | character-count slice based on frame |
| `hard-cut` | conditional render gated by frame |

Any timeline-based renderer expresses these with a few lines of math. Differences across frameworks are surface-level.

## Series consistency

The `series_lock` fields don't render directly, they govern the rendering. A bridge implementation typically:

- Passes `series_lock.character` / `environment` / `lighting` through context
- Uses these for text overlay color selection (avoiding combinations that fail against the lighting)
- Uses `color_grade` for global filter/grading on top of all sequences
- Surfaces them as props for any custom shot components

## Brand-lock integration

Brand-lock palette and typography typically get loaded as design tokens at composition mount. A common pattern:

1. Read `brand-lock.snapshot.md` at build time
2. Parse the palette table into CSS custom properties
3. Parse typography into web-font definitions
4. Expose to child components via context

This means the same composition can render against different brand-locks. Swap the snapshot, get a different brand's video.

## Audio

`shots.json` doesn't include audio. Most bridge implementations handle audio separately:

- VO comes from a separate `vo.json` or `vo/` directory keyed by `shot_id`
- Music comes from a single track with start/end timestamps
- Sound design lives in a downstream `audio.json`

A serious bridge merges these into the composition at render time. The skill pack doesn't reach into audio because the audio production workflow varies too much across teams to encode into a methodology.

## Why we're not including the implementation

Three reasons:

**Operational specifics vary.** Every team has different deployment targets, brand-loading strategies, audio workflows, render infrastructure. A reference implementation would need to be either too opinionated or too abstract.

**The methodology is what matters.** The architectural decisions, separating brand-lock from series-lock from shot-spec from text-layer, survive any implementation. The implementation is plumbing.

**Operating it well is part of the value WhyStrohm delivers.** The infrastructure that runs hundreds of rendered videos per month against the methodology is the product offering.

## Worth building yourself if

- You render more than 10 videos per month
- You have 3+ active brands needing consistent output
- You have engineers comfortable with React and CI/CD
- You have specific custom rendering needs that no SaaS handles

## Not worth building yourself if

- You render fewer than 10 videos per month
- You have one brand, infrequent updates
- You don't have engineering capacity for a Node/React video pipeline
- You're happy with manual editorial assembly

The skill pack works without a programmatic video framework. The bridge is for teams scaling beyond manual assembly.

WhyStrohm runs this commercially as a managed service for founder-led brands.
