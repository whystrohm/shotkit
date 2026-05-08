# Adapter: GPT Image (1.5 / 2)

GPT Image rewards paragraph-form prompts with explicit spatial reasoning and complex composition descriptions. It interprets relational language ("to the left of", "behind", "in the foreground") more accurately than any other generator. Choose GPT Image when the brief requires precise scene composition, multiple objects, or accurate text rendering.

## Syntax pattern

```
{Paragraph 1: subject, action, spatial composition}

{Paragraph 2: environment and contextual details}

{Paragraph 3: lighting, photographic specs, mood}
```

Paragraph breaks help GPT Image parse separate beats. One long monolithic paragraph underperforms, the model loses track of which detail applies where.

## Parameters

GPT Image is API-driven through OpenAI:

| Parameter | Default for storyboard work | Notes |
|---|---|---|
| `size` | `1024x1792` for 9:16, `1792x1024` for 16:9, `1024x1024` for 1:1 | Native aspect ratios |
| `quality` | `high` for hero shots, `medium` for series | |
| `style` | `natural` for photoreal, `vivid` for stylized | |
| `model` | `gpt-image-1.5` (or `gpt-image-2` if available) | |

Document in comment:
```
# shot_01, params: size=1024x1792, quality=high, style=natural, model=gpt-image-1.5
{prompt}
```

## Length

GPT Image handles **150–300 words** comfortably. Longer than other generators. Use the headroom for explicit spatial descriptions.

## Spatial language strength

GPT Image's distinctive capability, describe spatial relationships explicitly:

- "The founder is positioned in the left third of the frame, leaving the right two-thirds open."
- "A laptop sits on the desk in the foreground, a window with afternoon light is visible in the background."
- "The subject's shoulders are angled 30 degrees toward the camera, face turned to look at the off-frame light source."

Use this when the shot's composition is load-bearing.

## Composition pattern

```
{Subject paragraph: who is in the frame, what they're doing, where they are positioned in the composition. Reference series_lock character anchor verbatim.}

{Environment paragraph: setting, props, contextual elements. Pull from series_lock environment.}

{Technical paragraph: lighting from series_lock, photographic spec, color grade from brand_lock, mood. Close with "natural skin texture, no AI rendering artifacts" if photoreal.}
```

## Example

**Same shot data as previous examples.**

**Output prompt:**
```
A founder in his mid-thirties with salt-and-pepper hair, wearing a navy crewneck sweater, leans forward at his laptop. He is positioned in the left third of the frame, his face turned partially toward the window light off-camera left. The composition deliberately reserves the right two-thirds of the frame as negative space.

The setting is a minimalist home office. White walls, an oak desk in the immediate foreground, the laptop screen partially visible. A large window is implied off-frame to the left, source of the natural light. No clutter, no decorative objects.

Soft natural side-light from the window left, warm afternoon golden hour temperature, gentle shadow rolloff. Shot on a 50mm prime lens at f/2.0, shallow depth of field with the background softly out of focus. Warm filmic color grade with muted teal shadows. The mood is calm and considered, operator energy, not creator energy. Natural skin texture, no AI rendering artifacts.
```

## Text rendering

GPT Image handles text-in-image at roughly 95% accuracy, second only to Ideogram. When text is required:

- Put the exact text in straight double-quotes within the prompt
- Specify position explicitly ("centered in the lower third")
- Specify approximate typeface character ("bold sans-serif", "elegant serif")
- Limit to one text element per prompt for reliability

Default for storyboard work is still composited text, keep the override flag pattern from the Ideogram adapter.

## Pitfalls to avoid

- **Don't write Midjourney-style comma stacks**. GPT Image parses them as a list of disconnected concepts
- **Don't omit spatial language when the shot has specific composition**, you're paying for the model's strength; use it
- **Don't pile too many objects**, five or fewer distinct elements per scene; more degrades fidelity
- **Don't include `--ar` flags or weight syntax**. GPT Image ignores them
- **Don't forget that GPT Image's "AI look" is real**, the closing "natural skin texture, no AI rendering artifacts" line meaningfully helps but isn't a complete fix. For pure photoreal, Flux is still stronger

## API access

GPT Image is OpenAI-only as of Q2 2026. Standard `images.generate` endpoint. Pricing roughly $0.04–0.08 per image depending on size and quality. ChatGPT Plus and above gives UI access.
