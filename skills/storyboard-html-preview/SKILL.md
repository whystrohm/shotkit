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
├── storyboard.md              # input
├── shots.json                 # input
├── text-overlays.json         # input
├── brand-lock.snapshot.md     # input
└── preview.html               # ← what this skill produces
```

If the user has generated images (`output/generated/shot_01.png`, etc.), the HTML references them via relative paths so the file works when the whole `output/` folder is shared.

If no generated images exist yet, the HTML uses styled placeholder cards with the prompt text and shot spec, still useful for review and handoff.

## Workflow

### Step 1. Read inputs

Required:

- `shots.json`
- `text-overlays.json`
- `brand-lock.snapshot.md`

Optional:

- `storyboard.md` (for narrative context, surface the brief at the top)
- `output/generated/shot_NN.{png,jpg}` (if image generation has happened)

If shots.json doesn't validate against the schema, stop and tell the user.

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

### Step 4. Embed images if available

If `output/generated/shot_NN.{png,jpg}` files exist, the HTML references them via relative path:

```html
<img src="generated/shot_01.png" alt="Shot 01: hook beat" />
```

This works when the whole output folder is zipped and shared.

For hard-copy print (single file with no folder structure), the skill can offer to inline images as base64. Ask the user which they prefer if generated images are present.

If no images exist, render styled placeholder cards showing the framing, subject, and prompt summary. These are still useful for stakeholder review at the storyboard stage.

**Template flag convention.** When composing the per-shot context for `preview.html.tpl`, set exactly one of:

- `has_image: true` and `image_path: "generated/shot_NN.png"`, when a generated image exists
- `has_no_image: true`, when no generated image exists (renders the placeholder card)

The template uses two parallel `{{#if}}` blocks rather than `{{#if}}/{{else}}` to keep the rendering portable across template engines.

For text overlays, set `on_screen_text: true` (boolean flag) plus the resolved overlay fields (`overlay_content`, `overlay_position`, `overlay_size`, `overlay_font`, `overlay_weight`, `overlay_color`, `overlay_enter_at`, `overlay_enter_anim`, `overlay_exit_at`) when the shot has an `on_screen_text` reference in `shots.json`. Otherwise omit the flag.

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
- [ ] Brand colors appear (palette references work)
- [ ] Every shot from `shots.json` is present
- [ ] Every text overlay from `text-overlays.json` is rendered
- [ ] Brand-lock snapshot reference appears in footer
- [ ] Audit timestamp appears

## Examples

`examples/` contains generated `preview.html` files for the storyboard-architect example projects. Open them in a browser to calibrate quality.
