# Changelog

All notable changes to shotkit are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), versioning follows [SemVer](https://semver.org/).

## [0.1.0], 2026-05-08

Initial public release.

### The four skills

- **`storyboard-architect`**. Brief into structured storyboard. Produces `storyboard.md`, `shots.json`, `text-overlays.json`, and `brand-lock.snapshot.md`. Validates against schemas. Per-shot rationale on every output.
- **`visual-prompt-forge`**. Shot data into model-specific prompts. Adapters for Midjourney v7, Flux 2 Pro, Ideogram v3, GPT Image 1.5/2, Nano Banana (Gemini 2.5 Flash Image), Seedream 4.5, and Runway/Sora.
- **`visual-asset-critic`**. Generated image plus intent into structured critique. ACCEPT, REVISE, or REJECT verdict with concrete prompt-level or post-level fixes.
- **`storyboard-html-preview`**. Storyboard files into a single self-contained HTML preview. No external dependencies. Brand-aware. Prints clean.

### Brand-pack pattern

- Brand-lock template (`brand-packs/_template.md`)
- WhyStrohm flagship example (`brand-packs/whystrohm.md`)
- Neutral B2B SaaS example (`brand-packs/examples/saas-clean.md`)

### Tooling

- One-line install for Claude Code (`install.sh`)
- Three validation scripts (frontmatter, JSON schemas, brand-lock structure)
- Standalone HTML renderer (`tools/shots-to-html.py`)
- GitHub Actions workflow runs all validators on every PR

### Documentation

- `docs/why-this-exists.md`. The manifesto.
- `docs/the-five-layer-prompt.md`. The methodology.
- `docs/audit-trail-pattern.md`. Why brand-lock snapshots matter.
- `docs/connecting-to-video-pipelines.md`. How `shots.json` maps to a programmatic video framework.
- `docs/connecting-to-generators.md`. Where shotkit stops, where the pipeline starts.

### Worked examples

- 30-second pain-reframe-promise founder explainer (full output set)
- 60-second founder explainer (full output set)
- One shot rendered across all 7 generator adapters (`visual-prompt-forge/examples/`)

### Schemas

- `shots.schema.json` (v1.0)
- `text-overlays.schema.json` (v1.0)

### Compatibility

- Tested on Claude Opus 4.7 and Claude Sonnet 4.6
- Works in Claude.ai, Claude Code, Claude API
- Compatible with the SKILL.md open standard (Codex, Cursor, Gemini CLI, Antigravity, Windsurf, not officially tested)

### Known v0.2.0 work

- `brand-lock-extractor` skill (PDF/image/URL into brand-lock.md)
- PDF and PPTX exporters
- User-supplied asset folder convention
- Duration-rescale workflow with beat-aware redistribution
