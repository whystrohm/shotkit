# shotkit. Handoff to Claude Code

You are picking up an open-source skill pack mid-build. Read this entire file before touching anything. The work is 90% done; the remaining 10% is finishing touches and the launch. The previous build session ran in a constrained Claude.ai environment with read-only mounts; that's why this is being handed to you.

## What this is

`shotkit` is a four-skill Claude Skills pack for building production-grade storyboards. It's a lead magnet for WhyStrohm (whystrohm.com), a managed content infrastructure service. Apache 2.0. Targeting GitHub launch and a Reddit post in r/ClaudeAI.

The four skills:

1. `storyboard-architect`. Brief into structured storyboard.
2. `visual-prompt-forge`. Shot data into model-specific image prompts (7 generators).
3. `visual-asset-critic`. Generated image plus intent into structured critique.
4. `storyboard-html-preview`. Storyboard files into a single self-contained HTML preview.

## Who you're working for

Yuri Strohm (goes by Yurr). Motion Design and Narrative Visualization Specialist with a decade in defense systems engineering. Founder of WhyStrohm. Defense-grade systems thinker. Communicates casually, builds rigorously. Boston area, MassArt background.

His voice rules apply to everything in this repo:

- No em dashes anywhere. Use periods or commas.
- No emojis in copy or scripts.
- No bullet points in flowing prose.
- No hype words (revolutionary, game-changing, comprehensive, leverage, synergy, etc.).
- Specific numbers ("48 hours") not vague claims ("fast", "many videos").
- Operator language, not creator language. "Infrastructure" not "agency". "System" not "service".

If you find yourself wanting to write something the WhyStrohm brand-pack would reject, rewrite it.

## Repo location

When you receive the tarball, it should land somewhere like `~/Downloads/shotkit/` or wherever Yurr puts it. He'll likely move it to a new GitHub repo at `whystrohm/shotkit`.

## What's done (do not rebuild these)

### Top-level

- `README.md`. Launch front door. Just rewritten from scratch as the shotkit launch README.
- `LICENSE`. Apache 2.0.
- `CHANGELOG.md`. v0.1.0 release notes.
- `install.sh`. One-command install for Claude Code, brand-compliant (no emojis, no em dashes), tested working.
- `.gitignore`. Standard.

### CI

- `.github/workflows/validate-skills.yml`. Runs all three validators on PR and push.
- `.github/ISSUE_TEMPLATE/bug.md`. Bug report template.
- `.github/ISSUE_TEMPLATE/brand-pack-request.md`. Brand-pack contribution template.

### The four skills (ALL COMPLETE, ALL VALIDATING)

Each skill has a `SKILL.md` with proper YAML frontmatter (`name`, `description`). The descriptions are tuned for Claude's skill-selection mechanism. Don't rewrite the descriptions; they're load-bearing.

`skills/storyboard-architect/`
- `SKILL.md`. The main skill spec.
- `references/beat-frameworks.md`. PRP, Hero Trilogy, Founder Explainer, Content Spiral, Educational Demo, Custom.
- `references/shot-grammar.md`. Controlled vocabulary (framing, angle, motion, DOF).
- `references/timing-rules.md`. Pacing math, read-twice rule.
- `references/on-screen-text.md`. When text earns its keep.
- `templates/storyboard.md.tpl`. Handlebars-style template.
- `templates/shots.schema.json`. JSON Schema Draft 2020-12, $id points to shotkit.
- `templates/text-overlays.schema.json`. Same.
- `examples/30s-pain-proof-promise/`. Full output set INCLUDING rendered preview.html.
- `examples/60s-founder-explainer/`. Full output set INCLUDING rendered preview.html.

`skills/visual-prompt-forge/`
- `SKILL.md`.
- `adapters/midjourney.md` (v7).
- `adapters/flux.md` (Flux 2 Pro / 1.1 Pro / Schnell / Dev).
- `adapters/ideogram.md` (v3, with text-in-image override).
- `adapters/gpt-image.md` (1.5 / 2).
- `adapters/nano-banana.md` (Gemini 2.5 Flash Image).
- `adapters/seedream.md` (4.5 / 4.0).
- `adapters/runway-sora.md` (motion-aware).
- `references/prompt-anatomy.md`. The five-layer model.
- `references/consistency-locks.md`. Eight techniques for character/environment continuity.
- `references/failure-modes.md`. Seven common failures with prompt-level vs post-level fixes.
- `examples/one-shot-five-generators/README.md` plus `flux.txt` and `midjourney.txt`. Partial example.

