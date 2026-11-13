# Make the frames and clips with fal.ai

Shotkit writes the prompts. From 3.3.0 it can also send them: stills and video clips,
made on [fal.ai](https://fal.ai) with your own key and saved where the board and the
critic look. This is optional. Every prompt still works pasted into a generator by hand.

fal is a separate company. Shotkit has no partnership with it and takes no share of what
you spend there. fal bills your account for each generation, at the price shown on that
model's page.

## 1. Connect your key

1. Make an account at [fal.ai](https://fal.ai) and add credit.
2. Create a key at [fal.ai/dashboard/keys](https://fal.ai/dashboard/keys).
3. Give it to Shotkit in one of two ways.

In the shell, for this session:

```bash
export FAL_KEY="your-key"
```

Or in a file named `.env` in your project folder, so it is there every time:

```
FAL_KEY=your-key
```

Add `.env` to your `.gitignore`. Shotkit reads the key, sends it to fal and nowhere
else, and never prints it or writes it to a file.

## 2. See the plan first

Nothing is spent until you add `--yes`. Without it you get the plan:

```bash
~/.claude/shotkit-tools/sk generate output/ --model flux
```

```
  model    fal-ai/flux-2-pro
  prompts  flux
  make     shot_01  round 1  image_size=portrait_16_9, output_format=png, seed=41207
  make     shot_02  round 1  image_size=portrait_16_9, output_format=png, seed=41207
  ...

  This would send 5 requests to fal, one frame each.
  fal bills your account. The price is on https://fal.ai/models/fal-ai/flux-2-pro
  Nothing was sent. Add --yes to run it.
```

It lists each request and anything it will skip, with the reason.

## 3. Make the frames

```bash
~/.claude/shotkit-tools/sk generate output/ --model flux --yes
```

Each still is saved as `output/frames/round-N/shot_NN.png`. A live board picks them up
as they land. Then ask Claude to check the new frames.

In Claude Code you can just ask: "Make the frames with Flux on fal." Claude shows you
the plan and the number of requests, and runs it when you say yes.

## 4. Make the clips

A video model starts from a shot's frame, so make and check the stills first.

```bash
~/.claude/shotkit-tools/sk generate output/ --model kling --yes
```

Each clip is saved as `output/clips/round-N/shot_NN.mp4` and plays on the board under
its frame. The clip length is the shortest the model offers that covers the shot.

## Pick the model

`--model` takes a Shotkit generator name or any fal model id.

| Name | Sends to | Kind |
|---|---|---|
| `flux` | `fal-ai/flux-2-pro` | still |
| `nano-banana` | `fal-ai/nano-banana-2` | still |
| `seedream` | `bytedance/seedream/v5.5/text-to-image` | still |
| `ideogram` | `ideogram/v4.5` | still |
| `gpt-image` | `openai/gpt-image-2` | still |
| `kling` | `fal-ai/kling-video/v3/standard/image-to-video` | video |
| `seedance` | `bytedance/seedance-2.0/fast/image-to-video` | video |
| `hailuo` | `fal-ai/minimax/hailuo-02/pro/image-to-video` | video |

That table is `tools/fal-models.json`, checked against fal's model list on 2026-11-13.
fal adds models often. Edit the file to change a default, or skip it and name any model:

```bash
~/.claude/shotkit-tools/sk generate --list "image-to-video"       # search fal's models
~/.claude/shotkit-tools/sk generate output/ --model kling/v4/image-to-video --prompts kling --yes
```

`--prompts` says which of Shotkit's prompt files to send to a model named by id.
Midjourney and Veo have no entry: fal's list had no model for them on that date.

A new model needs no change to Shotkit. Each fal model publishes the inputs it accepts.
Shotkit reads that and fills what applies: the prompt, the aspect ratio in whichever
form the model takes it, the seed from the prompt file, and for video the start frame
and the length.

## Options

| Option | What it does |
|---|---|
| `--shots shot_02,shot_04` | only these shots |
| `--replace` | make a shot again when it already has a frame that has not been reviewed |
| `--workers 3` | how many requests run at once |
| `--yes` | send the requests |

## What it will not do

- **Spend without `--yes`.**
- **Replace a frame the critic has reviewed.** The critique records that file's hash. A
  shot that came back REVISE gets a new frame in the next round, after the prompts are
  revised.
- **Lose track of a request.** Each one is written to `output/generations.jsonl` with
  its fal request id the moment it is submitted, and again with the saved file's hash.
  If a run is cut off, the request ids are there to look up on fal.

## What you get, and what you do not

You get frames and clips that match the plan: raw material, and a fast way to see an
idea before anyone films or edits. You do not get a finished video. The clips are not
cut together, the on-screen text is not set on them, and nothing is graded or scored.
Finishing is editing work. WhyStrohm does that as a service, to the same plan, in your
brand. Write to [hello@whystrohm.com](mailto:hello@whystrohm.com) or see
[whystrohm.com](https://whystrohm.com).

## Keep the key out of git

- `.env` is in Shotkit's `.gitignore`. Add it to your project's too. `.env.example`
  shows the one line the file needs.
- Never paste a key into a chat, a prompt file or a brand lock.
- `tools/sk validate_no_secrets.py <folder>` scans a folder for keys before you share
  or commit it. It prints at most the first four characters of anything it finds.
- If a key was ever committed or shared, delete it at fal.ai/dashboard/keys and make a
  new one. Removing it from the file is not enough.
