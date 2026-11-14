<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="generator" content="shotkit board">
<meta name="color-scheme" content="dark">
<title>__TITLE__ · Shotkit board</title>
<!--__FONT_LINKS__-->
<style>
:root {
  --bg: #08090B; --p1: #0E1013; --p2: #14171B; --p3: #1B1F24;
  --line: #22262D; --line2: #2E333B;
  --ink: #F3F2EE; --mut: #9096A0; --dim: #5D636D;
  --acc: #FF5A2B; --acc-ink: #150703;
  --accept: #35D08A; --revise: #F2B33D; --check: #6AA8FF; --wait: #6B717C;
  --sans: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", Roboto, "Helvetica Neue", Arial, sans-serif;
  --mono: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace;
  --r: 10px; --gut: clamp(16px, 3.2vw, 44px);
}
* { box-sizing: border-box; }
html { background: var(--bg); color: var(--ink); -webkit-text-size-adjust: 100%; }
body { margin: 0; font: 400 14px/1.5 var(--sans); -webkit-font-smoothing: antialiased; overflow-x: hidden; }
button { font: inherit; color: inherit; background: none; border: 0; padding: 0; cursor: pointer; }
a { color: inherit; }
h1, h2, h3, p, dl, dd, ul, ol { margin: 0; padding: 0; }
ul, ol { list-style: none; }
:focus-visible { outline: 2px solid var(--acc); outline-offset: 2px; border-radius: 4px; }
.mono { font-family: var(--mono); font-feature-settings: "zero" 1; }
.lab { font: 500 10.5px/1 var(--mono); letter-spacing: .09em; text-transform: uppercase; color: var(--mut); }

/* Top bar */
.bar { position: sticky; top: 0; z-index: 30; display: flex; align-items: center; gap: 14px; height: 52px; padding: 0 var(--gut);
  background: color-mix(in srgb, var(--bg) 86%, transparent); backdrop-filter: blur(14px) saturate(1.3); -webkit-backdrop-filter: blur(14px) saturate(1.3); border-bottom: 1px solid var(--line); }
