/* ─────────────────────────────────────────────────────────────
   Storyboard HTML Preview · WhyStrohm
   Single-file output. No external deps. Prints clean.
   ───────────────────────────────────────────────────────────── */

:root {
  /* Brand-lock variables, get substituted at compose time */
  --sb-color-bg: {{BG_COLOR}};
  --sb-color-ink: {{INK_COLOR}};
  --sb-color-accent: {{ACCENT_COLOR}};
  --sb-color-muted: {{MUTED_COLOR}};
  --sb-color-rule: {{RULE_COLOR}};

  --sb-font-display: {{DISPLAY_FONT}}, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --sb-font-body: {{BODY_FONT}}, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --sb-font-mono: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;

  --sb-radius: 6px;
  --sb-pad: 24px;
  --sb-gap: 32px;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

html { scroll-behavior: smooth; }

body {
  font-family: var(--sb-font-body);
  font-size: 16px;
  line-height: 1.55;
  color: var(--sb-color-ink);
  background: var(--sb-color-bg);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

a {
  color: var(--sb-color-accent);
  text-decoration: none;
  border-bottom: 1px solid currentColor;
}

code {
  font-family: var(--sb-font-mono);
  font-size: 0.9em;
  background: var(--sb-color-rule);
  padding: 1px 6px;
  border-radius: 3px;
}

h1, h2, h3 {
  font-family: var(--sb-font-display);
  font-weight: 800;
  line-height: 1.15;
  letter-spacing: -0.01em;
}

/* ─── Header ─── */

.sb-header {
  border-bottom: 1px solid var(--sb-color-rule);
  padding: 64px var(--sb-pad) 40px;
}

.sb-header-inner {
  max-width: 960px;
  margin: 0 auto;
}

.sb-eyebrow {
  font-family: var(--sb-font-mono);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--sb-color-muted);
  margin-bottom: 16px;
}

.sb-title {
  font-size: clamp(32px, 5vw, 56px);
  margin-bottom: 32px;
}

.sb-meta {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 16px;
  font-size: 14px;
}
.sb-meta div { display: flex; flex-direction: column; gap: 2px; }
.sb-meta dt {
  font-family: var(--sb-font-mono);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--sb-color-muted);
}
.sb-meta dd { font-weight: 600; }

/* ─── Nav ─── */

.sb-nav {
  position: sticky;
  top: 0;
  background: var(--sb-color-bg);
  border-bottom: 1px solid var(--sb-color-rule);
  z-index: 10;
  overflow-x: auto;
}

.sb-nav ul {
  display: flex;
  gap: 4px;
  list-style: none;
  max-width: 960px;
  margin: 0 auto;
  padding: 12px var(--sb-pad);
}

.sb-nav a {
  display: inline-block;
  padding: 4px 10px;
  font-family: var(--sb-font-mono);
  font-size: 12px;
  border: 1px solid var(--sb-color-rule);
  border-radius: var(--sb-radius);
  color: var(--sb-color-ink);
  white-space: nowrap;
}

.sb-nav a:hover {
  background: var(--sb-color-accent);
  color: var(--sb-color-bg);
  border-color: var(--sb-color-accent);
}

/* ─── Sections ─── */

.sb-section {
  max-width: 960px;
  margin: 0 auto;
  padding: 56px var(--sb-pad);
  border-bottom: 1px solid var(--sb-color-rule);
}

.sb-section h2 {
  font-size: 14px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--sb-color-muted);
  margin-bottom: 24px;
}

.sb-brief p {
  font-size: clamp(18px, 2.5vw, 24px);
  line-height: 1.45;
  max-width: 700px;
}

/* ─── Series lock ─── */

.sb-series-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 24px;
}

.sb-series-grid > div {
  border-left: 2px solid var(--sb-color-accent);
  padding-left: 14px;
}

.sb-series-grid dt {
  font-family: var(--sb-font-mono);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--sb-color-muted);
  margin-bottom: 4px;
}

.sb-series-grid dd {
  font-size: 15px;
  line-height: 1.5;
}

/* ─── Shots ─── */

.sb-shots {
  background: var(--sb-color-bg);
}

.sb-shot {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: var(--sb-gap);
  padding: 40px 0;
  border-bottom: 1px solid var(--sb-color-rule);
  scroll-margin-top: 60px;
}

.sb-shot:last-child { border-bottom: none; }

