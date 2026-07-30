# Claude.ai Workflow

shotkit also runs in Claude.ai (web, desktop, mobile). The methodology is identical. The mechanics differ. This doc covers what changes when you run the pack through the Claude.ai interface instead of Claude Code.

## Installing through Settings

Claude.ai accepts skills as `.skill` zip uploads through the Settings panel.

To install all five shotkit skills:

1. Clone or download the shotkit repo
2. Zip each skill directory individually:

   ```bash
   cd shotkit/skills
   for s in *; do (cd "$s" && zip -r "../../$s.skill" .); done
   ```

3. In Claude.ai, open Settings, navigate to Skills, click Install
4. Upload each `.skill` file (five total)
5. Confirm all five show as Active in the skill list

Restart the Claude.ai session and the skills are live.

The zip-and-upload step is the operational difference from Claude Code. In Claude Code, the install script handles this against `~/.claude/skills/`. In Claude.ai, you upload each skill as a discrete artifact through the UI.

## File upload limits

Claude.ai sessions have file upload limits that affect how shotkit runs.

- Per-message attachment limits vary by plan. Pro and Team allow more attachments than Free.
- Brand-pack files (typically 1 to 3 KB) fit comfortably on any plan.
- Reference images for visual-asset-critic critique runs (typically 500 KB to 5 MB) work on all plans.
- Generated image batches (10+ images at 5 MB each) may need to be split across messages on lower-tier plans.

For solo operators running occasional storyboards, Free or Pro is enough. For agencies running sustained throughput, Pro or Team gives the headroom.

## Session expectations

Claude.ai sessions are stateful within a conversation but reset between conversations. This affects shotkit in two ways.

**Brand-pack files must be re-uploaded per session.** Claude Code reads them from disk on every run. Claude.ai needs them attached to the conversation. Drag the brand-pack file into the chat at the start of any storyboard session, and Claude holds it in context for the rest of the conversation.

**Output files must be downloaded before the session ends.** In Claude Code, the pack writes to your local filesystem. In Claude.ai, the pack produces output as message attachments. Click the attachment, save it locally, before closing the conversation. After the conversation closes, the attachment remains accessible through chat history but is no longer easy to bulk-download.

The pattern operators land on: one storyboard per Claude.ai conversation, brand-pack uploaded at conversation start, all four output files downloaded at conversation end, conversation archived for the audit trail.

## Differences from Claude Code

Three operational differences between the two surfaces.

**Auto-discovery does not apply.** Claude Code reads `~/.claude/skills/` automatically at session start. Claude.ai does not have a filesystem to read. Skills are uploaded explicitly per skill.

**Working directory does not exist.** Claude Code writes output relative to the directory where you started the session. Claude.ai produces output as message attachments. The "where files go" question gets answered differently in each surface.

**Session lifetime is bounded.** Claude Code sessions can run indefinitely. Claude.ai conversations have soft limits driven by message count and context window. For storyboards under 90 seconds, the limits are not a concern. For long-running review-and-iterate sessions, you may need to start a new conversation and re-upload the brand-pack.

The methodology is identical across surfaces. The skills produce the same `storyboard.md`, the same `shots.json`, the same prompt files. Only the file mechanics differ.

## Downloading output files

When a shotkit skill produces output in Claude.ai, the five core files appear as message attachments in order:

1. `run.json`
2. `storyboard.md`
3. `shots.json`
4. `text-overlays.json`
5. `brand-lock.snapshot.md`

If `visual-prompt-forge` ran in the same conversation, the per-generator prompts appear as additional attachments named `prompts-round-{N}-{generator}.txt`. Rebuild the directory structure locally when you save them; the round in the name is what keeps a revision pass from overwriting the original.

### Two limits worth knowing on this surface

**The validators are not there.** `tools/` is a repo directory, not part of a skill upload,
so nothing in a Claude.ai conversation can run `validate_shots.py` or the critique gate. The
model will check by hand against the schema, which is weaker. For work under real
accountability, save the output locally and run:

```bash
python tools/validate_shots.py path/to/output/
python tools/validate_provenance.py path/to/output/
```

**Cross-skill file references break.** Each skill is uploaded as a separate `.skill` zip, so
a path like `../storyboard-architect/templates/shots.schema.json` has no parent to resolve
against. If a skill asks for a schema it cannot reach, paste the schema into the
conversation rather than letting it work from memory of the format.

Click each attachment to download. Save them into a local directory matching the project structure documented in [`docs/audit-trail-pattern.md`](./audit-trail-pattern.md). The directory layout is identical regardless of which surface produced the files.

## When Claude.ai is the right surface

Claude.ai fits these cases better than Claude Code:

- **One-off storyboards.** No project structure, no recurring runs, just produce a single deliverable for review.
- **Stakeholder-led sessions.** A brand director without local Claude Code installed can run shotkit in Claude.ai through the browser.
- **Mobile work.** Claude.ai mobile apps can run the pack. Useful for capturing brief details in transit and producing a draft storyboard before the next desk session.
- **Cross-machine consistency.** Same Claude.ai login, same pack, any machine. No install required per device.

## When Claude Code is the right surface

Claude Code fits these cases better:

- **Repeated runs against the same brand-pack.** Filesystem persistence saves the per-session re-upload step.
- **Multi-storyboard projects.** Local directory layout, Git versioning, batch operations.
- **Composition with other skills.** Claude Code handles skill composition more cleanly because every skill writes to the same filesystem.
- **Programmatic invocation.** Scripts and CI can run Claude Code, Claude.ai is interactive only.

For solo operators running daily content infrastructure, Claude Code is the default. Claude.ai becomes the failover and the cross-machine surface.

## Pairing brand-packs with the skills

In Claude.ai, the brand-pack file is a per-conversation attachment. Drag `brand-packs/whystrohm.md` (or your own brand-pack) into the chat at the start of the conversation, then describe the storyboard:

> "Storyboard a 30-second pain-reframe-promise piece. Use the attached brand-pack as the brand lock. Aspect 9:16."

Claude reads the attached brand-pack, snapshots it into `brand-lock.snapshot.md` as part of the output, and produces the rest of the file set against it.

The snapshot output is what makes the audit trail work in Claude.ai despite the lack of a persistent filesystem. The snapshot is a frozen copy of the brand-pack at the time of the run. Six months later, replaying the conversation reconstructs the brand state without needing access to the original brand-pack file.

This is the audit-trail pattern (see [`docs/audit-trail-pattern.md`](./audit-trail-pattern.md)) applied across surfaces. Claude Code reads the brand-pack from disk, Claude.ai reads it from a chat attachment. The snapshot output is identical either way.
