import React from 'react';
import { AbsoluteFill } from 'remotion';
import { loadFont as loadInter } from '@remotion/google-fonts/Inter';
import { loadFont as loadJetBrainsMono } from '@remotion/google-fonts/JetBrainsMono';

import { COLORS } from './tokens';

// Static social-preview / README hero card. One frame, re-renderable.
// Render: npx remotion still SocialPreview ../docs/images/social-preview.png --frame=0
//
// This is the source of record for docs/images/social-preview.png. It was a baked
// PNG with no source until v0.2.0; now it is a composition so it stays in sync.

const { fontFamily: interFamily } = loadInter('normal', { weights: ['500', '900'] });
loadInter('italic', { weights: ['500'] });
const { fontFamily: monoFamily } = loadJetBrainsMono('normal', { weights: ['400', '700'] });

const VERSION = 'v0.2.0';
const DATE = '2026-06-18';
const DOC_ID = 'WS-SK-CARD-001';

const STAGES = [
  { n: '01', name: 'ARCHITECT', file: 'storyboard.md', icon: 'grid' as const },
  { n: '02', name: 'FORGE', file: 'prompts/*.txt', icon: 'lines' as const },
  { n: '03', name: 'CRITIQUE', file: 'critique.json', icon: 'crop' as const },
  { n: '04', name: 'PREVIEW', file: 'preview.html', icon: 'doc' as const },
];

const ROW_Y = 232;
const CARD_W = 210;
const GAP = 86;
const FIRST_X = 92;
const cardX = (i: number) => FIRST_X + i * (CARD_W + GAP);
const cardCenter = (i: number) => cardX(i) + CARD_W / 2;
const ICON_TOP = ROW_Y + 64;
const ICON_SIZE = 84;
const ICON_CENTER_Y = ICON_TOP + ICON_SIZE / 2;

export const SocialPreview: React.FC = () => {
  return (
    <AbsoluteFill
      style={{
        backgroundColor: COLORS.cream,
        fontFamily: interFamily,
        color: COLORS.ink,
      }}
    >
      <Header />

      {/* Connector arrows between stages */}
      {[0, 1, 2].map((i) => (
        <Connector key={i} x1={cardX(i) + CARD_W} x2={cardX(i + 1)} y={ICON_CENTER_Y} />
      ))}

      {/* The closed QA loop: CRITIQUE -> FORGE (revise the failed shots) */}
      <ReviseLoop fromX={cardCenter(2)} toX={cardCenter(1)} topY={ICON_TOP + ICON_SIZE + 14} />

      {/* Stage cards */}
      {STAGES.map((s, i) => (
        <StageCard key={s.n} stage={s} x={cardX(i)} />
      ))}

      {/* Brand-lock foundation bar */}
      <BrandLockBar />

      <Footer />
    </AbsoluteFill>
  );
};

const Header: React.FC = () => (
  <div style={{ position: 'absolute', top: 0, left: 0, width: 1280, height: 120 }}>
    <div style={{ position: 'absolute', left: 48, top: 34 }}>
      <svg width={44} height={44} viewBox="0 0 44 44" fill="none" style={{ position: 'absolute', top: -2, left: 0 }}>
        <path d="M2 14V2H14" stroke={COLORS.ink} strokeWidth={2} strokeLinecap="square" />
      </svg>
      <div style={{ fontWeight: 900, fontSize: 50, letterSpacing: '-0.02em', marginLeft: 58, marginTop: -6 }}>
        shotkit
      </div>
      <div
        style={{
          fontWeight: 500,
          fontSize: 15,
          color: COLORS.muted,
          marginLeft: 58,
          marginTop: 4,
          letterSpacing: '0.02em',
        }}
      >
        by WhyStrohm&nbsp;&nbsp;/&nbsp;&nbsp;{VERSION}
      </div>
    </div>
    <div
      style={{
        position: 'absolute',
        right: 48,
        top: 42,
        border: `1px solid ${COLORS.ink}`,
        borderRadius: 8,
        padding: '9px 16px',
        fontFamily: monoFamily,
        fontSize: 13,
        letterSpacing: '0.06em',
      }}
    >
      STORYBOARD PIPELINE / v.2.0
    </div>
  </div>
);

