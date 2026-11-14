# Background and reference

Longer material that used to sit in the README: why Shotkit exists, how a run goes round, the method, brand packs, the other WhyStrohm tools, what it runs on and what is planned.

## Why this exists

Every storyboard tool on the market is a SaaS app with a UI you log into. You upload a brief, you get illustrated panels, you export. The output never leaves the platform.

That's not how serious teams work. Serious teams want:

- **Files**, not cloud-locked panels
- **Audit trail**, not vibes. Every shot has rationale, every prompt is reproducible, every brand parameter is versioned.
- **Brand lock**, not "AI reads your URL". Explicit brand parameters that compose deterministically across every shot.
- **Model agnosticism**. Prompts adapt to whichever image generator you're using this month.
- **No vendor lock-in**. Markdown, JSON, HTML. Open formats only.

shotkit is the pre-production method WhyStrohm uses on its own work. We're publishing the methodology because the methodology isn't the moat. The operator is.

Read more in [`docs/why-this-exists.md`](./why-this-exists.md).

---

## Why this isn't another storyboard tool

The category isn't empty. It's full of tools that solve the wrong half.

- **Provenance you can check, not just claim.** Every run freezes brand state and records a content hash for every input, prompt, and reviewed frame. Six months later you can answer "what brand version was this built against" and *prove* the files have not moved since, because `validate_provenance.py` recomputes the hashes. A frame regenerated after its review fails that check instead of passing quietly on a stale ACCEPT.
- **Ten generators, one spec.** The same shot data adapts to six stills generators (Midjourney, Flux, Ideogram, GPT Image, Nano Banana, Seedream) and four motion-video models (Kling, Veo, Seedance, Hailuo). Every other storyboard skill on GitHub locks to one generator family.
- **Files, not panels.** The output is structured Markdown and JSON an editor, motion designer, or developer can act on. No dashboard, no export step, no platform.
- **Methodology over pipeline.** The plan, the prompts and the checks are the product. Generation is optional and uses your own key. Generator APIs churn monthly, the methodology stays stable. The pipeline lives where it belongs, in the operator's tooling.

---

## 60-second example

Drop this into a Claude Code session with the skills installed:

> *"30-second founder explainer for WhyStrohm. We help founder-led brands build content infrastructure instead of running content like a hobby. Pain-reframe-promise. Use `brand-packs/whystrohm.md` as the brand lock. Aspect 9:16."*

Claude produces the full `output/` set. Open `output/preview.html` in any browser. Print it. Share it. Hand it to an editor.

A complete worked example lives at [`skills/storyboard-architect/examples/30s-pain-proof-promise/`](../skills/storyboard-architect/examples/30s-pain-proof-promise/). Clone the repo and open `preview.html` in that folder to see what the deliverable looks like.

---

## Round-trip workflow

The complete loop, idea to revised image:

1. **Brief** describes the video.
2. **`storyboard-architect`** produces `run.json`, `storyboard.md`, `shots.json`, `text-overlays.json`, `brand-lock.snapshot.md`.
3. **`visual-prompt-forge`** writes a prompt file per generator under `output/prompts/round-1/`.
4. **`tools/copy-prompt.py`** pipes one shot's prompt to the clipboard. Paste into the generator UI.
5. **The generator** returns an image. It goes in `output/frames/round-1/shot_NN.png`.
6. **`visual-asset-critic`** scores the frame against the shot spec and brand-lock, writing `critiques/round-1/shot_NN.critique.json` with the hash of the frame, the prompt, and the brand-lock it judged.
7. **`tools/validate_provenance.py`** re-checks every hash and reports which shots are still open.
8. On REVISE, **`visual-prompt-forge` revision mode** re-emits prompts for only those shots into `round-2/`. On REJECT, it stops and asks: a REJECT means no fix path exists.
9. Repeat from 5 until `--require-accept` exits 0. It exits 0 only when every shot in
   `shots.json` has a critique and every latest verdict is ACCEPT.

```bash
~/.claude/shotkit-tools/sk validate_provenance.py output/ --require-accept || echo "work remains"
# from a repo clone: tools/sk validate_provenance.py output/ --require-accept
```

Files at every step. See [`docs/the-qa-loop.md`](./the-qa-loop.md) for the full loop and
[`skills/visual-asset-critic/examples/worked-run/`](../skills/visual-asset-critic/examples/worked-run/)
for a worked two-round example: every file and hash in place, with stand-in frames.

---

## The methodology

Four ideas. None negotiable.

**1. Five-layer prompt anatomy.** Every image prompt is composed from locked layers: Brand Lock, Series Lock, Shot Spec, Text Layer, Generator Adapter. Change a brand color once. Every prompt updates. See [`docs/the-five-layer-prompt.md`](./the-five-layer-prompt.md).

