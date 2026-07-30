---
name: storyboard-html-preview
description: Render a structured storyboard (storyboard.md, shots.json, text-overlays.json, brand-lock.snapshot.md) into a single-file HTML preview that is shareable, printable, and offline. Use when the user wants to share a storyboard, export for review, hand off to an editor, or print a hard copy. Triggers on "preview the storyboard", "share this", "export to HTML", "print version", or after a storyboard-architect run. Produces one self-contained .html file with no build or server.
---

# Storyboard HTML Preview

You are turning structured storyboard files into a single shareable HTML document. The output is what an editor, stakeholder, or client opens in a browser without thinking about it.

The constraint is non-negotiable: **single file, no build step, no server, works offline.** Any time the output requires "run this build command" or "host this somewhere," the skill has failed.

## When to use

Trigger when the user:

- Asks to preview, share, or export a storyboard
- Wants a printable version
- Says "what's the next step" after a storyboard-architect run
- Hands off `storyboard.md` + `shots.json` + asks for a deliverable for review

## What you produce

One file: `preview.html`. Self-contained. Inline CSS. No JavaScript dependencies (vanilla JS only, embedded). No external font files (uses system stack with brand-font fallbacks). No external images (placeholder slots; if generated images exist, embed as base64 OR reference relative paths).

```
output/
├── run.json                   # input, for the run id and date
├── storyboard.md              # input
├── shots.json                 # input
├── text-overlays.json         # input
├── brand-lock.snapshot.md     # input
├── frames/round-N/            # input, if generation has happened
├── critiques/round-N/         # input, for the verdict badges
└── preview.html               # ← what this skill produces
```

If the user has generated frames, the HTML references them via relative paths so the file
works when the whole `output/` folder is shared. Resolve a shot's frame in this order:

1. An entry in `shot.assets.generated` marked `accepted: true`
2. The newest entry in `shot.assets.generated`
3. `frames/round-{highest}/{shot_id}.{png,jpg,jpeg,webp}`
4. `generated/{shot_id}.{ext}`, the pre-3.0.0 flat layout

Data first, convention second. Reading the path convention first meant the page showed
whatever file happened to sit there, accepted or rejected, first draft or fifth re-roll.

If no frames exist yet, the HTML uses styled placeholder cards with the shot spec, still
useful for review and handoff.

## Workflow

### Step 1. Read inputs

Required:

- `shots.json`
- `text-overlays.json`
- `brand-lock.snapshot.md`

Optional:

- `run.json` (for the run id and date; without it the page says "not recorded")
- `storyboard.md` (for narrative context, surface the brief at the top)
- `frames/round-N/{shot_id}.{png,jpg,jpeg,webp}` (if generation has happened)
- `critiques/round-N/{shot_id}.critique.json` (for verdict badges)

Validate before rendering, and stop if it fails:

```bash
python tools/validate_shots.py output/
```

### Step 2. Extract brand parameters

From `brand-lock.snapshot.md`, extract:

- Palette (hex values), used for HTML accent colors
- Display font and body font names, used as font-family values with system fallbacks
- Brand voice / mood, used in subtle copy choices

The HTML preview should *feel* like the brand without going overboard. Quiet branding, not loud.

### Step 3. Generate the HTML

Use `templates/preview.html.tpl` as the structural template. Read it before generating.

The HTML structure:

```
<!DOCTYPE html>
<html>
<head>
  <meta>
  <title>{project title}</title>
  <style>
    /* All CSS inline. ~200 lines. Brand-aware. */
    /* Print stylesheet included. */
  </style>
</head>
<body>
  <header>
    <!-- Project title, duration, aspect, generated timestamp -->
  </header>

  <section class="brief">
    <!-- Brief summary if storyboard.md provides one -->
  </section>

  <section class="series-lock">
    <!-- Character / environment / lighting / color grade -->
  </section>

  <section class="shots">
    <!-- One card per shot -->
    <article class="shot" id="shot_01">
      <div class="shot-frame">
        <!-- generated image OR styled placeholder -->
      </div>
      <div class="shot-meta">
        <!-- timestamp, framing, angle, motion -->
      </div>
      <div class="shot-subject">
        <!-- subject description -->
      </div>
      <div class="shot-text-overlay">
        <!-- if on_screen_text exists, show overlay content with timing -->
      </div>
      <div class="shot-rationale">
        <!-- rationale text -->
      </div>
    </article>
    <!-- ... -->
  </section>

  <footer>
    <!-- audit trail: brand-lock snapshot reference, timestamp -->
  </footer>

  <script>
    /* Vanilla JS only. Optional: keyboard nav, jump-to-shot, expand/collapse. */
  </script>
</body>
</html>
```

### Step 4. Embed frames if available

Resolve each shot's frame by the order in "What you produce" above, then reference it by a
path relative to the output root:

```html
<img src="frames/round-2/shot_01.png" alt="shot_01: hook" loading="lazy" />
```

This works when the whole output folder is zipped and shared.

For hard-copy print (a single file with no folder structure), the skill can offer to inline
frames as base64. Ask the user which they prefer if frames are present.

If a shot's `assets.generated` entry carries a `sha256` and the file no longer matches it,
render the frame but say so on the page. That mismatch means the frame changed after it was
recorded, which is exactly the case where a preview quietly showing the new file is worse
than one that flags it.

