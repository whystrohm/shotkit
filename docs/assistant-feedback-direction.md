# Assistant and feedback direction

Confirmed by Yuri on November 15, 2026. These are product requirements for Shotkit,
the creative board, and its sequence/render workflow. They do not describe features
that are already implemented. The current render demo has source-based suggestions
and explicit language checks, with no connected model or learning system.

## Core experience

Natural language, chat, and voice are primary ways to build and revise the work.
They must operate on real project objects: assets, boards, shot plans, prompts,
captions, sequences, variants, and render jobs. A fixed phrase parser alone does
not meet this requirement.

The assistant should understand the active client, project, selected objects,
paid-ad or organic mode, platform, objective, brand guidance, and current revision.
It should help the person make decisions, recommend useful next steps, explain
its reasons, and carry accepted suggestions through to actual changes. Suggestions
must remain relevant to the work and easy to accept, edit, or dismiss.

Voice uses the same capabilities as chat. References such as "these clips" resolve
against the selection captured when the instruction begins. Ambiguous targets need
clarification. Manual, keyboard, chat, voice, CLI, and MCP actions should share one
validated command path, with undo and checks for intervening edits. A clear request
authorizes the requested action; avoid repeated confirmations for already authorized
work. Larger or ambiguous changes should have a reviewable proposal.

## Feedback is a core input

Capture likes, dislikes, preferred variants, accepted suggestions, rejected
suggestions, and the person's edits. Offer a quick optional reason such as voice,
hook, pacing, visual direction, captions, factual support, or client fit. Preserve
the actual before/after version and affected object, rather than only a rating.

Feedback needs a person, timestamp, project/client scope, task and mode, source
version, suggestion or action, decision, optional reason, and correction where
present. Preferences from one client must not silently become another client's
rules. Apply broader personal or niche preferences only with explicit scope.

Use relevant feedback to improve later recommendations and revisions. The person
should be able to inspect learned preferences, edit them, reverse a rating, and
remove a preference from future use. Show the applicable preference or example
behind a recommendation when useful. Store feedback and derived profiles locally
by default. Provider requests should receive only the context needed for the task.

## Keep distinct records

- A preference records what someone likes or dislikes.
- An editorial decision records the chosen version or edit.
- A critique records findings against a shot, media version, and brand state.
- Approval records an explicit sign-off. A like is not approval.
- Performance records observed publishing results and their context. A liked hook
  is not proof that it converts, and views alone do not establish a business result.

Brand rules, verified facts, and source restrictions remain authoritative. Learning
must not quietly weaken them. Preserve pinned Shotkit inputs and historical review
evidence. New intent needs a deliberate revision, not a rewrite of past records.

## Shared Shotkit capability

Client memory and feedback should be usable by Shotkit skills and future CLI/MCP
tools as well as the board. A useful correction made while planning a shot should
be available when recommending a hook, writing a caption, arranging a sequence,
or critiquing a later version. This must not depend on one chat transcript or model.

An initial implementation can use versioned client profiles, relevant approved
examples, correction history, and preference-aware retrieval or ranking. Changing
model weights is a separate technical choice. Do not claim model training or
performance improvement until it actually runs and is evaluated.

The event schema, profile format, model/provider integration, and evaluation method
remain design work. Shotkit shared contracts should define any eventual common
format rather than incompatible board-only records.

## Acceptance examples

- A chat or voice request builds a real sequence from selected clips and returns
  its rendered output to the board, with the source versions recorded.
- A rejected hook with a reason affects the next relevant proposal for that client.
- An accepted caption correction is available to later Shotkit work in its scope.
- Another client's suggestions do not inherit that correction without permission.
- Removing a learned preference changes future recommendations while preserving
  the historical decision record.
- Preference, approval, and measured performance stay visibly distinct.
