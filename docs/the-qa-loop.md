# The QA loop

AI image and video generation has one structural problem: it is non-deterministic, and most teams have no gate between "generated" and "shipped." They generate, glance, accept, and post. Off-brand frames, character drift, six-fingered hands, and wrong framing slip through because the only reviewer is a tired human at the end of a long day.

shotkit's five skills give you the pieces of a review. This document is how they form a **closed loop** that a person, or a pipeline, can run until every shot passes, and how the loop survives the three things that used to break it silently: two people working at once, a frame regenerated without a re-review, and a brand-lock that changes mid-project.

## The loop

```
  storyboard-architect ──▶ run.json + shots.json + brand-lock.snapshot.md
            │              (run.json hashes all three)
            ▼
  visual-prompt-forge ───▶ prompts/round-1/{generator}.txt
            │
            ▼
  YOU (or your generator API) ──▶ frames/round-1/shot_NN.png
            │
            ▼
  visual-asset-critic ───▶ critique.md (for the human)
                           critiques/round-1/shot_NN.critique.json (for the machine)
            │
            ├─ ACCEPT ──▶ done. ship the shot.
            │
            ├─ REVISE
            │     │
            │     ▼
            │   visual-prompt-forge (revision mode)
            │   re-emits prompts for only the failed shots
            │   into prompts/round-2/revised-{generator}.txt
            │     │
            │     └──────▶ back to "YOU generate", round 2
            │
            └─ REJECT ──▶ stop. no fix path exists. escalate to the human.
```

The loop runs until every shot is `ACCEPT`, or until you decide a shot is good enough and call it manually. Nothing here calls a generator API, shotkit emits prompts and verdicts; the generation step is yours. That boundary is deliberate (see [`connecting-to-generators.md`](connecting-to-generators.md)).

## Every artifact is addressed by round and shot

```
output/
├── run.json                                   written once, hashes every input
├── shots.json
├── text-overlays.json
├── brand-lock.snapshot.md
├── prompts/
│   ├── round-1/flux.txt
│   └── round-2/revised-flux.txt
├── frames/
│   ├── round-1/shot_01.png
│   └── round-2/shot_02.png
└── critiques/
    ├── round-1/shot_01.critique.json
    ├── round-1/shot_02.critique.json
    └── round-2/shot_02.critique.json
```

This layout is the point, not housekeeping. Previously every one of those artifacts had a
single fixed path: one `critique.json`, one `prompts/{generator}.txt`, one
`revised-{generator}.txt`, one `generated/shot_NN.png`. A 12-shot project through three
rounds produced 36 critiques and kept one, and the surviving prompt was round 3's while most
surviving frames came from round 1.

Now no two writes collide. Two operators reviewing different shots write different files.
Two operators reviewing the *same* shot in the same round produce two files whose contents
both name that shot, which is a conflict a person can resolve by reading it, rather than a
silent overwrite.

## The verdict is derived, not chosen

A critique that says "ACCEPT" while listing a blocking problem is worthless, and it is exactly what a tired reviewer (human or model) produces. So the verdict is **derived from issue severities**, not picked freely:

| If the issues include... | The verdict must be |
|---|---|
| any `blocking` | `REJECT` |
| three or more `major` | `REJECT` |
| one or two `major` | `REVISE` |
| only `minor`, or none | `ACCEPT` (with post notes) |

`tools/validate_critique.py` enforces this. Its `--selftest` builds fourteen documents,
including a deliberately contradictory one (ACCEPT plus a blocking issue), and fails if the
gate lets any wrong one through, so CI proves the gate fires on every run.

The three-major row used to read "escalate at your discretion," which meant the skill and
`critique-rubric.md` disagreed about the same case. Discretion inside a gate is not a gate.

## The verdict names the bytes it reviewed

A verdict is a claim about a specific file. From critique schema `1.1`, it has to prove it:

```json
{
  "version": "1.1",
  "run_id": "20260730T142300Z-9f2c1ab4",
  "round": 1,
  "shot_id": "shot_02",
  "image_ref": "frames/round-1/shot_02.png",
  "image_sha256": "e3b0c44298fc1c14...",
  "prompt_ref": "prompts/round-1/flux.txt",
  "prompt_sha256": "9f86d081884c7d65...",
  "brand_lock_ref": "brand-lock.snapshot.md",
  "brand_lock_sha256": "2c26b46b68ffc68f...",
  "generator": "flux",
  "model_version": "2 Pro",
  "seed": 481207,
  "verdict": "REVISE"
}
```

Every provenance field is **required and nullable**. `null` records that an input was
genuinely unavailable; a missing key records nothing at all. A `1.1` critique claiming HIGH
confidence with a null `prompt_ref` fails the gate, because HIGH means all three references
were available and that combination says otherwise.

Paths alone were never enough. `image_ref` still resolves after the frame behind it is
replaced, which is the whole failure mode.

## Running it by hand

```
1. Generate frames from prompts/round-N/{generator}.txt into frames/round-N/
2. For each frame, run visual-asset-critic with the shot_id and brand-lock
   -> writes critiques/round-N/shot_NN.critique.json
3. python tools/validate_provenance.py output/
   Recomputes every hash, so a frame swapped after review fails here.
4. If any verdict is REVISE:
   point visual-prompt-forge at output/ in revision mode
   -> prompts/round-{N+1}/revised-{generator}.txt
5. If any verdict is REJECT: stop and decide. Revision mode will not re-emit it.
6. Re-generate the revised shots into frames/round-{N+1}/. Go to 2.
```

## Running it in a pipeline

The same loop scripts cleanly because every step is a file:

```bash
# Is the chain intact, and is every shot done?
python tools/validate_provenance.py output/ --require-accept || exit 1
```

Exit 0 means every hash matches and every shot's latest verdict is ACCEPT. Exit 1 means
either the chain is broken or work remains, and the output says which. Add `--json` for a
machine-readable report.

Three things that used to end the loop quietly, and what now catches them:

| Failure | What it used to do | What catches it |
|---|---|---|
| Frame regenerated without a re-review | Stale ACCEPT satisfied the stop condition; the loop declared done on an unreviewed image | `image_sha256` mismatch |
| Frame dropped in with no critique at all | Nothing looked for it | frames-without-critiques check |
| Brand-lock edited mid-project | Old frames judged against new rules; every path still resolved | `brand_lock_sha256` mismatch against `run.json` |
| Two operators on one shot in one round | Second write destroyed the first verdict | two files, same shot, same round |

A max-rounds counter is still worth adding on your side. The loop has no opinion about when
to give up, and neither does the gate.

## What shotkit still does not do

It does not call generators, it does not render video, and it does not decide when a REJECT
is worth fighting. It emits prompts, verdicts, and a chain you can audit. The loop logic and
the generator calls live in your tooling, which is exactly where the operator's edge is.
