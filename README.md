# shotkit

**The pre-production system we use to ship 800+ videos a month. Open-sourced.**

Four Claude Skills that turn a creative brief into a production-grade storyboard with model-specific image prompts, on-screen text specs, an HTML preview, and a versioned audit trail. Built by [WhyStrohm](https://whystrohm.com). Apache 2.0.

```bash
git clone https://github.com/whystrohm/shotkit.git
cd shotkit && ./install.sh
```

That installs all four skills into `~/.claude/skills/`. Restart your Claude Code session and they're live.

---

## What it does

You describe a video. The kit produces a complete pre-production package:

```
output/
├── storyboard.md              # Human-readable, shot-by-shot
├── shots.json                 # Schema-validated, machine-readable
├── text-overlays.json         # On-screen text + timing
├── brand-lock.snapshot.md     # Frozen brand state at generation time
├── prompts/                   # Per-generator prompts, copy-paste ready
│   ├── midjourney.txt
│   ├── flux.txt
│   ├── ideogram.txt
│   ├── gpt-image.txt
│   ├── nano-banana.txt
│   ├── seedream.txt
│   └── runway-sora.txt
└── preview.html               # Single file. Shareable. Printable. Brand-aware.
```

Files. Not panels. Not a SaaS dashboard. Files an editor, agency, or developer can act on without asking follow-up questions.

---

## The four skills

| Skill | What it does |
|---|---|
| `storyboard-architect` | Brief → structured storyboard (`storyboard.md` + `shots.json`) |
| `visual-prompt-forge` | Shot data → model-specific prompts for 7 generators |
| `visual-asset-critic` | Generated image + intent → structured critique |
| `storyboard-html-preview` | Storyboard files → single-file shareable HTML |

They work alone. They work better together. They work in **Claude Code**, **Claude.ai**, and the **Claude API**.

---

## Why this exists

Every storyboard tool on the market is a SaaS app with a UI you log into. You upload a brief, you get illustrated panels, you export. The output never leaves the platform.

That's not how serious teams work. Serious teams want:

- **Files**, not cloud-locked panels
- **Audit trail**, not vibes. Every shot has rationale, every prompt is reproducible, every brand parameter is versioned.
- **Brand lock**, not "AI reads your URL". Explicit brand parameters that compose deterministically across every shot.
- **Model agnosticism**. Prompts adapt to whichever image generator you're using this month.
- **No vendor lock-in**. Markdown, JSON, HTML. Open formats only.

shotkit is what we use internally at WhyStrohm to ship 800+ videos from code. We're publishing the methodology because the methodology isn't the moat. The operator is.

Read more in [`docs/why-this-exists.md`](docs/why-this-exists.md).

---

## Why this isn't another storyboard tool

The category isn't empty. It's full of tools that solve the wrong half.

- **Brand-lock snapshots.** Every storyboard freezes brand state at run time. Six months later, you can still answer "what brand version was this approved against." None of the SaaS tools do this.
- **Seven generators, one spec.** The same shot data adapts to Midjourney, Flux, Ideogram, GPT Image, Nano Banana, Seedream, and Runway/Sora. Every other storyboard skill on GitHub locks to one generator family.
- **Files, not panels.** The output is structured Markdown and JSON an editor, motion designer, or developer can act on. No dashboard, no export step, no platform.
- **Methodology over pipeline.** The pack stops at prompts and specs. Generator APIs churn monthly, the methodology stays stable. The pipeline lives where it belongs, in the operator's tooling.

---

## 60-second example

Drop this into a Claude Code session with the skills installed:

> *"30-second founder explainer for WhyStrohm. We help founder-led brands build content infrastructure instead of running content like a hobby. Pain-reframe-promise. Use `brand-packs/whystrohm.md` as the brand lock. Aspect 9:16."*

Claude produces the full `output/` set. Open `output/preview.html` in any browser. Print it. Share it. Hand it to an editor.

A complete worked example lives at [`skills/storyboard-architect/examples/30s-pain-proof-promise/`](skills/storyboard-architect/examples/30s-pain-proof-promise/). Clone the repo and open `preview.html` in that folder to see what the deliverable looks like.

---

## The methodology

Four ideas. None negotiable.

**1. Five-layer prompt anatomy.** Every image prompt is composed from locked layers: Brand Lock, Series Lock, Shot Spec, Text Layer, Generator Adapter. Change a brand color once. Every prompt updates. See [`docs/the-five-layer-prompt.md`](docs/the-five-layer-prompt.md).

**2. Versioned brand state.** Every storyboard run snapshots the brand-lock file it was built against. Brand changes later? You can see exactly what version this storyboard targeted. Defense-grade audit trail applied to commercial output. See [`docs/audit-trail-pattern.md`](docs/audit-trail-pattern.md).

**3. Text never gets baked into images.** On-screen copy is a separate layer with its own timing, font, and animation spec. Always composited after generation. AI text rendering is not production-ready in 2026; treat text as a separate compositing pass.

**4. Per-shot rationale.** Every shot has a `rationale` field. Why this beat. Why this duration. Why this framing. Why this on-screen text. Decisions are logged so they can be challenged.

---

## Brand packs

A brand pack is a single Markdown file that locks palette, typography, voice, and visual rules for a project. Three live in this repo:

- [`brand-packs/_template.md`](brand-packs/_template.md). Empty starter.
- [`brand-packs/whystrohm.md`](brand-packs/whystrohm.md). Flagship example, real WhyStrohm brand.
- [`brand-packs/examples/saas-clean.md`](brand-packs/examples/saas-clean.md). Neutral B2B SaaS reference.

Roll your own from the template. Or generate one from existing brand assets with [media-tsunami](https://github.com/whystrohm/media-tsunami), WhyStrohm's open-source brand voice extractor.

See [`brand-packs/README.md`](brand-packs/README.md) for the full pattern.

---

## Where this stops, where the pipeline starts

shotkit produces **specs and prompts**, not rendered images or videos. The boundary is deliberate:

- **In scope.** The methodology, the structure, the prompts, the audit trail.
- **Out of scope.** API integrations to fal.ai or ElevenLabs, the Remotion render pipeline, automated publishing, the 48-hour content cycle.

If you want the version where this is wired into a Remotion pipeline with automated publishing across multiple brands: [whystrohm.com](https://whystrohm.com). The methodology is open. The operator is paid.

See [`docs/connecting-to-generators.md`](docs/connecting-to-generators.md) for how teams typically wire it up themselves, and [`docs/remotion-bridge.md`](docs/remotion-bridge.md) for how `shots.json` maps to Remotion props.

---

## Compatibility

- **Claude.ai** (web, mobile, desktop). All four skills via `.skill` zip uploads. See [`docs/claude-ai-workflow.md`](docs/claude-ai-workflow.md).
- **Claude Code** (CLI). Primary target. Drop the repo and run `./install.sh`. See [`docs/claude-code-workflow.md`](docs/claude-code-workflow.md).
- **Claude API**. All four skills via Skills API.
- **Other agents** that support the SKILL.md open standard (Codex, Cursor, Gemini CLI, Antigravity, Windsurf) should work, not officially tested.

Tested against Claude Opus 4.7 and Claude Sonnet 4.6.

---

## Roadmap

v0.1.0 ships the four core skills, the brand-pack pattern, and the methodology docs. Known v0.2.0 work:

- **`brand-lock-extractor`**. Upload a brand book (PDF, screenshots, URL), get a `brand-lock.md` back. The cold-start killer.
- **PDF + PPTX exporters**. Siblings to `storyboard-html-preview` for client review and agency handoff.
- **User-supplied asset folder**. Slot in your own images per shot instead of placeholders or AI-generated frames.
- **Duration rescale workflow**. Change a project from :30 to :60 and have the timing redistribute correctly across the beat framework.

If any of these are blocking for you, open an issue. Real use cases jump the queue.

---

## Contributing

PRs welcome for:

- New generator adapters (`skills/visual-prompt-forge/adapters/`)
- New beat frameworks (`skills/storyboard-architect/references/beat-frameworks.md`)
- Brand pack examples (`brand-packs/examples/`)

Open an issue first for anything that changes the file schemas. Run validators locally before opening a PR:

```bash
pip install pyyaml jsonschema
python tools/validate_skills.py
python tools/validate_schemas.py
python tools/validate_brand_lock.py brand-packs/_template.md
```

CI runs all three on every PR.

---

## License

Apache 2.0. See [LICENSE](LICENSE).

---

## Who built this

[Yuri Strohm](https://whystrohm.com). Motion Design and Narrative Visualization Specialist at RTX BBN Technologies, founder of WhyStrohm. A decade of defense-adjacent design work informs how I build content systems: deterministic, auditable, no surprises.

If you want the version where this is wired into a Remotion pipeline with automated publishing: [whystrohm.com](https://whystrohm.com).

- GitHub: [@whystrohm](https://github.com/whystrohm)
- Web: [whystrohm.com](https://whystrohm.com)