.mark { display: flex; align-items: center; gap: 9px; font: 650 13px/1 var(--sans); letter-spacing: -.01em; }
.mark i { width: 16px; height: 16px; border-radius: 3px; background: var(--acc); position: relative; display: block; }
.mark i::after { content: ""; position: absolute; inset: 4px; border-radius: 1px; background: var(--bg); }
.mark span { color: var(--dim); font-weight: 450; }
.bar__title { color: var(--mut); font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; min-width: 0; flex: 1; }
.pill { display: inline-flex; align-items: center; gap: 7px; height: 24px; padding: 0 9px; border: 1px solid var(--line2); border-radius: 99px; font: 500 10.5px/1 var(--mono); letter-spacing: .07em; text-transform: uppercase; color: var(--mut); white-space: nowrap; }
.pill b { width: 6px; height: 6px; border-radius: 50%; background: var(--wait); }
.pill[data-live] { color: var(--accept); border-color: color-mix(in srgb, var(--accept) 35%, transparent); }
.pill[data-live] b { background: var(--accept); animation: pulse 1.8s ease-in-out infinite; }
@keyframes pulse { 50% { opacity: .25; } }
.btn { display: inline-flex; align-items: center; gap: 8px; height: 32px; padding: 0 12px; border: 1px solid var(--line2); border-radius: 7px; background: var(--p2); font: 550 12.5px/1 var(--sans); white-space: nowrap; transition: background .15s, border-color .15s, transform .1s; }
.btn:hover { background: var(--p3); border-color: #3B414B; }
.btn:active { transform: translateY(1px); }
.btn--pri { background: var(--ink); color: #0B0C0E; border-color: var(--ink); }
.btn--pri:hover { background: #fff; border-color: #fff; }
.btn--sm { height: 26px; padding: 0 9px; font-size: 11.5px; border-radius: 6px; }
.btn svg { width: 13px; height: 13px; flex: none; }
.btn[data-done] { color: var(--accept); border-color: color-mix(in srgb, var(--accept) 45%, transparent); }
.btn--pri[data-done] { background: var(--accept); color: #04160D; }

/* Head */
.head { display: grid; grid-template-columns: minmax(0, 1fr) minmax(300px, 420px); gap: clamp(20px, 4vw, 56px); align-items: end; padding: clamp(24px, 3.4vw, 44px) var(--gut) clamp(22px, 3vw, 34px); }
.head h1 { font: 680 clamp(28px, 4.6vw, 58px)/1.02 var(--sans); letter-spacing: -.035em; text-wrap: balance; margin-top: 14px; }
.facts { display: flex; flex-wrap: wrap; gap: 6px 22px; margin-top: 18px; color: var(--mut); font: 400 12px/1.4 var(--mono); }
.facts b { color: var(--ink); font-weight: 500; }
.next { border: 1px solid var(--line2); border-radius: var(--r); background: linear-gradient(180deg, var(--p2), var(--p1)); padding: 16px; position: relative; overflow: hidden; }
.next::before { content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 2px; background: var(--acc); }
.next h2 { font: 620 16px/1.25 var(--sans); letter-spacing: -.01em; margin: 9px 0 6px; }
.next p { color: var(--mut); font-size: 13px; }
.say { display: flex; align-items: center; gap: 10px; margin-top: 12px; padding: 8px 8px 8px 11px; border: 1px solid var(--line); border-radius: 7px; background: var(--bg); font: 400 12px/1.45 var(--mono); }
.say span { flex: 1; min-width: 0; }
.say em { font-style: normal; color: var(--acc); margin-right: 6px; }

/* Stats */
.stats { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 1px; margin: 0 var(--gut); border: 1px solid var(--line); border-radius: var(--r); overflow: hidden; background: var(--line); }
.stat { background: var(--p1); padding: 14px 16px 15px; }
.stat__n { display: flex; align-items: baseline; gap: 6px; margin-top: 9px; font: 620 26px/1 var(--sans); letter-spacing: -.03em; font-variant-numeric: tabular-nums; }
.stat__n small { font: 400 12px/1 var(--mono); color: var(--dim); letter-spacing: 0; }
.meter { height: 3px; margin-top: 12px; border-radius: 2px; background: var(--p3); overflow: hidden; }
.meter i { display: block; height: 100%; border-radius: 2px; background: var(--c, var(--ink)); width: var(--w, 0%); transition: width .6s cubic-bezier(.2,.7,.2,1); }

/* Timeline */
.tl { margin: 18px var(--gut) 0; border: 1px solid var(--line); border-radius: var(--r); background: var(--p1); overflow: hidden; }
.tl__scroll { overflow-x: auto; scrollbar-width: thin; scrollbar-color: var(--line2) transparent; }
.tl__in { min-width: 640px; padding: 12px 14px 12px 0; display: grid; grid-template-columns: 54px 1fr; row-gap: 5px; align-items: center; }
.tl__k { padding-left: 14px; }
.ruler { position: relative; height: 16px; font: 400 10px/1 var(--mono); color: var(--dim); }
.ruler span { position: absolute; top: 0; transform: translateX(-50%); padding-top: 7px; }
.ruler span::before { content: ""; position: absolute; left: 50%; top: 0; width: 1px; height: 4px; background: var(--line2); }
.ruler span:first-child { transform: none; } .ruler span:first-child::before { left: 0; }
.ruler span:last-child { transform: translateX(-100%); } .ruler span:last-child::before { left: 100%; }
.track { position: relative; height: calc(22px * var(--lanes, 1)); }
.track--shots { height: 58px; display: flex; gap: 2px; }
.seg { position: relative; flex: var(--d) 1 0; min-width: 0; border-radius: 5px; overflow: hidden; background: var(--p3) center/cover no-repeat; border: 1px solid var(--line2); text-align: left; transition: border-color .15s, filter .15s; }
.seg::before { content: ""; position: absolute; inset: 0; background: linear-gradient(180deg, rgba(8,9,11,.15), rgba(8,9,11,.78)); }
.seg::after { content: ""; position: absolute; left: 0; right: 0; bottom: 0; height: 3px; background: var(--c); }
.seg:hover, .seg[aria-current] { border-color: var(--ink); filter: brightness(1.15); }
.seg b { position: absolute; left: 7px; bottom: 9px; font: 600 11px/1 var(--mono); }
.seg span { position: absolute; left: 7px; top: 7px; right: 5px; font: 500 9.5px/1 var(--mono); letter-spacing: .07em; text-transform: uppercase; color: rgba(243,242,238,.75); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.clip { position: absolute; top: calc(2px + 22px * var(--lane, 0)); height: 18px; padding: 0 7px; border-radius: 4px; display: flex; align-items: center; font: 500 10.5px/1 var(--sans); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; min-width: 6px; }
.clip--t { background: color-mix(in srgb, var(--acc) 20%, var(--p2)); border: 1px solid color-mix(in srgb, var(--acc) 50%, transparent); color: #FFD9CC; }
.clip--v { background: color-mix(in srgb, var(--check) 15%, var(--p2)); border: 1px solid color-mix(in srgb, var(--check) 38%, transparent); color: #CFE2FF; font-style: italic; }
.clip > span { overflow: hidden; text-overflow: ellipsis; }

/* Toolbar */
.tools { position: sticky; top: 52px; z-index: 20; display: flex; align-items: center; gap: 10px; flex-wrap: wrap; padding: 12px var(--gut); margin-top: 26px; background: color-mix(in srgb, var(--bg) 90%, transparent); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border-top: 1px solid var(--line); border-bottom: 1px solid var(--line); }
.tools h2 { font: 620 14px/1 var(--sans); margin-right: 6px; }
.chips { display: flex; gap: 6px; flex-wrap: wrap; flex: 1; }
.chip { display: inline-flex; align-items: center; gap: 7px; height: 28px; padding: 0 10px; border: 1px solid var(--line); border-radius: 99px; color: var(--mut); font: 500 12px/1 var(--sans); transition: all .15s; }
.chip:hover { color: var(--ink); border-color: var(--line2); }
.chip[aria-pressed="true"] { background: var(--ink); border-color: var(--ink); color: #0B0C0E; }
.chip i { width: 6px; height: 6px; border-radius: 50%; background: var(--c, var(--wait)); }
.chip small { font: 400 11px/1 var(--mono); opacity: .65; }
.sw { display: inline-flex; align-items: center; gap: 8px; color: var(--mut); font-size: 12px; }
.sws { display: flex; gap: 16px; margin-left: auto; } .sws .sw { margin-left: 0; }
.sw i { width: 28px; height: 16px; border-radius: 9px; background: var(--p3); border: 1px solid var(--line2); position: relative; transition: background .15s; }
.sw i::after { content: ""; position: absolute; top: 2px; left: 2px; width: 10px; height: 10px; border-radius: 50%; background: var(--mut); transition: transform .18s, background .15s; }
.sw[aria-pressed="true"] i { background: color-mix(in srgb, var(--acc) 35%, var(--p3)); border-color: var(--acc); }
.sw[aria-pressed="true"] i::after { transform: translateX(12px); background: var(--ink); }

/* Sheet */
.sheet { display: grid; grid-template-columns: repeat(auto-fill, minmax(var(--min, 240px), 1fr)); gap: 14px; padding: 18px var(--gut) 8px; }
.card { text-align: left; display: block; border: 1px solid var(--line); border-radius: var(--r); background: var(--p1); overflow: hidden; transition: border-color .15s, transform .2s cubic-bezier(.2,.7,.2,1), box-shadow .2s; animation: rise .5s cubic-bezier(.2,.7,.2,1) both; animation-delay: calc(var(--i) * 35ms); }
@keyframes rise { from { opacity: 0; transform: translateY(10px); } }
.card:hover { border-color: #414751; transform: translateY(-2px); box-shadow: 0 14px 34px -18px #000; }
.card[aria-current] { border-color: var(--ink); }
.card[hidden] { display: none; }
/* A live board reloads often. Only its first load plays the entrance. */
body[data-quiet] .card { animation: none; }
body[data-quiet] .meter i { transition: none; }
.card__meta { display: flex; align-items: center; gap: 8px; padding: 9px 11px 9px; }
.card__meta b { font: 600 12px/1 var(--mono); }
.card__meta span { flex: 1; min-width: 0; color: var(--mut); font: 500 10.5px/1 var(--mono); letter-spacing: .07em; text-transform: uppercase; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.card__sub { margin: 0 11px 12px; color: var(--mut); font-size: 12.5px; line-height: 1.45; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }

/* Frame */
.frame { position: relative; aspect-ratio: var(--ar); background: #050607; overflow: hidden; container-type: inline-size; }
.frame img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; display: block; }
/* No frame yet: the brand's own ground with a thirds grid, so the on-screen text
   reads the way it will on the finished shot. */
.ph { position: absolute; inset: 0; color: var(--ph-ink, #F3F2EE);
  background:
    linear-gradient(color-mix(in srgb, currentColor 13%, transparent) 1px, transparent 1px) 0 33.33%/100% 33.33%,
    linear-gradient(90deg, color-mix(in srgb, currentColor 13%, transparent) 1px, transparent 1px) 33.33% 0/33.33% 100%,
    var(--ph-bg, #0F1114); }
.ph b { display: none; }
.ph span { position: absolute; left: 10px; top: 11px; font: 500 clamp(8px, 2.6cqw, 10.5px)/1 var(--mono); letter-spacing: .1em; text-transform: uppercase; opacity: .55; }
/* Type over a frame. Overlays on the same side of the frame share one group, so they
   stack with a set gap and can never sit on top of each other. Sizes are in cqw, the
   frame's own width, and --s is the scale fit() settles on. */
.ovg { position: absolute; display: flex; flex-direction: column; gap: 2.4cqw; pointer-events: none; transition: opacity .2s; --s: 1; }
.ovg[data-pos="upper-third"] { top: 8%; left: 7%; right: 7%; align-items: center; text-align: center; }
.ovg[data-pos="lower-third"] { bottom: 8%; left: 7%; right: 7%; align-items: center; text-align: center; flex-direction: column-reverse; }
.ovg[data-pos="center"] { top: 50%; left: 7%; right: 7%; transform: translateY(-50%); align-items: center; text-align: center; }
.ovg[data-pos="left-third"] { top: 50%; left: 6.5%; width: 39%; transform: translateY(-50%); align-items: flex-start; text-align: left; }
.ovg[data-pos="right-third"] { top: 50%; right: 6.5%; width: 39%; transform: translateY(-50%); align-items: flex-end; text-align: right; }
.ovg[data-pos="custom"] { transform: translate(-50%, -50%); width: max-content; max-width: 86%; align-items: center; text-align: center; }
.ov { max-width: 100%; font-size: calc(var(--fs) * var(--s)); line-height: var(--lh); letter-spacing: var(--ls); font-kerning: normal; font-optical-sizing: auto; text-rendering: geometricPrecision;
  text-shadow: 0 1px 2px rgba(0,0,0,.34), 0 2px 20px rgba(0,0,0,.38); }
.ov[data-ink="dark"] { text-shadow: 0 0 1px rgba(255,255,255,.4), 0 2px 18px rgba(255,255,255,.4); }
.frame[data-empty] .ov, .ov[data-treat="plate"] { text-shadow: none; }
.ov[data-size="display"] { --fs: 9.4cqw; --lh: .98; --ls: -.032em; }
.ov[data-size="headline"] { --fs: 7cqw; --lh: 1.03; --ls: -.024em; }
.ov[data-size="body"] { --fs: 4.4cqw; --lh: 1.22; --ls: -.008em; }
.ov[data-size="caption"] { --fs: 3.3cqw; --lh: 1.25; --ls: 0em; }
.ovg[data-pos="left-third"] .ov[data-size="display"], .ovg[data-pos="right-third"] .ov[data-size="display"] { --fs: 7.4cqw; }
.ovg[data-pos="left-third"] .ov[data-size="headline"], .ovg[data-pos="right-third"] .ov[data-size="headline"] { --fs: 5.9cqw; }
.ovg[data-pos="left-third"] .ov[data-size="body"], .ovg[data-pos="right-third"] .ov[data-size="body"] { --fs: 3.9cqw; }
.frame[data-tall] .ov[data-size="display"] { --fs: 11.4cqw; } .frame[data-tall] .ov[data-size="headline"] { --fs: 8.8cqw; }
.frame[data-tall] .ov[data-size="body"] { --fs: 5.4cqw; } .frame[data-tall] .ov[data-size="caption"] { --fs: 4cqw; }
.frame[data-tall] .ov__k { font-size: max(calc(3cqw * var(--s)), 6.5px); } .frame[data-tall] .ov[data-treat="lockup"] { --fs: 3.3cqw; }
/* A vertical video plays under an app's own buttons. Type stays clear of the top bar,
   the caption area at the bottom and the column of buttons on the right. */
.frame[data-tall] .ovg[data-pos="upper-third"] { top: 14%; left: 8%; right: 15%; }
.frame[data-tall] .ovg[data-pos="lower-third"] { bottom: 23%; left: 8%; right: 15%; }
.frame[data-tall] .ovg[data-pos="center"] { left: 8%; right: 15%; }
.frame[data-tall] .ovg[data-pos="right-third"] { right: 15%; }
.frame[data-tall] .field[data-pos="upper-third"] { background: linear-gradient(180deg, rgba(var(--f), .6), rgba(var(--f), .58) 30%, rgba(var(--f), .24) 44%, transparent 58%); }
.frame[data-tall] .field[data-pos="lower-third"] { background: linear-gradient(0deg, rgba(var(--f), .6), rgba(var(--f), .58) 36%, rgba(var(--f), .24) 50%, transparent 62%); }
/* The areas an app covers, shown on request. */
.safe { position: absolute; inset: 0; pointer-events: none; display: none; z-index: 2; }
body[data-safe="on"] .safe, body[data-safe-peek] .frame[data-moving] .safe { display: block; }
.frame[data-move] .ov { pointer-events: auto; cursor: grab; touch-action: none; }
.frame[data-move] .ov:hover { outline: 1px dashed rgba(255,255,255,.55); outline-offset: 6px; }
.frame[data-moving] .ov { cursor: grabbing; }
.hint { margin-top: 9px; font: 400 11.5px/1.45 var(--mono); color: var(--dim); }
.safe i { position: absolute; background: repeating-linear-gradient(135deg, rgba(255,90,43,.34) 0 5px, rgba(255,90,43,.1) 5px 10px); outline: 1px solid rgba(255,90,43,.6); outline-offset: -1px; }
.safe[data-kind="tall"] i:nth-child(1) { left: 0; right: 0; top: 0; height: 12%; }
.safe[data-kind="tall"] i:nth-child(2) { left: 0; right: 0; bottom: 0; height: 21%; }
.safe[data-kind="tall"] i:nth-child(3) { right: 0; top: 12%; bottom: 21%; width: 13%; }
.safe[data-kind="wide"] i { inset: 5%; background: none; outline: 1px dashed rgba(255,90,43,.7); }
.safe[data-kind="wide"] i:nth-child(n+2) { display: none; }
.ov[data-case="upper"] .ov__t { text-transform: uppercase; letter-spacing: calc(var(--ls) + .045em); }
.ov__t { display: block; }
.ov__l { display: block; text-wrap: balance; }
/* The words that carry the line. They keep the line's colour and get a bar in the accent
   under them, which reads over any picture. On a flat dark frame an overlay can ask for
   the words themselves to take the accent colour instead. */
.ov em { font-style: normal; }
.ov[data-em="color"] em { color: var(--acc-o); }
.ov:not([data-em="color"]) em { background: linear-gradient(transparent 64%, var(--acc-o) 64%, var(--acc-o) 93%, transparent 93%); padding: 0 .07em; margin: 0 -.07em; -webkit-box-decoration-break: clone; box-decoration-break: clone; }
/* A small label above the line, led by a short rule in the accent. */
.ov__k { display: inline-flex; align-items: center; gap: .9em; margin-bottom: 1.15em; font-size: max(calc(2.35cqw * var(--s)), 6.5px); line-height: 1; letter-spacing: .15em; text-transform: uppercase; font-weight: 600; opacity: .92; white-space: nowrap; }
.ov__k::before { content: ""; width: 2.1em; height: max(.14em, 1.5px); background: var(--acc-o); flex: none; }
.ovg[data-pos="right-third"] .ov__k { flex-direction: row-reverse; }
/* A brand name set as a lockup: small, spaced capitals after a square in the accent. */
.ov[data-treat="lockup"] { --fs: 2.7cqw; --lh: 1; --ls: .16em; text-transform: uppercase; display: inline-flex; align-items: center; gap: .85em; white-space: nowrap; }
.ov[data-treat="lockup"]::before { content: ""; width: .78em; height: .78em; background: var(--acc-o); flex: none; }
.ovg[data-pos="left-third"] .ov[data-treat="lockup"], .ovg[data-pos="right-third"] .ov[data-treat="lockup"] { --fs: 2.4cqw; margin-top: 1.2cqw; }
/* Type on a solid plate in a brand colour, for a frame too busy to carry type alone. */
.ov[data-treat="plate"] .ov__l { display: table; margin: 0 auto .14em; padding: .16em .42em .2em; background: var(--plate); text-wrap: wrap; }
.ovg[data-pos="left-third"] .ov[data-treat="plate"] .ov__l { margin-left: 0; }
.ovg[data-pos="right-third"] .ov[data-treat="plate"] .ov__l { margin-right: 0; }
/* A soft field behind each line of type, on the side of the frame the type sits on.
   It is drawn by the board, not baked into the frame, and goes away with the text. */
.field { position: absolute; inset: 0; pointer-events: none; transition: opacity .2s; }
.field[data-pos="upper-third"] { background: linear-gradient(180deg, rgba(var(--f), .66), rgba(var(--f), .44) 18%, rgba(var(--f), .16) 34%, transparent 48%); }
.field[data-pos="lower-third"] { background: linear-gradient(0deg, rgba(var(--f), .66), rgba(var(--f), .44) 18%, rgba(var(--f), .16) 34%, transparent 48%); }
.field[data-pos="center"] { background: radial-gradient(75% 34% at 50% 50%, rgba(var(--f), .42), transparent 100%); }
.field[data-pos="left-third"] { background: linear-gradient(90deg, rgba(var(--f), .5), rgba(var(--f), .2) 34%, transparent 58%); }
.field[data-pos="right-third"] { background: linear-gradient(270deg, rgba(var(--f), .5), rgba(var(--f), .2) 34%, transparent 58%); }
body[data-text="off"] .field { opacity: 0; }
body[data-text="off"] .ovg { opacity: 0; }
.tag { display: inline-flex; flex: none; align-items: center; gap: 6px; height: 21px; padding: 0 8px; border-radius: 5px; background: var(--p2); font: 600 9.5px/1 var(--mono); letter-spacing: .09em; text-transform: uppercase; color: var(--c); border: 1px solid color-mix(in srgb, var(--c) 40%, transparent); }
.tag i { width: 5px; height: 5px; border-radius: 50%; background: var(--c); }
.tag--r { color: var(--mut); border-color: var(--line2); padding: 0 6px; }
.card__state { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; padding: 10px 11px 0; }
.card__meta time { color: var(--dim); font: 400 11px/1 var(--mono); white-space: nowrap; }
.frame[data-flip] .ph { background-color: var(--ph-ink, #F3F2EE); color: var(--ph-bg, #0F1114); }
.drop { position: absolute; inset: 6px; z-index: 3; border: 1.5px dashed var(--acc); border-radius: 7px; background: rgba(255,90,43,.14); display: none; place-items: center; font: 600 12px/1.3 var(--sans); text-align: center; padding: 10px; }
.frame[data-over] .drop { display: grid; }

/* Sections */
.sec { padding: 34px var(--gut) 0; scroll-margin-top: 110px; }
.sec > h2 { font: 620 14px/1 var(--sans); margin-bottom: 14px; display: flex; align-items: center; gap: 10px; }
.sec > h2 small { font: 400 11.5px/1 var(--mono); color: var(--dim); }
.grid4 { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1px; background: var(--line); border: 1px solid var(--line); border-radius: var(--r); overflow: hidden; }
.cell { background: var(--p1); padding: 14px 16px 16px; }
.cell p { margin-top: 9px; font-size: 13.5px; line-height: 1.5; }
.brand { display: grid; grid-template-columns: minmax(0, 1.5fr) minmax(0, 1fr); gap: 14px; }
.swatches { display: grid; grid-template-columns: repeat(auto-fill, minmax(128px, 1fr)); gap: 10px; }
.swatch { text-align: left; border: 1px solid var(--line); border-radius: var(--r); overflow: hidden; background: var(--p1); transition: border-color .15s, transform .15s; }
.swatch:hover { border-color: #414751; transform: translateY(-1px); }
.swatch i { display: block; height: 62px; background: var(--h); border-bottom: 1px solid var(--line); }
.swatch div { padding: 9px 10px 10px; }
.swatch b { display: block; font: 500 12px/1 var(--mono); }
.swatch span { display: block; margin-top: 6px; color: var(--mut); font-size: 11.5px; }
.box { border: 1px solid var(--line); border-radius: var(--r); background: var(--p1); padding: 14px 16px; }
.box dl > div { display: grid; grid-template-columns: 96px 1fr; gap: 10px; padding: 8px 0; border-bottom: 1px solid var(--line); font-size: 13px; }
.box dl > div:last-child { border: 0; padding-bottom: 0; } .box dl > div:first-child { padding-top: 0; }
.box dt { color: var(--mut); } .box dd { min-width: 0; overflow-wrap: anywhere; }
.files { border: 1px solid var(--line); border-radius: var(--r); background: var(--p1); overflow: hidden; }
.files__scroll { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font: 400 12px/1.4 var(--mono); min-width: 520px; }
th { text-align: left; font: 500 10.5px/1 var(--mono); letter-spacing: .09em; text-transform: uppercase; color: var(--mut); padding: 11px 14px; border-bottom: 1px solid var(--line); }
td { padding: 8px 14px; border-bottom: 1px solid var(--line); white-space: nowrap; }
tr:last-child td { border-bottom: 0; }
td.num { text-align: right; color: var(--mut); } td.sha { color: var(--dim); }
.st { display: inline-flex; align-items: center; gap: 6px; color: var(--c); }
.st i { width: 6px; height: 6px; border-radius: 50%; background: var(--c); }
.note { margin: 14px var(--gut) 0; padding: 11px 14px; border: 1px solid color-mix(in srgb, var(--revise) 40%, transparent); background: color-mix(in srgb, var(--revise) 8%, var(--p1)); border-radius: var(--r); color: #F6DFAE; font-size: 13px; }
.note li + li { margin-top: 4px; }
.foot { margin-top: 44px; padding: 20px var(--gut) 40px; border-top: 1px solid var(--line); display: flex; flex-wrap: wrap; gap: 8px 24px; justify-content: space-between; color: var(--dim); font: 400 11.5px/1.5 var(--mono); }
.foot a { color: var(--mut); }

/* Panel */
.scrim { position: fixed; inset: 0; z-index: 40; background: rgba(4,5,6,.62); opacity: 0; pointer-events: none; transition: opacity .25s; }
.panel { position: fixed; z-index: 41; top: 0; right: 0; bottom: 0; width: min(100%, 980px); background: var(--p1); border-left: 1px solid var(--line2); display: flex; flex-direction: column; transform: translateX(102%); transition: transform .34s cubic-bezier(.2,.75,.2,1); box-shadow: -30px 0 80px -30px #000; }
body[data-open] .scrim { opacity: 1; pointer-events: auto; }
body[data-open] .panel { transform: none; }
body[data-open] { overflow: hidden; }
.panel__bar { display: flex; align-items: center; gap: 10px; height: 52px; padding: 0 16px; border-bottom: 1px solid var(--line); flex: none; }
.panel__bar b { font: 600 13px/1 var(--mono); }
.panel__bar span { color: var(--mut); font: 500 10.5px/1 var(--mono); letter-spacing: .08em; text-transform: uppercase; flex: 1; min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.ib { width: 30px; height: 30px; display: grid; place-items: center; border: 1px solid var(--line2); border-radius: 7px; color: var(--mut); transition: all .15s; }
.ib:hover { color: var(--ink); background: var(--p3); } .ib:disabled { opacity: .3; cursor: default; }
.ib svg { width: 14px; height: 14px; }
.panel__body { flex: 1; overflow-y: auto; display: grid; grid-template-columns: var(--pc, minmax(0, 340px)) minmax(0, 1fr); align-items: start; }
.pv { position: sticky; top: 0; padding: 16px; }
.pv .frame { border-radius: 8px; border: 1px solid var(--line2); }
.media { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 12px; }
.mi { border: 1px solid var(--line); border-radius: var(--r); background: var(--p1); overflow: hidden; display: flex; flex-direction: column; }
.mi[data-unused] { opacity: .62; }
.mi__pic { position: relative; aspect-ratio: 4 / 3; overflow: hidden; background: #000; display: grid; grid-auto-flow: column; grid-auto-columns: minmax(0, 1fr); grid-template-rows: minmax(0, 1fr); gap: 1px; }
.mi__pic img { width: 100%; height: 100%; min-width: 0; object-fit: contain; display: block; }
.mi__pic[data-n="3"] img { object-fit: cover; }
.mi__pic .tag { position: absolute; left: 8px; top: 8px; background: rgba(8,9,11,.8); backdrop-filter: blur(6px); }
.mi__pic time { position: absolute; right: 8px; bottom: 8px; padding: 3px 6px; border-radius: 4px; background: rgba(8,9,11,.8); font: 500 10.5px/1 var(--mono); color: var(--ink); }
.mi__b { padding: 10px 11px 12px; display: grid; gap: 7px; }
.mi__h { display: flex; gap: 8px; align-items: baseline; font: 600 12px/1.2 var(--mono); }
.mi__h span { flex: 1; min-width: 0; color: var(--mut); font-weight: 400; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.mi__h small { color: var(--dim); font: 400 10.5px/1 var(--mono); white-space: nowrap; }
.mi__n { font-size: 12.5px; line-height: 1.45; color: var(--ink); }
.mi__n[data-none] { color: var(--dim); }
.mi__w { display: flex; gap: 5px; flex-wrap: wrap; }
.mi__w button.tag { cursor: pointer; }
.dropz { border: 1.5px dashed var(--line2); border-radius: var(--r); padding: 26px 20px; text-align: center; color: var(--mut); font-size: 13.5px; line-height: 1.5; margin-bottom: 12px; transition: border-color .15s, background .15s, color .15s; }
.dropz b { display: block; color: var(--ink); font: 620 15.5px/1.3 var(--sans); margin-bottom: 5px; }
.dropz .btn { margin-top: 13px; }
.dropz[data-small] { padding: 16px 20px; display: flex; flex-wrap: wrap; align-items: center; justify-content: center; gap: 6px 16px; }
.dropz[data-small] b { margin: 0; font-size: 14px; } .dropz[data-small] .btn { margin: 0; } .dropz[data-small] .up { margin: 0; flex-basis: 100%; min-height: 0; }
.dropz p { max-width: 520px; margin: 0 auto; }
body[data-drag] .dropz { border-color: var(--acc); background: rgba(255,90,43,.1); color: var(--ink); }
.up { margin-top: 10px; font: 500 11.5px/1.5 var(--mono); color: var(--mut); min-height: 1.5em; }
.srcb { display: grid; gap: 6px; padding: 11px 13px; border: 1px solid var(--line2); border-radius: 8px; background: var(--p2); font-size: 13px; line-height: 1.45; }
.srcb .lab { display: flex; align-items: center; gap: 8px; }
.srcb .lab i { width: 6px; height: 6px; border-radius: 50%; background: var(--c); }
.srcb p { color: var(--mut); }
.vid { margin-top: 12px; }
.vid video { display: block; width: 100%; border-radius: 8px; border: 1px solid var(--line2); background: #000; aspect-ratio: var(--ar); }
.vid .lab { display: block; margin-bottom: 7px; }
.rounds { display: flex; gap: 6px; margin-top: 10px; flex-wrap: wrap; }
.rounds button { height: 26px; padding: 0 10px; border: 1px solid var(--line); border-radius: 6px; font: 500 11px/1 var(--mono); color: var(--mut); }
.rounds button[aria-pressed="true"] { border-color: var(--ink); color: var(--ink); background: var(--p3); }
.save { margin-top: 10px; padding: 10px 11px; border: 1px dashed var(--line2); border-radius: 8px; color: var(--mut); font-size: 12px; line-height: 1.5; }
.save code { display: block; margin-top: 5px; color: var(--ink); font: 400 11.5px/1.4 var(--mono); overflow-wrap: anywhere; }
.pd { padding: 16px 18px 40px 6px; min-width: 0; }
.blk { padding: 16px 0; border-bottom: 1px solid var(--line); }
.blk:first-child { padding-top: 2px; } .blk:last-child { border: 0; }
.blk > h3 { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.blk > h3 .lab { flex: 1; }
.spec { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px; }
.spec span { height: 24px; display: inline-flex; align-items: center; gap: 6px; padding: 0 9px; border: 1px solid var(--line); border-radius: 6px; font: 500 11.5px/1 var(--mono); }
.spec small { color: var(--dim); font-size: 10px; letter-spacing: .08em; text-transform: uppercase; }
.lead { font-size: 15px; line-height: 1.5; letter-spacing: -.005em; }
.quote { margin-top: 10px; padding-left: 11px; border-left: 2px solid var(--check); color: #CFE2FF; font-style: italic; font-size: 13.5px; }
.why { margin-top: 10px; color: var(--mut); font-size: 13px; }
.txt { padding: 10px 12px; border: 1px solid var(--line); border-radius: 8px; background: var(--bg); }
.txt + .txt { margin-top: 8px; }
.txt b { display: block; font: 600 14.5px/1.3 var(--sans); }
.txt span { display: block; margin-top: 6px; color: var(--mut); font: 400 11px/1.5 var(--mono); }
.tabs { display: flex; gap: 4px; flex-wrap: wrap; margin-bottom: 10px; }
.tabs button { height: 27px; padding: 0 10px; border-radius: 6px; border: 1px solid transparent; color: var(--mut); font: 500 12px/1 var(--sans); display: inline-flex; align-items: center; gap: 6px; }
.tabs button:hover { color: var(--ink); background: var(--p2); }
.tabs button[aria-selected="true"] { color: var(--ink); background: var(--p3); border-color: var(--line2); }
.tabs small { font: 500 9px/1 var(--mono); letter-spacing: .08em; color: var(--dim); text-transform: uppercase; }
.prompt { border: 1px solid var(--line); border-radius: 8px; background: var(--bg); overflow: hidden; }
.prompt__h { display: flex; align-items: center; gap: 8px; padding: 8px 8px 8px 12px; border-bottom: 1px solid var(--line); color: var(--mut); font: 400 11px/1.3 var(--mono); }
.prompt__h span { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.prompt pre { margin: 0; padding: 12px; white-space: pre-wrap; overflow-wrap: anywhere; font: 400 12.5px/1.6 var(--mono); color: #DADBD6; max-height: 300px; overflow-y: auto; }
.kv { padding: 9px 12px; border-top: 1px solid var(--line); font: 400 11px/1.6 var(--mono); color: var(--mut); overflow-wrap: anywhere; }
.kv b { color: var(--dim); font-weight: 500; letter-spacing: .08em; text-transform: uppercase; font-size: 9.5px; margin-right: 8px; }
.kv--fix { color: #F6DFAE; }
.crit { border: 1px solid var(--line); border-radius: 8px; overflow: hidden; }
.crit + .crit { margin-top: 8px; }
.crit__h { display: flex; align-items: center; gap: 10px; padding: 9px 12px; background: var(--p2); font: 500 11px/1 var(--mono); color: var(--mut); }
.crit__h .st { font-weight: 600; letter-spacing: .08em; }
.crit__h span:last-child { margin-left: auto; }
.crit ul { padding: 4px 12px 10px; }
.crit li { padding: 9px 0 0; font-size: 13px; line-height: 1.5; }
.crit li small { display: block; margin-bottom: 3px; font: 500 9.5px/1 var(--mono); letter-spacing: .09em; text-transform: uppercase; color: var(--c, var(--mut)); }
.crit li em { display: block; margin-top: 3px; font-style: normal; color: var(--mut); }
.empty { color: var(--dim); font-size: 13px; }
.toast { position: fixed; z-index: 60; left: 50%; bottom: 24px; transform: translate(-50%, 20px); padding: 9px 14px; border-radius: 8px; background: var(--ink); color: #0B0C0E; font: 600 12.5px/1 var(--sans); opacity: 0; pointer-events: none; transition: all .22s cubic-bezier(.2,.7,.2,1); box-shadow: 0 12px 30px -10px #000; }
.toast[data-on] { opacity: 1; transform: translate(-50%, 0); }
.toast[data-bad] { background: var(--revise); }
kbd { font: 500 10px/1 var(--mono); padding: 3px 5px; border: 1px solid var(--line2); border-radius: 4px; color: var(--mut); }

@media (max-width: 900px) {
  .head { grid-template-columns: 1fr; align-items: start; }
  .stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .brand { grid-template-columns: 1fr; }
  .panel__body { grid-template-columns: 1fr; }
  .pv { position: static; padding-bottom: 4px; } .pv .frame { max-height: 62vh; margin: 0 auto; }
  .pd { padding: 10px 16px 40px; }
  .bar .hide-s { display: none; }
  .tools { top: 52px; }
}
@media (max-width: 520px) {
  .sheet { --min: 150px !important; gap: 10px; }
  .card__sub { display: none; }
  .stat__n { font-size: 22px; }
}
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation: none !important; transition: none !important; } }
@media print { .bar, .tools, .panel, .scrim, .toast, .next .say { display: none !important; } html { background: #fff; color: #111; } }
</style>
</head>
<body>
<div id="app"></div>
<div class="scrim" id="scrim"></div>
<aside class="panel" id="panel" aria-label="Shot detail" aria-hidden="true"></aside>
<div class="toast" id="toast" role="status" aria-live="polite"></div>
<noscript><p style="padding:24px">This board needs JavaScript. The same storyboard is in storyboard.md and preview.html.</p></noscript>
<script id="data" type="application/json">/*__DATA__*/null</script>
<script>
(function () {
  "use strict";
  var D = JSON.parse(document.getElementById("data").textContent);
  var app = document.getElementById("app"), panel = document.getElementById("panel");
  var STATUS = {
    plan:   { label: "Needs prompt", color: "var(--wait)" },
    frame:  { label: "Needs frame",  color: "var(--mut)" },
    check:  { label: "Needs check",  color: "var(--check)" },
    revise: { label: "Revise",       color: "var(--revise)" },
    accept: { label: "Accepted",     color: "var(--accept)" }
  };
  var ICON = {
    copy: "M5 5V3.5A1.5 1.5 0 0 1 6.5 2h6A1.5 1.5 0 0 1 14 3.5v6a1.5 1.5 0 0 1-1.5 1.5H11M3.5 5h6A1.5 1.5 0 0 1 11 6.5v6A1.5 1.5 0 0 1 9.5 14h-6A1.5 1.5 0 0 1 2 12.5v-6A1.5 1.5 0 0 1 3.5 5Z",
    left: "M10 3 5 8l5 5", right: "M6 3l5 5-5 5", close: "M3.5 3.5l9 9M12.5 3.5l-9 9"
  };

  // Every string from the run goes in as a text node, never as markup.
  function el(tag, props) {
    var node = document.createElement(tag), i, kid;
    if (props) for (var k in props) {
      var v = props[k];
      if (v == null || v === false) continue;
      if (k === "class") node.className = v;
      else if (k === "text") node.textContent = v;
      else if (k === "style") node.setAttribute("style", v);
      else if (k.slice(0, 2) === "on") node.addEventListener(k.slice(2), v);
      else node.setAttribute(k, v === true ? "" : v);
    }
    for (i = 2; i < arguments.length; i++) {
      kid = arguments[i];
      if (kid == null || kid === false) continue;
      if (Array.isArray(kid)) kid.forEach(function (c) { if (c) node.appendChild(c); });
      else node.appendChild(typeof kid === "string" ? document.createTextNode(kid) : kid);
    }
    return node;
  }
  function icon(name) {
    var s = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    s.setAttribute("viewBox", "0 0 16 16"); s.setAttribute("fill", "none"); s.setAttribute("stroke", "currentColor");
    s.setAttribute("stroke-width", "1.5"); s.setAttribute("stroke-linecap", "round"); s.setAttribute("stroke-linejoin", "round"); s.setAttribute("aria-hidden", "true");
    var p = document.createElementNS("http://www.w3.org/2000/svg", "path"); p.setAttribute("d", ICON[name]); s.appendChild(p);
    return s;
  }
  function safeColor(v) { return /^#[0-9a-fA-F]{3,8}$/.test(v || "") ? v : "#F3F2EE"; }
  function fmt(n) { return (Math.round(n * 10) / 10).toString(); }
  function bytes(n) { return n > 1048576 ? (n / 1048576).toFixed(1) + " MB" : n > 1024 ? Math.round(n / 1024) + " KB" : n + " B"; }

  var toastTimer;
  function toast(msg, bad) {
    var t = document.getElementById("toast");
    t.textContent = msg; t.toggleAttribute("data-bad", !!bad); t.setAttribute("data-on", "");
    clearTimeout(toastTimer); toastTimer = setTimeout(function () { t.removeAttribute("data-on"); }, bad ? 5200 : 1500);
  }
  function copy(text, button, label) {
    function done() {
      toast(label || "Copied");
      if (button) { button.setAttribute("data-done", ""); setTimeout(function () { button.removeAttribute("data-done"); }, 1300); }
    }
    function fallback() {
      var ta = el("textarea", { style: "position:fixed;opacity:0;top:0;left:0" }); ta.value = text;
      // Selecting a field can scroll the page to it, so the place is kept and put back.
      var x = window.scrollX, y = window.scrollY;
      ta.setAttribute("readonly", ""); document.body.appendChild(ta); ta.focus({ preventScroll: true }); ta.select();
      try { document.execCommand("copy"); done(); } catch (e) { toast("Copy failed. Select the text and copy it by hand.", true); }
      ta.remove(); window.scrollTo(x, y);
    }
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(done, fallback);
    else fallback();
  }
  function copyBtn(label, getText, cls, said) {
    var b = el("button", { class: "btn " + (cls || ""), type: "button" }, icon("copy"), label);
    b.addEventListener("click", function (e) { e.stopPropagation(); copy(getText(), b, said); });
    return b;
  }

  // Markdown for one shot, with its newest prompts, for pasting into another model.
  function shotMarkdown(s) {
    var L = ["# " + D.project.title + ": " + s.id, "",
      "Beat: " + s.beat + ". " + s.start + "s to " + s.end + "s of " + D.project.duration_s + "s. Aspect " + D.project.aspect + ".", "",
      "## Shot", "",
      "- Camera: " + [s.framing, s.angle, s.motion].filter(Boolean).join(", ") + (s.depth_of_field ? ", " + s.depth_of_field + " depth of field" : ""),
      "- Subject: " + s.subject];
    if (s.vo) L.push('- Voiceover: "' + s.vo + '"');
    s.overlays.forEach(function (o) { L.push('- On-screen text: "' + o.content + '" (' + o.position_label + ", " + o.size + ", in at " + o.enter_at + "s, out at " + o.exit_at + "s)"); });
    L.push("- Why: " + s.rationale, "", "## Series lock", "");
    ["character", "environment", "lighting", "color_grade"].forEach(function (k) { if (D.series_lock[k]) L.push("- " + k.replace("_", " ") + ": " + D.series_lock[k]); });
    var last = s.critiques[s.critiques.length - 1];
    if (last) {
      L.push("", "## Latest check: " + last.verdict + ", round " + last.round, "");
      last.working.forEach(function (w) { L.push("- Working: " + w); });
      last.issues.forEach(function (i) { L.push("- " + i.layer + " (" + i.severity + "): " + i.note + " Fix: " + i.fix); });
    }
    var gens = Object.keys(s.prompts);
    if (gens.length) {
      L.push("", "## Prompts", "");
      gens.forEach(function (g) { var p = s.prompts[g][s.prompts[g].length - 1]; L.push("### " + genName(g) + ", round " + p.round, "", "```", p.body, "```", ""); });
    }
    return L.join("\n").trim() + "\n";
  }
  function genName(id) { for (var i = 0; i < D.generators.length; i++) if (D.generators[i].id === id) return D.generators[i].name; return id; }

  var ar = (D.project.aspect || "16:9").split(":"), ratio = (+ar[0] || 16) / (+ar[1] || 9);
  document.documentElement.style.setProperty("--ar", (+ar[0] || 16) + " / " + (+ar[1] || 9));
  var phBg = 0.006, brandAccent = "";
  (D.brand.palette || []).forEach(function (p) {
    var role = String(p.role).toLowerCase();
    if (role.indexOf("background") === 0) { document.documentElement.style.setProperty("--ph-bg", safeColor(p.hex)); phBg = luminance(p.hex); }
    if (role === "ink") document.documentElement.style.setProperty("--ph-ink", safeColor(p.hex));
    if (role.indexOf("accent") === 0 && !brandAccent) brandAccent = safeColor(p.hex);
  });
  if (!brandAccent) brandAccent = "#FF5A2B";

  function frameNode(s, f, opts) {
    opts = opts || {};
    var box = el("div", { class: "frame", "data-tall": ratio < 0.8 ? true : null });
    if (f) box.appendChild(el("img", { src: f.src, alt: s.id + ", " + s.beat + ", round " + f.round, loading: opts.eager ? "eager" : "lazy", decoding: "async" }));
    else { box.setAttribute("data-empty", ""); box.appendChild(el("div", { class: "ph" }, el("b", { text: s.n }), el("span", { text: [s.framing, s.angle, s.motion].filter(Boolean).join(" · ") }))); }
    var seen = {};
    s.overlays.forEach(function (o) {
      if (o.treatment === "plate" || o.treatment === "lockup") return;
      var pos = o.xy ? "custom" : o.position, dark = luminance(o.color) < 0.4;
      // One field per side of the frame, and only over a real frame. Light type gets a
      // dark field and dark type a light one.
      if (f && !o.xy && !seen[pos]) { seen[pos] = 1; box.appendChild(el("div", { class: "field", "data-pos": pos, style: "--f:" + (dark ? "255,255,255" : "0,0,0") })); }
    });
    var groups = {};
    s.overlays.forEach(function (o, i) {
      var pos = o.xy ? "custom" : o.position, key = o.xy ? "custom" + i : pos, g = groups[key];
      if (!g) {
        g = groups[key] = el("div", { class: "ovg", "data-pos": pos });
        if (o.xy) g.setAttribute("style", "left:" + (+o.xy.x || 50) + "%;top:" + (+o.xy.y || 50) + "%");
        box.appendChild(g);
      }
      g.appendChild(overlayNode(o));
    });
    // With no frame, type that would vanish into the brand's ground is shown on the
    // brand's ink colour instead, which is the kind of field it was written for.
    if (!f && s.overlays.some(function (o) { return contrast(luminance(o.color), phBg) < 2.2; })) box.setAttribute("data-flip", "");
    if (opts.move) wireMove(box);
    box.appendChild(el("div", { class: "safe", "data-kind": ratio < 0.8 ? "tall" : "wide" }, el("i"), el("i"), el("i")));
    fitLater(box);
    if (D.live) {
      box.appendChild(el("div", { class: "drop", text: "Drop the frame for " + s.id }));
      wireDrop(box, s);
    }
    return box;
  }
  // One overlay: an optional label, then the line, broken where its sentences end.
  function overlayNode(o) {
    var ink = luminance(o.color) < 0.4 ? "dark" : "light", treat = o.treatment || "plain";
    var style = "color:" + safeColor(o.color) + ";font-weight:" + (+o.weight || 700) + ";--acc-o:" + safeColor(o.accent || brandAccent) + ";"
      + (o.family ? "font-family:'" + o.family.replace(/[^A-Za-z0-9 _-]/g, "") + "'," + "var(--sans);" : "")
      + (treat === "plate" ? "--plate:" + safeColor(o.plate || (ink === "dark" ? "#FFFFFF" : "#000000")) + ";" : "");
    var node = el("div", { class: "ov", "data-id": o.id, "data-size": o.size || "headline", "data-ink": ink, "data-treat": treat, "data-case": o["case"] || null, "data-em": o.emphasis_style === "color" ? "color" : null, style: style });
    var text = String(o.content == null ? "" : o.content);
    if (treat === "lockup") { node.appendChild(document.createTextNode(text)); return node; }
    if (o.kicker) node.appendChild(el("span", { class: "ov__k", text: o.kicker }));
    var body = el("span", { class: "ov__t" });
    lines(text).forEach(function (line) {
      var row = el("span", { class: "ov__l" }), at = o.emphasis ? line.indexOf(o.emphasis) : -1;
      if (at < 0) row.textContent = line;
      else { row.appendChild(document.createTextNode(line.slice(0, at))); row.appendChild(el("em", { text: o.emphasis })); row.appendChild(document.createTextNode(line.slice(at + o.emphasis.length))); }
      body.appendChild(row);
    });
    node.appendChild(body);
    return node;
  }
  // Two or three short sentences each get their own line. Anything else wraps as one block.
  function lines(text) {
    var parts = text.split(/(?<=[.!?])\s+/).filter(Boolean);
    if (parts.length < 2 || parts.length > 3 || parts.some(function (x) { return x.length > 26; })) return [text];
    return parts;
  }
  function contrast(a, b) { return (Math.max(a, b) + .05) / (Math.min(a, b) + .05); }
  function luminance(hex) {
    var m = /^#([0-9a-f]{6})$/i.exec(hex || ""); if (!m) return 1;
    var n = parseInt(m[1], 16), c = [n >> 16 & 255, n >> 8 & 255, n & 255].map(function (v) { v /= 255; return v <= .03928 ? v / 12.92 : Math.pow((v + .055) / 1.055, 2.4); });
    return .2126 * c[0] + .7152 * c[1] + .0722 * c[2];
  }
  // Type is never clipped and never covers the frame: each line is scaled down until it
  // fits its side of the frame, and stacked lines are spaced by their real height.
  function fit(box) {
    var W = box.clientWidth, H = box.clientHeight; if (!W || !H) return;
    box.querySelectorAll(".ovg").forEach(function (g) {
      var pos = g.getAttribute("data-pos"), scale = 1;
      g.style.setProperty("--s", "1");
      var maxH = H * (pos === "center" || pos === "custom" ? .56 : pos === "left-third" || pos === "right-third" ? .8 : .36);
      var maxW = pos === "custom" ? W * .86 : g.clientWidth;
      // A word that cannot break (a web address) makes the group wider than its column, so it is scaled until it fits.
      while (scale > .3 && (g.scrollWidth > maxW + 1 || g.offsetHeight > maxH)) { scale -= .05; g.style.setProperty("--s", scale.toFixed(2)); }
    });
  }
  var pending = [];
  function fitLater(box) { pending.push(box); requestAnimationFrame(function () { var list = pending; pending = []; list.forEach(fit); }); }
  function fitAll() { document.querySelectorAll(".frame").forEach(fit); }
  function srcTag(s) {
    if (!s.source) return null;
    if (s.source.type === "own") return el("span", { class: "tag tag--r", title: "Your own media" + (s.source.media ? ", " + s.source.media : ""), text: "Yours" });
    return el("span", { class: "tag tag--r", title: s.source.why || "A gap to fill with a generator", text: s.source.start && s.source.end ? "Bridge" : s.frames.length ? "Made" : "To make" });
  }
  function mediaById(id) { var m = D.media.items; for (var i = 0; i < m.length; i++) if (m[i].id === id) return m[i]; return null; }
  function sourceBlock(s) {
    var src = s.source; if (!src) return null;
    if (src.type === "own") {
      var m = mediaById(src.media), cut = src.in != null && src.out != null ? fmt(src.in) + " to " + fmt(src.out) + "s of it" : null;
      return el("div", { class: "srcb", style: "--c:var(--accept)" }, el("div", { class: "lab" }, el("i"), "Your " + (m && m.kind === "clip" ? "clip" : "photo") + " · " + (src.media || "")),
        el("div", { text: (m && m.name ? m.name : "not in the media list") + (cut ? " · " + cut : "") }), m && m.note ? el("p", { text: m.note }) : null);
    }
    var bridge = src.start && src.end;
    return el("div", { class: "srcb", style: "--c:var(--revise)" }, el("div", { class: "lab" }, el("i"), bridge ? "Bridge to make" : "Gap to make" + (src.model ? " · " + src.model : "")),
      src.why ? el("div", { text: src.why }) : null,
      bridge ? el("p", { text: "The clip starts on the last frame of " + src.start + " and ends on the first frame of " + src.end + ", so the cut between them disappears." }) : null);
  }
  var upQueue = [], upBusy = false, upLine = null;
  function upload(files) {
    for (var i = 0; i < files.length; i++) upQueue.push(files[i]);
    if (!upBusy) nextUp(0, 0);
  }
  function nextUp(done, failed) {
    var file = upQueue.shift();
    if (!file) { upBusy = false; if (upLine) upLine.textContent = done + " added" + (failed ? ", " + failed + " refused" : "") + ". Ask Claude to look at them and plan."; return; }
    upBusy = true; if (upLine) upLine.textContent = "Adding " + file.name + " (" + bytes(file.size) + ")" + (upQueue.length ? ", " + upQueue.length + " to go" : "");
    fetch("/__media?name=" + encodeURIComponent(file.name), { method: "POST", headers: { "Content-Type": file.type || "application/octet-stream" }, body: file })
      .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
      .then(function (r) { if (!r.ok) toast(file.name + ": " + (r.j.error || "could not be added"), true); nextUp(done + (r.ok ? 1 : 0), failed + (r.ok ? 0 : 1)); })
      .catch(function () { toast("The live board is not running any more", true); upQueue = []; upBusy = false; });
  }
  function mediaSection() {
    var items = D.media.items; if (!items.length && !D.live) return null;
    var used = items.filter(function (m) { return m.shots.length; }).length, seen = items.filter(function (m) { return m.note; }).length;
    var sec = el("section", { class: "sec", id: "media" }, el("h2", null, "Your media",
      el("small", { text: items.length ? items.length + (items.length === 1 ? " file · " : " files · ") + seen + " looked at · " + used + " on a shot" : "nothing added yet" })));
    if (D.live) {
      var input = el("input", { type: "file", multiple: true, accept: "image/*,video/*", hidden: true });
      input.addEventListener("change", function () { if (input.files.length) upload(input.files); input.value = ""; });
      upLine = el("div", { class: "up", role: "status" });
      sec.appendChild(el("div", { class: "dropz", "data-small": items.length ? true : null }, el("b", { text: items.length ? "Drop more photos and clips anywhere on this page" : "Drop photos and clips anywhere on this page" }),
        items.length ? null : el("p", { text: "They are saved to media/inbox/ in this folder and listed here. Nothing leaves this computer." }),
        el("button", { class: "btn", type: "button", onclick: function () { input.click(); } }, "Choose files"), input, upLine));
    }
    if (items.length) sec.appendChild(el("div", { class: "media" }, items.map(function (m) {
      var meta = [m.width && m.height ? m.width + "×" + m.height : null, m.aspect].filter(Boolean).join(" · ");
      return el("article", { class: "mi", "data-unused": m.shots.length || !D.shots.length ? null : true },
        el("div", { class: "mi__pic", "data-n": String(m.thumbs.length) },
          m.thumbs.map(function (t) { return el("img", { src: t, alt: "", loading: "lazy", decoding: "async" }); }),
          el("span", { class: "tag tag--r", text: m.kind === "clip" ? "Clip" : "Photo" }),
          m.duration_s ? el("time", { text: fmt(m.duration_s) + "s" }) : null),
        el("div", { class: "mi__b" },
          el("div", { class: "mi__h" }, el("b", { text: m.id }), el("span", { text: m.name || "", title: m.name || "" }), el("small", { text: meta })),
          el("div", { class: "mi__n", "data-none": m.note ? null : true, text: m.note || "Not looked at yet." }),
          el("div", { class: "mi__w" }, m.shots.length ? m.shots.map(function (id) {
            return byId(id) ? el("button", { class: "tag", type: "button", style: "--c:var(--accept)", onclick: function () { open(id); } }, el("i"), id.replace("shot_", "Shot ")) : null; })
            : D.shots.length ? el("span", { class: "tag tag--r", text: "Not used" }) : null)));
    })));
    return sec;
  }
  // On a live board the text on the open shot can be dragged. Where it is dropped is
  // saved as that overlay's position, held inside the area an app leaves clear.
  function wireMove(box) {
    box.setAttribute("data-move", "");
    box.addEventListener("pointerdown", function (e) {
      var ov = e.target.closest ? e.target.closest(".ov") : null; if (!ov || !box.contains(ov)) return;
      e.preventDefault();
      var g = ov.parentNode, fr = box.getBoundingClientRect(), r0 = ov.getBoundingClientRect(), x0 = e.clientX, y0 = e.clientY, moved = false;
      var tall = box.hasAttribute("data-tall"), L = tall ? .06 : .05, R = tall ? .87 : .95, T = tall ? .12 : .05, B = tall ? .79 : .95;
      function at(ev) {
        var cx = r0.left + r0.width / 2 + (ev.clientX - x0) - fr.left, cy = r0.top + r0.height / 2 + (ev.clientY - y0) - fr.top;
        cx = Math.max(fr.width * L + r0.width / 2, Math.min(fr.width * R - r0.width / 2, cx));
        cy = Math.max(fr.height * T + r0.height / 2, Math.min(fr.height * B - r0.height / 2, cy));
        return { x: cx, y: cy };
      }
      function move(ev) {
        if (!moved && Math.abs(ev.clientX - x0) + Math.abs(ev.clientY - y0) < 4) return;
        moved = true; box.setAttribute("data-moving", ""); document.body.setAttribute("data-safe-peek", "");
        var p = at(ev); ov.style.transform = "translate(" + (p.x - (r0.left + r0.width / 2 - fr.left)) + "px," + (p.y - (r0.top + r0.height / 2 - fr.top)) + "px)";
      }
      function up(ev) {
        window.removeEventListener("pointermove", move); window.removeEventListener("pointerup", up);
        box.removeAttribute("data-moving"); document.body.removeAttribute("data-safe-peek");
        if (!moved) return;
        var p = at(ev), pos = { x: Math.round(p.x / fr.width * 1000) / 10, y: Math.round(p.y / fr.height * 1000) / 10 };
        fetch("/__overlay?id=" + encodeURIComponent(ov.getAttribute("data-id")), { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ position: pos }) })
          .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
          .then(function (r) { if (r.ok) toast("Moved. Saved to text-overlays.json"); else { ov.style.transform = ""; toast(r.j.error || "Could not save that", true); } })
          .catch(function () { ov.style.transform = ""; toast("The live board is not running any more", true); });
      }
      window.addEventListener("pointermove", move); window.addEventListener("pointerup", up);
    });
  }
  function wireDrop(box, s) {
    box.addEventListener("dragover", function (e) { e.preventDefault(); box.setAttribute("data-over", ""); });
    box.addEventListener("dragleave", function () { box.removeAttribute("data-over"); });
    box.addEventListener("drop", function (e) {
      e.preventDefault(); e.stopPropagation(); box.removeAttribute("data-over");
      var file = e.dataTransfer.files && e.dataTransfer.files[0];
      if (!file) return;
      fetch("/__frame?shot=" + encodeURIComponent(s.id), { method: "POST", headers: { "Content-Type": file.type }, body: file })
        .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
        .then(function (r) { if (r.ok) toast("Saved " + r.j.saved); else toast(r.j.error || "Could not save that file", true); })
        .catch(function () { toast("The live board is not running any more", true); });
    });
  }

  // ---------- page ----------
  var counts = { plan: 0, frame: 0, check: 0, revise: 0, accept: 0 };
  D.shots.forEach(function (s) { counts[s.status]++; });
  var total = D.shots.length || 1;
  var prompted = total - counts.plan, framed = D.shots.filter(function (s) { return s.frames.length; }).length;
  var checked = D.shots.filter(function (s) { return s.critiques.length; }).length;

  function stat(label, n, color) {
    return el("div", { class: "stat" }, el("div", { class: "lab", text: label }),
      el("div", { class: "stat__n" }, String(n), el("small", { text: "/ " + D.shots.length })),
      el("div", { class: "meter" }, el("i", { style: "--w:" + Math.round(n / total * 100) + "%;--c:" + color })));
  }

  var filter = "all";
  var cards = {}, segs = {};

  function build() {
    var bar = el("header", { class: "bar" },
      el("div", { class: "mark" }, el("i"), "shotkit", el("span", { text: "board" })),
      el("div", { class: "bar__title", text: D.project.title }),
      el("span", { class: "pill hide-s", "data-live": D.live ? true : null }, el("b"), D.live ? "Live" : "Rendered " + D.rendered_at.replace("T", " ").replace("Z", " UTC")),
      D.shots.length && (D.live || D.has_preview) ? el("a", { class: "btn hide-s", href: D.live ? "/__preview?print=1" : "preview.html", target: "_blank", rel: "noopener", title: "Opens the client preview. Print it, and choose Save as PDF." }, "PDF") : null,
      copyBtn("Copy for LLM", function () { return D.markdown; }, "btn--pri", "Storyboard copied as Markdown"));

    var n = D.next;
    var next = el("aside", { class: "next" }, el("div", { class: "lab", text: "Next step" }), el("h2", { text: n.title }), el("p", { text: n.body }),
      n.say ? el("div", { class: "say" }, el("span", null, el("em", { text: ">" }), n.say), copyBtn("Copy", function () { return n.say; }, "btn--sm", "Copied. Paste it into Claude.")) : null);

    var head = el("section", { class: "head" },
      el("div", null,
        el("div", { class: "lab", text: "Storyboard" + (D.shotkit_version ? " · Shotkit " + D.shotkit_version : "") }),
        el("h1", { text: D.project.title }),
        el("div", { class: "facts" },
          D.project.duration_s ? el("span", null, el("b", { text: D.project.duration_s + "s" }), " length") : null,
          D.shots.length ? el("span", null, el("b", { text: D.project.aspect }), " aspect") : null,
          el("span", null, el("b", { text: String(D.shots.length) }), " shots"),
          D.media.items.length ? el("span", null, el("b", { text: String(D.media.items.length) }), " of your own files") : null,
          D.project.framework ? el("span", null, el("b", { text: D.project.framework }), " framework") : null,
          D.shots.length ? el("span", null, "run ", el("b", { text: D.run.id })) : null)),
      next);

    var stats = el("section", { class: "stats", "aria-label": "Progress" },
      stat("Planned", D.shots.length, "var(--ink)"), stat("Prompted", prompted, "var(--mut)"),
      stat("Framed", framed, "var(--check)"), stat("Accepted", counts.accept, "var(--accept)"));

    app.appendChild(bar); app.appendChild(head);
    if (!D.shots.length) {
      if (D.warnings.length) app.appendChild(el("ul", { class: "note" }, D.warnings.map(function (w) { return el("li", { text: w }); })));
      var only = mediaSection(); if (only) app.appendChild(only);
      app.appendChild(el("footer", { class: "foot" }, el("span", { text: "Shotkit. The plan for a video." })));
      return;
    }
    app.appendChild(stats);
    if (D.warnings.length) app.appendChild(el("ul", { class: "note" }, D.warnings.map(function (w) { return el("li", { text: w }); })));
    app.appendChild(timeline());

    var chips = el("div", { class: "chips", role: "group", "aria-label": "Filter shots" });
    [["all", "All", D.shots.length, null]].concat(Object.keys(STATUS).map(function (k) { return [k, STATUS[k].label, counts[k], STATUS[k].color]; })).forEach(function (c) {
      if (c[0] !== "all" && !c[2]) return;
      chips.appendChild(el("button", { class: "chip", type: "button", "aria-pressed": c[0] === "all" ? "true" : "false", "data-f": c[0],
        onclick: function () { setFilter(c[0]); } }, c[3] ? el("i", { style: "--c:" + c[3] }) : null, c[1], el("small", { text: String(c[2]) })));
    });
    var textSw = el("button", { class: "sw", type: "button", "aria-pressed": "true", onclick: function () {
      var on = textSw.getAttribute("aria-pressed") !== "true"; textSw.setAttribute("aria-pressed", String(on)); document.body.setAttribute("data-text", on ? "on" : "off"); } }, el("i"), "Text on frames");
    var safeSw = el("button", { class: "sw", type: "button", "aria-pressed": "false", title: ratio < 0.8 ? "The parts of a vertical video an app covers with its own buttons" : "The margin a title should stay inside", onclick: function () {
      var on = safeSw.getAttribute("aria-pressed") !== "true"; safeSw.setAttribute("aria-pressed", String(on)); document.body.setAttribute("data-safe", on ? "on" : "off"); } }, el("i"), "Safe zones");
    app.appendChild(el("div", { class: "tools" }, el("h2", { text: "Shots" }), chips, el("div", { class: "sws" }, safeSw, textSw)));

    var sheet = el("section", { class: "sheet", id: "sheet", style: "--min:" + (ratio < 0.8 ? 190 : ratio < 1.2 ? 230 : 300) + "px" });
    D.shots.forEach(function (s, i) {
      var card = el("button", { class: "card", type: "button", id: s.id, style: "--i:" + i, "aria-label": "Open " + s.id + ", " + s.beat, onclick: function () { open(s.id); } },
        frameNode(s, s.frames[s.frames.length - 1]),
        el("div", { class: "card__state" }, el("span", { class: "tag", style: "--c:" + STATUS[s.status].color }, el("i"), STATUS[s.status].label),
          s.frames.length > 1 ? el("span", { class: "tag tag--r", title: "Round " + s.frames[s.frames.length - 1].round, text: "R" + s.frames[s.frames.length - 1].round }) : null,
          s.clips && s.clips.length ? el("span", { class: "tag tag--r", title: "This shot has a clip", text: "Clip" }) : null,
          srcTag(s)),
        el("div", { class: "card__meta" }, el("b", { text: s.n }), el("span", { text: s.beat || "" }), el("time", { text: fmt(s.start) + " to " + fmt(s.end) + "s" })),
        el("div", { class: "card__sub", text: s.subject || "" }));
      cards[s.id] = card; sheet.appendChild(card);
    });
    app.appendChild(sheet);
    var mine = mediaSection(); if (mine) app.appendChild(mine);

    var L = D.series_lock;
    app.appendChild(el("section", { class: "sec" }, el("h2", null, "Series lock", el("small", { text: "true for every shot" })),
      el("div", { class: "grid4" }, [["Character", L.character], ["Environment", L.environment], ["Lighting", L.lighting], ["Color grade", L.color_grade]].map(function (r) {
        return el("div", { class: "cell" }, el("div", { class: "lab", text: r[0] }), el("p", { text: r[1] || "not set" })); }))));

    var B = D.brand;
    if (B.found) {
      var fonts = [["Display", B.fonts.display_font], ["Body", B.fonts.body_font], ["Mono", B.fonts.mono_font]].filter(function (f) { return f[1]; });
      app.appendChild(el("section", { class: "sec" },
        el("h2", null, "Brand lock", el("small", { text: B.name || B.ref }), copyBtn("Copy brand lock", function () { return B.markdown; }, "btn--sm", "Brand lock copied as Markdown")),
        B.unconfigured || D.run.brand_configured === false ? el("p", { class: "note", style: "margin:0 0 14px", text: "This run used a starter brand, not yours. Ask Claude to read your site and write a brand lock, then run the storyboard again." }) : null,
        el("div", { class: "brand" },
          el("div", { class: "swatches" }, B.palette.map(function (p) {
            return el("button", { class: "swatch", type: "button", title: "Copy " + p.hex, onclick: function () { copy(p.hex, null, p.hex + " copied"); } },
              el("i", { style: "--h:" + safeColor(p.hex) }), el("div", null, el("b", { text: p.hex }), el("span", { text: p.role }))); })),
          el("div", { class: "box" }, el("dl", null,
            fonts.map(function (f) { return el("div", null, el("dt", { text: f[0] }), el("dd", { text: f[1] })); }),
            el("div", null, el("dt", { text: "Source" }), el("dd", { class: "mono", text: D.run.brand_source || "not recorded" })),
            el("div", null, el("dt", { text: "Frozen" }), el("dd", { class: "mono", text: B.snapshot_taken || "not recorded" })))))));
    }

    if (D.run.rounds.length) {
      app.appendChild(el("section", { class: "sec" }, el("h2", null, "Rounds", el("small", { text: D.run.rounds.length + " recorded" })),
        el("div", { class: "box" }, el("dl", null, D.run.rounds.map(function (r) {
          return el("div", null, el("dt", { class: "mono", text: "Round " + r.round }), el("dd", null, el("span", { text: r.reason || "" }), el("span", { class: "mono", style: "display:block;color:var(--dim);font-size:11.5px;margin-top:3px", text: r.started_at || "" }))); })))));
    }

    var FS = { match: ["Matches run.json", "var(--accept)"], changed: ["Changed since the run", "var(--revise)"], missing: ["Missing", "var(--revise)"], unpinned: ["Not pinned", "var(--wait)"] };
    var bad = D.files.filter(function (f) { return f.state === "changed" || f.state === "missing"; }).length;
    var pinned = D.files.filter(function (f) { return f.state === "match"; }).length;
    app.appendChild(el("section", { class: "sec" }, el("h2", null, "Files", el("small", { text: D.files.length + " files · " + pinned + " match run.json" + (bad ? " · " + bad + " changed" : "") })),
      el("div", { class: "files" }, el("div", { class: "files__scroll" }, el("table", null,
        el("thead", null, el("tr", null, el("th", { text: "Path" }), el("th", { text: "State" }), el("th", { text: "SHA-256" }), el("th", { style: "text-align:right", text: "Size" }))),
        el("tbody", null, D.files.map(function (f) { var s = FS[f.state];
          return el("tr", null, el("td", { text: f.path }), el("td", null, el("span", { class: "st", style: "--c:" + s[1] }, el("i"), s[0])), el("td", { class: "sha", text: f.sha }), el("td", { class: "num", text: f.bytes ? bytes(f.bytes) : "" })); })))))));

    app.appendChild(el("footer", { class: "foot" },
      el("span", { text: "Run " + D.run.id + " started " + D.run.created_at + ". Board rendered " + D.rendered_at + "." }),
      el("span", null, el("kbd", { text: "←" }), " ", el("kbd", { text: "→" }), " move  ", el("kbd", { text: "C" }), " copy prompt  ", el("kbd", { text: "Esc" }), " close"),
      el("span", null, "Made with ", el("a", { href: "https://github.com/whystrohm/shotkit", text: "Shotkit" }), ". For the finished video: ", el("a", { href: "mailto:hello@whystrohm.com", text: "hello@whystrohm.com" }))));
  }

  function timeline() {
    var dur = +D.project.duration_s || (D.shots.length ? +D.shots[D.shots.length - 1].end : 1) || 1;
    function pct(t) { return Math.max(0, Math.min(100, (+t || 0) / dur * 100)); }
    var ruler = el("div", { class: "ruler" });
    var marks = D.shots.map(function (s) { return +s.start; }).concat([dur]);
    marks.forEach(function (t, i) { if (i && i < marks.length - 1 && (t - marks[i - 1]) / dur < 0.06) return; ruler.appendChild(el("span", { style: "left:" + pct(t) + "%", text: fmt(t) + "s" })); });

    var shots = el("div", { class: "track track--shots" });
    D.shots.forEach(function (s) {
      var f = s.frames[s.frames.length - 1];
      var seg = el("button", { class: "seg", type: "button", title: s.id + " · " + s.beat + " · " + STATUS[s.status].label, style: "--d:" + Math.max(0.2, s.end - s.start) + ";--c:" + STATUS[s.status].color,
        onclick: function () { open(s.id); } }, el("span", { text: s.beat || "" }), el("b", { text: s.n }));
      if (f) seg.style.backgroundImage = "url(" + JSON.stringify(f.src) + ")";
      segs[s.id] = seg; shots.appendChild(seg);
    });
    var text = el("div", { class: "track" }), vo = el("div", { class: "track" }), anyT = false, anyV = false, lanes = [];
    D.shots.forEach(function (s) {
      s.overlays.forEach(function (o) {
        var a = o.enter_at != null ? +o.enter_at : +s.start, b = o.exit_at != null ? +o.exit_at : +s.end;
        if (b <= a) { a = +s.start; b = +s.end; }
        // Two lines on screen at once sit on separate rows, as they would in an edit.
        var lane = 0; while (lanes[lane] != null && lanes[lane] > a + 0.001) lane++;
        lanes[lane] = b;
        anyT = true; text.appendChild(el("div", { class: "clip clip--t", title: o.content, style: "--lane:" + lane + ";left:" + pct(a) + "%;width:calc(" + (pct(b) - pct(a)) + "% - 2px)" }, el("span", { text: o.content })));
      });
      if (s.vo) { anyV = true; vo.appendChild(el("div", { class: "clip clip--v", title: s.vo, style: "left:" + pct(s.start) + "%;width:calc(" + (pct(s.end) - pct(s.start)) + "% - 2px)" }, el("span", { text: s.vo }))); }
    });
    text.style.setProperty("--lanes", Math.max(1, lanes.length));
    var grid = el("div", { class: "tl__in" }, el("span"), ruler, el("span", { class: "lab tl__k", text: "Shots" }), shots);
    if (anyT) { grid.appendChild(el("span", { class: "lab tl__k", text: "Text" })); grid.appendChild(text); }
    if (anyV) { grid.appendChild(el("span", { class: "lab tl__k", text: "VO" })); grid.appendChild(vo); }
    return el("section", { class: "tl", "aria-label": "Timeline" }, el("div", { class: "tl__scroll" }, grid));
  }

  function setFilter(f) {
    filter = f;
    document.querySelectorAll(".chip").forEach(function (c) { c.setAttribute("aria-pressed", String(c.getAttribute("data-f") === f)); });
    D.shots.forEach(function (s) { cards[s.id].hidden = !(f === "all" || s.status === f); });
  }

  // ---------- panel ----------
  var current = null, pick = {}, lastFocus = null;
  function visible() { return D.shots.filter(function (s) { return filter === "all" || s.status === filter; }); }
  function byId(id) { for (var i = 0; i < D.shots.length; i++) if (D.shots[i].id === id) return D.shots[i]; return null; }

  function open(id, quiet) {
    var s = byId(id); if (!s) return;
    if (!current) lastFocus = document.activeElement;
    current = s;
    Object.keys(cards).forEach(function (k) { cards[k].toggleAttribute("aria-current", k === id); if (segs[k]) segs[k].toggleAttribute("aria-current", k === id); });
    drawPanel(s);
    document.body.setAttribute("data-open", ""); panel.setAttribute("aria-hidden", "false");
    if (!quiet) { try { history.replaceState(null, "", "#" + id); } catch (e) {} }
    var c = panel.querySelector("[data-close]"); if (c) c.focus({ preventScroll: true });
  }
  function close() {
    if (!current) return;
    current = null; document.body.removeAttribute("data-open"); panel.setAttribute("aria-hidden", "true");
    Object.keys(cards).forEach(function (k) { cards[k].removeAttribute("aria-current"); if (segs[k]) segs[k].removeAttribute("aria-current"); });
    try { history.replaceState(null, "", location.pathname + location.search); } catch (e) {}
    if (lastFocus && lastFocus.focus) lastFocus.focus({ preventScroll: true });
  }
  function step(dir) {
    var list = visible(), i = list.indexOf(current);
    if (i === -1) return; var n = list[i + dir]; if (n) open(n.id);
  }
  function currentPrompt(s) {
    var gens = Object.keys(s.prompts); if (!gens.length) return null;
    var g = pick.gen && s.prompts[pick.gen] ? pick.gen : gens[0];
    var runs = s.prompts[g]; return { gen: g, p: runs[runs.length - 1], runs: runs };
  }

  function drawPanel(s) {
    panel.textContent = "";
    var list = visible(), i = list.indexOf(s), st = STATUS[s.status];
    var prev = el("button", { class: "ib", type: "button", "aria-label": "Previous shot", disabled: i <= 0 ? true : null, onclick: function () { step(-1); } }, icon("left"));
    var nextB = el("button", { class: "ib", type: "button", "aria-label": "Next shot", disabled: i === -1 || i >= list.length - 1 ? true : null, onclick: function () { step(1); } }, icon("right"));
    panel.appendChild(el("div", { class: "panel__bar" },
      el("b", { text: s.id }), el("span", { text: (s.beat || "") + " · " + fmt(s.start) + " to " + fmt(s.end) + "s" }),
      el("span", { class: "st", style: "--c:" + st.color + ";flex:none;font:600 10.5px/1 var(--mono);letter-spacing:.08em;text-transform:uppercase" }, el("i"), st.label),
      copyBtn("Copy shot for LLM", function () { return shotMarkdown(s); }, "btn--sm hide-s", "Shot copied as Markdown"),
      prev, nextB, el("button", { class: "ib", type: "button", "aria-label": "Close", "data-close": true, onclick: close }, icon("close"))));

    // left: the frame
    var shown = s.frames.length ? s.frames[s.frames.length - 1] : null;
    var pv = el("div", { class: "pv" });
    var holder = el("div"); pv.appendChild(holder);
    function showFrame(f) { shown = f; holder.textContent = ""; holder.appendChild(frameNode(s, f, { eager: true, move: D.live && s.overlays.length > 0 })); }
    showFrame(shown);
    if (D.live && s.overlays.length) pv.appendChild(el("div", { class: "hint", text: "Drag the text to move it. It stays inside the safe zone and is saved to text-overlays.json." }));
    if (s.frames.length > 1) {
      var rounds = el("div", { class: "rounds" });
      s.frames.forEach(function (f) {
        var b = el("button", { type: "button", "aria-pressed": String(f === shown), text: "Round " + f.round, onclick: function () {
          showFrame(f); rounds.querySelectorAll("button").forEach(function (x) { x.setAttribute("aria-pressed", String(x === b)); }); } });
        rounds.appendChild(b);
      });
      pv.appendChild(rounds);
    }
    if (s.status === "frame" || s.status === "revise" || s.status === "plan") {
      var cp = currentPrompt(s), round = cp ? Math.max.apply(null, Object.keys(s.prompts).map(function (g) { return s.prompts[g][s.prompts[g].length - 1].round; })) : Math.max(1, D.rounds);
      var path = "frames/round-" + round + "/" + s.id + ".png";
      if (cp && !(s.frames.length && s.frames[s.frames.length - 1].round >= round)) {
        pv.appendChild(el("div", { class: "save" }, D.live ? "Drop the image here, or save it as" : "Save the frame you make as", el("code", { text: path })));
      }
    }
    if (s.clips && s.clips.length) {
      var c = s.clips[s.clips.length - 1];
      pv.appendChild(el("div", { class: "vid" }, el("span", { class: "lab", text: "Clip · round " + c.round }),
        el("video", { src: c.src + (s.source && s.source.in != null && s.source.out != null ? "#t=" + s.source.in + "," + s.source.out : ""), controls: true, loop: true, muted: true, playsinline: true, preload: "metadata" })));
    }

    // right: the detail
    var pd = el("div", { class: "pd" });
    var sb = sourceBlock(s); if (sb) pd.appendChild(el("div", { class: "blk" }, sb));
    pd.appendChild(el("div", { class: "blk" },
      el("div", { class: "spec" }, [["Framing", s.framing], ["Angle", s.angle], ["Motion", s.motion], ["DOF", s.depth_of_field]].filter(function (x) { return x[1]; }).map(function (x) { return el("span", null, el("small", { text: x[0] }), x[1]); })),
      el("p", { class: "lead", text: s.subject || "" }),
      s.vo ? el("p", { class: "quote", text: s.vo }) : null,
      s.rationale ? el("p", { class: "why", text: "Why this shot: " + s.rationale }) : null));

    if (s.overlays.length) pd.appendChild(el("div", { class: "blk" }, el("h3", null, el("span", { class: "lab", text: "On-screen text" })),
      s.overlays.map(function (o) { return el("div", { class: "txt" }, el("b", { text: o.content }),
        el("span", { text: [o.id, o.size, o.position_label, o.font, "in " + o.enter_at + "s " + (o.enter_animation || ""), "out " + o.exit_at + "s " + (o.exit_animation || "")].filter(Boolean).join(" · ") })); })));

    // prompts
    var pb = el("div", { class: "blk" }), cp2 = currentPrompt(s);
    pb.appendChild(el("h3", null, el("span", { class: "lab", text: "Prompts" })));
    if (!cp2) pb.appendChild(el("p", { class: "empty", text: "No prompt yet. Ask Claude to write prompts for the generator you use." }));
    else {
      var tabs = el("div", { class: "tabs", role: "tablist" }), body = el("div");
      Object.keys(s.prompts).forEach(function (g) {
        var meta = D.generators.filter(function (x) { return x.id === g; })[0] || {};
        tabs.appendChild(el("button", { type: "button", role: "tab", "aria-selected": String(g === cp2.gen), onclick: function () { pick.gen = g; drawPanel(s); } }, genName(g), el("small", { text: meta.motion ? "video" : "still" })));
      });
      var p = cp2.p;
      body.appendChild(el("div", { class: "prompt" },
        el("div", { class: "prompt__h" }, el("span", { text: p.file + (p.model ? " · " + p.model : "") + (p.revised ? " · revision" : "") }), copyBtn("Copy prompt", function () { return p.body; }, "btn--sm btn--pri", genName(cp2.gen) + " prompt copied")),
        el("pre", { text: p.body }),
        p.params.map(function (x) { return el("div", { class: "kv" }, el("b", { text: "Params" }), x); }),
        p.fixes.map(function (x) { return el("div", { class: "kv kv--fix" }, el("b", { text: "Fix" }), x.replace(/^fix\s*/i, "")); })));
      if (cp2.runs.length > 1) body.appendChild(el("p", { class: "empty", style: "margin-top:8px;font-size:12px", text: "Showing round " + p.round + ". Round " + cp2.runs[0].round + " is kept in " + cp2.runs[0].file + "." }));
      pb.appendChild(tabs); pb.appendChild(body);
    }
    pd.appendChild(pb);

    // critiques, newest first
    var cb = el("div", { class: "blk" });
    cb.appendChild(el("h3", null, el("span", { class: "lab", text: "Checks" })));
    if (!s.critiques.length) cb.appendChild(el("p", { class: "empty", text: s.frames.length ? "This frame has not been checked. Ask Claude to check the new frames." : "A check appears here once the shot has a frame." }));
    s.critiques.slice().reverse().forEach(function (c) {
      var color = c.verdict === "ACCEPT" ? "var(--accept)" : "var(--revise)";
      var items = [];
      c.issues.forEach(function (x) { items.push(el("li", null, el("small", { style: "--c:var(--revise)", text: [x.layer, x.severity, x.fix_type].filter(Boolean).join(" · ") }), x.note || "", x.fix ? el("em", { text: "Fix: " + x.fix }) : null)); });
      c.working.forEach(function (x) { items.push(el("li", null, el("small", { style: "--c:var(--accept)", text: "Working" }), x)); });
      c.post_notes.forEach(function (x) { items.push(el("li", null, el("small", { text: "Post note" }), x)); });
      cb.appendChild(el("div", { class: "crit" },
        el("div", { class: "crit__h" }, el("span", { class: "st", style: "--c:" + color }, el("i"), c.verdict || "NO VERDICT"), el("span", { text: "Round " + c.round + (c.confidence ? " · " + String(c.confidence).toLowerCase() + " confidence" : "") }),
          el("span", { text: c.image_ok === false ? "frame changed since this check" : c.image_ok === "missing" ? "reviewed file not in this folder" : (c.generator ? genName(c.generator) : "") })),
        items.length ? el("ul", null, items) : null));
    });
    pd.appendChild(cb);

    document.documentElement.style.setProperty("--pc", ratio < 0.8 ? "minmax(0, 330px)" : ratio < 1.2 ? "minmax(0, 400px)" : "minmax(0, 470px)");
    panel.appendChild(el("div", { class: "panel__body" }, pv, pd));
  }

  // ---------- wiring ----------
  build();
  document.getElementById("scrim").addEventListener("click", close);
  document.addEventListener("keydown", function (e) {
    if (e.metaKey || e.ctrlKey || e.altKey || /^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName)) return;
    if (e.key === "Escape") close();
    else if (current && (e.key === "ArrowRight" || e.key === "j")) { e.preventDefault(); step(1); }
    else if (current && (e.key === "ArrowLeft" || e.key === "k")) { e.preventDefault(); step(-1); }
    else if (current && (e.key === "c" || e.key === "C")) { var cp = currentPrompt(current); if (cp) copy(cp.p.body, null, genName(cp.gen) + " prompt copied"); }
  });
  if (/^#shot_\d+$/.test(location.hash)) open(location.hash.slice(1), true);
  var refit; window.addEventListener("resize", function () { clearTimeout(refit); refit = setTimeout(fitAll, 120); });
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(fitAll);
  panel.addEventListener("transitionend", fitAll);
  var dragOff;
  window.addEventListener("dragover", function (e) {
    e.preventDefault();
    if (D.live) { document.body.setAttribute("data-drag", ""); clearTimeout(dragOff); dragOff = setTimeout(function () { document.body.removeAttribute("data-drag"); }, 180); }
  });
  // A file dropped on a shot's frame is that shot's frame. Anywhere else, it joins the media.
  window.addEventListener("drop", function (e) {
    e.preventDefault(); document.body.removeAttribute("data-drag");
    if (D.live && e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length) {
      upload(e.dataTransfer.files);
      var tray = document.getElementById("media"); if (tray) tray.scrollIntoView({ block: "nearest" });
    }
  });

  if (D.live) {
    // A reload should feel like an update, not a new page: no entrance, same scroll.
    try {
      if (sessionStorage.getItem("sk-seen")) {
        document.body.setAttribute("data-quiet", "");
        // The browser also scrolls to the open shot's anchor after load, so the saved
        // place is put back once now and once after that.
        var y = +sessionStorage.getItem("sk-y") || 0;
        var back = function () { window.scrollTo(0, y); };
        try { history.scrollRestoration = "manual"; } catch (e) {}
        back(); requestAnimationFrame(back); window.addEventListener("load", function () { back(); setTimeout(back, 60); });
      }
      sessionStorage.setItem("sk-seen", "1");
      window.addEventListener("pagehide", function () { sessionStorage.setItem("sk-y", String(window.scrollY)); });
    } catch (e) {}
    var stamp = null;
    setInterval(function () {
      fetch("/__stamp", { cache: "no-store" }).then(function (r) { return r.text(); }).then(function (t) {
        if (stamp === null) stamp = t; else if (t !== stamp && !upBusy) location.reload();
      }).catch(function () {});
    }, 1500);
  }
})();
</script>
</body>
</html>
