import React from 'react';
import {
  AbsoluteFill,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import { loadFont as loadInter } from '@remotion/google-fonts/Inter';
import { loadFont as loadJetBrainsMono } from '@remotion/google-fonts/JetBrainsMono';

import { COLORS } from './tokens';

const { fontFamily: interFamily } = loadInter('normal', { weights: ['500', '900'] });
loadInter('italic', { weights: ['500'] });
const { fontFamily: monoFamily } = loadJetBrainsMono('normal', { weights: ['400'] });

const BRIEF_LINES = [
  '30-second founder explainer.',
  'Pain-reframe-promise structure.',
  'Use brand-packs/whystrohm.md',
  'Aspect 9:16',
];
const BRIEF_TEXT = BRIEF_LINES.join('\n');

type TreeRow = { at: number; text: string; coralDot?: boolean };

const FILE_TREE_ROWS: TreeRow[] = [
  { at: 78, text: 'output/' },
  { at: 84, text: '├── storyboard.md' },
  { at: 90, text: '├── shots.json' },
  { at: 96, text: '├── text-overlays.json' },
  { at: 102, text: '├── brand-lock.snapshot.md' },
  { at: 108, text: '├── prompts/' },
  { at: 111, text: '│   ├── midjourney.txt' },
  { at: 114, text: '│   ├── flux.txt' },
  { at: 117, text: '│   ├── ideogram.txt' },
  { at: 120, text: '│   ├── gpt-image.txt' },
  { at: 123, text: '│   ├── nano-banana.txt' },
  { at: 126, text: '│   ├── seedream.txt' },
  { at: 129, text: '│   └── runway-sora.txt' },
  { at: 135, text: '└── preview.html', coralDot: true },
];

const PANEL = {
  leftX: 120,
  rightX: 700,
  width: 460,
  topY: 140,
  contentTopY: 200,
};

const CHROME = {
  headerHeight: 120,
  footerY: 570,
};

const WIPE_ORIGIN = { x: 875, y: 486 };
const WIPE_MAX_RADIUS = 1000;

const TYPING_START = 12;
const TYPING_END = 66;
const CHARS_PER_SECOND = 50;
const FPS = 30;

export const ShotkitDemo: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const inOpeningOrLoop = frame < TYPING_START || frame >= 228;
  const middleFade = interpolate(frame, [210, 228], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const isTyping = frame >= TYPING_START && frame < TYPING_END;
  let charsToShow = 0;
  if (isTyping) {
    charsToShow = Math.min(
      BRIEF_TEXT.length,
      Math.floor((frame - TYPING_START) * (CHARS_PER_SECOND / FPS)),
    );
  } else if (frame >= TYPING_END && frame < 228) {
    charsToShow = BRIEF_TEXT.length;
  }
  const briefSlice = BRIEF_TEXT.slice(0, charsToShow);

  const cursorVisible = isTyping ? true : Math.floor(frame / 8) % 2 === 0;
  const briefTextOpacity = inOpeningOrLoop ? 1 : middleFade;

  let dotOpacity = 0;
  let dotScale = 1;
  let dotColor: string = COLORS.ink;
  if (frame < 72) {
    dotOpacity = 0.3 + 0.4 * Math.abs(Math.sin((Math.PI * frame) / 30));
  } else if (frame < 78) {
    const cueProg = (frame - 72) / 6;
    dotScale = 1 + 0.2 * Math.sin(cueProg * Math.PI);
    dotColor = COLORS.coral;
    dotOpacity = 1.0;
  } else if (frame >= 228) {
    dotOpacity = 0.3 + 0.4 * Math.abs(Math.sin((Math.PI * frame) / 30));
  }

  const showIframeLayer = frame >= 150;
  const wipeRadius = interpolate(frame, [150, 162], [0, WIPE_MAX_RADIUS], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const iframeScrollY = interpolate(frame, [162, 204], [0, 1200], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const iframeLayerOpacity = inOpeningOrLoop ? 0 : middleFade;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: COLORS.cream,
        fontFamily: interFamily,
        color: COLORS.ink,
      }}
    >
      <CenterPanels
        briefSlice={briefSlice}
        briefTextOpacity={briefTextOpacity}
        cursorVisible={cursorVisible}
        dotOpacity={dotOpacity}
        dotScale={dotScale}
        dotColor={dotColor}
        frame={frame}
        middleFade={middleFade}
        inOpeningOrLoop={inOpeningOrLoop}
      />
      {showIframeLayer && (
        <IframeReveal
          wipeRadius={wipeRadius}
          scrollY={iframeScrollY}
          opacity={iframeLayerOpacity}
        />
      )}
      <Header />
      <Footer />
    </AbsoluteFill>
  );
};