const StageCard: React.FC<{ stage: (typeof STAGES)[number]; x: number }> = ({ stage, x }) => (
  <div style={{ position: 'absolute', left: x, top: ROW_Y, width: CARD_W }}>
    <div style={{ display: 'flex', alignItems: 'baseline', gap: 12 }}>
      <span style={{ fontFamily: monoFamily, fontSize: 26, fontWeight: 700 }}>{stage.n}</span>
      <span style={{ fontFamily: monoFamily, fontSize: 17, letterSpacing: '0.08em' }}>{stage.name}</span>
    </div>
    <div
      style={{
        marginTop: 26,
        width: ICON_SIZE,
        height: ICON_SIZE,
        marginLeft: (CARD_W - ICON_SIZE) / 2,
        border: `1.5px solid ${COLORS.ink}`,
        borderRadius: 10,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: COLORS.cream,
      }}
    >
      <StageIcon kind={stage.icon} />
    </div>
    <div
      style={{
        marginTop: 18,
        textAlign: 'center',
        fontFamily: monoFamily,
        fontSize: 15,
        color: COLORS.ink,
      }}
    >
      {stage.file}
    </div>
  </div>
);

const StageIcon: React.FC<{ kind: 'grid' | 'lines' | 'crop' | 'doc' }> = ({ kind }) => {
  const s = COLORS.ink;
  if (kind === 'grid') {
    return (
      <svg width={44} height={44} viewBox="0 0 44 44" fill="none">
        {[2, 16, 30].map((y) =>
          [2, 16, 30].map((x) => (
            <rect key={`${x}-${y}`} x={x} y={y} width={12} height={12} stroke={s} strokeWidth={1.6} />
          )),
        )}
      </svg>
    );
  }
  if (kind === 'lines') {
    return (
      <svg width={46} height={40} viewBox="0 0 46 40" fill="none">
        {[4, 14, 24, 34].map((y, i) => (
          <line key={y} x1={2} y1={y} x2={i === 3 ? 30 : 44} y2={y} stroke={s} strokeWidth={2} strokeLinecap="square" />
        ))}
      </svg>
    );
  }
  if (kind === 'crop') {
    return (
      <svg width={44} height={44} viewBox="0 0 44 44" fill="none">
        <path d="M2 12V2H12" stroke={s} strokeWidth={1.8} />
        <path d="M32 2H42V12" stroke={s} strokeWidth={1.8} />
        <path d="M42 32V42H32" stroke={s} strokeWidth={1.8} />
        <path d="M12 42H2V32" stroke={s} strokeWidth={1.8} />
        <circle cx={22} cy={22} r={4} stroke={s} strokeWidth={1.8} />
      </svg>
    );
  }
  return (
    <svg width={38} height={46} viewBox="0 0 38 46" fill="none">
      <path d="M3 2H24L35 13V44H3V2Z" stroke={s} strokeWidth={1.8} strokeLinejoin="round" />
      <path d="M24 2V13H35" stroke={s} strokeWidth={1.8} strokeLinejoin="round" />
      <line x1={10} y1={24} x2={28} y2={24} stroke={s} strokeWidth={1.6} />
      <line x1={10} y1={32} x2={28} y2={32} stroke={s} strokeWidth={1.6} />
    </svg>
  );
};

const Connector: React.FC<{ x1: number; x2: number; y: number }> = ({ x1, x2, y }) => {
  const mid = (x1 + x2) / 2;
  return (
    <svg style={{ position: 'absolute', left: 0, top: 0 }} width={1280} height={720}>
      <line x1={x1 + 8} y1={y} x2={x2 - 8} y2={y} stroke={COLORS.ink} strokeWidth={1.6} />
      <path d={`M${x2 - 16} ${y - 5}L${x2 - 8} ${y}L${x2 - 16} ${y + 5}`} stroke={COLORS.ink} strokeWidth={1.6} fill="none" />
      <circle cx={mid} cy={y} r={4.5} fill={COLORS.coral} />
    </svg>
  );
};

// The v0.2.0 closed loop: critique.json feeds prompt-forge revision mode.
const ReviseLoop: React.FC<{ fromX: number; toX: number; topY: number }> = ({ fromX, toX, topY }) => {
  const dip = topY + 40;
  return (
    <svg style={{ position: 'absolute', left: 0, top: 0 }} width={1280} height={720}>
      <path
        d={`M${fromX} ${topY} C ${fromX} ${dip}, ${toX} ${dip}, ${toX} ${topY + 6}`}
        stroke={COLORS.coral}
        strokeWidth={1.8}
        fill="none"
        strokeDasharray="5 5"
      />
      <path d={`M${toX - 5} ${topY + 14}L${toX} ${topY + 5}L${toX + 5} ${topY + 14}`} stroke={COLORS.coral} strokeWidth={1.8} fill="none" />
      <text
        x={(fromX + toX) / 2}
        y={dip + 4}
        fill={COLORS.coral}
        fontFamily={monoFamily}
        fontSize={13}
        letterSpacing="0.06em"
        textAnchor="middle"
      >
        revise loop
      </text>
    </svg>
  );
};

