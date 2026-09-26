# Changelog

All notable changes to shotkit are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), versioning follows [SemVer](https://semver.org/).

## [Unreleased]

`VERSION` stays at 3.0.0 until this is tagged. An install from a git clone also records the
exact checkout on line 2 of `~/.claude/shotkit-tools/VERSION`.

### Added

- `contracts/`: the canonical schemas for files the WhyStrohm skills share through a `brand/`
  folder. First one: `voice-profile.v1.schema.json`, written by whystrohm-voice-extract and read
  by whystrohm-voice-scorer. `tools/validate_contracts.py` checks each schema and its example,
  and `--against <repo>` checks another repo's copy is byte-identical. `check.sh` runs it.
- `VERSION` at the repo root. `install.sh` writes it to `~/.claude/shotkit-tools/VERSION`, and
  `storyboard-architect` reads it for `run.json`'s `shotkit_version`.
- `NOTICE`, and a line in the README License section on the Shotkit and WhyStrohm names.
- `--no-web-fonts` on `tools/shots-to-html.py`.
- `# covers:` lines in prompt files, for a multi-shot sequence that renders several shots in
  one block.
- Optional `project.seed` in `shots.json` and `run.json`.
- `semibold` (600) in the overlay weight enum.
- 15-second timings in the beat frameworks and timing rules.
- `rack` in the shot-grammar motion table, so all eleven motion values are explained.
- Selftests for `validate_skills.py` and `validate_schemas.py`.

### Changed

- Every `SKILL.md` names the installed paths first, `~/.claude/shotkit-tools/` and
  `~/.claude/shotkit-brand-packs/`, with the repo paths after them.
- `tools/check.sh` runs from a clone or from `~/.claude/shotkit-tools/`, from any folder.
- `validate_skills.py`, `validate_schemas.py` and `validate_brand_lock.py --snapshots` look at
  the five shotkit skills only.
- `validate_provenance.py --require-accept` counts a shot with no critique as outstanding. Its
  summary line gives the shot count and how many were reviewed.
- The preview splits a brand-lock font value into a quoted family, a weight and a width, takes
  the mono font from the brand-lock, and links the brand fonts from Google Fonts with a system
  fallback. A dark brand's ground is its page background, as Rule 4 now says.
- Every adapter writes parameters on a `# params:` line under the block header.
  `validate_prompts.py` explains the old form when it sees it, and checks a shot's
  `environment_ref` or `lighting_ref` override in place of the series anchor.
  `copy-prompt.py --list` names params lines, fix notes and variant lines separately.
- Nano Banana moves to Gemini 3.1 Flash Image (Nano Banana 2), and its word ceiling goes from
  120 to 160 so the four verbatim series anchors leave room for the shot.
- `brand-packs/whystrohm.md` is version 2.0: dark ground `#07080A`, ink `#F6F5F2`, Signal
  `#E4552A`, Archivo and IBM Plex Mono, with the install film's motion and voice rules. The
  bundled examples stay on pack 1.0, the look their shots and frames were built on.
- `run.json` has one rule: everything except `rounds` is written once, and `rounds` is
  append-only.
- Narrower triggers for `storyboard-html-preview`, `visual-prompt-forge` and
  `storyboard-architect`.
- Plain, true statements in the README, docs, skills and examples: no volume or cadence
  figures, no price, no personal credential lines, and model support stated without a tested
  version. media-tsunami is described by what it writes, and brand-lock generation points at
  `brand-lock-extractor`.
- The CHANGELOG and release notes describe each version by what it does.

### Removed

- The v0.1.0 explainer videos and the `shotkit-explainer` example storyboard. The README links
  the install film on whystrohm.com.
- `AUDIT-v2.md` and `.archive/`, internal notes.

## [3.0.0] - 2026-07-30

An audit trail you can check rather than one you have to trust.

Every input, prompt and reviewed frame is pinned by content hash, the output tree is addressed
by round and shot so concurrent work never lands on the same path, and the validators run
against a real project as well as against this repo.

**Breaking.** The output directory layout changed, and the layout is the public interface.

| Before | Now |
|---|---|
| `output/critique.json` | `output/critiques/round-{N}/{shot_id}.critique.json` |
| `output/prompts/{generator}.txt` | `output/prompts/round-{N}/{generator}.txt` |
| `output/prompts/revised-{generator}.txt` | `output/prompts/round-{N}/revised-{generator}.txt` |
| `output/generated/{shot_id}.png` | `output/frames/round-{N}/{shot_id}.png` |

Existing trees still read: the tools fall back to `generated/` and to a root `critique.json`,
and critique schema `1.0` documents still validate with a warning. Nothing auto-migrates.

### Upgrading from v2.0.0

Update the install with `git pull` and `./install.sh`. The validators install to
`~/.claude/shotkit-tools/` and need `pip install pyyaml jsonschema`. New runs write the new
layout. A v2.0.0 output tree stays where it is until you move it.

**What still reads as it is.**

- `tools/shots-to-html.py` finds frames in `generated/` and shows the verdict from a root
  `critique.json`. With no `run.json` it warns and prints "not recorded" for the run date.
- `tools/validate_prompts.py` reads flat `prompts/*.txt` when there are no `round-N/`
  directories. It warns that each header has no `# Run:` and no `# Round:` line.
- `tools/validate_critique.py` accepts a critique with `version` `1.0` and warns that it
  carries no run id, no round, and no hashes.

**What a v2.0.0 tree has to add.**

- `tools/validate_provenance.py` requires a `run.json`, so a tree with nothing pinned cannot
  pass a gate. It looks for frames under `frames/round-N/`, so move frames out of
  `generated/` to have them checked against their critiques.
- `tools/validate_shots.py` checks timing, gaps, overlaps, overlay references, and overlay
  colors against the brand-lock palette. It also requires a `critique_ref` on any
  `assets.generated` entry marked `accepted: true`. A v2.0.0 storyboard may need edits to pass.

**Moving a tree by hand.** Work in this order. Each hash has to be taken after its file stops
changing, so edit first and hash last.

1. Move each frame from `generated/{shot_id}.png` to `frames/round-N/{shot_id}.png`, where N is
   the round whose prompt file produced it. With no revision pass, that is round 1.
2. Move `prompts/{generator}.txt` to `prompts/round-1/` and `prompts/revised-{generator}.txt`
   to `prompts/round-2/`. Add `# Run: {run_id}` and `# Round: N` to each header now.
3. Fix `shots.json` until `validate_shots.py` passes. Repoint any `assets.generated` paths
   from `generated/` to `frames/round-N/`, and give each `accepted: true` entry a
   `critique_ref` or remove the flag.
4. Write `run.json` to `skills/storyboard-architect/templates/run.schema.json`. It needs a
   `run_id` (`YYYYMMDDTHHMMSSZ-` plus 8 hex characters, with the timestamp equal to
   `created_at`), `shotkit_version`, `project`, the SHA-256 of `shots.json`,
   `text-overlays.json`, and `brand-lock.snapshot.md`, and one `rounds` entry per prompt round
   with each prompt file's hash. `shasum -a 256` prints the hashes.
5. Move the critique. v2.0.0 wrote every review to the same `critique.json`, so it holds the
   last review only. Move it to `critiques/round-N/{shot_id}.critique.json`, then run
   `visual-asset-critic` on every other frame. The critic writes schema `1.1` with the frame,
   prompt, and brand-lock hashes. A moved `1.0` critique passes with a warning and ties to no
   bytes.

**Confirm.** Run the four validators against the moved tree:

```bash
python ~/.claude/shotkit-tools/validate_shots.py output/
python ~/.claude/shotkit-tools/validate_prompts.py output/
python ~/.claude/shotkit-tools/validate_critique.py output/
python ~/.claude/shotkit-tools/validate_provenance.py output/ --require-accept
```

The last one exits 0 only when every recorded hash matches the file on disk, every frame has a
critique for its round, and every shot's latest verdict is `ACCEPT`. Drop `--require-accept` to
check the chain without the verdict gate. A hash mismatch right after a migration means a file
changed after you hashed it. Recompute that hash.

### Added

- **`run.json`.** Records a `run_id`, a `created_at` instant, and a SHA-256 for `shots.json`,
  `text-overlays.json`, and `brand-lock.snapshot.md` as written, plus the generators targeted
  and a per-round record of prompt files with their hashes. Schema at
  `skills/storyboard-architect/templates/run.schema.json`. This is the file that turns a
  storyboard's name references into provable ones.
- **`tools/validate_provenance.py`.** Walks an output tree and recomputes every recorded hash.
  Catches a frame regenerated after its critique, a brand-lock edited mid-project, a frame with
  no critique for its round, two critiques for the same shot in the same round, skipped rounds,
  and a critique carrying another run's id. `--require-accept` makes it the pipeline stop
  condition; `--json` emits a machine-readable report. Its `--selftest` builds each of those
  failures from the bundled worked run.
- **`tools/validate_shots.py`.** Validates `shots.json` and `text-overlays.json` as instances:
  `end` after `start`, no duplicate ids, no gaps, no overlaps, span matching
  `project.duration_s`, overlay references resolving in both directions, every overlay
  reachable from some shot, overlay timing inside its shot window, and every overlay color
  present in the brand-lock palette.
- **Critique schema `1.1`.** Adds `run_id`, `round`, `created_at`, `image_sha256`,
  `prompt_ref`, `prompt_sha256`, `brand_lock_sha256`, `generator`, `model_version`, `seed`, and a
  `meta` passthrough. Every provenance field is required and nullable: `null` records that an
  input was unavailable, a missing key records nothing.
- **`tools/validate_prompts.py`.** Validates the prompt files the forge writes: header
  completeness, generator id, aspect agreement, the `max_prompt_words` ceiling, shot coverage,
  duplicate blocks, and the forge's two hard rules. Rule 1, no on-screen text copy inside a
  prompt. Rule 3, `environment` / `lighting` / `color_grade` appearing verbatim, with the
  character anchor as a warning since a shot with no person can omit it. Rule 3 is what keeps a
  series consistent, and it is the rule a fluent writer is most likely to paraphrase.
- **`tools/check.sh`.** One entry point for every check, called by CI, so a green local run
  means a green PR. It preflights `pyyaml` and `jsonschema` and prints one install command.
- **A `--selftest` on every validator.** Each builds failing fixtures and fails if the check
  does not catch them. `validate_critique.py` runs fourteen cases.
- **Worked run example** at `skills/visual-asset-critic/examples/worked-run/`: two shots through
  two rounds with real hashes, per-round prompts and frames, one critique per shot per round, and
  a rendered preview with verdict badges.
- **`run.json` for the bundled storyboard examples.**
- **Verdict badges in the HTML preview**, read from the critique tree.
- **`tools/_shotkit.py` and `tools/_template.py`**, shared internals for hashing, brand-lock
  parsing, output-tree conventions, and the template engine.

### Changed

- **The critique gate has a threshold.** Three or more `major` issues force `REJECT`, matching
  `critique-rubric.md`.
- **Revision mode stops on `REJECT`.** It lists the rejected shots and asks, since a REJECT
  means no fix path exists.
- **`post-level`-only shots are recorded on disk** in `run.json`'s `post_only_shots`, so the
  compositing work is written down.
- **`tools/shots-to-html.py` renders the skill's own template** through `_template.py`, so the
  CLI and the skill share one `preview.html.tpl`.
- **Every interpolated value in the preview is HTML-escaped**, so model-written prose cannot
  change the page structure.
- **The preview shows a run date and a render date, separately**, so re-rendering a page never
  restamps the run.
- **The preview reads `brand_lock_ref` from `shots.json`**, resolves frames from `shot.assets`
  before the path convention, and reads fonts from the brand-lock.
- **`shots.json` `on_screen_text` accepts an array** (schema `1.2`), so a shot can carry several
  overlays, as `text-overlays.json` always allowed.
- **`shot.assets.generated` entries carry `sha256`, `round`, `prompt_ref`, `prompt_sha256`, and
  `critique_ref`** (schema `1.2`). `accepted: true` requires a `critique_ref`.
- **`tools/validate_capabilities.py` compares the adapter prose to the matrix.** Word budgets
  sit inside `max_prompt_words`, and each adapter documents the `aspect_param` the matrix names.
- **`tools/validate_critique.py` accepts a directory** and enforces provenance coupling: a hash
  needs its path, `image_ref` cannot be null, and `HIGH` confidence needs an identified prompt.
- **`tools/validate_brand_lock.py` gained `--snapshot` and `--require-configured`.** The
  snapshot header is checked, and an unfilled template fails as a production brand-lock.
- **`tools/copy-prompt.py` reads revision files.** A block is found by its shot id, and comment
  lines inside a block are annotations, shown but never copied.
- **`install.sh` installs `tools/` and `brand-packs/`** to `~/.claude/shotkit-tools/` and
  `~/.claude/shotkit-brand-packs/`, so the paths the skills cite exist after an install.
  `--uninstall` removes all three. It skips `.DS_Store`, and `--help` prints plain usage.
- **CI calls `tools/check.sh`** and re-renders every bundled preview with a pinned timestamp,
  failing if a byte moves.
- **`critique-rubric.md` maps pass/soft/hard onto `minor`/`major`/`blocking`** and defers to the
  gate table.
- **`nano-banana` `aspect_param` is `aspectRatio`**, the name its API expects.
- **`midjourney` `max_prompt_words` is 100** and **`gpt-image` is 300**, matching their adapters.
  `max_prompt_words` is documented as a ceiling, with the adapter range as the target.
- **Font names in a brand-lock go in backticks** immediately after the label, in every pack,
  template and example.
- **Docs match the tree:** skill and adapter counts, what the schema and the validators each
  enforce, and `brand-lock-extractor` listed as shipped. A monthly price in
  `connecting-to-generators.md` now points at the live offer.

### Fixed

- Overlay reachability and palette membership in the bundled examples.
- The snapshot headers in the bundled examples carry a full UTC instant.
- A table row in `critique-rubric.md`.
- `SKILL.md` for the preview lists the previews where they live.
- `brand-packs/examples/saas-clean.md` typography parses.

### Not in this release

- **An approval log.** `run.json` records what was built and reviewed. Who approved it, and
  when, is not recorded.
- **Worked examples for Veo, Seedance, or Hailuo** in `one-shot-all-adapters/`. Each has a
  prompt example in its adapter file.
- **Deterministic application of `fix` strings.** The forge and critic apply English `fix`
  strings by judgement. The file formats are deterministic; the edit in between is a model
  reading a sentence.
- **A migration tool for v2.0.0 output trees.** The tools read the old layout; they do not
  move it.

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

The `v2.0.0` tag points at `39c2227`. The next commit, `673ee99`, added the full Apache-2.0
`LICENSE` text and refreshed `demo.gif`, so `LICENSE` at that tag is the short-form notice.
Fetch `main` for the complete licence. `v0.1.0` has no tag.

### Planned after 0.1.0

Recorded at the time. Of these, `brand-lock-extractor` shipped in 2.0.0. The other three are
still on the roadmap.

- `brand-lock-extractor` skill (PDF/image/URL into brand-lock.md)
- PDF and PPTX exporters
- User-supplied asset folder convention
- Duration-rescale workflow with beat-aware redistribution
