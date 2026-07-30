# Adapter: Midjourney (v7)

> Capability data (length ceiling, text/motion support, aspect param) is canonical in `_capabilities.json`. This file is the how-to-prompt guidance. `max_prompt_words` there is a ceiling; the range below is the recommended target and has to sit inside it. Where a fact here and a fact in the JSON disagree, the JSON wins, and `tools/validate_capabilities.py` fails the build instead of letting the two drift.

Midjourney rewards short, high-signal prompts with strong adjective stacking and cinematic vocabulary. Long descriptive paragraphs underperform, the model interprets them as competing weights and produces muddled output.

## Syntax pattern

```
{subject}, {action}, {composition}, {environment}, {lighting}, {color/mood}, {style modifiers} --ar {ratio} --style {style} --s {stylize} {extras}
```

Comma-separated phrases. No full sentences. No connective words ("the", "with", "and") unless they're load-bearing.

## Parameter reference (current as of Q2 2026)

| Param | Values | Default to use | Notes |
|---|---|---|---|
| `--ar` | aspect ratio | from `project.aspect` | `--ar 9:16`, `--ar 16:9`, `--ar 1:1` |
| `--style` | `raw` / `4a` / `4b` / `4c` | `raw` | `raw` for photorealistic, omit for default Midjourney aesthetic |
| `--s` | 0–1000 | `50` for branded, `250` for artistic | Stylization weight. Lower = closer to prompt, higher = more MJ aesthetic |
| `--c` | 0–100 | omit | Chaos. Use only when exploring variations |
| `--seed` | integer | omit unless reproducing | For series consistency, set per-storyboard |
| `--cref` | image URL | use when character anchor exists | Character reference. Pair with `--cw` |
| `--cw` | 0–100 | `50` | Character weight. 100 = strict character match, 0 = clothing only |
| `--sref` | image URL | use when style anchor exists | Style reference |

## Length

Aim for **40–80 words per prompt** including parameters. Anything over 100 words underperforms.

## Composition mapping

Translate shot grammar into Midjourney-friendly phrases:

| shot_grammar | Midjourney phrase |
|---|---|
| `MCU eye-level` | `medium close-up, eye level` |
| `WS overhead` | `wide shot, overhead view, top-down` |
| `static` | (omit, static is default) |
| `push` | `dolly in, pushing forward` |
| `handheld` | `handheld documentary feel, slight motion blur` |
| `shallow DOF` | `shallow depth of field, f/1.8, bokeh background` |
| `deep DOF` | `deep focus, everything sharp, f/8` |

## Lighting language

Midjourney rewards specific lighting vocabulary:

- `soft natural light, large window left, warm afternoon golden hour`
- `hard top-light, single key, deep shadows, studio black backdrop`
- `practical mixed sources, neon accents, urban night, atmospheric haze`
- `volumetric backlight, rim light separating subject, cinematic haze`
- `chiaroscuro, dramatic side-light, painterly`

Pull verbatim from `series_lock.lighting`.

## Composition pattern

```
{framing} of {subject character_anchor}, {action}, {compositional note}, {environment from series_lock}, {lighting from series_lock}, {color_grade}, cinematic photography, {brand mood adjectives} --ar {aspect} --style raw --s 50
```

## Example

**Shot data:**
```json
{
  "id": "shot_03",
  "framing": "MS",
  "angle": "eye-level",
  "motion": "static",
  "subject": "Founder mid-thirties, leaning forward at laptop, face partially turned to window",
  "rationale": "MS framing leaves negative space right for text overlay"
}
```

**Series lock:**
```
character: founder, mid-thirties, salt-and-pepper hair, navy crewneck
environment: minimalist home office, white walls, oak desk
lighting: soft natural side-light, large window left, warm afternoon
color_grade: warm filmic, muted teal shadows
```

**Brand lock palette:** `#0F1F3A navy`, `#F5F0E8 cream`, `#D94F3A coral`

**Brand mood:** `calm, considered, operator, not creator`

**Output prompt:**
```
medium shot of founder mid-thirties, salt-and-pepper hair, navy crewneck, leaning forward at laptop, face partially turned to window light, negative space right of frame, minimalist home office, white walls, oak desk, soft natural side-light large window left, warm afternoon golden hour, warm filmic color grade, muted teal shadows, cinematic photography, calm considered operator mood --ar 9:16 --style raw --s 50
```

## Pitfalls to avoid

- **Don't use "AI" or "rendered"**, produces stylized outputs that look generated
- **Don't over-stack adjectives**, three adjectives per noun phrase max
- **Don't include text content**, even if the shot has `on_screen_text`, leave it out. Composited separately.
- **Don't use `--c` for series work**, chaos kills consistency
- **Don't change `--seed` mid-storyboard**, set once at series_lock level

## API access note

Midjourney still has limited API access as of Q2 2026. For programmatic workflows, the prompts in `midjourney.txt` are designed to be pasted into Discord or the web UI. Some teams use third-party wrappers (PiAPI, Useapi.net), those generally accept the same prompt syntax.
