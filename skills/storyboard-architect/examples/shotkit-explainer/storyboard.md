# shotkit. The Explainer.

**Project:** shotkit explainer film
**Duration:** 90 seconds
**Aspect:** 16:9 (1280x720 hero render, 1080x1920 vertical cut for socials)
**Framework:** founder-explainer
**Brand-lock:** [brand-lock.snapshot.md](./brand-lock.snapshot.md) snapshotted 2026-05-08
**Generated:** 2026-05-08

## Brief

90-second explainer for shotkit. Targets founder-led brands at $500K to $5M ARR who run their own content and feel the prompt-engineering tax. Walks through the diagnosis (vague brief plus model-roulette equals brand drift), the methodology (five-layer prompt anatomy), the build moment (brief in, files out), the proof (rendered preview from a real shotkit run), and the install command. Lives at the top of the shotkit blog post on whystrohm.com.

## Series lock

| Field | Value |
|---|---|
| **Character** | No human subject. Typography-driven explainer with document-control aesthetic. |
| **Environment** | Operator-grade dashboard. Cream canvas, JetBrains Mono headers, Inter body, single coral accent per beat. |
| **Lighting** | Even diffuse. No shadow rolloff. Flat operator-doc grading throughout. |
| **Color grade** | Cream highlights (#F5F0E8), ink shadows (#2A2A32), coral (#D94F3A) reserved for signature beats. No saturation drift. |

## Shots

### shot_01: 0.0 to 12.0s. WS. eye-level. static.

**Beat:** pain. **Subject:** vague founder brief types into the left panel in JetBrains Mono. Cursor blinks. Then a chaos cut shows four image generators producing slightly off-brand outputs in a 2x2 grid. Each tile renders the same shot with a different palette, framing, font.
**On-screen text:** "You don't have a content problem. You have a pre-production problem." (Inter Black 900, center, fade)
**Rationale:** Cold open names the failure mode every founder recognizes. Vague brief plus model-roulette equals brand drift. The 2x2 grid does the work text cannot.

### shot_02: 12.0 to 30.0s. MS. eye-level. static.

**Beat:** reframe. **Subject:** Five horizontal layers stack from top to bottom. Each labeled in JetBrains Mono caps with 0.08em letter-spacing: brand lock, series lock, shot spec, text layer, generator adapter. Each layer slides in from below on a 6-frame stagger. Coral dot lands on brand lock as it appears.
**On-screen text:** "Five layers. Locked top to bottom." (Inter Black 900, upper-third, type-on)
**Rationale:** Architecture beat. The reader needs to see the layers exist before any claim about composability lands. Stack layout is the diagram doing the explanation.

### shot_03: 30.0 to 50.0s. MS. eye-level. push.

**Beat:** proof-1. **Subject:** Split panel. Left BRIEF column types out a brief slowly. Right OUTPUT column starts empty with a pulsing waiting dot, then file tree assembles row by row in JetBrains Mono Regular 16pt. storyboard.md, shots.json, text-overlays.json, brand-lock.snapshot.md, prompts/ directory with seven adapter files, preview.html. Coral dot lands on preview.html on completion.
**On-screen text:** "Brief in. Storyboard out. Audit trail included." (Inter Medium 500, upper-third, fade)
**Rationale:** The build moment is the centerpiece. Brief in, structured files out. Same animation language as the social demo so brand consistency reads across both surfaces.

### shot_04: 50.0 to 65.0s. MCU. eye-level. push.

**Beat:** proof-2. **Subject:** Coral wipe expands radially from the preview.html dot. Wipe reveals the rendered preview iframe scrolling vertically. The reader sees actual shot cards from the 30-second example pass through frame, including framing, angle, motion, color-grade rows. Subtle 10% vignette on edges.
**On-screen text:** "Files. Not panels. Not a SaaS dashboard." (Inter Black 900, lower-third, type-on)
**Rationale:** Reveal beat. The reader has now seen the methodology and the file outputs. The iframe shows the actual deliverable, not a mock.

### shot_05: 65.0 to 80.0s. MS. eye-level. static.

**Beat:** proof-3. **Subject:** Single shot description card sits center-frame. Seven generator adapter labels fan out radially around it. Midjourney, Flux, Ideogram, GPT Image, Nano Banana, Seedream, Runway/Sora. Lines connect center card to each adapter in 1px ink. Each adapter shows its prompt syntax appearing as a typewriter pass running simultaneously.
**On-screen text:** "One shot. Seven generators. One spec." (Inter Black 900, upper-third, fade)
**Rationale:** Cross-generator demonstration. Same shot description compiles to seven different prompt syntaxes simultaneously. The visual proves model-agnosticism is structural, not aspirational.

### shot_06: 80.0 to 90.0s. WS. eye-level. static.

**Beat:** promise. **Subject:** Full-frame typography. Install command appears via type-on in JetBrains Mono Regular at 22pt. Below it the project tagline in Inter italic 500 18pt, color muted. Coral period on the signature beat. Standard footer chrome holds.
**On-screen text:** "git clone github.com/whystrohm/shotkit / cd shotkit && ./install.sh" (JetBrains Mono, center, type-on) plus tagline "Pre-production for founder-led video at scale." (Inter italic 500, lower-third, fade).
**Rationale:** Promise beat. The viewer has the diagnosis, the architecture, the artifact, and the proof. The CTA is one paste-into-terminal command. No friction surface.

## Audit trail

- Brief, this document, scoped from the shotkit blog launch sequence.
- Brand-lock snapshotted from `brand-packs/whystrohm.md` on 2026-05-08.
- Shot list designed to compose with the existing ShotkitDemo composition (same chrome, complementary content, longer arc).
- Render shipped at [whystrohm.com/blog/you-dont-have-a-content-problem](https://whystrohm.com/blog/you-dont-have-a-content-problem) as the "we used shotkit to make this video" dogfood reveal.
- Landscape MP4 served from the blog: `/media/shotkit-explainer/shotkit-explainer.mp4`.
