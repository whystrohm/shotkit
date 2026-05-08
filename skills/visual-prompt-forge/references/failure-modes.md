# Failure Modes

What goes wrong when generated images don't match the storyboard, and what to fix at the prompt level vs. accept as editorial work.

## Failure 1. The "AI look"

**Symptoms:** plastic skin, oversaturated colors, eyes too symmetrical, hands wrong, generic stock-photo composition, lighting that's too even, "rendered" feel.

**Causes:**
- Generic mood adjectives ("beautiful", "stunning", "amazing")
- Stable Diffusion crutches ("4k", "highly detailed", "masterpiece") in non-SD generators
- Missing photographic specifics
- No "never" list applied from brand-lock

**Prompt-level fixes:**
- Add specific lens and aperture ("50mm prime, f/2.0")
- Add film stock or camera reference ("Sony FX6", "Kodak Portra 400 film stock")
- Add "natural skin texture, no AI rendering artifacts" closing line (Flux, GPT Image)
- Verify brand-lock "never" list is being applied, if it includes "no AI uncanny", surface that into the prompt
- Use Flux 2 Pro or Midjourney v7 instead of cheaper models for hero shots

**Accept editorially when:** the brief is for stylized content where realism isn't the goal.

## Failure 2. Character drift across shots

**Symptoms:** same person looks different in shot 1 vs shot 5; clothing changes; hair color shifts; age perceived differently.

**Causes:**
- Series_lock character string paraphrased rather than verbatim
- No reference image passed (`--cref`, omni-reference)
- Seed not locked
- Too few features described in character anchor (gives generator too much room)

**Prompt-level fixes:**
- Verify character string is verbatim across every prompt
- Add 1–2 more specific features ("small scar above left eyebrow", "black wireframe glasses")
- Use reference image after the first successful shot
- Lock seed at storyboard level
- For Midjourney, use `--cref` with `--cw 50`

**Accept editorially when:** character consistency is genuinely impossible to lock. Budget re-rolls, typically 2–3× per problematic shot.

## Failure 3. Text in image looks bad

**Symptoms:** text is misspelled, kerning is off, font is wrong, multiple text elements compete.

**Causes:**
- Text was put in the image prompt instead of being composited
- Wrong generator chosen (using Midjourney for text-heavy work)
- Multiple text elements in one prompt

**Prompt-level fixes:**
- The right answer is almost always: **don't put text in the prompt**. Composite separately from `text-overlays.json`.
- If text must be in-image (poster work), use Ideogram v3 with explicit override flag
- Limit to one text element per prompt
- Use simple fonts (sans-serif, clean serif), cursive and decorative fonts fail even on Ideogram

**Accept editorially when:** the deliverable genuinely requires baked-in text and Ideogram's output is close enough to retouch.

## Failure 4. Lighting direction inconsistency

**Symptoms:** shot 3 has light from window-left, shot 4 has light from window-right, they cut together as a continuity error.

**Causes:**
- Lighting language paraphrased rather than verbatim from series_lock
- Reverse-angle shots not flagged in rationale
- Generator interpreting lighting ambiguously

**Prompt-level fixes:**
- Verify lighting string is verbatim across prompts
- Be explicit about direction: "from camera-left" not "from one side"
- For reverse-angle shots, flag in rationale and update lighting language for that shot only
- For Flux and GPT Image, add the photographic spec ("key light camera-left at 45 degrees")

**Accept editorially when:** lighting drift is subtle enough that color grading will fix it.

## Failure 5. Composition doesn't reserve space for text overlay

**Symptoms:** the storyboard says text goes in the right third, but the generated image has the subject filling the right third.

**Causes:**
- Shot subject didn't include negative-space note
- Generator interpreting "centered subject" by default

**Prompt-level fixes:**
- Add explicit composition note: "subject framed in left third, right two-thirds open for text overlay"
- For GPT Image (best at spatial reasoning), use percentage references: "subject at left 30% of frame"
- Re-roll with explicit composition prompt, this often fixes on second try

**Accept editorially when:** image is otherwise great. Reposition text overlay to fit the actual composition.

## Failure 6. Series feels "different" even with locks applied

**Symptoms:** all locks are in place, prompts look right, but the storyboard feels disjointed when viewed end-to-end.

**Causes:**
- Color grade language drifting between shots (one says "warm filmic", another says "cinematic")
- Aspect ratio drift (some 9:16 generations are taller than others)
- Mood adjectives shifting ("calm" in shot 1 vs "energetic" in shot 5 even though brief was uniform)

**Prompt-level fixes:**
- Audit every prompt against series_lock and brand-lock, verbatim check
- Verify aspect ratio is identical across all prompts
- Lock the brand mood adjectives, same set in every prompt

**Accept editorially when:** the disjoint feel is below the noise floor for the medium (e.g. fast-cut social where each shot is on screen <2s).

## Failure 7, "Looks fine but doesn't match the brief"

**Symptoms:** image is technically good but doesn't capture what the brief was actually about.

**Causes:**
- The shot subject in `shots.json` was vague
- The brief context wasn't surfaced into the prompt
- The generator is producing competent generic output rather than specific intent

**Prompt-level fixes:**
- Tighten the shot's subject field, what specifically is the audience meant to feel or notice
- Include a one-phrase intent at the end ("the moment of recognition", "the calm before the decision")
- For complex scenes, add a "what this shot conveys" line

**Accept editorially when:** generation is close enough that retouching gets there. Don't burn API credits chasing perfect on-prompt.

## When to stop iterating prompts

Three signs:

1. You've re-rolled the same shot 5+ times with no improvement → the prompt is fine; the model can't render this concept; pick a different shot or different generator
2. You're tweaking single words and hoping → you've hit prompt-level diminishing returns; move to image-to-image refinement (Nano Banana) or post-production
3. The image is 80% right and the gap is editorial → ship to post and let the editor finish

Generation is one stage in a pipeline. Don't try to make it the whole pipeline.
