<!-- snapshot taken: 2026-11-19T12:00:00Z -->
<!-- source: brand/brightdock.md -->
# Brand Lock: Brightdock (fictional product)

Brightdock is a fictional product made for this example. It is not a real company.

## Identity

**Brand:** Brightdock
**One-line description:** A fictional deploy log for small software teams: every release on one page, what changed in it, who shipped it, and a button to roll it back.
**Archetype:** Sage
**Voice posture:** Plain and exact. Short sentences that say what the product shows, in the words an engineer would use.

## Palette

Every hex value here is allowed. Anything outside this list is not.

| Role | Hex | Use |
|---|---|---|
| Background | `#0B0D10` | Near-black, the ground of every frame |
| Ink | `#F4F5F0` | Off-white, all headline type |
| Accent | `#C8F250` | Lime, one accent per frame: a live status, a button, the mark |
| Muted | `#8A9099` | Grey, secondary text inside the product |
| Rule | `#232830` | Panel borders and dividers |

## Typography

**Display font:** `Bricolage Grotesque ExtraBold 800`
**Body font:** `Inter Medium 500`

The font name goes in backticks, immediately after the label. Downstream tools read
that backticked value; prose before it is not parsed.

## Mood adjectives

- calm, not sleepy
- exact, not cold
- a tool at work, not a pitch deck
- dark and flat, not glossy

## Never list

- never stock photos of people at laptops
- never 3D devices, floating phones or tilted screens
- never gradients across type
- never more than one lime element as the focus of a frame
- never exclamation points
- never the words "seamless", "powerful" or "effortless"
- never a made-up customer logo, review or number

## Aspect ratios

Default: 9:16 for social video, 4:5 for feed posts and carousels.

## Color grade direction

> Flat screen colour, no grade. Near-black ground, off-white type, one lime accent. Red and amber appear only inside the product, as the status of a deploy.

## Motion language

> Hard cuts on the beat. Each screen holds still long enough to read. Type cuts in and cuts out. No zooms through the interface, no cursor trails.

## Voice rules

- no exclamation points, anywhere
- never "seamless", "powerful", "effortless" or "blazing"
- on-screen lines of seven words or fewer
- say what the screen shows, not how it feels
- one question at most, and only as the opening line

## Extraction notes

Audit trail for this extraction. The source was one written description from the team
(`brand/brightdock-description.md`). Values not listed here were read directly from it
(`extracted`): all five palette hex values, both font names, the never-list items and the
voice rules.

**Inferred** (reasoned from evidence, reasonable to ship):
- Archetype "Sage", from "we show you what happened": the product explains, it does not cheer.
- Mood adjectives, from "it should feel like a tool, not an ad".
- "One question at most", from the single question the description opens with.

**Needs confirmation** (best estimate, please verify):
- Motion language: from "keep it still enough to read". No existing video was provided.
- 4:5 for feed posts: the description names social video only; 4:5 is inferred from the channel.

---

**Last updated:** 2026-11-19
**Owner:** extracted
**Version:** 1.0
