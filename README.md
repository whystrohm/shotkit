<p align="center"><a href="https://whystrohm.com/blog/shotkit-canvas-one-real-run"><picture><source media="(max-width: 700px)" srcset="docs/images/demo-phone.webp"><img src="docs/images/demo.webp" alt="Shotkit demo: a brief typed in Claude Code, every shot planned and every frame checked, the rough cut with its lines, then a board where the clips play and a shot is moved, and one cut in 16:9, 9:16, 4:5 and 1:1." width="100%"></picture></a></p>

<h3 align="center">Ship on-brand video at scale.</h3>

<p align="center">Plan every shot on a board, check every frame, render every size.<br>
Bring your own footage or use AI where it helps. Every price waits for your yes.<br>
It runs on your Mac, with Claude Code or Codex, and your own keys.</p>

<p align="center"><strong>English</strong> · <a href="README.zh-CN.md">简体中文</a></p>

<p align="center">
  <a href="https://github.com/whystrohm/shotkit/actions/workflows/validate-skills.yml"><img alt="Checks" src="https://github.com/whystrohm/shotkit/actions/workflows/validate-skills.yml/badge.svg"></a>
  <a href="https://github.com/whystrohm/shotkit/releases"><img alt="Latest release" src="https://img.shields.io/github/v/release/whystrohm/shotkit?include_prereleases&label=release&color=E4552A"></a>
  <a href="LICENSE"><img alt="Apache 2.0" src="https://img.shields.io/badge/license-Apache%202.0-informational"></a>
  <a href="https://github.com/whystrohm/shotkit"><img alt="Stars" src="https://img.shields.io/github/stars/whystrohm/shotkit?style=flat&color=informational"></a>
</p>

<p align="center">
  <a href="https://whystrohm.com/shotkit"><strong>Full tour</strong></a> ·
  <a href="#try-canvas">Try Canvas</a> ·
  <a href="https://whystrohm.com/blog/shotkit-canvas-one-real-run">Watch a real run</a> ·
  <a href="https://whystrohm.com/shotkit/examples/whystrohm-how-we-work/board.html">Open its board</a> ·
  <a href="#install">Claude Code</a> ·
  <a href="#use-canvas-from-codex">Codex</a>
</p>

<p align="center"><strong>New in 3.7: Shotkit Canvas.</strong> Every clip plays on the board, shots move and trim,<br>
and one cut comes out in every size. Free and open source. <a href="https://github.com/whystrohm/shotkit/releases">Get it</a></p>

## What it does

Making one clip is easy now. Shipping fifty that look like one brand is not. Shotkit gives
that work a board: plan it, leave notes, break it, make it better, and render the version you
approve. It still takes your taste.

- **Keeps it on brand.** Paste your website. Shotkit saves your colours, type, voice and
  never-rules, and plans and checks every shot against them.
- **Remembers what you like.** Like or dislike a clip, caption or render and say why. Canvas
  keeps it as a preference for that brand that you can read and edit, and its chat follows
  it next time. Nothing is trained on your files.
- **Starts from your own footage.** Drop in photos and clips, or a long recording with its
  transcript. Shotkit places them on shots and chapters and shows what is missing.
- **Uses AI for concepts and gaps.** Generate frames and clips to test an idea or fill a
  shot you cannot film. Not every generation is good, so a critic checks each one, only the
  misses are redone, and nothing runs until you approve the price.
- **Lets you see and cut.** Every clip plays on the board. Move shots, trim clips, change
  the lines and render the cut in 16:9, 9:16, 4:5 and 1:1 with Remotion.
- **Shares the plan.** A storyboard page, a client page you can print to PDF, a PowerPoint
  deck and stills, so the people you work with can review it anywhere.
- **Hands off to your editor.** Export the cut as an edit decision list (CMX 3600) for
  Premiere or Resolve, the on-screen lines as timed captions, and a shot list for the crew.
  See [Export](docs/export.md).
- **Built for agents.** Claude Code plans the shots and a separate critic checks each frame.
  Codex can read the Canvas board and make edits you can undo. Every spend waits for your yes.

## Two ways to use it

