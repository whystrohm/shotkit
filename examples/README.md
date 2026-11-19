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

`tools/check.sh` runs these checks on the example on every change.
