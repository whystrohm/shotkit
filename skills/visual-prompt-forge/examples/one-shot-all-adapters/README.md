# One Shot, All Adapters

This example takes a single shot from the WhyStrohm 30-second pitch and renders it through the generator adapters in the pack. Use it as a calibration reference: same intent, same data, different prompt syntaxes. Six stills adapters are shown, plus the default motion adapter (Kling) standing in for the motion video lane.

## The source shot

From `examples/30s-pain-proof-promise/shots.json`:

```json
{
  "id": "shot_04",
  "beat": "reframe",
  "start": 11.0,
  "end": 16.0,
  "framing": "MCU",
  "angle": "eye-level",
  "motion": "push",
  "depth_of_field": "shallow",
  "subject": "founder, same posture, looking at camera, expression shifts from tired to clear, small almost-smile",
  "rationale": "Slow push as the reframe lands. Same character, same environment, only the expression changes. The change is the point."
}
```

## Series lock context (constant across all adapters)

```
character: founder, mid-thirties, salt-and-pepper hair, navy crewneck, calm posture
environment: minimalist home office, white walls, oak desk, single houseplant
lighting: soft natural side-light, large window camera-left, warm afternoon golden hour
color_grade: warm filmic, muted teal shadows, slight grain
```

## Brand mood

`calm, considered, operator (not creator), confident without volume`

## Outputs

Each `.txt` file in this directory is the prompt for one adapter:

- `midjourney.txt`. Midjourney v7
- `flux.txt`. Flux 2 Pro
- `ideogram.txt`. Ideogram v3 (composited mode)
- `gpt-image.txt`. GPT Image 1.5
- `nano-banana.txt`. Gemini 2.5 Flash Image
- `seedream.txt`. Seedream 4.5
- `kling.txt`. Kling 3.0 (motion video, the default motion adapter)

The other three motion adapters (`veo` for dialogue/lipsync, `seedance` for multi-shot sequences, `hailuo` for budget iteration) follow the same five-layer anatomy as Kling and are chosen by need; see their files in `adapters/`. This single silent push shot doesn't exercise dialogue or a sequence, so Kling is the representative motion example here.

Note the differences:

- **Midjourney** is a comma-separated stack with `--ar`, `--style raw`, `--s 50` flags
- **Flux** is natural-language paragraphs with no flags, parameters live in the API call
- **GPT Image** uses paragraph breaks and explicit spatial language
- **Seedream** is the shortest, comma stack like Midjourney but no flags
- **Kling** (and every motion adapter) leads with camera motion (the stills adapters let it be implicit)

Same intent. Different syntax. Same brand-lock and series-lock anchors flowing through all of them.

## What's not in any prompt

The on-screen text content. Even though shot_04 has an on-screen text overlay (`text_03`, "You don't have a content problem. You have an infrastructure problem."), none of the prompts contain that text. It's composited separately per the five-layer model.

This is the discipline: the image generator handles the image, the compositor handles the text, neither tries to do the other's job.
