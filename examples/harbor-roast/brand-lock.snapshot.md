<!-- snapshot taken: 2026-09-26T13:40:00Z -->
<!-- source: brand/harbor-roast.md -->
# Brand Lock: Harbor Roast (fictional brand)

Harbor Roast is a fictional brand made for this example. It is not a real company.

## Identity

**Brand:** Harbor Roast
**One-line description:** A fictional small-batch coffee roaster that roasts on one drum roaster in a small room by the water and sells whole-bean coffee by the bag, with one limited roast each season.
**Archetype:** Maker
**Voice posture:** Quiet. Short declaratives that name the roast, the roast day and the taste, and never tell the reader how to feel.

## Palette

Every hex value here is allowed. Anything outside this list is not.

| Role | Hex | Use |
|---|---|---|
| Background | `#1C1510` | Dark roast brown, primary canvas |
| Ink | `#F2E8DA` | Cream, primary text on dark |
| Accent | `#D9822B` | Amber, the one accent, one element per frame |
| Muted | `#9C8B78` | Driftwood grey, secondary text and captions |
| Rule | `#3A2E25` | Char, borders and dividers |

## Typography

**Display font:** `Fraunces SemiBold 600`
**Body font:** `Work Sans Regular 400`

The font name goes in backticks, immediately after the label. Downstream tools read
that backticked value; prose before it is not parsed.

## Mood adjectives

- early-morning quiet, not sleepy
- warm, not cozy-cute
- a working roastery, not a cafe
- dark and matte, not moody-glossy

## Never list

- never latte art, coffee-bean clip art or drawn steam swirls
- never smiling people holding mugs toward the camera; people appear as hands or from behind
- never bright white product-on-white shots
- never more than one amber accent element in a frame
- never exclamation points
- never the words "artisanal", "premium" or "the best"
- never legible text, labels or logos inside generated images; all copy is composited

## Aspect ratios

Default: 9:16 for Instagram and TikTok, 4:5 for feed posts.

## Color grade direction

> Warm, dark and matte, blacks lifted just off crush, cream highlights, one amber accent, fine film grain, in the manner of Dutch Golden Age still-life light: one soft source and deep surrounding shadow.

## Motion language

> Slow and held. Static frames or one slow push per shot. Cuts land on an action, such as beans dropping or a cup set down. Type fades in and sits still. No whip pans, no speed ramps.

## Voice rules

- no exclamation points, anywhere
- never "artisanal", "premium", "the best" or "curated"
- sentences under ten words on screen
- name the roast, the roast day or the taste rather than a feeling
- no questions in on-screen copy

## Extraction notes

Audit trail for this extraction. The source was one written description from the owner
(`brand/harbor-roast-description.md`). Values not listed here were read directly from it
(`extracted`): all five palette hex values, both font names, the never-list items, the voice
rules on exclamation points and banned words, and the vertical-first aspect ratios.

**Inferred** (reasoned from evidence, reasonable to ship):
- Archetype "Maker", from "we roast on one drum roaster" and "not a cafe": the brand frames itself by the work, not the lifestyle.
- Voice posture "Quiet", from "short sentences" and "we do not tell people how to feel".
- Mood adjectives, from "the roastery at six in the morning", "not a cafe" and "not cozy-cute".
- The never-list line on legible text inside images, from the no-clip-art rule and the brand's use of composited type; the description does not say it in those words.
- "No questions in on-screen copy", from the declarative voice described.

**Needs confirmation** (best estimate, please verify):
- Font weights: the description names Fraunces SemiBold and Work Sans Regular; the numeric weights 600 and 400 are the standard values for those names. Confirm against the bag artwork.
- Color grade direction: there is no photography to read. The grade is built from the palette and the "six in the morning" description, with a Dutch Golden Age still-life reference chosen by the extractor. Confirm against any existing photos.
- Motion language: from "video should be slow" and "rather hold a shot than cut fast". No existing video was provided.
- 4:5 for feed posts: the description says "vertical first" and names Instagram; 4:5 is inferred from that channel.

---

**Last updated:** 2026-09-26
**Owner:** extracted
**Version:** 1.0
