# Critique: shot_03, round 2

Frame `frames/round-2/shot_03.png` (sha256 `18862adb0405`), prompt `prompts/round-2/revised-flux.txt`, generator flux 2 Pro, seed 41207, judged against `brand-lock.snapshot.md`. Shot spec: ECU overhead static, hero beat, 6.5-9.5s.

Review method: Viewed the full 1072x1920 frame, then measured mean RGB of the upper third, the lower two-thirds and the top 5 percent.

## Verdict
ACCEPT

## What's working
- Camera looks straight down; beans fill the frame edge to edge in the perforated steel tray, with a faint oil sheen on some beans. The round-1 Shot Spec failure is cleared.
- The stirring blade crosses the lower-right corner as specified.
- No window and no counter in frame. The warm glow on the blade is the only amber element.
- Light falls off toward the top: the upper third measures about RGB 38,33,25 against 58,43,28 for the lower two-thirds, so cream text_03 has a dark field. The round-1 Composition failure is cleared.
- No text, labels, logos or faces.

## What's not working
- **Composition, minor.** The top 5 percent of the frame is the lit tray rim and a pale, out-of-focus shape above it (mean about RGB 90,88,74), and the bottom edge shows the tray lip and machine parts below it. The prompt asked for no roaster in frame.
- **Shot Spec, minor.** The upper third is dark brown beans, not near-black shadow as prompted. Contrast with cream #F2E8DA is still strong.

## Revision plan
- **Composition:** Post-level. Crop 6 percent from the top and 4 percent from the bottom and scale to fill, or burn the top strip down to #1C1510.
- **Shot Spec:** Post-level. If text_03 needs more separation, lay a #1C1510 gradient over the top third at about 30 percent opacity.

## Confidence
HIGH
