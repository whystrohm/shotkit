# The Audit Trail Pattern

A storyboard isn't just a creative artifact. It's a decision record. Six months from now, someone, maybe you, needs to be able to answer:

- Why does this shot look this way?
- What brand state was this approved against?
- What changed between version 1 and version 2?
- If we want to regenerate this, what inputs do we need?

The audit trail is the answer to all of those.

## The five files that make a storyboard auditable

Every storyboard run produces these five files. None are optional.

```
output/
├── run.json                   # Run identity, and every input pinned by content hash
├── storyboard.md              # Human-readable spec, with rationale per shot
├── shots.json                 # Machine-readable, schema-validated
├── text-overlays.json         # On-screen text, separated from images
└── brand-lock.snapshot.md     # Frozen copy of the brand-lock at run-time
```

Each file does one job in the audit trail.

### `run.json`, the thing that makes the other four provable

Reading this answers "are the files next to these frames the files they were built from."

The other four files are named references to each other. `shots.json` points at
`brand-lock.snapshot.md` by filename. A filename survives its contents being replaced, so
for a long time this pattern could tell you *which file* a storyboard targeted and not
*which version of it*. Re-run the architect against an updated brand-pack and the snapshot
is overwritten in place; every reference still resolves and nothing reports a change.

`run.json` closes that by recording a SHA-256 for each input alongside a `run_id` and a
`created_at` instant:

```json
{
  "run_id": "20260730T142300Z-9f2c1ab4",
  "created_at": "2026-07-30T14:23:00Z",
  "inputs": {
    "shots_ref": "shots.json",
    "shots_sha256": "e3b0c44298fc1c14...",
    "brand_lock_ref": "brand-lock.snapshot.md",
    "brand_lock_sha256": "2c26b46b68ffc68f...",
    "brand_lock_source": "brand-packs/whystrohm.md",
    "brand_lock_configured": true
  }
}
```

`tools/validate_provenance.py` recomputes those hashes. A mid-project brand-lock edit fails
there instead of silently repointing the project's history.

### `storyboard.md`, the human-readable record

Reading this should answer "what was the intent." It includes:

- The brief summary
- The beat framework chosen
- Series lock (character, environment, lighting, color grade)
- Every shot with timing, framing, motion, subject, and rationale
- Every text overlay with content, timing, and styling

If a stakeholder asks "why is shot 3 a wide shot," the answer is in the rationale field of shot 3.

### `shots.json`, the machine-readable record

Reading this answers "what does the pipeline need to act on." It's the source of truth for every downstream tool:

- `visual-prompt-forge` consumes it to produce per-generator prompts
- `storyboard-html-preview` consumes it to render the preview
- `visual-asset-critic` consumes the relevant shot to critique a generated image
- A custom video-pipeline bridge can consume it to render the final video

When the JSON is the source of truth, regenerating any artifact is one command. When the source of truth is "the AI's response," nothing is reproducible.

### `text-overlays.json`, the text record

Reading this answers "what was meant to appear on screen, when, in what style." Separated from images deliberately, text and image have different production paths.

### `brand-lock.snapshot.md`, the frozen brand state

Reading this answers "what brand version was this built against." This is the file most teams skip and most often regret skipping later.

The brand-lock evolves. Palettes shift. Type changes. Mood adjectives get refined. When a storyboard from March looks slightly off compared to a storyboard from June, the difference is in the brand-lock state at run time.

Snapshotting the brand-lock per run captures this. The snapshot is dated and references the source path:

```html
<!-- snapshot taken: 2026-05-07T14:23:00Z -->
<!-- source: brand-packs/whystrohm.md -->
```

If the brand-lock is updated later, the snapshot stays frozen. The storyboard remains reproducible against its original inputs.

## The defense influence

This pattern came from defense-adjacent design work. In defense contexts:

- Every artifact has a chain back to the source decision
- "Why does it look this way" is answered by reading the file, not asking a person
- Reproducibility is a requirement, not a feature
- Stakeholders six months later have access to everything they need without asking the team

These reflexes don't get less useful in commercial work. They get less common, but not less useful.

When a client asks "what version of our brand did this storyboard target," and you can hand them a frozen snapshot from the date of approval, that's a different conversation than "let me check with the designer."

