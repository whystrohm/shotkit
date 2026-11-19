<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Shotkit designed frame</title>
/*__FONTS__*/
<style>
/* A designed frame: one panel of interface, data or words, drawn from the brand lock.
   Everything is sized in --u, one 1080th of the frame's short side, so the same card
   is the same picture at any size. No model is involved. */
* { box-sizing: border-box; }
html, body { margin: 0; width: 100vw; height: 100vh; overflow: hidden; background: var(--bg); color: var(--ink); font-family: var(--body), "Helvetica Neue", Arial, sans-serif; -webkit-font-smoothing: antialiased; }
body::before { content: ""; position: absolute; inset: 0; background: radial-gradient(70% 34% at 50% 0%, color-mix(in srgb, var(--acc) 8%, transparent), transparent 70%), radial-gradient(60% 30% at 50% 100%, color-mix(in srgb, var(--acc) 5%, transparent), transparent 70%); }
.mono { font-family: "JetBrains Mono", ui-monospace, Menlo, monospace; }
#zone { position: absolute; left: var(--zl); right: var(--zr); top: var(--zt); bottom: var(--zb); display: flex; flex-direction: column; justify-content: var(--zj); }
.card { position: relative; background: color-mix(in srgb, var(--ink) 4%, var(--bg)); border: calc(2 * var(--u)) solid var(--rule); border-radius: calc(40 * var(--u)); box-shadow: 0 calc(60 * var(--u)) calc(140 * var(--u)) rgba(0,0,0,.45); overflow: hidden; }
.pad { padding: calc(54 * var(--u)) calc(54 * var(--u)) calc(50 * var(--u)); }
.dot { width: calc(22 * var(--u)); height: calc(22 * var(--u)); border-radius: 50%; background: var(--tone, var(--acc)); box-shadow: 0 0 0 calc(8 * var(--u)) color-mix(in srgb, var(--tone, var(--acc)) 15%, transparent); flex: none; }
[data-tone="warn"] { --tone: #F2B450; } [data-tone="bad"] { --tone: #FF6B5E; } [data-tone="good"] { --tone: var(--acc); }
.lab { font: 500 calc(26 * var(--u))/1 "JetBrains Mono", ui-monospace, monospace; letter-spacing: .14em; text-transform: uppercase; color: var(--mut); }
/* lines */
.lines { position: absolute; left: 0; right: 0; top: var(--zt); bottom: 0; padding-left: calc(56 * var(--u)); font: 400 calc(30 * var(--u))/calc(58 * var(--u)) "JetBrains Mono", ui-monospace, monospace; color: color-mix(in srgb, var(--mut) 62%, var(--bg)); white-space: nowrap; -webkit-mask-image: linear-gradient(transparent, #000 14%, #000 72%, transparent 97%); }
.lines i { font-style: normal; opacity: .6; } .lines b { font-weight: 500; color: var(--mut); }
.lines .flag { margin-left: calc(-56 * var(--u)); padding-left: calc(56 * var(--u)); background: color-mix(in srgb, var(--tone) 14%, transparent); color: color-mix(in srgb, var(--tone) 80%, var(--ink)); box-shadow: inset calc(8 * var(--u)) 0 0 var(--tone); }
.lines .flag b { color: color-mix(in srgb, var(--tone) 55%, var(--ink)); font-weight: 700; }
/* list */
.hd { display: flex; align-items: center; gap: calc(22 * var(--u)); padding: calc(46 * var(--u)) calc(50 * var(--u)) calc(38 * var(--u)); border-bottom: calc(2 * var(--u)) solid var(--rule); }
.hd h1 { margin: 0; flex: 1; font: 700 calc(56 * var(--u))/1 var(--body), sans-serif; letter-spacing: -.03em; }
.pill { font: 500 calc(28 * var(--u))/1 "JetBrains Mono", monospace; color: var(--mut); border: calc(2 * var(--u)) solid var(--rule); border-radius: 99px; padding: calc(14 * var(--u)) calc(24 * var(--u)); }
.row { display: flex; align-items: center; gap: calc(30 * var(--u)); padding: 0 calc(50 * var(--u)); height: calc(172 * var(--u)); border-bottom: calc(2 * var(--u)) solid var(--rule); }
.row .n { font: 700 calc(34 * var(--u))/1 "JetBrains Mono", monospace; min-width: calc(104 * var(--u)); flex: none; }
.row .t { flex: 1; min-width: 0; } .row .t b { display: block; font: 600 calc(40 * var(--u))/1.15 var(--body), sans-serif; letter-spacing: -.02em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.row .t span { display: block; margin-top: calc(14 * var(--u)); font: 400 calc(28 * var(--u))/1 var(--body), sans-serif; color: var(--mut); }
.row .st { font: 500 calc(26 * var(--u))/1 "JetBrains Mono", monospace; color: var(--tone, var(--acc)); flex: none; }
.fade { position: absolute; left: 0; right: 0; bottom: 0; height: 17vh; background: linear-gradient(transparent, var(--bg) 78%); }
/* detail */
.big { display: flex; align-items: flex-end; gap: calc(26 * var(--u)); margin: calc(26 * var(--u)) 0 calc(30 * var(--u)); } .big b { font: 800 calc(148 * var(--u))/.86 var(--body), sans-serif; letter-spacing: -.055em; }
.chip { font: 500 calc(30 * var(--u))/1 "JetBrains Mono", monospace; border: calc(2 * var(--u)) solid var(--rule); border-radius: calc(14 * var(--u)); padding: calc(14 * var(--u)) calc(20 * var(--u)); margin-bottom: calc(8 * var(--u)); }
.state { display: flex; align-items: center; gap: calc(22 * var(--u)); font: 600 calc(38 * var(--u))/1 var(--body), sans-serif; color: var(--tone, var(--acc)); padding-bottom: calc(46 * var(--u)); border-bottom: calc(2 * var(--u)) solid var(--rule); margin-bottom: calc(44 * var(--u)); }
.ch { display: flex; align-items: baseline; gap: calc(20 * var(--u)); padding: calc(26 * var(--u)) 0; border-bottom: calc(2 * var(--u)) solid var(--rule); font: 500 calc(38 * var(--u))/1.15 var(--body), sans-serif; letter-spacing: -.015em; }
.ch span { flex: 1; } .ch em { font: 500 calc(28 * var(--u))/1 "JetBrains Mono", monospace; font-style: normal; color: var(--mut); }
.foot { margin-top: calc(44 * var(--u)); font: 400 calc(30 * var(--u))/1.2 var(--body), sans-serif; color: var(--mut); }
/* action */
.alert { display: flex; align-items: center; gap: calc(26 * var(--u)); font: 600 calc(42 * var(--u))/1.15 var(--body), sans-serif; letter-spacing: -.02em; }
.sub { margin: calc(18 * var(--u)) 0 0 calc(48 * var(--u)); font: 400 calc(30 * var(--u))/1 var(--body), sans-serif; color: var(--mut); }
.btn { position: relative; margin-top: calc(56 * var(--u)); height: calc(164 * var(--u)); border-radius: calc(28 * var(--u)); background: var(--acc); color: var(--on-acc); font: 700 calc(50 * var(--u))/calc(164 * var(--u)) var(--body), sans-serif; letter-spacing: -.025em; text-align: center; box-shadow: 0 0 0 calc(12 * var(--u)) color-mix(in srgb, var(--acc) 13%, transparent); }
.cur { position: absolute; right: calc(150 * var(--u)); top: calc(104 * var(--u)); width: calc(64 * var(--u)); height: calc(64 * var(--u)); }
.done { display: flex; align-items: center; gap: calc(24 * var(--u)); margin-top: calc(64 * var(--u)); padding-top: calc(50 * var(--u)); border-top: calc(2 * var(--u)) solid var(--rule); font: 600 calc(40 * var(--u))/1 var(--body), sans-serif; }
.done svg { width: calc(52 * var(--u)); height: calc(52 * var(--u)); flex: none; } .done span { margin-left: auto; color: var(--mut); font-weight: 400; font-size: calc(30 * var(--u)); }
/* notices */
.stack { position: relative; } .note { position: relative; padding: calc(42 * var(--u)) calc(46 * var(--u)) calc(46 * var(--u)); margin-bottom: calc(22 * var(--u)); transform-origin: 50% 0; }
.note .top { display: flex; align-items: center; gap: calc(18 * var(--u)); font: 500 calc(28 * var(--u))/1 var(--body), sans-serif; color: var(--mut); } .note .top span { margin-left: auto; font: 400 calc(26 * var(--u))/1 "JetBrains Mono", monospace; }
.note h2 { margin: calc(28 * var(--u)) 0 0; font: 700 calc(46 * var(--u))/1.1 var(--body), sans-serif; letter-spacing: -.025em; } .note p { margin: calc(16 * var(--u)) 0 0; font: 400 calc(32 * var(--u))/1.3 var(--body), sans-serif; color: var(--mut); }
/* mark, also used small on a notice */
.mk { position: relative; background: var(--acc); flex: none; } .mk i { position: absolute; left: 23.5%; height: 11.2%; border-radius: 99px; background: var(--on-acc); }
.mk i:nth-child(1) { top: 27%; width: 53%; } .mk i:nth-child(2) { top: 44.4%; width: 35%; } .mk i:nth-child(3) { top: 61.8%; width: 44%; }
.mk.s { width: calc(44 * var(--u)); height: calc(44 * var(--u)); border-radius: calc(11 * var(--u)); }
.markbox { align-self: center; text-align: center; } .mk.l { width: calc(340 * var(--u)); height: calc(340 * var(--u)); border-radius: calc(84 * var(--u)); margin: 0 auto; box-shadow: 0 0 0 calc(26 * var(--u)) color-mix(in srgb, var(--acc) 9%, transparent), 0 0 0 calc(62 * var(--u)) color-mix(in srgb, var(--acc) 4.5%, transparent); }
.wm { margin-top: calc(96 * var(--u)); font: 800 calc(92 * var(--u))/1 var(--body), sans-serif; letter-spacing: -.045em; }
/* stat and quote */
.stat b { display: block; font: 800 calc(260 * var(--u))/.9 var(--body), sans-serif; letter-spacing: -.06em; color: var(--acc); } .stat span { display: block; margin-top: calc(34 * var(--u)); font: 500 calc(44 * var(--u))/1.25 var(--body), sans-serif; } .stat small { display: block; margin-top: calc(26 * var(--u)); font: 400 calc(28 * var(--u))/1.3 var(--body), sans-serif; color: var(--mut); }
.quote p { margin: 0; font: 500 calc(52 * var(--u))/1.25 var(--body), sans-serif; letter-spacing: -.02em; } .quote p::before { content: "\201C"; } .quote p::after { content: "\201D"; } .quote .foot { margin-top: calc(40 * var(--u)); }
</style></head>
<body>
<div id="zone"></div>
<script id="data" type="application/json">/*__DATA__*/null</script>
<script>
(function () {
  "use strict";
  var D = JSON.parse(document.getElementById("data").textContent), c = D.card, root = document.documentElement.style;
  var W = window.innerWidth, H = window.innerHeight, tall = W / H < 0.8;
  // One unit is a 1080th of the width on a vertical frame. On a wide frame the panel
  // takes a column, so the unit comes from that column.
  var colW = tall ? W : Math.min(W * 0.5, H * 0.9);
  root.setProperty("--u", (colW / 1080) + "px");
  ["bg", "ink", "acc", "mut", "rule"].forEach(function (k) { root.setProperty("--" + k, D.colours[k]); });
  root.setProperty("--on-acc", D.colours.on_acc); root.setProperty("--body", "'" + D.body + "'");
  // The panel sits where the on-screen text is not.
  var z = { zl: "5.5%", zr: "5.5%", zt: "40%", zb: "0%", zj: "flex-start" };
  if (tall) { if (D.text === "lower-third") { z.zt = "13%"; z.zb = "36%"; } else if (D.text === "center" || !D.text) { z.zt = "14%"; z.zb = "8%"; z.zj = "center"; } }
  else { z.zt = "8%"; z.zb = "8%"; z.zj = "center"; var side = D.text === "right-third" ? "l" : "r"; z.zl = side === "r" ? (W - colW * 0.94 - W * 0.04) + "px" : "4%"; z.zr = side === "r" ? "4%" : (W - colW * 0.94 - W * 0.04) + "px"; }
  for (var k in z) root.setProperty("--" + k, z[k]);

  function el(tag, cls, text) { var n = document.createElement(tag); if (cls) n.className = cls; if (text != null) n.textContent = String(text); return n; }
  function add(p) { for (var i = 1; i < arguments.length; i++) if (arguments[i]) p.appendChild(arguments[i]); return p; }
  function dot(tone) { var d = el("div", "dot"); if (tone) d.setAttribute("data-tone", tone); return d; }
  function mark(size) { return add(el("div", "mk " + size), el("i"), el("i"), el("i")); }
  var zone = document.getElementById("zone"), K = {};

  K.lines = function () {
    var box = el("div", "lines"); zone.remove(); document.body.appendChild(box);
    (c.lines || []).forEach(function (l) {
      var row = el("div", l.flag ? "flag" : null); if (l.flag) row.setAttribute("data-tone", l.flag === true ? "bad" : l.flag);
      add(row, el("i", null, (l.at || "") + " "), el("b", null, (l.tag || "") + " "), document.createTextNode(l.text || "")); box.appendChild(row);
    });
  };
  K.list = function () {
    var card = el("div", "card"); card.style.marginBottom = "-6vh";
    add(card, add(el("div", "hd"), el("h1", null, c.title), c.tag ? el("div", "pill", c.tag) : null));
    (c.rows || []).forEach(function (r) {
      var st = r.status ? el("div", "st", r.status) : null; if (st && r.tone) st.setAttribute("data-tone", r.tone);
      add(card, add(el("div", "row"), dot(r.tone), r.key ? el("div", "n", r.key) : null, add(el("div", "t"), el("b", null, r.title), r.sub ? el("span", null, r.sub) : null), st));
    });
    zone.appendChild(card); document.body.appendChild(el("div", "fade"));
  };
  K.detail = function () {
    var pad = el("div", "pad");
    add(pad, c.label ? el("div", "lab", c.label) : null, add(el("div", "big"), el("b", null, c.big), c.chip ? el("div", "chip", c.chip) : null));
    if (c.status) { var s = add(el("div", "state"), dot(c.tone), document.createTextNode(c.status)); if (c.tone) s.setAttribute("data-tone", c.tone); pad.appendChild(s); }
    if (c.section) pad.appendChild(el("div", "lab", c.section));
    (c.rows || []).forEach(function (r) { add(pad, add(el("div", "ch"), el("span", null, r.text), r.right ? el("em", null, r.right) : null)); });
    if (c.foot) pad.appendChild(el("div", "foot", c.foot));
    zone.appendChild(add(el("div", "card"), pad));
  };
  K.action = function () {
    var pad = el("div", "pad"), btn = el("div", "btn", c.button);
    btn.insertAdjacentHTML("beforeend", '<svg class="cur" viewBox="0 0 64 64"><path d="M10 6l40 22-17 5 11 19-9 5-11-19-12 13z" fill="#0B0D10" stroke="#F4F5F0" stroke-width="4" stroke-linejoin="round"/></svg>');
    add(pad, add(el("div", "alert"), dot(c.tone || "bad"), document.createTextNode(c.alert || "")), c.sub ? el("div", "sub", c.sub) : null, btn);
    if (c.done) { var d = el("div", "done"); d.insertAdjacentHTML("beforeend", '<svg viewBox="0 0 52 52"><circle cx="26" cy="26" r="24" fill="none" stroke="currentColor" stroke-width="4"/><path d="M15 27l8 8 15-17" fill="none" stroke="currentColor" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/></svg>'); d.firstChild.style.color = "var(--acc)"; add(d, document.createTextNode(c.done), c.done_right ? el("span", null, c.done_right) : null); pad.appendChild(d); }
    zone.appendChild(add(el("div", "card"), pad));
  };
  K.notices = function () {
    var stack = el("div", "stack");
    (c.items || []).slice(0, 3).forEach(function (it, i) {
      var n = el("div", "card note"); n.style.transform = "scale(" + (1 - i * 0.05) + ")"; n.style.opacity = String([1, 0.7, 0.38][i]);
      add(n, add(el("div", "top"), mark("s"), document.createTextNode(it.from || ""), el("span", null, it.when || "")), el("h2", null, it.title), it.text ? el("p", null, it.text) : null); stack.appendChild(n);
    });
    zone.appendChild(stack);
  };
  K.mark = function () { root.setProperty("--zj", "center"); if (tall) { root.setProperty("--zt", D.text === "lower-third" ? "12%" : "34%"); root.setProperty("--zb", "26%"); } zone.appendChild(add(el("div", "markbox"), mark("l"), c.name ? el("div", "wm", c.name) : null)); };
  K.stat = function () { zone.appendChild(add(el("div", "card"), add(el("div", "pad stat"), c.label ? el("div", "lab", c.label) : null, el("b", null, c.value), c.text ? el("span", null, c.text) : null, c.note ? el("small", null, c.note) : null))); };
  K.quote = function () { zone.appendChild(add(el("div", "card"), add(el("div", "pad quote"), el("p", null, c.text), c.by ? el("div", "foot", c.by) : null))); };
  (K[c.kind] || function () {})();
})();
</script>
</body></html>