`skills/visual-asset-critic/`
- `SKILL.md`. ACCEPT/REVISE/REJECT verdict pattern.
- `references/critique-rubric.md`. Six-layer rubric, hard/soft fail thresholds.

`skills/storyboard-html-preview/`
- `SKILL.md`.
- `templates/preview.html.tpl`. Handlebars-style HTML template. Already audited, two bugs fixed during build.
- `templates/styles.css.tpl`. Production CSS, brand-aware via {{COLOR}} variable substitution.
- `templates/print.css.tpl`. Print stylesheet that gets inlined into styles at compose time.

### Brand packs

- `brand-packs/_template.md`. Empty starter, all sections present.
- `brand-packs/whystrohm.md`. Real WhyStrohm flagship. Use as the canonical example.
- `brand-packs/examples/saas-clean.md`. Neutral B2B SaaS reference (Vercel/Linear/Stripe-style).
- `brand-packs/README.md`. Explains the pattern.

### Docs (5 of 8 originally planned exist; 3 went missing during build)

EXIST:
- `docs/why-this-exists.md`. The manifesto.
- `docs/the-five-layer-prompt.md`. Methodology in 600 words.
- `docs/audit-trail-pattern.md`. Defense-grade angle.
- `docs/remotion-bridge.md`. How `shots.json` maps to Remotion components (pointer doc, no implementation).
- `docs/connecting-to-generators.md`. Where shotkit stops, where the pipeline starts.

MISSING (need to be regenerated, see "Remaining Work" below):
- `docs/brand-lock-anatomy.md`
- `docs/claude-code-workflow.md`
- `docs/claude-ai-workflow.md`

Note that the README links to claude-code-workflow.md and claude-ai-workflow.md were just removed when the loss was discovered. If those docs come back, add the links back to the Compatibility section of README.md.

### Tools

- `tools/validate_skills.py`. Validates SKILL.md frontmatter and structure.
- `tools/validate_schemas.py`. Validates *.schema.json files are valid JSON Schema Draft 2020-12.
- `tools/validate_brand_lock.py`. Validates brand-lock files have required sections.
- `tools/shots-to-html.py`. Standalone CLI version of storyboard-html-preview skill. Already had a quote-escaping bug fixed during build.
- `tools/README.md`. How to use the tools.

All four tools work and have been tested. The shots-to-html.py tool requires absolute paths for `--out` parameter when output is going to a different folder than input.

## Validation status

Run this after any changes:

```bash
pip install pyyaml jsonschema
python tools/validate_skills.py
python tools/validate_schemas.py
python tools/validate_brand_lock.py brand-packs/whystrohm.md brand-packs/_template.md brand-packs/examples/saas-clean.md
```

As of handoff, all three validators pass on all files. Both example shots.json files validate against the schema. Both example text-overlays.json files validate against the schema.

## Critical bugs fixed during build (don't reintroduce)

1. **Quote-escaping in inline styles.** Both `templates/preview.html.tpl` and `tools/shots-to-html.py` had `style="font-family: ...; ..."` which broke when font names contained double quotes (e.g. `"PP Editorial"`). Fixed by switching to single-quoted attributes: `style='font-family: ...;'`. Don't change back.

2. **Template handlebars portability.** `preview.html.tpl` used `{{#if x}}/{{else}}/{{/if}}` for the placeholder fallback. The `{{else}}` clause isn't portable across template engines. Replaced with two parallel `{{#if has_image}}` and `{{#if has_no_image}}` blocks. The skill SKILL.md documents this convention.

3. **512 em dashes** were stripped from 41 files during a brand-compliance pass. If you regenerate any docs, do not write em dashes. Use periods or commas.

## Remaining work (the punch list)

In priority order.

### 1. Regenerate the three missing docs

These are referenced from the methodology and were originally written in this session but disappeared from disk before handoff. Voice and structure should match the existing five docs in `docs/`. Each should be roughly 100 to 200 lines.