**2. Versioned brand state, pinned by hash.** Every run snapshots the brand-lock it was built against and records its SHA-256 in `run.json`. Brand changes later? The snapshot stays frozen, and if someone overwrites it, the hash mismatch says so. A filename alone never proved anything, which is the whole reason the hashes are there. See [`docs/audit-trail-pattern.md`](./audit-trail-pattern.md).

**3. Text never gets baked into images.** On-screen copy is a separate layer with its own timing, font, and animation spec. Always composited after generation. AI text rendering is not production-ready in 2026; treat text as a separate compositing pass.

**4. Per-shot rationale.** Every shot has a `rationale` field. Why this beat. Why this duration. Why this framing. Why this on-screen text. Decisions are logged so they can be challenged.

---

## Brand packs

A brand pack is a single Markdown file that locks palette, typography, voice, and visual rules for a project. Three live in this repo:

- [`brand-packs/_template.md`](../brand-packs/_template.md). Empty starter.
- [`brand-packs/whystrohm.md`](../brand-packs/whystrohm.md). Flagship example, the real WhyStrohm brand: dark ground, one accent, Archivo and IBM Plex Mono.
- [`brand-packs/examples/saas-clean.md`](../brand-packs/examples/saas-clean.md). Neutral B2B SaaS reference.

Roll your own from the template. Or generate one from a site, a brand book or screenshots with the `brand-lock-extractor` skill in this repo.

See [`brand-packs/README.md`](../brand-packs/README.md) for the full pattern.

---

## Companion tools

shotkit is part of a broader WhyStrohm open-source ecosystem of brand-infrastructure tools:

- [media-tsunami](https://github.com/whystrohm/media-tsunami)
  brand voice extraction. Writes a CLAUDE.md and a
  brand-config.json from a site.
- [whystrohm-audit](https://github.com/whystrohm/whystrohm-audit)
  content audit against a 5-layer framework.
- [whystrohm-voice-extract](https://github.com/whystrohm/whystrohm-voice-extract)
  structured voice profile from any URL.
- [whystrohm-voice-scorer](https://github.com/whystrohm/whystrohm-voice-scorer)
  voice drift between site and social content.
- [digital-twin](https://github.com/whystrohm/digital-twin-of-yourself)
  personal voice as system prompt.
- [ritual](https://github.com/whystrohm/ritual)
  drafts a Claude Code routine from your own work history.

The voice tools and shotkit work side by side. A voice profile from media-tsunami or
whystrohm-voice-extract is a good source for a brand-lock's voice rules. The brand-lock file
itself comes from `brand-lock-extractor` or the template.

The skills connect through shared file formats in a `brand/` folder in your project, not through
one big repo. This repo holds the canonical schemas in [`contracts/`](../contracts/):
`brand/voice-profile.json` (voice-extract writes it, voice-scorer reads it),
`brand/audit-findings.json` (whystrohm-audit writes it, `storyboard-architect` can take it as
a brief input) and `brand/foundrkit.rules.json` (foundrkit-lint builds it from the brand folder
and lints against it).

For the operated version of the full pipeline, see [whystrohm.com](https://whystrohm.com).

---

## Compatibility

- **Claude.ai** (web, mobile, desktop). All five skills via `.skill` zip uploads. See [`docs/claude-ai-workflow.md`](./claude-ai-workflow.md).
- **Claude Code** (CLI). Primary target. Drop the repo and run `./install.sh`. See [`docs/claude-code-workflow.md`](./claude-code-workflow.md).
- **Claude API**. All five skills via Skills API.
- **Other agents** that support the SKILL.md open standard (Codex, Cursor, Gemini CLI, Antigravity, Windsurf) should work, not officially tested.

Built for current Claude models (Opus, Sonnet).

---

## Roadmap

v3.0.0 makes the audit trail checkable: content hashes on every input and reviewed frame, an
output tree addressed by round and shot so concurrent work cannot overwrite itself, and
validators that run against a real project instead of only against the repo. See the
[changelog](../CHANGELOG.md). Still on the roadmap:

- **PDF + PPTX exporters**. Siblings to `storyboard-html-preview` for client review and agency handoff.
- **Approval log**. `run.json` records what was built and reviewed, not who signed it off. Approver identity and timestamp is the missing link for regulated handoffs.
- **Duration rescale workflow**. Change a project from :30 to :60 and have the timing redistribute correctly across the beat framework.
- **Worked examples for the motion adapters**. `one-shot-all-adapters/` covers the six stills generators plus Kling; Veo, Seedance, and Hailuo have prompt examples in their adapter files but no side-by-side entry.
- **A CLI or MCP surface**, so the pipeline runs outside Claude-skill hosts.

If any of these are blocking for you, open an issue. Real use cases jump the queue.

---