| | **Plugin** · in Claude Code | **Canvas** · for Mac |
|---|---|---|
| **Best for** | Turning a brief and your photos into a clear plan to share | Planning, checking and cutting the video in one place |
| **You get** | A storyboard page, a client page you print to PDF, a PowerPoint deck, stills and a rough cut | The plugin's plan plus chat, prices you approve, clips on a live board, and cuts in every size |
| **Start** | `/plugin install shotkit --marketplace whystrohm/shotkit` · [steps](#install) | Download from [Releases](https://github.com/whystrohm/shotkit/releases), run `./start.sh --open` · [steps](#try-canvas) |

## How it works

![1. Add your brand from your website. 2. Plan the board: say what you want or bring footage. 3. Approve the price: nothing runs until you say yes. 4. Check every frame: a critic sends the misses back. 5. Cut every size: trim, move and render 16:9, 9:16, 4:5 and 1:1.](docs/images/how-it-works.png)

Our run for WhyStrohm: five shots, three sent back and remade, four sizes, about ten minutes
from brief to clips and $2.34 of generation at fal's quoted prices.

## See it in Canvas

![Recorded in Canvas, in eight steps: open Canvas and pick where to start; add a brand from its website; ask for a video in one sentence; the plan lands on the board; see the price and approve it; the critic checks every frame; move a shot and pin a note; cut it in every size.](docs/images/canvas-tour.webp)

Recorded in the app, start to finish: open it, add your brand, ask for a video, approve the
price, let the critic check the frames, move shots and pin notes, then cut every size.
[Watch the 55-second film](https://whystrohm.com/blog/shotkit-canvas-one-real-run).

## Done for you

Shotkit is free. It is one part of the system WhyStrohm runs on a Mac Studio. If you want the
whole system on your brand, we set it up and run it: your brand, footage library and templates,
finished videos rendered in every size, and posting every month.
[Talk to us](https://whystrohm.com/apply).

## Long recordings

Start a storyboard from a timecoded transcript (an SRT file) and add the MP4 recording.
Canvas splits it into chapters and shots at the timecodes, plays each piece, and cuts any
chapter straight from the recording. You can also start from a script, one shot per line.

## Try Canvas

Canvas is a preview for macOS. It needs Python 3.10 or later.

1. From [Releases](https://github.com/whystrohm/shotkit/releases), download
   `shotkit-canvas-*.zip` and the matching `.zip.sha256` into their own folder.
2. Verify, extract and open it:

   ```sh
   shasum -a 256 -c shotkit-canvas-*.zip.sha256 &&
   unzip shotkit-canvas-*.zip &&
   cd shotkit-canvas &&
   ./start.sh --isolated --open --port 0
   ```

3. Open the bundled example **WhyStrohm · How it works** and play it.

To preview and render cuts, install Node.js and run `npm ci` and `npm run build` once in the
Canvas folder. Cuts render with [Remotion](https://www.remotion.dev); if you render for a
company, check [Remotion's license](https://www.remotion.dev/license).

### Connect Claude in Canvas

Run `./start.sh --open`, then paste a key from
[Claude Console](https://platform.claude.com/settings/keys) in **Settings and keys → Claude**.
Now you can add brands, plan videos and chat. The key stays in the macOS Keychain.

### Make frames and clips from Canvas

Generation also needs Claude Code signed in, a clone of this repo and a
[fal.ai](https://fal.ai) key saved in **Settings and keys**. Start Canvas this way and plan
the video in this mode:

```sh
SHOTKIT_HOME=/path/to/shotkit SHOTKIT_CANVAS_DATA="$HOME/.shotkit/canvas" python3 serve.py --open
```

Claude Code writes the prompts, runs the critic and writes revisions. Shotkit's tools price
and make the frames and clips. Every quote waits for your approval.

### Use Canvas from Codex

Start Canvas on port **4711**, sign in with `codex login` and add the Canvas MCP server:

```sh
codex mcp add shotkit-canvas -- python3 "/path/to/shotkit-canvas/mcp.py"
```

Codex can then list boards, read shots and notes, and make edits you can undo. For another
port, pass `--env SHOTKIT_CANVAS_URL=http://127.0.0.1:PORT` before the `--`.

### Install

In Claude Code:

```
/plugin install shotkit --marketplace whystrohm/shotkit
/shotkit:shotkit 30-second launch video for https://example.com, 9:16
```

Then ask for the next step in plain words: "check the frames", "export the stills".

<details>
<summary>More setup</summary>

**Older Claude Code** (before 2.1.275): `/plugin marketplace add whystrohm/shotkit`, then
`/plugin install shotkit@shotkit`. **Without plugins:** clone this repo and run
`./install.sh`; the command is then `/shotkit`.

**Open a run in Canvas.** `sk` is in the plugin's `tools/` folder, at
`~/.claude/shotkit-tools/sk` after `./install.sh`, and at `tools/sk` in a clone.

```bash
sk workspace "/path/to/project" --runtime "/path/to/shotkit-canvas" --open
```

`sk doctor` checks the setup. `--rules-only` reviews without AI, `--port 0` picks a free port.

**Your brand by hand.** Start from `brand-packs/_template.md`. See
[`brand-packs/README.md`](brand-packs/README.md) and
[a worked example](skills/brand-lock-extractor/examples/brand-lock.md) based on whystrohm.com.

**Codex tools.** `board_state` lists runs, `storyboard_state` reads one board with its
revision, and `run_commands` edits it when you pass that revision as `expected_board_revision`.

</details>

## What you get

| | |
|---|---|
| **The board** | Every shot, prompt, frame, verdict and clip on one page. It opens offline. |
| **Your files, organized** | Frames and clips filed by round and shot. Round 2 never overwrites round 1. |
| **Cuts** | Editable cuts in every size, with your lines in your type. |
| **Exports** | Carousel stills, a PowerPoint deck, a rough-cut MP4, a shot list, subtitles and an edit list. |
| **A client page** | The plan as a clean page you can send or print before anything is made. |
| **A record** | Every input pinned by hash. Approvals and fal request IDs saved with the run. |

Everything stays in a folder on your computer. What goes out: the pages Add a brand reads,
your requests to Claude, price checks and the jobs you approve on fal, Google Fonts when a
board is online, and anything you choose to send to GoHighLevel. [Security and data](SECURITY.md)

## Examples

Two real WhyStrohm runs. Each picture opens the live board.

| How we work · made in Canvas · 16:9 | Media Tsunami · 16:9 |
|---|---|
| [![The How we work board](docs/images/example-whystrohm-how-we-work.jpg)](https://whystrohm.com/shotkit/examples/whystrohm-how-we-work/board.html) | [![The Media Tsunami board](docs/images/example-whystrohm-media-tsunami.jpg)](https://whystrohm.com/shotkit/examples/whystrohm-media-tsunami/board.html) |

<details>
<summary>Under the hood</summary>

**The skills**

| Skill | What it does |
|---|---|
| `shotkit` | Runs the others in order and opens the board |
| `brand-lock-extractor` | Website, PDF or screenshots → `brand-lock.md` |
| `storyboard-architect` | Brief → `storyboard.md` and `shots.json` |
| `visual-prompt-forge` | Shots → prompts for 10 generators |
| `visual-asset-critic` | Frame and intent → a verdict and `critique.json` |
| `storyboard-html-preview` | Storyboard → one shareable page |

**The run folder**

```
output/
├── run.json             # every input pinned by hash
├── storyboard.md        # shot by shot, for people
├── shots.json           # the same, for tools
├── brand-lock.snapshot.md
├── prompts/round-1/     # one file per generator
├── frames/round-1/      # yours or generated
├── clips/round-1/
├── critiques/round-1/   # one verdict per shot
├── approvals/           # a person's yes, from `sk approve`
├── export/              # stills, deck, rough cut
├── board.html
└── preview.html         # the client page
```

**A person's approval.** `sk approve output/ --by "Your Name" --what frames` records who
approved what, by hash. The board says when an approval no longer holds.

**Offline example.** From a clone, `tools/sk board --example` builds the bundled Brightdock
board, a fictional software launch.

</details>

## Docs

[Quickstart](https://whystrohm.com/shotkit/docs/quickstart) ·
[Your own photos and clips](docs/own-media.md) ·
[Frames and clips with fal.ai](docs/generate-with-fal.md) ·
[Designed frames](docs/designed-frames.md) ·
[Export](docs/export.md) ·
[The check and revise loop](docs/the-qa-loop.md) ·
[Brand locks](docs/brand-lock-anatomy.md) ·
[The audit trail](docs/audit-trail-pattern.md) ·
[Connecting generators](docs/connecting-to-generators.md) ·
[Changelog](CHANGELOG.md)

## Feedback

Tell us what broke or what you want next.
[Open an issue](https://github.com/whystrohm/shotkit/issues),
[start a discussion](https://github.com/whystrohm/shotkit/discussions), or write to
[hello@whystrohm.com](mailto:hello@whystrohm.com).

## Contributing, license and who built this

Pull requests are welcome: run `tools/sk check` first. See [CONTRIBUTING.md](CONTRIBUTING.md)
and [SECURITY.md](SECURITY.md). Apache 2.0, see [LICENSE](LICENSE) and [NOTICE](NOTICE); the
license does not grant rights to the Shotkit or WhyStrohm names.

Yuri Strohm made Shotkit at [WhyStrohm](https://whystrohm.com). OpenAI Codex and Anthropic
Claude helped with the code and review. Shotkit plans, checks and cuts; if you want the video
finished, edited and posted every month, [that is what WhyStrohm does](https://whystrohm.com/apply).
