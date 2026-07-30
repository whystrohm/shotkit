# shotkit/remotion

Remotion composition source for the repo's rendered assets: the demo GIF at
`../docs/images/demo.gif`, the social preview card at `../docs/images/social-preview.png`, and
the explainer film at `../docs/images/shotkit-explainer.mp4`. Ships with the repo so
contributors can regenerate them after brand-pack updates.

This is composition source, not a redistributable Remotion framework. It exists for the repo's
own assets only.

## Which sources are current

| Composition | Rendered asset | State |
|---|---|---|
| `SocialPreview.tsx` | `social-preview.png` | Current |
| `ShotkitDemo.tsx` | `demo.gif` | Current |
| `ShotkitExplainer.tsx` | `shotkit-explainer.mp4`, `-vertical.mp4` | v0.1.0, not re-cut |

`ShotkitExplainer.tsx` still shows seven generator adapters including Runway/Sora, and stamps
`v0.1.0`. Sora was discontinued in 2026 and the motion lane moved to Kling, Veo, Seedance, and
Hailuo.

The source is left matching the video it produced rather than edited to describe a render that
does not exist. Re-cutting means updating the adapter list, the file tree, and the version
stamp, then re-rendering both cuts and the storyboard example beside them. Until that happens,
source and artifact agree, and both are labelled.

## Install

```bash
cd remotion
npm install
```

First install also pulls Remotion's bundled Chromium. Around 200MB on disk.

## Preview in studio

```bash
npx remotion studio
```

Opens the Remotion Studio at `http://localhost:3000`. Scrub through the `ShotkitDemo` composition timeline to verify the four animation phases:

1. Frames 0-72: brief types into the left panel.
2. Frames 72-150: output file tree assembles in the right panel.
3. Frames 150-210: coral wipe reveals the rendered preview, vertical scroll passes through several shot cards.
4. Frames 210-240: crossfade back to the opening state for a seamless loop.

## Render the GIF

```bash
./render.sh
```

The script copies `../skills/storyboard-architect/examples/30s-pain-proof-promise/preview.html` into `public/preview.html` so the composition iframe can load it via `staticFile()`. Then it renders the composition to `../docs/images/demo.gif`.

Target output: 1280x720, 30fps, 8 seconds, under 8MB.

If the output exceeds 8MB:

- Add `--quality=80` to the render command.
- If still over, drop fps from 30 to 24 in `src/Root.tsx`.
- GitHub README has a 10MB image cap. Leave a 2MB margin.

## Brand tokens

Brand colors and font names live in `src/tokens.ts`. If the WhyStrohm brand-pack updates, change the hex values there and re-render. The composition pulls every color from that file.

## Files

```
remotion/
├── package.json           Remotion + react + typescript
├── tsconfig.json          Standard Remotion TS config
├── remotion.config.ts     PNG image format, overwrite output, 4-way concurrency
├── render.sh              One-command render to ../docs/images/demo.gif
├── README.md              This file
├── public/
│   └── preview.html       Copied at render time, not committed
└── src/
    ├── index.ts           Calls registerRoot
    ├── Root.tsx           Registers ShotkitDemo composition
    ├── ShotkitDemo.tsx    The demo composition
    └── tokens.ts          Brand color and font constants
```
