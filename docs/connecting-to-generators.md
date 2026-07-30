# Connecting to Generators

This skill pack stops at the prompt. It produces structured shots, model-specific prompt files, on-screen text specs, and audit-rich preview artifacts. It does not run any image or video generators on your behalf. It does not call any API.

This is deliberate. This doc explains why, and how to wire up the generator side yourself.

## The boundary

```
       brief
         │
         ▼
   storyboard-architect ──▶ shots.json
                            │
                            ▼
                  visual-prompt-forge ──▶ prompts/round-1/midjourney.txt
                                          prompts/round-1/flux.txt
                                          prompts/round-1/ideogram.txt
                                          prompts/round-1/gpt-image.txt
                                          prompts/round-1/nano-banana.txt
                                          prompts/round-1/seedream.txt
                                          prompts/round-1/kling.txt
                                          prompts/round-1/veo.txt
                                          prompts/round-1/seedance.txt
                                          prompts/round-1/hailuo.txt

      ◀────── this is where the skill pack stops ──────▶

                  YOU                                ──▶ generated images
                  (or your generator API of choice)      generated video
                                                        VO files
                                                        final composite
```

Everything to the left of that line is the methodology. Everything to the right is the pipeline. The pack is the methodology, distributed openly. The pipeline is the work.

## Why this boundary

**Methodology is stable. Pipelines are not.** Generators churn monthly. Flux 2 Pro replaced Flux 1.1 Pro in months. Seedream 4.5 dropped right after 4.0. Nano Banana joined the Gemini family. Sora was discontinued outright and Kling, Veo, and Seedance took the motion lane. If the pack hard-coded any specific API integration, half of it would be broken every quarter. (When the Sora adapter died, swapping in the new motion lineup was a single capability-matrix edit and four adapter files, exactly the point.)

**The methodology survives generator change.** A prompt file produced for Flux today is still a usable prompt for whatever replaces Flux. The shot structure in `shots.json` is generator-agnostic. The brand-lock is generator-agnostic. Only the adapter layer touches generator-specific syntax, and adapters are the easiest layer to update.