**`docs/brand-lock-anatomy.md`**. Anatomy of a brand-lock file. Cover: identity (name, archetype, posture), palette (hex roles, exclusivity), typography (named fonts with weights, two-font max), mood adjectives (3-5, specific not generic), never list (specificity wins), aspect ratios, color grade, motion language, voice rules. Use `brand-packs/whystrohm.md` and `brand-packs/examples/saas-clean.md` as references.

**`docs/claude-code-workflow.md`**. Primary install target documentation. Cover: install via `./install.sh`, the user-scope vs project-scope distinction, how skills auto-discover from `~/.claude/skills/`, expected first-run behavior, how to compose skills with other Claude Code skills, file outputs landing in working directory.

**`docs/claude-ai-workflow.md`**. Web/desktop/mobile install. Cover: skill installation through Settings UI, file upload limits, session expectations, downloading the output files. Different mechanics than Claude Code; same skills.

When done, re-add the links to README.md under the Compatibility section. The pattern is:

```markdown
- **Claude.ai** (web, mobile, desktop). All four skills via `.skill` zip uploads. See [`docs/claude-ai-workflow.md`](docs/claude-ai-workflow.md).
- **Claude Code** (CLI). Primary target. See [`docs/claude-code-workflow.md`](docs/claude-code-workflow.md).
```

### 2. Build the visual-prompt-forge example completion

`skills/visual-prompt-forge/examples/one-shot-five-generators/` currently has a README and only two adapter files (`flux.txt`, `midjourney.txt`). The directory name says "five-generators" but in the README, the intent was to show the same shot rendered across all seven adapter formats. Either:

- Add the missing five files: `ideogram.txt`, `gpt-image.txt`, `nano-banana.txt`, `seedream.txt`, `runway-sora.txt`. Use the same source shot (the `shot_03` reframe from the 30s-pain-proof-promise example). Apply each adapter pattern from `skills/visual-prompt-forge/adapters/{name}.md`.
- Or rename the directory to match what's actually there (`one-shot-two-generators`) and update the README. Less work, but the seven-adapter example is more impressive for a launch.

Recommendation: do all seven. It's a strong showpiece for the README and Reddit post.

### 3. Run the full preflight before launch

```bash
# Verify install works on a clean slate
mkdir -p /tmp/shotkit-test && cd /tmp/shotkit-test
cp -R /path/to/shotkit/* .
./install.sh
# Expected: four [install] lines, no errors

# Verify renders work
python tools/shots-to-html.py skills/storyboard-architect/examples/30s-pain-proof-promise/ --out /tmp/test-30.html
python tools/shots-to-html.py skills/storyboard-architect/examples/60s-founder-explainer/ --out /tmp/test-60.html
# Expected: each writes a ~25KB HTML file

# Open in a browser
open /tmp/test-30.html
open /tmp/test-60.html
# Expected: clean rendering, no broken styles, brand colors visible

# Print preview both
# Expected: clean PDF, one shot per page-ish, brand colors converted appropriately
```

### 4. Pre-launch GitHub setup

When pushing to `github.com/whystrohm/shotkit`:

- Settings: enable Issues
- Settings: set repository description to "The pre-production system we use to ship hundreds of videos a month. Open-sourced."
- Add topics: `claude`, `claude-skills`, `storyboard`, `pre-production`, `video-production`, `ai-workflow`, `creative-tools`
- Set main as default branch
- Verify the GitHub Actions workflow runs green on first push (pyyaml and jsonschema install, then three validators run)

### 5. The Reddit post (when ready)

Yurr will write this in his voice. The angle to support:

- "I built shotkit, the storyboard skill pack we use internally to ship hundreds of videos a month. Open-sourcing it."
- Subreddits: r/ClaudeAI primary. Possibly r/Anthropic, r/MachineLearning (selectively), r/programming if the methodology framing lands.
- Don't post in r/Entrepreneur. The pack is technical; that audience isn't.
- The honest boundary statement ("free methodology, paid pipeline") is a feature. Don't bury it.

Linkable artifacts when posting:
- The repo: github.com/whystrohm/shotkit
- The 30s example preview rendered: link directly to `examples/30s-pain-proof-promise/preview.html` after pushing
- The five-layer prompt doc: `docs/the-five-layer-prompt.md`

