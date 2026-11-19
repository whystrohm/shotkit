# Brightdock: the deploy log your team can read

| | |
|---|---|
| **Duration** | 20s |
| **Aspect** | 9:16 |
| **Beat framework** | Educational Demo |
| **Brand lock** | [`brand-lock.snapshot.md`](./brand-lock.snapshot.md) |
| **Pictures** | Drawn in code from the brand lock, six of six shots |
| **Generated** | 2026-11-19 12:00:00 UTC |

---

## Brief

The brief, as given: "20-second 9:16 launch video for Brightdock. Draw the product screens, do not generate them. No voiceover. Use brand/brightdock.md as the brand lock."

Brightdock is a fictional product made for this example.

A vertical launch video for a deploy log. The audience is engineers on small teams who scroll with the sound off, so every line is on screen. The goal is to show the product doing its three jobs and name it.

Every frame was drawn in code by `sk design` from the cards in `design/cards.json`. No model made a picture, so there are no prompts in this run.

Sound, as intent for the edit: one steady electronic pulse at about 100 bpm, with cuts on the beat. The brief did not ask for sound, so this is a suggestion.

## Beat framework: Educational Demo

- 0.0 to 3.0s. Problem (a wall of raw logs, the hook in the first 2s)
- 3.0 to 6.5s. Reveal (every deploy on one page)
- 6.5 to 16.5s. Walk-through (open one, roll back, the team is told)
- 16.5 to 20.0s. Result (the product named, and where to find it)

## Series lock

| | |
|---|---|
| **Character anchor** | no people on screen; the product's own interface is the subject of every shot |
| **Environment** | Brightdock's dark interface on a near-black ground, one panel per shot in the lower two-thirds, the upper third left empty |
| **Lighting** | flat screen light, a faint lime glow at the top and bottom edges of the frame |
| **Color grade** | no grade: near-black #0B0D10, off-white #F4F5F0, one lime accent #C8F250; red and amber only as deploy status inside the product |

## Shots

| # | Time | Beat | On screen | Picture |
|---|---|---|---|---|
| 01 | 0.0 to 3.0s | Problem | Who shipped what, and when? | `lines` card, raw deploy logs with one failed line in red |
| 02 | 3.0 to 6.5s | Reveal | Every deploy on one page. | `list` card, the deploy list |
| 03 | 6.5 to 10.0s | Walk-through | Open one. See what changed. | `detail` card, deploy 214 open |
| 04 | 10.0 to 13.5s | Walk-through | Roll back in one click. | `action` card, the roll back button |
| 05 | 13.5 to 16.5s | Walk-through | Your team hears first. | `notices` card, three notices |
| 06 | 16.5 to 20.0s | Result | The deploy log your team can read. | `mark` card, the mark and the name |

All type is Bricolage Grotesque ExtraBold in off-white, with the words that carry each line in lime. It cuts in and cuts out. Nothing fades.