type CenterProps = {
  briefSlice: string;
  briefTextOpacity: number;
  cursorVisible: boolean;
  dotOpacity: number;
  dotScale: number;
  dotColor: string;
  frame: number;
  middleFade: number;
  inOpeningOrLoop: boolean;
};

const CenterPanels: React.FC<CenterProps> = ({
  briefSlice,
  briefTextOpacity,
  cursorVisible,
  dotOpacity,
  dotScale,
  dotColor,
  frame,
  middleFade,
  inOpeningOrLoop,
}) => {
  return (
    <>
      <div
        style={{
          position: 'absolute',
          left: PANEL.leftX,
          top: PANEL.topY,
          width: PANEL.width,
        }}
      >
        <PanelHeader>BRIEF</PanelHeader>
        <pre
          style={{
            margin: 0,
            marginTop: 24,
            fontFamily: monoFamily,
            fontSize: 18,
            lineHeight: 1.5,
            color: COLORS.ink,
            whiteSpace: 'pre-wrap',
            opacity: briefTextOpacity,
          }}
        >
          {briefSlice}
          <span
            style={{
              display: 'inline-block',
              width: 2,
              height: '1em',
              backgroundColor: COLORS.ink,
              marginLeft: 1,
              verticalAlign: 'text-bottom',
              opacity: cursorVisible ? 1 : 0,
            }}
          />
        </pre>
      </div>

      <div
        style={{
          position: 'absolute',
          left: PANEL.rightX,
          top: PANEL.topY,
          width: PANEL.width,
        }}
      >
        <PanelHeader>OUTPUT</PanelHeader>
        {dotOpacity > 0 && (
          <div
            style={{
              marginTop: 28,
              width: 6,
              height: 6,
              borderRadius: 3,
              backgroundColor: dotColor,
              opacity: dotOpacity,
              transform: `scale(${dotScale})`,
              transformOrigin: 'center',
            }}
          />
        )}
        <FileTree frame={frame} opacity={inOpeningOrLoop ? 0 : middleFade} />
      </div>
    </>
  );
};

const PanelHeader: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div
    style={{
      fontFamily: monoFamily,
      fontSize: 14,
      letterSpacing: '0.08em',
      color: COLORS.ink,
      textTransform: 'uppercase',
    }}
  >
    {children}
  </div>
);

const FileTree: React.FC<{ frame: number; opacity: number }> = ({ frame, opacity }) => {
  return (
    <div style={{ marginTop: 24, opacity }}>
      {FILE_TREE_ROWS.map((row) => {
        const localFrame = frame - row.at;
        const reveal = interpolate(localFrame, [0, 8], [0, 1], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        });
        const translate = interpolate(localFrame, [0, 8], [8, 0], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        });
        let dotPulse = 0;
        if (row.coralDot && frame >= 144 && frame <= 150) {
          dotPulse = Math.sin(((frame - 144) / 6) * Math.PI);
        }
        return (
          <div
            key={row.at}
            style={{
              fontFamily: monoFamily,
              fontSize: 16,
              lineHeight: 1.5,
              color: COLORS.ink,
              opacity: reveal,
              transform: `translateY(${translate}px)`,
              display: 'flex',
              alignItems: 'center',
            }}
          >
            <span style={{ whiteSpace: 'pre' }}>{row.text}</span>
            {row.coralDot && (
              <span
                style={{
                  marginLeft: 12,
                  width: 8,
                  height: 8,
                  borderRadius: 4,
                  backgroundColor: COLORS.coral,
                  opacity: frame >= 135 ? 1 : 0,
                  transform: `scale(${1 + 0.3 * dotPulse})`,
                }}
              />
            )}
          </div>
        );
      })}
    </div>
  );
};

const IframeReveal: React.FC<{
  wipeRadius: number;
  scrollY: number;
  opacity: number;
}> = ({ wipeRadius, scrollY, opacity }) => {
  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        clipPath: `circle(${wipeRadius}px at ${WIPE_ORIGIN.x}px ${WIPE_ORIGIN.y}px)`,
        opacity,
      }}
    >
      <div
        style={{
          position: 'absolute',
          left: 40,
          top: CHROME.headerHeight + 20,
          width: 1200,
          height: 410,
          backgroundColor: '#FFFFFF',
          border: `1px solid ${COLORS.ink}`,
          borderRadius: 8,
          overflow: 'hidden',
        }}
      >
        <iframe
          src={staticFile('preview.html')}
          title="shotkit example preview"
          style={{
            width: '100%',
            height: 4000,
            border: 'none',
            transform: `translateY(${-scrollY}px)`,
            backgroundColor: '#FFFFFF',
          }}
        />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(ellipse at center, transparent 60%, rgba(0,0,0,0.10) 100%)',
            pointerEvents: 'none',
          }}
        />
      </div>
    </div>
  );
};

