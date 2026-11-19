# Examples

## harbor-roast

One finished Shotkit run, with its frames: a 15-second 9:16 ad for a fictional coffee
roaster. Harbor Roast is not a real company. Five shots, ten generators, two rounds. The
critic sent two shots back after round 1. One passed in round 2 and one is still marked
REVISE, so the board shows a run that is not finished yet.

Open its board:

```bash
tools/sk board --example            # from a clone
~/.claude/shotkit-tools/sk board --example   # after ./install.sh
```

The frames were generated with the prompts in `prompts/`. They are here as web-size JPEG
copies. The critiques pin the original PNG files by hash, and those are not in the repo.
So check this example with `--frames-optional`, which reports the seven reviewed frames
as not in the folder and checks everything else:

```bash
tools/sk validate examples/harbor-roast --frames-optional
```

Without the flag the provenance check fails on those seven frames, which is what it
should do for a run of your own. The board marks each of them "reviewed file not in this
folder". `tools/check.sh` runs this example with the flag on every change.
