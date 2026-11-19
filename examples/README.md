# Examples

## brightdock

A 20-second 9:16 launch video for a software product. Six shots, all accepted. Brightdock
is not a real product.

Every frame was drawn in code from the brand lock by `sk design`. Nothing was generated.
The cards are in `design/cards.json`. Change one and draw it again:

```bash
tools/sk design examples/brightdock           # redraw the six frames
tools/sk design examples/brightdock --check   # after a redraw, prove a second draw matches
```

This is the run `sk board --example` opens:

```bash
tools/sk board --example                     # from a clone
~/.claude/shotkit-tools/sk board --example   # after ./install.sh
```

Export it:

```bash
tools/sk export examples/brightdock
```

That writes carousel stills at 9:16 and 4:5, a PowerPoint deck, a 20-second rough cut and
the shoot and edit files to `examples/brightdock/export/`. See [Export](../docs/export.md)
and [Designed frames](../docs/designed-frames.md).

It passes every check as it is:

```bash
tools/sk validate examples/brightdock
```

`tools/check.sh` runs these checks on the example on every change.
