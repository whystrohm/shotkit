@media print {
  /* ─── Page setup ─── */
  @page {
    size: letter;
    margin: 0.5in;
  }

  /* ─── Color & background ─── */
  body {
    background: white;
    color: black;
    font-size: 10pt;
    line-height: 1.4;
  }

  a {
    color: black;
    border-bottom: none;
  }

  a[href]::after {
    content: " (" attr(href) ")";
    font-family: var(--sb-font-mono);
    font-size: 8pt;
    color: #555;
  }

  /* Don't print sticky nav, JS controls, or footer scripts */
  .sb-nav { display: none; }

  /* ─── Header ─── */
  .sb-header {
    border-bottom: 2px solid black;
    padding: 0 0 16pt;
    margin-bottom: 24pt;
    page-break-after: avoid;
  }

  .sb-eyebrow {
    color: black;
    font-size: 9pt;
  }

  .sb-title {
    font-size: 24pt;
    margin-bottom: 12pt;
  }

  .sb-meta {
    grid-template-columns: repeat(4, 1fr);
    gap: 12pt;
    font-size: 9pt;
  }

  .sb-meta dt {
    color: #555;
    font-size: 7pt;
  }

  /* ─── Sections ─── */
  .sb-section {
    padding: 16pt 0;
    border-bottom: 1pt solid #999;
    page-break-inside: avoid;
  }

  .sb-section h2 {
    font-size: 9pt;
    margin-bottom: 12pt;
  }

  .sb-brief p {
    font-size: 12pt;
  }

  /* ─── Series lock ─── */
  .sb-series-grid {
    grid-template-columns: 1fr 1fr;
    gap: 12pt;
  }

  .sb-series-grid > div {
    border-left: 2pt solid black;
  }

  .sb-series-grid dt {
    color: #555;
    font-size: 7pt;
  }

  .sb-series-grid dd {
    font-size: 10pt;
  }

  /* ─── Shots, one shot per page ─── */
  .sb-shots h2 {
    page-break-after: avoid;
  }

  .sb-shot {
    page-break-inside: avoid;
    page-break-before: always;
    grid-template-columns: 1fr 1.2fr;
    gap: 18pt;
    padding: 18pt 0;
    border-bottom: none;
  }

  .sb-shot:first-of-type {
    page-break-before: avoid;
  }

  .sb-shot-frame {
    background: #f0f0f0;
    border: 1pt solid #999;
    border-radius: 0;
  }

  .sb-placeholder {
    background: #f5f5f5;
    color: #666;
  }

  .sb-overlay-text {
    text-shadow: none;
    background: rgba(255,255,255,0.85);
    padding: 2pt 6pt;
    color: black;
  }

  .sb-shot-id {
    color: black;
    font-size: 12pt;
  }

  .sb-shot-time, .sb-shot-beat {
    color: #555;
  }

  .sb-shot-rationale {
    background: #f5f5f5;
    border-left: 2pt solid black;
    padding: 8pt 10pt;
    page-break-inside: avoid;
  }

  .sb-shot-rationale p {
    font-size: 9pt;
  }

  .sb-shot-meta dt,
  .sb-shot-subject h3,
  .sb-shot-vo h3,
  .sb-shot-text h3,
  .sb-shot-rationale h3 {
    color: #555;
    font-size: 7pt;
  }

  .sb-shot-subject p,
  .sb-shot-vo p {
    font-size: 9.5pt;
  }

  /* ─── Footer ─── */
  .sb-footer {
    background: white;
    border-top: 1pt solid #999;
    padding: 12pt 0;
    font-size: 8pt;
    page-break-before: always;
  }

  .sb-footer-inner {
    flex-direction: column;
    gap: 4pt;
  }
}
