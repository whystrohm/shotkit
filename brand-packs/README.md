# Brand Packs

A brand pack is a single Markdown file that locks in palette, typography, voice, and visual rules for a project. The skills in this pack consume it. Every storyboard, every prompt, every generated frame inherits from it.

## How to use

1. Copy `_template.md` to a new file (e.g. `acme.md`)
2. Fill in every field. No placeholders left behind.
3. Reference it from your storyboard requests:

   > "30-second founder explainer. Use `brand-packs/acme.md` as the brand lock."

4. The skill reads it, snapshots it into the output as `brand-lock.snapshot.md`, and applies it through the pipeline.

## How to write a good one

The template is a checklist, not a creative-writing exercise. Three rules:

**Be specific.** "Modern, clean, professional" is not a brand. "Calm, considered, operator energy, confident without shouting" is.

**Be exclusive.** The "never" list is more valuable than the "always" list. Listing what the brand will not do narrows the generator's space and produces tighter output.

**Be hex-precise.** Every color is a hex value. Every font is named. The skills consume structured data; vagueness here cascades into bad prompts later.

## Examples

The pack ships with two reference brand packs:

- **`whystrohm.md`** (flagship). The actual brand pack WhyStrohm uses on its own content. Real palette, real voice rules, real "never" list. Use this as the reference for the level of specificity production work requires.
- **`examples/saas-clean.md`**. B2B SaaS, restrained, professional. Light backgrounds, single accent. Inter type stack. A neutral counterpoint to the WhyStrohm flagship.

More example brand packs will land in v0.2.0. PRs welcome.

## Generating a brand pack from existing assets

Don't hand-author from scratch if the brand already exists. The **`brand-lock-extractor`** skill (ships in this repo at `skills/brand-lock-extractor/`) takes a website URL, a brand book PDF, screenshots, or a written description and produces a `brand-lock.md` in this exact format, with a confidence and source noted for every value:

> "Extract a brand-lock from acme.com" or "build a brand pack from this brand book PDF."

For bulk or programmatic extraction across many URLs, [media-tsunami](https://github.com/whystrohm/media-tsunami) (WhyStrohm's open-source brand voice extractor) scrapes URLs and produces a `brand-lock.md` in the same format.

## Versioning

Every storyboard run snapshots the brand pack it was built against. If you update `acme.md` later, previous storyboards still reference the version they were built on. This is intentional, the audit trail tells you exactly what brand state any given piece of content was built against.

When you make a brand-pack revision that materially changes look or voice, bump the `Version:` field at the bottom and note the change. e.g.:

```
Version: 1.1 (2026-05-12: switched accent from #D94F3A coral to #C44233 deeper coral)
```

## Contributing examples

PRs welcome for new brand-pack examples that fill gaps in the current set. Open an issue with the `brand-pack-request` template before submitting.
