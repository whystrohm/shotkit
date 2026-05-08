# Timing Rules

Pacing is math, not feel. Use these as defaults. Override only with reason documented in rationale.

## Shot duration baselines

| Content type | Default shot duration | Range |
|---|---|---|
| Kinetic typography / opinion | 1.0–1.5s | 0.5–2.0s |
| Founder talking-head | 2.5–4.0s | 2.0–6.0s |
| Product/lifestyle b-roll | 1.5–2.5s | 1.0–3.5s |
| Demo / how-to | 3.0–5.0s | 2.0–7.0s |
| Cinematic brand film | 3.5–6.0s | 2.0–10.0s |

If a single shot is longer than 7 seconds in a 30-second piece, justify it in rationale. Long shots are not bad. Unjustified long shots are.

## Hook timing (the first beat)

The hook is 0–2s. Always. There are no exceptions in short-form content. Specifically:

- 9:16 social: first frame must telegraph the topic. Auto-play on mute means the first half-second is fighting a swipe.
- 16:9 in-feed: first 2s decides watch-time.

The hook shot framing should be high-contrast against the shots that follow. If shot 2 is MS, shot 1 should not be MS. Visual contrast = retention.

## CTA timing (the final beat)

The CTA is the final 4–6s for 30s content, 6–10s for 60s content. Specifically:

- Last shot should hold long enough for someone to read the CTA text and act
- Don't put motion on the CTA shot, let the text breathe
- If there's a logo lockup, it lives in the final 2s, not earlier

## On-screen text duration math

A text overlay needs to be on screen long enough to be **read twice**. Not once, twice. Why: viewers are skimming, eyes don't always lock on first frame.

Reading speed reference (assume average viewer):
- 1 short word (≤5 chars): 0.6s minimum read
- Short phrase (≤6 words): 1.2s
- Sentence (≤14 words): 2.4s
- Long sentence (15–25 words): 4.0s

Multiply by 2 for the "read twice" rule. So a 6-word phrase needs **2.4s on screen minimum**.

If a shot is 2 seconds and you need a 14-word sentence, you have a problem. Either:
1. Shorten the copy
2. Carry the text across two consecutive shots (text persists during cut)
3. Lengthen the shot

Do not under-time text. It's the most common storyboard failure.

## Pacing curve

For 30-second content, the natural energy curve:

```
0s ─────────────────────────────────── 30s

Energy
  ▲     ╱╲
  │    ╱  ╲___
  │   ╱       ╲___
  │  ╱            ╲___
  │ ╱                 ╲___
  └─────────────────────────►
   hook  build  apex  release  CTA
   0-2   2-12   12-20  20-26   26-30
```

The apex is two-thirds in, not at the end. The CTA is a release, not a peak.

For 60-second content, scale the same curve. Apex around 0:40, CTA from 0:50.

## Validating timing

Before declaring done, check:

1. Sum of `(end - start)` across all shots equals project duration ±0.1s
2. No shot has `start >= end`
3. No two shots overlap
4. First shot starts at 0.0
5. Last shot ends at project duration
6. Every text overlay's `enter.at` is ≥ its shot's `start`
7. Every text overlay's `exit.at` is ≤ its shot's `end` (or carries to a flagged successor shot)
8. Every text overlay's on-screen duration ≥ read-twice threshold
