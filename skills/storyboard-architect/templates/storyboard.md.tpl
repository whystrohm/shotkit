# {{PROJECT_TITLE}}

| | |
|---|---|
| **Duration** | {{DURATION}}s |
| **Aspect** | {{ASPECT}} |
| **Beat framework** | {{FRAMEWORK}} |
| **Brand lock** | [`brand-lock.snapshot.md`](./brand-lock.snapshot.md) |
| **Generated** | {{TIMESTAMP}} |

---

## Brief

{{BRIEF_SUMMARY}}

## Series lock

| | |
|---|---|
| **Character anchor** | {{SERIES_CHARACTER}} |
| **Environment** | {{SERIES_ENVIRONMENT}} |
| **Lighting** | {{SERIES_LIGHTING}} |
| **Color grade** | {{SERIES_COLOR_GRADE}} |

---

## Shots

{{#each shots}}
### {{id}} · {{start}}–{{end}}s · {{framing}} · {{motion}}

**Beat:** {{beat}}

**Subject:** {{subject}}

**On-screen text:** {{on_screen_text_resolved}}

**VO:** {{vo}}

**Rationale:** {{rationale}}

---
{{/each}}

## Text overlays

{{#each overlays}}
### {{id}}: `{{shot_id}}`

> {{content}}

| | |
|---|---|
| **Font** | {{font}} {{weight}} |
| **Size** | {{size}} |
| **Position** | {{position}} |
| **Color** | `{{color}}` |
| **Enter** | {{enter.at}}s · {{enter.animation}} |
| **Exit** | {{exit.at}}s · {{exit.animation}} |
| **On-screen** | {{duration}}s |

{{/each}}

---

## Handoff notes

- **For image generation:** run `visual-prompt-forge` against `shots.json`
- **For HTML preview:** run `storyboard-html-preview` against this folder
- **For QA on generated frames:** run `visual-asset-critic` with the generated image and the shot ID

## Audit trail

This storyboard was generated against `brand-lock.snapshot.md` (frozen at {{TIMESTAMP}}). If the brand-lock changes after this date, re-run to pick up the new state.
