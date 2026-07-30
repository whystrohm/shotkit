# Changelog

All notable changes to shotkit are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), versioning follows [SemVer](https://semver.org/).

## [3.0.0] - Unreleased

An audit trail you can check rather than one you have to trust.

v2.0.0 shipped a QA loop where every artifact had a single fixed path and every reference was a
filename. Both held until someone regenerated a frame, edited a brand-lock mid-project, or ran
the loop at the same time as a colleague. This release fixes the layout and adds the hashes,
then makes validators run against a real project instead of only against this repo.

**Breaking.** The output directory layout changed, and the layout is the public interface.

| Before | Now |
|---|---|
| `output/critique.json` | `output/critiques/round-{N}/{shot_id}.critique.json` |
| `output/prompts/{generator}.txt` | `output/prompts/round-{N}/{generator}.txt` |
| `output/prompts/revised-{generator}.txt` | `output/prompts/round-{N}/revised-{generator}.txt` |
| `output/generated/{shot_id}.png` | `output/frames/round-{N}/{shot_id}.png` |

Existing trees still read: the tools fall back to `generated/` and to a root `critique.json`,
and critique schema `1.0` documents still validate with a warning. Nothing auto-migrates.

### Added

- **`run.json`, written once per run.** Records a `run_id`, a `created_at` instant, and a
  SHA-256 for `shots.json`, `text-overlays.json`, and `brand-lock.snapshot.md` as written, plus
  the generators targeted and a per-round record of prompt files with their hashes. Schema at
  `skills/storyboard-architect/templates/run.schema.json`. This is the file that turns a
  storyboard's name references into provable ones.
- **`tools/validate_provenance.py`.** Walks an output tree and recomputes every recorded hash.
  Catches a frame regenerated after its critique, a brand-lock edited mid-project, a frame with
  no critique for its round, two critiques for the same shot in the same round, skipped rounds,
  and a critique carrying another run's id. `--require-accept` makes it the pipeline stop
  condition; `--json` emits a machine-readable report. Its `--selftest` builds each of those
  failures from the bundled worked run and fails if any goes uncaught.
- **`tools/validate_shots.py`.** The first instance validator in the repo. `shots.json` and
  `text-overlays.json` had schemas and no way to check a file against them, so every rule lived
  in a SKILL.md as a checkbox. It now enforces: `end` after `start`, no duplicate ids, no gaps,
  no overlaps, span matching `project.duration_s`, overlay references resolving in both
  directions, every overlay reachable from some shot, overlay timing inside its shot window, and
  every overlay color present in the brand-lock palette.
- **Critique schema `1.1`.** Adds `run_id`, `round`, `created_at`, `image_sha256`,
  `prompt_ref`, `prompt_sha256`, `brand_lock_sha256`, `generator`, `model_version`, `seed`, and a
  `meta` passthrough. Every provenance field is required and nullable: `null` records that an
  input was unavailable, a missing key records nothing. `additionalProperties: false` with no
  `meta` previously made it impossible to add provenance without a schema bump.
- **`tools/validate_prompts.py`.** Validates the prompt files the forge writes: header
  completeness, generator id, aspect agreement, the `max_prompt_words` ceiling, shot coverage,
  duplicate blocks, and the forge's two hard rules. Rule 1, no on-screen text copy inside a
  prompt. Rule 3, `environment` / `lighting` / `color_grade` appearing verbatim, with the
  character anchor as a warning since a shot with no person can omit it.

  Rule 3 is the reason this exists. Series consistency depends on those anchors landing
  unedited in every prompt, and it is the easiest rule in the kit to break, because
  paraphrasing an anchor is what writing good prose feels like. Driving the pipeline through a
  real seven-shot brief drifted on it in all seven shots with every other validator green. The
  `worked-run` fixture shipped earlier in this release had drifted on it too.
- **`tools/check.sh`.** One entry point for all eighteen checks, called by CI, so a green local
  run means a green PR. It preflights `pyyaml` and `jsonschema` and prints one install command,
  rather than failing every check with the same message.
- **A `--selftest` on every validator.** Each constructs failing fixtures and fails if the check
  does not catch them. `validate_critique.py` now runs fourteen cases, up from two.
- **Worked run example** at `skills/visual-asset-critic/examples/worked-run/`: two shots through
  two rounds with real hashes, per-round prompts and frames, one critique per shot per round, and
  a rendered preview with verdict badges. The provenance mechanism ships with something to check.
- **`run.json` for all three bundled storyboard examples**, so they model the current standard.
- **Verdict badges in the HTML preview**, read from the critique tree.
- **`tools/_shotkit.py` and `tools/_template.py`**, shared internals for hashing, brand-lock
  parsing, output-tree conventions, and the template engine.

### Changed

- **The critique gate has a threshold instead of discretion.** Three or more `major` issues now
  force `REJECT`. It read "escalate to REJECT at your discretion," which disagreed with
  `critique-rubric.md`, which called three hard fails a REJECT outright.
- **Revision mode stops on `REJECT`.** It treated every non-ACCEPT shot identically, so a verdict
  meaning "no fix path exists" got a re-emitted prompt with the fix applied. It now lists the
  rejected shots and asks.
- **`post-level`-only shots are recorded on disk** in `run.json`'s `post_only_shots`. Saying it in
  chat left the compositing obligation nowhere once the critique was overwritten.
- **`tools/shots-to-html.py` renders the actual template.** It built HTML inline while
  `tools/README.md` claimed it shared `preview.html.tpl` with the skill. It now renders that
  template through `_template.py`.
- **Every interpolated value in the preview is HTML-escaped.** Subjects, rationales, VO lines,
  and overlay fonts went in raw; one angle bracket in a rationale broke the page.
- **The preview shows a run date and a render date, separately.** A single "Generated" date meant
  re-rendering a preview restamped the run as today, over a footer asserting what brand-lock it
  was built against.
- **The preview reads `brand_lock_ref` from `shots.json`** instead of hardcoding
  `brand-lock.snapshot.md`, resolves frames from `shot.assets` before falling back to the path
  convention, and reads fonts from the brand-lock instead of hardcoding Inter.
- **`shots.json` `on_screen_text` accepts an array** (schema `1.2`). `text-overlays.json` always
  allowed several overlays per shot while `shots.json` allowed one id, so the second overlay on a
  shot rendered nowhere and nothing reported it.
- **`shot.assets.generated` entries carry `sha256`, `round`, `prompt_ref`, `prompt_sha256`, and
  `critique_ref`** (schema `1.2`). `accepted: true` with no `critique_ref` is now an error: an
  approval with no source.
- **`tools/validate_capabilities.py` compares the adapter prose to the matrix.** Word budgets have
  to sit inside `max_prompt_words`, and each adapter has to document the `aspect_param` the matrix
  names. Both rules were stated in all ten adapters and enforced nowhere.
- **`tools/validate_critique.py` accepts a directory** and enforces provenance coupling: a hash
  without its path, a null `image_ref`, or `HIGH` confidence with an unidentified prompt now fail.
- **`tools/validate_brand_lock.py` gained `--snapshot` and `--require-configured`.** The snapshot
  header that `storyboard-architect` promises to write is now checked, and an unfilled template no
  longer passes as a production brand-lock.
- **`tools/copy-prompt.py` reads revision files.** Its regex required the shot id immediately
  after `#`, and the documented revision header led with "Revision of", so it found no shot blocks
  at all in the one file an operator pastes from most. Comment lines inside a block are now
  annotations, shown but never copied.
- **`install.sh` installs `tools/` and `brand-packs/`** to `~/.claude/shotkit-tools/` and
  `~/.claude/shotkit-brand-packs/`. The skills cite `tools/validate_critique.py` and
  `tools/copy-prompt.py`, and `storyboard-architect` falls back to `brand-packs/_template.md`
  when no brand-lock is given. None of those paths existed after an install. `--uninstall`
  removes all three. It also stops copying `.DS_Store` into the skills directory, and `--help`
  no longer prints a line of shell.
- **CI calls `tools/check.sh`** and re-renders every bundled preview with a pinned timestamp,
  failing if a byte moves. That is the determinism claim, tested.
- **`critique-rubric.md` maps pass/soft/hard onto `minor`/`major`/`blocking`** and defers to the
  gate table. It graded checks and never mentioned severity, which is the field the gate runs on.
- **`nano-banana` `aspect_param` corrected to `aspectRatio`.** The matrix said `aspect_ratio`
  while the adapter documented `aspectRatio`, and the precedence rule meant the wrong one won on
  every prompt.
- **`midjourney` `max_prompt_words` raised to 100** to match its own note, and **`gpt-image` to
  300** to match its adapter's stated range. `max_prompt_words` is now documented as a ceiling
  with the adapter range as the recommended target.
- **Font names in a brand-lock go in backticks** immediately after the label. Two packs did this
  and the extractor's template and example did not, so its own worked example was unreadable to
  the tools it claims to feed.
- **Docs corrected against the tree:** `the-qa-loop.md` said four skills, `connecting-to-generators.md`
  said seven adapters, `brand-lock-anatomy.md` said the schema enforced palette membership when
  nothing did, `audit-trail-pattern.md` claimed the spec-to-artifact link while listing it as an
  unshipped extension, and `README.md` listed `brand-lock-extractor` as roadmap in the release
  that shipped it. A monthly price committed in `connecting-to-generators.md` now points at the
  live offer instead.

### Fixed

- **`text_07` in the `shotkit-explainer` example was unreachable.** It attached to `shot_06`,
  which pointed at `text_06`, so no renderer showed it. Both are now listed and both render.
- **An off-palette overlay color in the same example.** `#6B6B73` was not in that project's
  brand-lock; it is now `#7A7580`, the palette's Muted.
- **The `shotkit-explainer` snapshot header** carried a bare date where the other two carried a
  full instant. Normalised to the commit instant the file entered the repo.
- **A broken table row in `critique-rubric.md`** (a stray comma as the aspect-ratio soft-fail cell).
- **`skills/storyboard-html-preview/examples/`** was an empty untracked directory that `SKILL.md`
  described as containing generated previews. Removed; the previews are listed where they live.
- **`brand-packs/examples/saas-clean.md` typography** did not parse, which would have silently
  rendered its previews in a fallback font.

### Known gaps

Named rather than left to be discovered:

- **No approval log.** `run.json` records what was built and reviewed. Who approved it, and when,
  is not recorded anywhere.
- **The explainer video and demo GIF are v0.1.0** and still show Runway/Sora.
  `remotion/src/ShotkitExplainer.tsx` is deliberately left matching the artifact it produced; both
  are labelled in `remotion/README.md` and `README.md`.
- **No worked example for Veo, Seedance, or Hailuo** in `one-shot-all-adapters/`. Each has a prompt
  example in its adapter file.
- **The forge and critic still apply English `fix` strings by judgement.** The file formats no
  longer fight determinism, but the edit in between is a model reading a sentence.
- **Nothing auto-migrates a v2.0.0 output tree.** The tools read the old layout; they do not move it.

## [2.0.0] - 2026-06-18

The QA loop closes: the critic now emits a machine-readable verdict, the prompt-forge can act on it, and the capability matrix is guarded so it can't silently rot.

### Added

- **`brand-lock-extractor` skill (fifth skill).** Point it at a website URL, brand book PDF, screenshots, or a written description and it produces a validate-ready `brand-lock.md` in the nine-section format, with a confidence and source flagged for every value. Kills the blank-template cold-start. Ships with an extraction rubric and a worked example (input assets plus the extracted brand-lock with audit trail).
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
- Regenerated `docs/images/social-preview.png` from a new versioned `SocialPreview` Remotion composition (it was a sourceless baked PNG). The card now reads v2.0.0 and reflects what shipped: `critique.json`, the revise loop (CRITIQUE to FORGE), and brand-lock-extractor feeding the brand-lock bar. The demo.gif and explainer videos are unchanged.

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
- Three validation scripts at the time (frontmatter, JSON schemas, brand-lock structure)
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

## Release notes

The `v2.0.0` tag points at `39c2227`, one commit behind the branch tip. The commit it excludes,
`673ee99`, completed the Apache-2.0 `LICENSE` text and refreshed `demo.gif`, so `LICENSE` at the
tag is the short-form notice rather than the full text. Fetch `main` rather than the tag for the
complete license. `v0.1.0` was never tagged.

### Planned after 0.1.0

Recorded at the time. Of these, `brand-lock-extractor` shipped in 2.0.0; the other three had
not shipped as of 3.0.0.

- `brand-lock-extractor` skill (PDF/image/URL into brand-lock.md)
- PDF and PPTX exporters
- User-supplied asset folder convention
- Duration-rescale workflow with beat-aware redistribution
