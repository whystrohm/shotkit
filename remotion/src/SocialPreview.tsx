import React from 'react';
import { AbsoluteFill } from 'remotion';
import { loadFont as loadInter } from '@remotion/google-fonts/Inter';
import { loadFont as loadJetBrainsMono } from '@remotion/google-fonts/JetBrainsMono';

// Static social-preview / README hero card. One frame, re-renderable.
// Render: npx remotion still SocialPreview ../docs/images/social-preview.png --frame=0 --scale=1.306
//
// Bold blueprint look: white ground, near-black ink, vermilion key nodes.
// Source of record for docs/images/social-preview.png.

const { fontFamily: inter } = loadInter('normal', { weights: ['500', '700', '900'] });
const { fontFamily: mono } = loadJetBrainsMono('normal', { weights: ['400', '700'] });

const C = {
  bg: '#FFFFFF',
  ink: '#111114',
  orange: '#FB5B28',
  muted: '#8C8C92',
};

const VERSION = 'v2.0.0';
const DATE = '2026-06-18';
const DOC_ID = 'WS-SK-CARD-001';

const STAGES = [
  { n: '01', name: 'ARCHITECT', file: 'storyboard.md', icon: 'grid' as const },
  { n: '02', name: 'FORGE', file: 'prompts/*.txt', icon: 'lines' as const },
  { n: '03', name: 'CRITIQUE', file: 'critique.json', icon: 'crop' as const },
  { n: '04', name: 'PREVIEW', file: 'preview.html', icon: 'doc' as const },
];

const CENTERS = [196, 497, 798, 1099];
const ICON = 116;
const ICON_TOP = 238;
const ICON_MID_Y = ICON_TOP + ICON / 2;

export const SocialPreview: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: C.bg, fontFamily: inter, color: C.ink }}>
      <Bracket />
      <Header />

      {[0, 1, 2].map((i) => (
        <Arrow key={i} x1={CENTERS[i] + ICON / 2} x2={CENTERS[i + 1] - ICON / 2} y={ICON_MID_Y} />
      ))}

      <ReviseLoop fromX={CENTERS[2]} toX={CENTERS[1]} yStart={ICON_TOP + ICON + 44} yBus={ICON_TOP + ICON + 68} />

      {STAGES.map((s, i) => (
        <StageCard key={s.n} stage={s} cx={CENTERS[i]} />
      ))}

      <BrandLockBar />
      <Footer />
    </AbsoluteFill>
  );
};

const Bracket: React.FC = () => (
  <svg width={48} height={48} viewBox="0 0 48 48" fill="none" style={{ position: 'absolute', top: 28, left: 38 }}>
    <path d="M3 16V3H16" stroke={C.ink} strokeWidth={3} strokeLinecap="square" />
  </svg>
);

const Header: React.FC = () => (
  <>
    <div style={{ position: 'absolute', left: 84, top: 30 }}>
      <div style={{ fontWeight: 900, fontSize: 84, letterSpacing: '-0.03em', lineHeight: 1 }}>shotkit</div>
      <div style={{ fontFamily: mono, fontWeight: 700, fontSize: 20, color: C.muted, marginTop: 14, letterSpacing: '0.01em' }}>
        by WhyStrohm&nbsp;/&nbsp;{VERSION}
      </div>
    </div>
    <Pill style={{ position: 'absolute', right: 48, top: 46 }}>
      <span style={{ fontFamily: mono, fontWeight: 700, fontSize: 20, letterSpacing: '0.04em' }}>
        STORYBOARD PIPELINE / {VERSION}
      </span>
    </Pill>
  </>
);

const Pill: React.FC<{ children: React.ReactNode; style?: React.CSSProperties }> = ({ children, style }) => (
  <div
    style={{
      border: `2.5px solid ${C.ink}`,
      borderRadius: 16,
      padding: '11px 20px',
      display: 'inline-flex',
      alignItems: 'center',
      ...style,
    }}
  >
    {children}
  </div>
);

