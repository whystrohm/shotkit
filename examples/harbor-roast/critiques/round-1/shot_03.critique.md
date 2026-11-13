# Critique: shot_03, round 1

Frame `frames/round-1/shot_03.png` (sha256 `3f5e2d5ffcf5`), prompt `prompts/round-1/flux.txt`, generator flux 2 Pro, seed 41207, judged against `brand-lock.snapshot.md`. Shot spec: ECU overhead static, hero beat, 6.5-9.5s.

Review method: Viewed the full frame, then the top 700px at 60 percent where text_03 lands.

## Verdict
REVISE

## What's working
- Freshly roasted beans with a light oil sheen heaped in a perforated steel tray, stirring arm crossing toward the lower-right.
- Walnut counter and the black drum roaster match the environment anchor.

## What's not working
- **Shot Spec, major.** Spec is an ECU looking straight down. The frame is a high-angle medium shot of the whole tray with the roaster and the window behind it, so it repeats shot_02 instead of cutting in.
- **Composition, major.** The upper third is a bright fogged window and the roaster, not shadow, so cream text_03 has no dark field to sit on.
- **Brand Lock, minor.** Two amber points: the sight glass and a small indicator light at its lower left.

## Revision plan
- **Shot Spec:** Prompt-level. Open the prompt with 'Top-down flat lay, camera directly overhead and parallel to the tray, frame filled edge to edge with beans' and add 'no roaster, no window, no counter visible'.
- **Composition:** Prompt-level. Add 'light falls off toward the top edge so the upper third of the frame is near-black beans in shadow'.
- **Brand Lock:** Post-level. Resolved by the reframe; if it persists, desaturate the second point.

## Confidence
HIGH
