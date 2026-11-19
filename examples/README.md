# Examples

## brightdock

A 20-second 9:16 launch video for a software product, made from the team's own screens.
Six shots, all accepted, nothing generated. Brightdock is not a real product. Its screens
were drawn in HTML for this example and used the way a team would use screenshots of its
own app.

This is the run `sk board --example` opens:

```bash
tools/sk board --example                     # from a clone
~/.claude/shotkit-tools/sk board --example   # after ./install.sh
```

Export it:

```bash
tools/sk export examples/brightdock
```

That writes carousel stills at 9:16 and 4:5, a PowerPoint deck and a 20-second rough cut
to `examples/brightdock/export/`. See [Export](../docs/export.md).

It passes every check as it is:

```bash
tools/sk validate examples/brightdock
```

## harbor-roast

A 15-second 9:16 ad for a fictional coffee roaster, with generated frames. Harbor Roast
is not a real company. Five shots, ten generators, two rounds. The critic sent two shots
back after round 1. One passed in round 2 and one is still marked REVISE, so the board
shows a run that is not finished yet.

```bash
tools/sk board examples/harbor-roast --open
```

The frames were generated with the prompts in `prompts/`. They are here as web-size JPEG
copies. The critiques pin the original PNG files by hash, and those are not in the repo.
So check this example with `--frames-optional`, which reports the seven reviewed frames
as not in the folder and checks everything else:

```bash
tools/sk validate examples/harbor-roast --frames-optional
```

Without the flag the provenance check fails on those seven frames, which is what it
should do for a run of your own. `tools/check.sh` runs both examples on every change.