If no frames exist, render styled placeholder cards showing the framing, subject, and shot
spec. These are still useful for stakeholder review at the storyboard stage.

**Template flag convention.** When composing the per-shot context for `preview.html.tpl`, set exactly one of:

- `has_image: true` and `image_path: "frames/round-2/shot_NN.png"`, when a frame exists
- `has_no_image: true`, when none does (renders the placeholder card)

The template uses two parallel `{{#if}}` blocks rather than `{{#if}}/{{else}}` to keep the rendering portable across template engines.

For text overlays, set `has_overlays: true` and an `overlays` array on the shot. Each entry
carries `id`, `content`, `font`, `weight`, `color`, `size`, `position_class`,
`position_label`, `enter_at`, `enter_animation`, `exit_at`, `exit_animation`. The template
iterates that array with `{{#each overlays}}`.

It is an array because `shots.json` lets a shot carry several overlays and
`text-overlays.json` always did. A single set of `overlay_*` fields could hold one, so the
second overlay on a shot rendered nowhere and nothing reported it.

For verdict badges, set `has_verdict`, `verdict`, `verdict_round`, and `verdict_class`
(the lowercased verdict) from the newest critique for that shot under `critiques/`. Omit
them when the shot has no critique.

**Escape everything.** Subjects, rationales, VO lines, and overlay copy are model-generated
prose that lands in both text and attribute contexts. One angle bracket in a rationale, or
one quote in an overlay font name, breaks the page a client is reading.
`tools/shots-to-html.py` escapes every substitution by default and reserves raw output for
the inlined CSS alone.

### Step 5. Render text overlays visually

For every shot with an `on_screen_text` reference, the HTML shows:

- The text content rendered in approximately the brand font (or visible fallback)
- The position indicated visually (lower-third, center, etc.)
- Timing info (enter/exit beats)

This gives the reviewer a sense of what the final composited frame will look like, even before final compositing happens.

### Step 6. Print stylesheet

Include `@media print` rules that:

- Hide nav, footer scripts, expand/collapse UI
- Force one shot per page (or two if compact)
- Ensure text overlays render legibly
- Use black-on-white where brand colors won't print well

The user should be able to hit Cmd-P / Ctrl-P and get a clean PDF.

## Hard rules

### Rule 1. Single file, no exceptions

The output is one `.html` file. If you find yourself wanting a separate stylesheet or JS file, inline it. If you find yourself wanting a build step, you're solving the wrong problem.

### Rule 2. No external dependencies at runtime

No CDN scripts. No Google Fonts. No external CSS frameworks. The file must work with no internet connection.

The exception: if the user explicitly opts in (e.g. "make it pretty, I'm online"), Tailwind via CDN is acceptable. Default is no.

### Rule 3. Print must work

Hit Cmd-P. The result should be a clean PDF. If layout breaks across page boundaries, the print stylesheet is broken.

### Rule 4. Brand-aware but quiet

Use brand colors as accents, not as full backgrounds. The reviewer's job is to read the storyboard, not admire the design. Subtle.

### Rule 5. Mobile-readable

Stakeholders open links on phones. The HTML should be readable on mobile without horizontal scroll. Simple responsive CSS.

## Templates

- `templates/preview.html.tpl`, the structural template
- `templates/styles.css.tpl`, the CSS to inline
- `templates/print.css.tpl`, the print rules

The skill reads all three and assembles them into a single `preview.html`.

## Quality bar

Before declaring done, verify:

- [ ] File opens in any browser (Chrome, Safari, Firefox) with no errors
- [ ] No external network requests fire on load
- [ ] Print preview produces a clean PDF
- [ ] Mobile viewport (375px) renders without horizontal scroll
- [ ] Brand colors and fonts come from the brand-lock, not from a fallback
- [ ] Every shot from `shots.json` is present
- [ ] Every overlay referenced by a shot is rendered, including second and third overlays
- [ ] `brand_lock_ref` from `shots.json` is what the footer links to, not a hardcoded name
- [ ] The run date and the render date are both shown, and labelled differently
- [ ] No `{{` remains anywhere in the output

The CLI renderer checks the mechanical half of that list against itself:

```bash
python tools/shots-to-html.py --selftest
```

## Two timestamps, not one

"Run" is when the storyboard was produced, read from `run.json`. "Rendered" is when the page
was written. They are separate lines in the footer and they must stay separate.

Collapsing them into a single "Generated" date meant re-rendering a preview six months later
restamped the run as today, and the footer went on asserting the page was built against a
brand-lock on a date that had nothing to do with the frames above it.

If the brand-lock on disk no longer hashes to what `run.json` recorded, say so on the page.
The reader is looking at frames built against a brand state they can no longer see.

## Examples

Generated `preview.html` files ship next to the storyboards that produced them:

- `../storyboard-architect/examples/30s-pain-proof-promise/preview.html`
- `../storyboard-architect/examples/60s-founder-explainer/preview.html`
- `../storyboard-architect/examples/shotkit-explainer/preview.html`, including the
  two-overlay shot
- `../visual-asset-critic/examples/worked-run/preview.html`, with frames and verdict badges

Open them in a browser to calibrate quality. All four are re-rendered in CI with pinned
timestamps and the build fails if the output moves, so they are also the regression test for
this skill's output.
