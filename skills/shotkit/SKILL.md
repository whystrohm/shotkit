---
name: shotkit
description: Run the whole Shotkit pipeline from one line of brief and open the board. Use when the user types /shotkit, or asks to "plan a video", "storyboard this and show me", "make a shot plan with prompts", or wants a storyboard, the prompts for their image or video generator and one page to see it all on. Plans the shots, writes the prompts, renders the board and opens it in a browser. For one step only, such as prompts for an existing shots.json or a check of one frame, use that step's own skill.
---

# Shotkit

One line of brief in. A plan, prompts and an open board out.

This skill runs the other four in order and puts the result on screen. The user should
not have to know the skills' names, ask for each step, or go looking for files. They
type a brief and a browser tab opens with every shot on it.

## What the user sees

1. They type a brief, for example `/shotkit 30-second founder explainer for Harbor Roast, 9:16`.
2. About two minutes later a browser tab opens: the board, with every shot on a timeline
   and a contact sheet.
3. The board fills in with a prompt for each shot.
4. Your reply is short: what was made, what you assumed, and the one next step.

## Where the tools are

`~/.claude/shotkit-tools/sk` after `./install.sh`. A `--project` install puts it at
`./.claude/shotkit-tools/sk`, and a repo clone has it at `tools/sk`. Use whichever exists,
and write it as `SK` below. It needs no setup: the checks make their own Python
environment the first time they run.

## Steps

### 1. Read the brief and fill the gaps yourself

Take from the brief: what the video is for, who it is for, the length, the aspect ratio,
the brand, and the generators the user names.

Do not stop to ask for what a sensible default covers. State each default in your final
reply so the user can change it.

| Missing | Use |
|---|---|
| Length | 30 seconds |
| Aspect | 9:16 when the brief says Reels, Shorts, TikTok, Stories or "vertical"; otherwise 16:9 |
| Framework | the one `storyboard-architect` would pick for this brief |
| Voiceover | on-screen text only, unless the brief mentions a speaker or a script |
| Generators | Flux for stills and Kling for motion |

Ask one question, and only one, when the brief does not say what the video is about.

### 2. Settle the brand

In this order, first match wins:

1. A brand lock the user names, or a `brand-lock.md` or `brand/*.md` in the project.
2. A site URL, a PDF or screenshots in the brief: run `brand-lock-extractor` on them
   and save the result as `brand/<name>.brand-lock.md`.
3. A pack named in the brief, from `~/.claude/shotkit-brand-packs/`.
4. None of these: use `~/.claude/shotkit-brand-packs/_starter.md`. Set
   `brand_lock_configured: false` in `run.json`. Do not invent a palette for a real
   company, and do not put the company's name on a palette you made up.

### 3. Plan the shots

Follow `storyboard-architect` and write its five files into `./output/`. If `./output/`
already holds a run, write to `./output-<short-name>/` instead and say so. Never
overwrite a run.

Then check them:

```bash
SK validate output/
```

Fix what it reports and run it again until it passes.

### 4. Open the board

Start the live board in the background, so it stays up while you work and reloads by
itself as files land:

```bash
SK board output/ --serve --open
```

Run that as a background command. If you cannot run background commands, write the page
and open it instead:

```bash
SK board output/ --open
```

Tell the user in one line that the board is open.

### 5. Write the prompts

Follow `visual-prompt-forge` for the generators from step 1. Then:

```bash
SK validate output/
SK board output/
```

A live board reloads on its own. The second command keeps `output/board.html` current
for when the live board is closed.

### 6. Report

Keep it short. The board carries the detail.

- One line: what was made and where (`output/`, and the board address or path).
- The defaults you used, as a short list.
- The next step, which is the one the board shows: make the frames from the prompts.
  Say that a frame dropped on a shot in the live board is saved to the right folder, and
  that "check the frames" runs the critic when they are in.

## Later turns

The user comes back with frames, or asks for changes. Do the step and refresh the board
every time, without being asked:

| The user says | Do |
|---|---|
| "check the frames", or frames have appeared in `output/frames/` | `visual-asset-critic` on each new frame, then `SK board output/` |
| "revise", or the board says a shot needs another pass | `visual-prompt-forge` in revision mode, then `SK board output/` |
| "add Midjourney", or names another generator | `visual-prompt-forge` for that generator, then `SK board output/` |
| "open the board" | `SK board output/ --open` |
| "send this to the client" | `SK preview output/`, and give them `output/preview.html` |

## Rules

- The board opens without the user asking. That is the point of this skill.
- Never claim a frame exists that the user has not made. Shotkit writes prompts and
  checks frames. It does not generate images or video.
- Never put a fact, a number, a price or a customer on screen that the brief did not give.
- Never overwrite a finished run.