## What the audit trail enables

**Versioning across time.** Storyboards from before a brand refresh stay valid against their original brand-lock. New storyboards target the new state. Both are explicit.

**Regeneration on demand.** If a client wants to re-run a storyboard with a different generator or a different aspect ratio, the JSON is the input and you do not start over.

Be precise about what is reproducible, though. The spec files are: same `shots.json` and
brand-lock produce the same prompts, and `tools/shots-to-html.py` re-renders the same
preview byte for byte given a pinned timestamp, which CI checks on every push. The *frames*
are not. Image generation is non-deterministic even at a fixed seed on most services. That
is why the audit trail records the hash of the frame you actually shipped rather than
implying you could conjure it again.

**Cross-team handoff.** An editor reading `storyboard.md` knows the intent. A motion designer reading `shots.json` knows the spec. A brand director reading `brand-lock.snapshot.md` knows the constraints. Each role gets what they need without asking.

**Quality assurance.** The visual-asset-critic skill compares a generated image against the shot's spec and the brand-lock. Without the snapshot, it can't critique against historical brand state.

**Legal and compliance.** When a regulated industry asks "show us the state this was approved in," the five files plus the critique tree are the answer, and `validate_provenance.py` is how you show the files have not moved since. Approver identity is not in there, so if the question is "who signed this off," that part is still on you.

## What breaks without the audit trail

- "I made the storyboard last month, but I can't remember which brand version we were on", common when working across multiple clients
- "Why does this shot have a coral overlay?", answer is buried in a Slack thread
- "Can we regenerate this with new colors?", requires recreating the whole storyboard from scratch
- "The client wants to know what changed in v2", diff is impossible without snapshots

These aren't hypothetical. They're the daily friction of running content infrastructure without an audit trail.

## The spec-to-artifact half

The five files above cover the spec. Generation adds the other half, and it is addressed by
round and shot so nothing overwrites anything:

```
output/
├── prompts/round-1/flux.txt                    the prompt, hashed in run.json
├── frames/round-1/shot_02.png                  the frame
└── critiques/round-1/shot_02.critique.json     the verdict, hashing both of the above
```

A critique at schema `1.1` carries `image_sha256`, `prompt_sha256`, `brand_lock_sha256`,
`generator`, `model_version`, and `seed`. That is the link from spec to artifact: given a
frame, you can name the prompt that produced it, the generator and model version that ran,
the brand state it was judged against, and the verdict it received, and you can prove the
frame has not changed since.

Earlier versions of this document described that link as an optional extension, a
`renders.json` a team might add, while also claiming the pattern already let you point to
"the prompt that drove the generation" and "the image that was approved." Both statements
could not be true. The mechanism is now shipped, so the claim is now safe to make.

**Still not shipped: approval logs.** Who signed off, and when, is not recorded anywhere.
`accepted: true` on a frame carries a `critique_ref`, so an acceptance traces to a critique,
but a critique is a review and not a human approval. If you need approver identity, that is
yours to add.

**Also worth adding: diff outputs.** When a storyboard is revised, a diff against the
previous version helps stakeholders see what changed without re-reading the spec. Git does
this well enough that shotkit does not try.

## How to use the audit trail in practice

**On a single project:**

- Commit all four output files to Git per major revision
- Tag commits with the storyboard version
- Reference the commit in approval communications

**Across many projects:**

- Each project has its own `output/` directory
- Brand-locks live in a shared `brand-packs/` directory
- A central registry maps projects to brand-lock versions

**For long-running brands:**

- Brand-lock changes get version-bumped, never overwritten
- Storyboards from before the change reference the prior brand-lock version
- New storyboards reference the current version
- The brand-lock change log itself is committed

## The audit trail is also the operator's defense

If something goes wrong with a piece of content, wrong color, wrong messaging, wrong character, the audit trail makes the failure analyzable. You can point to:

- The brief that drove the storyboard
- The brand-lock that governed the styling
- The shot spec that defined the composition
- The prompt that drove the generation
- The image that was approved

When the failure is in the brief, you can show that. When it's in the generation, you can show that. When it's in the approval process, you can show that.

Without the audit trail, every failure looks like operator error. With it, you can answer the question with evidence.

This is the operator's protection. It's also the operator's edge.
