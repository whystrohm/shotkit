<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="generator" content="storyboard-html-preview / WhyStrohm">
<title>{{PROJECT_TITLE}} · Storyboard</title>
<style>
{{{INLINE_CSS}}}
</style>
</head>
<body>

<header class="sb-header">
  <div class="sb-header-inner">
    <div class="sb-eyebrow">Storyboard · shots {{SHOTS_VERSION}}</div>
    <h1 class="sb-title">{{PROJECT_TITLE}}</h1>
    <dl class="sb-meta">
      <div><dt>Duration</dt><dd>{{DURATION}}s</dd></div>
      <div><dt>Aspect</dt><dd>{{ASPECT}}</dd></div>
      <div><dt>Framework</dt><dd>{{FRAMEWORK}}</dd></div>
      <div><dt>Run</dt><dd>{{RUN_CREATED_AT}}</dd></div>
    </dl>
  </div>
</header>

<nav class="sb-nav" aria-label="Shot navigation">
  <ul>
    {{#each shots}}
    <li><a href="#{{id}}">{{id_short}}</a></li>
    {{/each}}
  </ul>
</nav>

{{#if BRIEF}}
<section class="sb-section sb-brief">
  <h2>Brief</h2>
  <p>{{BRIEF}}</p>
</section>
{{/if}}

<section class="sb-section sb-series-lock">
  <h2>Series lock</h2>
  <dl class="sb-series-grid">
    <div>
      <dt>Character</dt>
      <dd>{{SERIES_CHARACTER}}</dd>
    </div>
    <div>
      <dt>Environment</dt>
      <dd>{{SERIES_ENVIRONMENT}}</dd>
    </div>
    <div>
      <dt>Lighting</dt>
      <dd>{{SERIES_LIGHTING}}</dd>
    </div>
    <div>
      <dt>Color grade</dt>
      <dd>{{SERIES_COLOR_GRADE}}</dd>
    </div>
  </dl>
</section>

<section class="sb-section sb-shots">
  <h2>Shots</h2>
  {{#each shots}}
  <article class="sb-shot" id="{{id}}">
    <div class="sb-shot-frame {{aspect_class}}">
      {{#if has_image}}
      <img src="{{image_path}}" alt="{{id}}: {{beat}}" loading="lazy">
      {{/if}}
      {{#if has_no_image}}
      <div class="sb-placeholder">
        <div class="sb-placeholder-id">{{id_short}}</div>
        <div class="sb-placeholder-meta">{{framing}} · {{angle}} · {{motion}}</div>
      </div>
      {{/if}}

      {{#each overlays}}
      <div class="sb-overlay sb-overlay-{{position_class}}">
        <span class="sb-overlay-text" style="font-family: {{font}}; font-weight: {{weight}}; color: {{color}};">{{content}}</span>
      </div>
      {{/each}}
    </div>

    <div class="sb-shot-body">
      <header class="sb-shot-header">
        <span class="sb-shot-id">{{id_short}}</span>
        <span class="sb-shot-time">{{start}}–{{end}}s</span>
        <span class="sb-shot-beat">{{beat}}</span>
        {{#if has_verdict}}
        <span class="sb-verdict sb-verdict-{{verdict_class}}">{{verdict}}<span class="sb-verdict-round">round {{verdict_round}}</span></span>
        {{/if}}
      </header>

      <dl class="sb-shot-meta">
        <div><dt>Framing</dt><dd>{{framing}}</dd></div>
        <div><dt>Angle</dt><dd>{{angle}}</dd></div>
        <div><dt>Motion</dt><dd>{{motion}}</dd></div>
        {{#if depth_of_field}}
        <div><dt>DOF</dt><dd>{{depth_of_field}}</dd></div>
        {{/if}}
      </dl>

      <div class="sb-shot-subject">
        <h3>Subject</h3>
        <p>{{subject}}</p>
      </div>

      {{#if vo}}
      <div class="sb-shot-vo">
        <h3>VO</h3>
        <p>"{{vo}}"</p>
      </div>
      {{/if}}

      {{#if has_overlays}}
      <div class="sb-shot-text">
        <h3>On-screen text</h3>
        {{#each overlays}}
        <p class="sb-text-content">"{{content}}"</p>
        <p class="sb-text-meta">{{id}} · {{size}} · {{position_label}} · enter {{enter_at}}s ({{enter_animation}}) · exit {{exit_at}}s ({{exit_animation}})</p>
        {{/each}}
      </div>
      {{/if}}

      <div class="sb-shot-rationale">
        <h3>Rationale</h3>
        <p>{{rationale}}</p>
      </div>
    </div>
  </article>
  {{/each}}
</section>

<footer class="sb-footer">
  <div class="sb-footer-inner">
    <div>
      Built against <a href="{{BRAND_LOCK_REF}}"><code>{{BRAND_LOCK_REF}}</code></a>{{#if BRAND_LOCK_SHA_SHORT}} (<code>{{BRAND_LOCK_SHA_SHORT}}</code>){{/if}}.
    </div>
    <div>Built with <a href="https://github.com/whystrohm/shotkit">shotkit</a> · WhyStrohm</div>
  </div>
  <div class="sb-footer-inner sb-provenance">
    <div>
      Run {{RUN_ID}} started {{RUN_CREATED_AT}}. This page rendered {{RENDERED_AT}}.
      {{#if PROVENANCE_NOTE}}{{PROVENANCE_NOTE}}{{/if}}
    </div>
  </div>
</footer>

<script>
// Keyboard navigation: arrow keys move between shots
(function() {
  const shots = Array.from(document.querySelectorAll('.sb-shot'));
  if (!shots.length) return;

  function shotInView() {
    const mid = window.innerHeight / 2;
    let best = 0;
    let bestDist = Infinity;
    shots.forEach((shot, i) => {
      const rect = shot.getBoundingClientRect();
      const dist = Math.abs(rect.top + rect.height / 2 - mid);
      if (dist < bestDist) { bestDist = dist; best = i; }
    });
    return best;
  }

  document.addEventListener('keydown', function(e) {
    if (e.target.matches('input, textarea')) return;
    const i = shotInView();
    if (e.key === 'ArrowDown' || e.key === 'j') {
      e.preventDefault();
      const next = shots[Math.min(shots.length - 1, i + 1)];
      next.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    if (e.key === 'ArrowUp' || e.key === 'k') {
      e.preventDefault();
      const prev = shots[Math.max(0, i - 1)];
      prev.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  });
})();
</script>

</body>
</html>