const Header: React.FC = () => (
  <div
    style={{
      position: 'absolute',
      top: 0,
      left: 0,
      width: 1280,
      height: CHROME.headerHeight,
      pointerEvents: 'none',
    }}
  >
    <div style={{ position: 'absolute', left: 40, top: 28 }}>
      <BracketMark />
      <div
        style={{
          fontFamily: interFamily,
          fontWeight: 900,
          fontSize: 48,
          color: COLORS.ink,
          letterSpacing: '-0.02em',
          marginLeft: 56,
          marginTop: -4,
        }}
      >
        shotkit
      </div>
      <div
        style={{
          fontFamily: interFamily,
          fontWeight: 500,
          fontSize: 14,
          color: COLORS.muted,
          marginLeft: 56,
          marginTop: 4,
          letterSpacing: '0.02em',
        }}
      >
        by WhyStrohm  /  v0.1.0
      </div>
    </div>
    <div
      style={{
        position: 'absolute',
        right: 40,
        top: 36,
        border: `1px solid ${COLORS.ink}`,
        borderRadius: 8,
        padding: '8px 14px',
        fontFamily: monoFamily,
        fontSize: 12,
        color: COLORS.ink,
        letterSpacing: '0.06em',
      }}
    >
      STORYBOARD PIPELINE / v.1.0
    </div>
  </div>
);

const BracketMark: React.FC = () => (
  <svg
    width={44}
    height={44}
    viewBox="0 0 44 44"
    fill="none"
    style={{ position: 'absolute', top: -4, left: 0 }}
  >
    <path
      d="M2 14V2H14"
      stroke={COLORS.ink}
      strokeWidth={2}
      strokeLinecap="square"
    />
  </svg>
);

const Footer: React.FC = () => (
  <div
    style={{
      position: 'absolute',
      top: CHROME.footerY,
      left: 0,
      width: 1280,
      height: 720 - CHROME.footerY,
      pointerEvents: 'none',
    }}
  >
    <div
      style={{
        position: 'absolute',
        left: 40,
        top: 20,
        fontFamily: monoFamily,
        fontSize: 11,
        color: COLORS.ink,
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
        left: 480,
        top: 22,
        border: `1px solid ${COLORS.ink}`,
        borderRadius: 6,
        padding: '8px 14px',
        fontFamily: monoFamily,
        fontSize: 11,
        color: COLORS.ink,
        letterSpacing: '0.06em',
        lineHeight: 1.6,
        textAlign: 'left',
      }}
    >
      <div style={{ fontWeight: 700 }}>SPECIFICATIONS</div>
      <div>STORYBOARD PIPELINE ARCHITECTURE</div>
      <div>SCALE 1:1</div>
    </div>

    <div
      style={{
        position: 'absolute',
        right: 40,
        top: 22,
        border: `1px solid ${COLORS.ink}`,
        borderRadius: 6,
        padding: '8px 14px',
        fontFamily: monoFamily,
        fontSize: 11,
        color: COLORS.ink,
        letterSpacing: '0.06em',
        lineHeight: 1.7,
        minWidth: 220,
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16 }}>
        <span style={{ color: COLORS.muted }}>DATE</span>
        <span>2026-05-08</span>
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16 }}>
        <span style={{ color: COLORS.muted }}>DOC ID</span>
        <span>WS-SK-DEMO-001</span>
      </div>
    </div>

    <div
      style={{
        position: 'absolute',
        bottom: 22,
        left: 0,
        width: 1280,
        textAlign: 'center',
        fontFamily: interFamily,
        fontStyle: 'italic',
        fontWeight: 500,
        fontSize: 14,
        color: COLORS.muted,
      }}
    >
      the pre-production system we use to ship hundreds of videos a month / open-sourced
    </div>
  </div>
);

const LegendRow: React.FC<{ label: string; symbol: React.ReactNode }> = ({
  label,
  symbol,
}) => (
  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
    <span style={{ minWidth: 80 }}>{label}</span>
    {symbol}
  </div>
);

const ArrowSymbol: React.FC = () => (
  <svg width={28} height={10} viewBox="0 0 28 10" fill="none">
    <path
      d="M0 5H24M20 1L24 5L20 9"
      stroke={COLORS.ink}
      strokeWidth={1.4}
      fill="none"
      strokeLinecap="square"
    />
  </svg>
);

const DotSymbol: React.FC = () => (
  <svg width={28} height={10} viewBox="0 0 28 10" fill="none">
    <circle cx={14} cy={5} r={3.5} fill={COLORS.coral} />
  </svg>
);