## Architectural notes worth knowing

### Why this isn't bigger

The original plan flirted with adding ElevenLabs API integration, fal.ai integration, a brand-lock extractor, PDF/PPTX exporters, asset folder support, and duration rescale. All cut from v0.1.0 deliberately. They're listed as v0.2.0 roadmap in README.md. Don't add them now; ship the lead magnet first, gather feedback, then expand.

### Why "shotkit" as the name

Two-syllable, six-letter. "Shot" anchors the film/video domain. "Kit" matches Anthropic's "skill pack" tonal space without copying it. Extensible: future siblings could be `voicekit`, `renderkit`. Repo URL `whystrohm/shotkit` reads as a real product.

### Why skills keep their original names

The pack is `shotkit`. The skills inside (`storyboard-architect`, `visual-prompt-forge`, etc.) are individually named for what they do. Skills should be named functionally. The kit is the brand.

### Why no API integration

The pack's job is methodology, not pipeline. If the pack hard-codes API integration, it churns every time a generator API changes. By stopping at prompts and specs, the pack stays stable across the generator landscape (which currently shifts monthly). The commercial WhyStrohm offering wires it up; the lead magnet does not. This is the same pattern as media-tsunami.

### Why on-screen text is composited, never in prompts

Even Ideogram (best at text-in-image) produces text that lags professional design tools in 2026. Composited text is editable, animatable, brand-typeface-accurate. The skill enforces this: text content never enters image prompts (Ideogram Mode 2 is the only override, and it requires explicit rationale flag).

### Why the brand-lock snapshot pattern matters

Defense-grade audit trail. Six months from now, someone needs to know what brand state a given storyboard was generated against. The snapshot file is frozen, the storyboard references it, the trail is bidirectional. This is the most distinctive methodology in the pack and worth understanding before touching anything brand-related.

## Final inventory

```
60 files, ~8,000 lines

shotkit/
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── brand-pack-request.md
│   │   └── bug.md
│   └── workflows/validate-skills.yml
├── brand-packs/
│   ├── README.md
│   ├── _template.md
│   ├── examples/saas-clean.md
│   └── whystrohm.md
├── docs/
│   ├── audit-trail-pattern.md
│   ├── connecting-to-generators.md
│   ├── remotion-bridge.md
│   ├── the-five-layer-prompt.md
│   └── why-this-exists.md
│   [MISSING: brand-lock-anatomy.md, claude-code-workflow.md, claude-ai-workflow.md]
├── skills/
│   ├── storyboard-architect/
│   │   ├── SKILL.md
│   │   ├── examples/
│   │   │   ├── 30s-pain-proof-promise/ (5 files including preview.html)
│   │   │   └── 60s-founder-explainer/ (5 files including preview.html)
│   │   ├── references/ (4 files)
│   │   └── templates/ (3 files)
│   ├── storyboard-html-preview/
│   │   ├── SKILL.md
│   │   └── templates/ (3 files)
│   ├── visual-asset-critic/
│   │   ├── SKILL.md
│   │   └── references/critique-rubric.md
│   └── visual-prompt-forge/
│       ├── SKILL.md
│       ├── adapters/ (7 files)
│       ├── examples/one-shot-five-generators/ (3 files, needs 5 more)
│       └── references/ (3 files)
├── tools/
│   ├── README.md
│   ├── shots-to-html.py
│   ├── validate_brand_lock.py
│   ├── validate_schemas.py
│   └── validate_skills.py
├── CHANGELOG.md
├── LICENSE
├── README.md
├── install.sh
└── .gitignore
```

## Quick orientation commands

```bash
# Read the README first
cat README.md

# See the methodology
cat docs/the-five-layer-prompt.md

# See the example output
ls skills/storyboard-architect/examples/30s-pain-proof-promise/
open skills/storyboard-architect/examples/30s-pain-proof-promise/preview.html

# Run validators
python tools/validate_skills.py
python tools/validate_schemas.py
python tools/validate_brand_lock.py brand-packs/whystrohm.md

# See the WhyStrohm flagship brand pack
cat brand-packs/whystrohm.md
```

You are inheriting a clean handoff. Don't second-guess decisions that are documented here. Finish the punch list, run the preflight, and ship.
