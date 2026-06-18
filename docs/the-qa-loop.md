# The QA loop

AI image and video generation has one structural problem: it is non-deterministic, and most teams have no gate between "generated" and "shipped." They generate, glance, accept, and post. Off-brand frames, character drift, six-fingered hands, and wrong framing slip through because the only reviewer is a tired human at the end of a long day.

shotkit's four skills already give you the pieces of a review. This document is how they form a **closed loop** that a person, or a pipeline, can run until every shot passes.

## The loop

```
  storyboard-architect ──▶ shots.json + brand-lock.snapshot.md
            │
            ▼
  visual-prompt-forge ───▶ prompts/{generator}.txt
            │
            ▼
  YOU (or your generator API) ──▶ output/generated/shot_NN.png
            │
            ▼
  visual-asset-critic ───▶ critique.md (for the human)
                           output/critique.json (for the machine)
            │
            ├─ verdict ACCEPT ──▶ done. ship the shot.
            │
            └─ verdict REVISE / REJECT
                       │
                       ▼
        visual-prompt-forge (revision mode)
        reads critique.json, re-emits prompts
        for only the failed shots
                       │
                       └──────▶ back to "YOU generate", repeat
```

The loop runs until every shot is `ACCEPT`, or until you decide a shot is good enough and call it manually. Nothing here calls a generator API, shotkit emits prompts and verdicts; the generation step is yours. That boundary is deliberate (see [`connecting-to-generators.md`](connecting-to-generators.md)).

## What makes it close

Two things the v0.2.0 batch added:

1. **A machine-readable verdict.** `visual-asset-critic` writes `output/critique.json` next to the markdown critique. Same review, two surfaces. The markdown is for the human; the JSON is for the loop.
2. **A prompt-forge that can read it.** `visual-prompt-forge` revision mode takes `shots.json` + one or more `critique.json` files and re-emits prompts for only the shots that failed.

## The verdict is derived, not chosen

A critique that says "ACCEPT" while listing a blocking problem is worthless, and it is exactly what a tired reviewer (human or model) produces. So the verdict is **derived from issue severities**, not picked freely:

| If the issues include... | The verdict must be |
|---|---|
| any `blocking` | `REJECT` |
| any `major` (no blocking) | `REVISE` (or `REJECT`), never `ACCEPT` |
| only `minor`, or none | `ACCEPT` (with post notes) |

`tools/validate_critique.py` enforces this. It validates a `critique.json` against the schema **and** checks the gating rule, which JSON Schema alone cannot express. Its `--selftest` constructs a deliberately contradictory document (ACCEPT + a blocking issue) and fails if the gate lets it through, so CI proves the gate fires on every run.

This is what lets you put the loop in a pipeline: you can branch on `critique.json.verdict` and trust it.

## How revision mode decides what to re-emit

For each non-ACCEPT shot, revision mode walks the critique's `issues[]` and branches on `fix_type`:

| `fix_type` | What revision mode does |
|---|---|
| `prompt-level` | recompose the shot's prompt with the fix applied, re-emit it |
| `re-roll` | keep the prompt identical, flag it for 2-3 fresh samples |
| `post-level` | do **not** re-emit, the fix happens in compositing, not a new generation |

A shot whose only issues are `post-level` needs no new prompt. A shot that already passed is left alone. You re-generate only what actually needs re-generating, which is where the cost savings live.

## Running it by hand

```
1. Generate frames from prompts/{generator}.txt
2. For each frame, run visual-asset-critic with the shot_id and brand-lock
   -> writes output/critique.json
3. python tools/validate_critique.py output/critique.json   # sanity gate
4. If any verdict != ACCEPT:
   hand shots.json + the critique.json files to visual-prompt-forge
   in revision mode -> output/prompts/revised-{generator}.txt
5. Re-generate the revised shots. Go to 2.
```

## Running it in a pipeline

The same loop scripts cleanly because every step is a file:

- `critique.json` is schema-valid and gate-checked, so `verdict` is trustworthy to branch on.
- revision mode writes `revised-{generator}.txt`, so your generation step has a stable input.
- a stop condition is just "no critique.json has a verdict other than ACCEPT" or a max-rounds counter.

shotkit stops at the prompt and the verdict. The loop logic and the generator calls live in your tooling, which is exactly where the operator's edge is.