const StageCard: React.FC<{ stage: (typeof STAGES)[number]; cx: number }> = ({ stage, cx }) => (
  <>
    <div style={{ position: 'absolute', left: cx - ICON / 2, top: 184, display: 'flex', alignItems: 'baseline', gap: 13 }}>
      <span style={{ fontWeight: 900, fontSize: 42, letterSpacing: '-0.02em' }}>{stage.n}</span>
      <span style={{ fontWeight: 900, fontSize: 23, letterSpacing: '0.04em' }}>{stage.name}</span>
    </div>
    <div
      style={{
        position: 'absolute',
        left: cx - ICON / 2,
        top: ICON_TOP,
        width: ICON,
        height: ICON,
        border: `3px solid ${C.ink}`,
        borderRadius: 22,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: C.bg,
      }}
    >
      <StageIcon kind={stage.icon} />
    </div>
    <div
      style={{
        position: 'absolute',
        left: cx - 130,
        top: ICON_TOP + ICON + 16,
        width: 260,
        textAlign: 'center',
        fontFamily: mono,
        fontWeight: 700,
        fontSize: 23,
      }}
    >
      {stage.file}
    </div>
  </>
);

const StageIcon: React.FC<{ kind: 'grid' | 'lines' | 'crop' | 'doc' }> = ({ kind }) => {
  const k = C.ink;
  if (kind === 'grid') {
    return (
      <svg width={60} height={60} viewBox="0 0 64 64" fill="none">
        {[4, 25, 46].map((y) =>
          [4, 25, 46].map((x) => <rect key={`${x}-${y}`} x={x} y={y} width={14} height={14} rx={2} fill={k} />),
        )}
      </svg>
    );
  }
  if (kind === 'lines') {
    return (
      <svg width={62} height={52} viewBox="0 0 66 56" fill="none">
        {[6, 22, 38, 50].map((y, i) => (
          <line key={y} x1={4} y1={y} x2={i === 3 ? 44 : 62} y2={y} stroke={k} strokeWidth={i === 0 ? 5 : 4} strokeLinecap="round" />
        ))}
      </svg>
    );
  }
  if (kind === 'crop') {
    return (
      <svg width={60} height={60} viewBox="0 0 64 64" fill="none">
        <path d="M4 18V4H18" stroke={k} strokeWidth={3.4} strokeLinecap="round" />
        <path d="M46 4H60V18" stroke={k} strokeWidth={3.4} strokeLinecap="round" />
        <path d="M60 46V60H46" stroke={k} strokeWidth={3.4} strokeLinecap="round" />
        <path d="M18 60H4V46" stroke={k} strokeWidth={3.4} strokeLinecap="round" />
        <circle cx={32} cy={32} r={5} stroke={k} strokeWidth={3.2} />
      </svg>
    );
  }
  return (
    <svg width={52} height={62} viewBox="0 0 56 66" fill="none">
      <path d="M4 3H35L52 20V63H4V3Z" stroke={k} strokeWidth={3.2} strokeLinejoin="round" />
      <path d="M35 3V20H52" stroke={k} strokeWidth={3.2} strokeLinejoin="round" />
      <line x1={14} y1={36} x2={42} y2={36} stroke={k} strokeWidth={3} strokeLinecap="round" />
      <line x1={14} y1={47} x2={42} y2={47} stroke={k} strokeWidth={3} strokeLinecap="round" />
    </svg>
  );
};

const Arrow: React.FC<{ x1: number; x2: number; y: number }> = ({ x1, x2, y }) => {
  const mid = (x1 + x2) / 2;
  return (
    <svg style={{ position: 'absolute', left: 0, top: 0 }} width={1280} height={720}>
      <line x1={x1} y1={y} x2={x2 - 14} y2={y} stroke={C.ink} strokeWidth={5} strokeLinecap="round" />
      <path d={`M${x2 - 16} ${y - 10} L${x2} ${y} L${x2 - 16} ${y + 10} Z`} fill={C.ink} />
      <circle cx={mid} cy={y} r={8} fill={C.orange} />
    </svg>
  );
};

