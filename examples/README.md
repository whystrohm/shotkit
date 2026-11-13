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
copies. The critiques pin the original PNG files by hash, and those are not in the repo,
so the provenance check reports seven reviewed frames as missing and the board marks
each of those checks "reviewed file not in this folder". The shots, the brand lock and
the prompt files all pass `tools/sk validate examples/harbor-roast`.
