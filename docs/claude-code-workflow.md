# Claude Code Workflow

Claude Code is the primary install target for shotkit. The skills auto-discover, compose with other Claude Code skills, and write output files directly into your working directory. This doc covers the install mechanics, scope decisions, and how to drive the pack from natural-language prompts.

## Installing

The repo ships an `install.sh` script that copies all five skills into a Claude Code skills directory.

```bash
git clone https://github.com/whystrohm/shotkit.git
cd shotkit
./install.sh             # user scope: ~/.claude/skills/
./install.sh --project   # project scope: ./.claude/skills/
```

After install, restart your Claude Code session. The five skills appear in the available-skills list and trigger on natural-language prompts.

To verify install:

```bash
ls ~/.claude/skills/ | grep -E "storyboard|visual|brand-lock"
# expected:
#   brand-lock-extractor
#   storyboard-architect
#   storyboard-html-preview
#   visual-asset-critic
#   visual-prompt-forge
```

If those five directories are present, you are wired.

## User scope vs project scope

Two install targets. Different use cases.

**User scope** (`~/.claude/skills/`) makes the pack available across every Claude Code session on your machine. Use this when shotkit is part of your daily content workflow regardless of project.

**Project scope** (`./.claude/skills/`) installs the pack into a single project directory. Use this when you want shotkit available only inside a specific repo, typically because the project commits its `.claude/` directory to share skills with collaborators.

For solo operators running shotkit across multiple brand directories, user scope is correct. For agencies sharing a project repo with a client, project scope keeps the install scoped to that engagement.

The two scopes are not mutually exclusive. User-scope install plus a project-scope override on a specific machine is a valid pattern.

## How auto-discovery works

Claude Code reads `~/.claude/skills/` and `./.claude/skills/` at session start. Each subdirectory containing a valid `SKILL.md` becomes an available skill, indexed by the `name` and `description` fields in the YAML frontmatter.

When you describe a task in a prompt, Claude matches against the descriptions of available skills and triggers the most relevant one. The shotkit descriptions are tuned for natural-language patterns operators actually use:

- "Extract a brand-lock from acme.com" triggers `brand-lock-extractor`
- "Storyboard a 30-second explainer for X" triggers `storyboard-architect`
- "Generate prompts for these shots" triggers `visual-prompt-forge`
- "Critique this generated image" triggers `visual-asset-critic`
- "Render a preview of this storyboard" triggers `storyboard-html-preview`

You do not need to invoke them by name. Describe the work and the right skill takes over.

## First-run behavior

The first time you trigger a shotkit skill in a session, expect Claude to:

1. Acknowledge the skill (briefly, by name)
2. Ask any clarifying questions the brief left ambiguous
3. Read the relevant brand-lock file from `brand-packs/`
4. Produce the output set into your working directory under `output/`
5. Write `run.json`, pinning each of those files by content hash

If a brand-lock is missing or invalid, the skill says so before producing anything. If the brief is missing required information (duration, beat framework, brand), the skill asks for it.

A clean first run looks like:

```
You: 30s pain-proof-promise for WhyStrohm. Use brand-packs/whystrohm.md.

Claude: storyboard-architect engaging. Reading brand-packs/whystrohm.md.
        Brief looks complete. Producing storyboard.

[output/ directory created with 5 spec files]

Claude: Done. Open output/preview.html to review.
```

If the run takes more than one round-trip, the brief was ambiguous. The follow-up question will be specific (which beat framework, which generator, which aspect ratio).

## Composing with other Claude Code skills

shotkit is designed to compose. The five skills cooperate by file format, not by import. They also compose with other community skills:

- **Brand-voice extractors** (e.g. media-tsunami) feed into `brand-packs/`
- **Frontmatter-aware editors** can hand-edit `shots.json` between runs
- **Render skills** can read `shots.json` and produce video without re-running storyboard-architect
- **Publishing skills** can read `text-overlays.json` and post per-platform copy

The composition pattern is consistent: shotkit produces files, other skills consume files. No skill in the pack calls another skill directly. Every step in the pipeline is a file boundary.

## Where output files land

The skills write to your current working directory by default. The default output path is `./output/`.

Override the path by including a target in the prompt:

> "Storyboard a 30-second explainer for WhyStrohm. Output into ./projects/launch-q3/."

The skill creates the target directory and writes the five spec files. Generation and review
add the round directories underneath.

For multi-storyboard projects, name the output directory after the storyboard:

```
projects/launch-q3/
├── 30s-pain-proof-promise/
│   ├── run.json
│   ├── storyboard.md
│   ├── shots.json
│   ├── text-overlays.json
│   ├── brand-lock.snapshot.md
│   ├── prompts/round-1/flux.txt
│   ├── frames/round-1/shot_01.png
│   └── critiques/round-1/shot_01.critique.json
└── 60s-founder-explainer/
    └── ...
```

Round-and-shot paths are what let two people work the same project without overwriting each
other. See [`docs/the-qa-loop.md`](./the-qa-loop.md).

The audit-trail pattern (see [`docs/audit-trail-pattern.md`](./audit-trail-pattern.md)) makes this directory structure trivial to manage in Git. Commit `run.json` with the spec files: it is what proves, later, that the snapshot in the directory is the snapshot the frames were built from.

## Common Claude Code patterns

A few patterns operators run frequently.

**Render a preview from existing files.**

> "Render a preview of the storyboard in ./output/."

Triggers `storyboard-html-preview` against the existing files. Useful after hand-editing `shots.json` between generations.

**Critique a generated image.**

> "Critique this image against shot_03 in ./output/shots.json."

Triggers `visual-asset-critic`. Compares the image against the shot spec and the brand-lock snapshot. Returns ACCEPT, REVISE, or REJECT with rationale.

**Regenerate prompts for a different generator.**

> "Generate Flux prompts for ./output/shots.json."

Triggers `visual-prompt-forge` with the Flux adapter. Writes `output/prompts/round-1/flux.txt`.

**Update a single shot.**

> "Hand-edit shot_03 in ./output/ to use a tighter framing."

Claude reads the file, edits the shot, and offers to re-render the preview. The single-file edit pattern works because the shots.json schema is the source of truth.

## Invoking a specific skill explicitly

Most of the time, natural-language prompts route to the correct skill. When they do not, you can name the skill directly.

> "Run storyboard-architect on this brief: ..."

This bypasses the skill-routing layer and engages the named skill directly. Useful when:

- Two skills could plausibly handle the prompt and you want the specific one
- You are debugging a workflow and want to isolate one skill's behavior
- You are running the pack programmatically and want deterministic routing

For day-to-day work, natural-language prompts are sufficient.

## Updating shotkit

```bash
cd shotkit
git pull
./install.sh
```

`install.sh` also refreshes `~/.claude/shotkit-tools/`, which is where the validators land.
Re-run the checks after an update:

```bash
./tools/check.sh
```

Upgrading from v2.0.0 changes the output layout: critiques, prompts, and frames now live under
`round-N/` directories. Existing trees still read, and nothing is migrated for you. See the
breaking-change table at the top of `CHANGELOG.md`.

The script handles existing installs by replacing the skill directories. No state carries over from the prior version. Brand-packs, output files, and project state live outside the skills directory and are unaffected.

For shotkit, the install is idempotent. Running `./install.sh` repeatedly produces the same result. There is no upgrade-migration to manage because the pack owns no persistent state.