**Open methodology, paid pipeline.** This is the WhyStrohm thesis. The methodology is what we publish. The operated pipeline (running generators, managing rendering, publishing) is what WhyStrohm offers commercially. Current scope and pricing live at [whystrohm.com](https://whystrohm.com).

## How to wire up image generation

The ten adapters in `visual-prompt-forge` produce prompts in the syntax each generator expects, six for stills and four for motion. Here's what each adapter pairs with in production:

### Midjourney

The `prompts/round-1/midjourney.txt` file is designed for paste into Discord or the Midjourney web app. Limited API access as of Q2 2026, so most teams use:

- **Discord**, paste prompts manually for hero work
- **PiAPI** or **useapi.net**, third-party Midjourney API wrappers, accept the same prompt syntax
- **Midjourney official API** (when broadly available), same syntax

### Flux

The `prompts/round-1/flux.txt` file works on multiple platforms:

- **fal.ai**, fastest for series work, supports all Flux variants
- **Replicate**, broader model selection, slightly slower
- **Black Forest Labs API**, official, requires their key
- **WaveSpeedAI**, unified across many models

The prompt syntax is identical across all four surfaces. Pass the params alongside (aspect ratio, seed, model variant).

### Ideogram

The `prompts/round-1/ideogram.txt` file works on:

- **Ideogram official API**, direct, all features
- **fal.ai**, Ideogram v3 with a clean wrapper
- **Replicate**, also available

For text-in-image work (Mode 2), Ideogram is the right choice. For everything else, default to Flux or Midjourney and composite text separately.

### GPT Image

The `prompts/round-1/gpt-image.txt` file feeds into:

- **OpenAI Images API**, standard `images.generate` endpoint
- **ChatGPT Plus** UI for one-off work

Strong on prompt accuracy and spatial reasoning. Use for shots where composition specificity matters.

### Nano Banana (Gemini 2.5 Flash Image)

The `prompts/round-1/nano-banana.txt` file feeds into:

- **Gemini API direct**, Google's native surface
- **Vertex AI**, for enterprise GCP integration
- **fal.ai**, unified wrapper
- **Replicate**, also available

Strongest for image-to-image work and rapid variation generation. Pair with hero shots from Midjourney or Flux.

### Seedream

The `prompts/round-1/seedream.txt` file feeds into:

- **fal.ai**, `bytedance/seedream-4.5` and `seedream-4.0`
- **Replicate**, same models
- **BytePlus** direct API

Use for high-volume series work where cost matters more than peak quality.

### Motion video (Kling, Veo, Seedance, Hailuo)

The motion adapters each write their own per-shot prompt file. All run on fal.ai:

- **Kling 3.0** (`prompts/round-1/kling.txt`), the default. Best camera-motion realism per dollar, strong image-to-video.
- **Veo 3** (`prompts/round-1/veo.txt`), dialogue and lipsync with synchronised native audio.
- **Seedance 2.0** (`prompts/round-1/seedance.txt`), multi-shot sequences in one generation.
- **Hailuo 02 Pro** (`prompts/round-1/hailuo.txt`), cheap, fast iteration to find the shot before a final-tier re-roll.

For storyboard-to-video pipelines. Generated clips are raw material: assemble to timing, composite text overlays, grade, and add audio in post.

## How to wire up VO and audio

The skill pack writes per-shot VO content into `shots.json`'s `vo` field. It does not produce audio files. To bridge:

- **ElevenLabs**, most popular for AI VO. Take each shot's `vo` text, set voice and tone parameters, generate WAV per shot keyed by `shot_id`. Save to `output/vo/shot_NN.wav`.
- **Murf, Resemble, Cartesia**, alternative AI VO providers, same pattern
- **Human voice talent**, hand them `storyboard.md` (or a derived script doc), receive clean recordings keyed by shot_id

Music and sound design are out of scope for this pack. Most teams handle these in their editorial tool (After Effects, Premiere, Resolve, CapCut) or in a programmatic video composition (see [`connecting-to-video-pipelines.md`](./connecting-to-video-pipelines.md)).

## How to wire up final assembly

Three common paths:

**1. Manual editorial.** Drop generated images, VO files, and text overlays into After Effects, Premiere, or Resolve. Cut to the timing in `storyboard.md`. Slow but flexible.

**2. Programmatic video framework.** Build a composition (Remotion, Motion Canvas, or similar React-based renderer) that reads `shots.json`, renders each shot from generated images, animates text overlays from `text-overlays.json`, and outputs MP4. See [`connecting-to-video-pipelines.md`](./connecting-to-video-pipelines.md). Fast, version-controlled, scales to many brands. This is what WhyStrohm runs commercially.

**3. CapCut, Descript, hybrid.** For social-first content where speed matters more than precision. Hand off `storyboard.md` to an editor working in a fast tool.

## Why "free methodology, paid pipeline"

Three reasons this isn't just clever positioning:

**Methodology genuinely is reusable across teams.** A serious operator running their own brands benefits from the brand-lock, audit trail, and shot-grammar discipline regardless of which pipeline they wire up. Open-sourcing the methodology grows the category.

**Pipelines genuinely are operational work.** Wiring image generators, voice tools, a programmatic video framework, and automated publishing into a fast content cycle across multiple active brands is not "code I can publish." It's a continuously-operated system with infrastructure, monitoring, brand-specific configs, and a person on call. That's a service.

**The two layers serve different audiences.** The methodology serves operators who want to learn or run their own systems. The pipeline serves brands who want the output without operating it themselves. Both are real markets. They don't overlap.

If you want the methodology, this repo is the methodology. If you want the operated version, [whystrohm.com](https://whystrohm.com).

## When you've outgrown self-wired pipelines

Signs that managed infrastructure starts to make sense:

- You're generating for 3+ brands and the prompt-to-publish friction is daily-pain level
- Your output cadence is slower than 48 hours and you want it faster
- You're spending more time on pipeline maintenance than creative work
- Generator API breaking changes cost you a day each time
- You're rebuilding the same render-pipeline components for every new client

These aren't hypothetical. They're the daily friction of self-running content infrastructure at scale. Most teams hit them around the third active brand.

The pack itself remains useful at any scale. The pipeline question is separate.
