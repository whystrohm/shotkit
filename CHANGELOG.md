# Changelog

All notable changes to shotkit are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), versioning follows [SemVer](https://semver.org/).

## [Unreleased]

The QA loop closes: the critic now emits a machine-readable verdict, the prompt-forge can act on it, and the capability matrix is guarded so it can't silently rot.

### Added

- **Structured critique output.** `visual-asset-critic` now writes `output/critique.json` alongside the markdown critique, conforming to `skills/visual-asset-critic/templates/critique.schema.json`. A pipeline can gate on the verdict instead of parsing prose.
- **`tools/validate_critique.py`.** Validates a `critique.json` against the schema **and** enforces the gating invariant JSON Schema cannot express: any `blocking` issue forces `REJECT`, any `major` issue forbids `ACCEPT`. `--selftest` proves the gate fires (and runs in CI).
- **Generator capability matrix.** `skills/visual-prompt-forge/adapters/_capabilities.json` is the single source of truth for per-generator limits (`max_prompt_words`, `supports_text_render`, `supports_motion`, `aspect_param`, ...), with a companion `capabilities.schema.json`.
- **`tools/validate_capabilities.py`.** Schema-validates the matrix, enforces adapter-to-capability parity (every generator id has an adapter file and vice versa), and warns when an entry is past its freshness window.
- **Revision mode in `visual-prompt-forge`.** Consumes a `critique.json` and re-emits prompts for only the non-ACCEPT shots, branching on each issue's `fix_type` (prompt-level / re-roll / post-level). This is what closes the QA loop, and it stays file-native, no generator API calls.
- **Motion video lineup (fal.ai):** `kling` (default), `veo` (dialogue/lipsync + native audio), `seedance` (multi-shot sequences), `hailuo` (budget iteration) adapters, each with a capability entry.
- **Worked critique fixtures:** `skills/visual-asset-critic/examples/critique.accept.json` and `critique.revise.json`, exercised by CI.
- **shots schema v1.1:** optional `shot.assets` (source/generated frames) and a top-level `meta` passthrough. Backward compatible, every valid v1.0 file is a valid v1.1 file (verified against all bundled examples).
- **New doc** [`docs/the-qa-loop.md`](docs/the-qa-loop.md), the closed review loop end to end: critic verdict to revision to re-critique.

### Changed

- `shots.schema.json` bumped to v1.1 (additive, backward compatible).
- Adapter `.md` files now defer to `_capabilities.json` for numeric limits, the JSON owns the numbers, the prose owns the how-to-prompt guidance. Conflicts resolve to the JSON.
- `install.sh` hardened: array-based execution instead of `eval`, errors to stderr, added `--help`.
- CI runs the two new validators, including the critique-gate selftest.

### Removed

- **`runway-sora` adapter and its capability entry.** Sora was discontinued; the motion lane moved to the fal.ai models the kit actually uses (Kling / Veo / Seedance / Hailuo). Swapping it was one capability-matrix edit and four adapter files, the model-agnostic design working as intended.

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