const ReviseLoop: React.FC<{ fromX: number; toX: number; yStart: number; yBus: number }> = ({ fromX, toX, yStart, yBus }) => {
  const r = 12;
  const d =
    `M ${fromX} ${yStart} ` +
    `L ${fromX} ${yBus - r} Q ${fromX} ${yBus} ${fromX - r} ${yBus} ` +
    `L ${toX + r} ${yBus} Q ${toX} ${yBus} ${toX} ${yBus - r} ` +
    `L ${toX} ${yStart}`;
  return (
    <svg style={{ position: 'absolute', left: 0, top: 0 }} width={1280} height={720}>
      <path d={d} stroke={C.orange} strokeWidth={3} fill="none" strokeDasharray="3 9" strokeLinecap="round" strokeLinejoin="round" />
      <path
        d={`M ${toX - 8} ${yStart + 13} L ${toX} ${yStart} L ${toX + 8} ${yStart + 13}`}
        stroke={C.orange}
        strokeWidth={3}
        fill="none"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <text x={(fromX + toX) / 2} y={yBus + 30} fill={C.orange} fontFamily={inter} fontWeight={900} fontSize={20} letterSpacing="0.04em" textAnchor="middle">
        REVISE LOOP
      </text>
    </svg>
  );
};

const BrandLockBar: React.FC = () => (
  <div
    style={{
      position: 'absolute',
      left: 64,
      right: 64,
      top: 478,
      border: `3px solid ${C.ink}`,
      borderRadius: 22,
      height: 62,
      display: 'flex',
      alignItems: 'center',
      paddingLeft: 26,
      paddingRight: 26,
    }}
  >
    <LockIcon />
    <span style={{ fontWeight: 900, fontSize: 22, letterSpacing: '0.04em', marginLeft: 16 }}>BRAND-LOCK</span>
    <span style={{ fontFamily: mono, fontWeight: 700, fontSize: 21, marginLeft: 30 }}>brand-lock.snapshot.md</span>
    <span style={{ color: C.orange, fontWeight: 900, fontSize: 22, marginLeft: 20 }}>&bull;</span>
    <span style={{ fontFamily: mono, fontWeight: 700, fontSize: 21, marginLeft: 20 }}>audit trail</span>
    <span style={{ marginLeft: 'auto', fontFamily: mono, fontWeight: 700, fontSize: 18, color: C.muted }}>
      &larr; brand-lock-extractor
    </span>
  </div>
);

const LockIcon: React.FC = () => (
  <svg width={26} height={30} viewBox="0 0 26 30" fill="none">
    <rect x={2} y={12} width={22} height={16} rx={3} fill={C.ink} />
    <path d="M7 12V8A6 6 0 0 1 19 8V12" stroke={C.ink} strokeWidth={3} fill="none" />
  </svg>
);

const Footer: React.FC = () => (
  <>
    <div style={{ position: 'absolute', left: 64, top: 576 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 18 }}>
        <svg width={40} height={16} viewBox="0 0 40 16" fill="none">
          <line x1={2} y1={8} x2={28} y2={8} stroke={C.ink} strokeWidth={4} strokeLinecap="round" />
          <path d="M26 2 L36 8 L26 14 Z" fill={C.ink} />
        </svg>
        <span style={{ fontWeight: 900, fontSize: 18, letterSpacing: '0.03em' }}>DATA FLOW</span>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 18, marginTop: 16 }}>
        <span style={{ width: 40, display: 'flex', justifyContent: 'center' }}>
          <span style={{ width: 18, height: 18, borderRadius: 9, backgroundColor: C.orange, display: 'block' }} />
        </span>
        <span style={{ fontWeight: 900, fontSize: 18, letterSpacing: '0.03em' }}>KEY NODE</span>
      </div>
    </div>

    <div
      style={{
        position: 'absolute',
        left: 470,
        top: 566,
        border: `2.5px solid ${C.ink}`,
        borderRadius: 16,
        padding: '13px 22px',
        fontFamily: mono,
        fontWeight: 700,
        fontSize: 16,
        lineHeight: 1.55,
        minWidth: 320,
      }}
    >
      <div>SPECIFICATIONS</div>
      <div>STORYBOARD PIPELINE ARCHITECTURE</div>
      <div>SCALE 1:1</div>
    </div>

    <Pill style={{ position: 'absolute', right: 48, top: 570, borderRadius: 16, padding: '13px 22px', minWidth: 250 }}>
      <div style={{ width: '100%', fontFamily: mono, fontWeight: 700, fontSize: 16, lineHeight: 1.7 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 22 }}>
          <span style={{ color: C.muted }}>DATE</span>
          <span>{DATE}</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 22 }}>
          <span style={{ color: C.muted }}>DOC ID</span>
          <span>{DOC_ID}</span>
        </div>
      </div>
    </Pill>
  </>
);