.sb-shot-frame {
  position: relative;
  width: 100%;
  background: var(--sb-color-rule);
  border-radius: var(--sb-radius);
  overflow: hidden;
}

.sb-shot-frame.aspect-9-16 { aspect-ratio: 9 / 16; }
.sb-shot-frame.aspect-16-9 { aspect-ratio: 16 / 9; }
.sb-shot-frame.aspect-1-1  { aspect-ratio: 1 / 1; }
.sb-shot-frame.aspect-4-5  { aspect-ratio: 4 / 5; }
.sb-shot-frame.aspect-21-9 { aspect-ratio: 21 / 9; }

.sb-shot-frame img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.sb-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: linear-gradient(135deg, var(--sb-color-rule) 0%, var(--sb-color-bg) 100%);
  color: var(--sb-color-muted);
}

.sb-placeholder-id {
  font-family: var(--sb-font-mono);
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 0.05em;
}

.sb-placeholder-meta {
  font-family: var(--sb-font-mono);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

/* On-screen text overlay preview (rendered over the frame) */
.sb-overlay {
  position: absolute;
  left: 0; right: 0;
  padding: 0 16px;
  pointer-events: none;
}

.sb-overlay-center        { top: 50%; transform: translateY(-50%); text-align: center; }
.sb-overlay-lower-third   { bottom: 12%; text-align: center; }
.sb-overlay-upper-third   { top: 12%; text-align: center; }
.sb-overlay-left-third    { top: 50%; transform: translateY(-50%); text-align: left; }
.sb-overlay-right-third   { top: 50%; transform: translateY(-50%); text-align: right; }

.sb-overlay-text {
  display: inline-block;
  font-size: clamp(14px, 2.2vw, 22px);
  line-height: 1.1;
  text-shadow: 0 2px 8px rgba(0,0,0,0.4);
}

/* ─── Shot body ─── */

.sb-shot-body { display: flex; flex-direction: column; gap: 20px; }

.sb-shot-header {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: baseline;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--sb-color-rule);
}

.sb-shot-id {
  font-family: var(--sb-font-mono);
  font-size: 16px;
  font-weight: 700;
  color: var(--sb-color-accent);
}

.sb-shot-time {
  font-family: var(--sb-font-mono);
  font-size: 13px;
  color: var(--sb-color-muted);
}

.sb-shot-beat {
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-weight: 600;
  color: var(--sb-color-muted);
  margin-left: auto;
}

.sb-shot-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  font-size: 13px;
}

.sb-shot-meta div { display: flex; flex-direction: column; gap: 2px; }
.sb-shot-meta dt {
  font-family: var(--sb-font-mono);
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--sb-color-muted);
}
.sb-shot-meta dd { font-weight: 600; }

.sb-shot-subject h3,
.sb-shot-vo h3,
.sb-shot-text h3,
.sb-shot-rationale h3 {
  font-family: var(--sb-font-mono);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--sb-color-muted);
  margin-bottom: 6px;
  font-weight: 600;
}

.sb-shot-subject p,
.sb-shot-vo p,
.sb-shot-rationale p {
  font-size: 15px;
  line-height: 1.55;
}

.sb-shot-vo p {
  font-style: italic;
  color: var(--sb-color-muted);
}

.sb-text-content {
  font-family: var(--sb-font-display);
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 4px;
}

.sb-text-meta {
  font-family: var(--sb-font-mono);
  font-size: 11px;
  color: var(--sb-color-muted);
}

.sb-shot-rationale {
  background: var(--sb-color-rule);
  padding: 14px 16px;
  border-radius: var(--sb-radius);
  border-left: 3px solid var(--sb-color-accent);
}

.sb-shot-rationale p {
  font-size: 14px;
  font-style: italic;
}

/* ─── Footer ─── */

.sb-footer {
  padding: 40px var(--sb-pad);
  background: var(--sb-color-rule);
  font-size: 12px;
  color: var(--sb-color-muted);
}

.sb-footer-inner {
  max-width: 960px;
  margin: 0 auto;
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 16px;
}

/* ─── Responsive ─── */

@media (max-width: 720px) {
  .sb-shot {
    grid-template-columns: 1fr;
    gap: 20px;
    padding: 28px 0;
  }
  .sb-section { padding: 40px var(--sb-pad); }
  .sb-header { padding: 48px var(--sb-pad) 28px; }
}

/* ─── Print ─── */
{{INLINE_PRINT_CSS}}