const BrandLockBar: React.FC = () => (
  <div
    style={{
      position: 'absolute',
      left: 92,
      right: 92,
      top: 468,
      border: `1px solid ${COLORS.ink}`,
      borderRadius: 8,
      height: 52,
      display: 'flex',
      alignItems: 'center',
      paddingLeft: 22,
      paddingRight: 22,
      fontFamily: monoFamily,
      fontSize: 15,
    }}
  >
    <span style={{ fontWeight: 700, letterSpacing: '0.08em' }}>BRAND-LOCK</span>
    <span style={{ marginLeft: 24, color: COLORS.ink }}>brand-lock.snapshot.md</span>
    <span style={{ marginLeft: 18, color: COLORS.muted }}>·</span>
    <span style={{ marginLeft: 18, color: COLORS.ink }}>audit trail</span>
    <span style={{ marginLeft: 'auto', color: COLORS.muted, fontSize: 13 }}>
      &larr; brand-lock-extractor
    </span>
  </div>
);

const Footer: React.FC = () => (
  <div style={{ position: 'absolute', top: 562, left: 0, width: 1280, height: 158 }}>
    <div
      style={{
        position: 'absolute',
        left: 48,
        top: 14,
        fontFamily: monoFamily,
        fontSize: 11,
        letterSpacing: '0.06em',
      }}
    >
      <LegendRow label="DATA FLOW" symbol={<ArrowSymbol />} />
      <div style={{ height: 6 }} />
      <LegendRow label="KEY NODE" symbol={<DotSymbol />} />
    </div>

    <div
      style={{
        position: 'absolute',
        left: 470,
        top: 16,
        border: `1px solid ${COLORS.ink}`,
        borderRadius: 6,
        padding: '8px 14px',
        fontFamily: monoFamily,
        fontSize: 11,
        letterSpacing: '0.06em',
        lineHeight: 1.6,
      }}
    >
      <div style={{ fontWeight: 700 }}>SPECIFICATIONS</div>
      <div>STORYBOARD PIPELINE ARCHITECTURE</div>
      <div>SCALE 1:1</div>
    </div>

    <div
      style={{
        position: 'absolute',
        right: 48,
        top: 16,
        border: `1px solid ${COLORS.ink}`,
        borderRadius: 6,
        padding: '8px 14px',
        fontFamily: monoFamily,
        fontSize: 11,
        letterSpacing: '0.06em',
        lineHeight: 1.7,
        minWidth: 230,
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16 }}>
        <span style={{ color: COLORS.muted }}>DATE</span>
        <span>{DATE}</span>
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16 }}>
        <span style={{ color: COLORS.muted }}>DOC ID</span>
        <span>{DOC_ID}</span>
      </div>
    </div>

    <div
      style={{
        position: 'absolute',
        bottom: 18,
        left: 0,
        width: 1280,
        textAlign: 'center',
        fontStyle: 'italic',
        fontWeight: 500,
        fontSize: 15,
        color: COLORS.muted,
      }}
    >
      the pre-production system we use to ship hundreds of videos a month / open-sourced
    </div>
  </div>
);

const LegendRow: React.FC<{ label: string; symbol: React.ReactNode }> = ({ label, symbol }) => (
  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
    <span style={{ minWidth: 80 }}>{label}</span>
    {symbol}
  </div>
);

const ArrowSymbol: React.FC = () => (
  <svg width={28} height={10} viewBox="0 0 28 10" fill="none">
    <path d="M0 5H24M20 1L24 5L20 9" stroke={COLORS.ink} strokeWidth={1.4} fill="none" strokeLinecap="square" />
  </svg>
);

const DotSymbol: React.FC = () => (
  <svg width={28} height={10} viewBox="0 0 28 10" fill="none">
    <circle cx={14} cy={5} r={3.5} fill={COLORS.coral} />
  </svg>
);
