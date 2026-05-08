import React from 'react';
import {
  AbsoluteFill,
  interpolate,
  staticFile,
  useCurrentFrame,
} from 'remotion';
import { loadFont as loadInter } from '@remotion/google-fonts/Inter';
import { loadFont as loadJetBrainsMono } from '@remotion/google-fonts/JetBrainsMono';

import { COLORS } from './tokens';

const { fontFamily: interFamily } = loadInter('normal', { weights: ['500', '900'] });
loadInter('italic', { weights: ['500'] });
const { fontFamily: monoFamily } = loadJetBrainsMono('normal', { weights: ['400'] });

// Content zone: between the static header and footer chrome.
// Header: 0-120. Footer: 570-720. Content: 130-560.
const CHROME = { headerHeight: 120, footerY: 570 };
const CONTENT = {
  top: 130,
  bottom: 560,
  centerX: 640,
};

// Act boundaries in frames at 30fps.
const ACT_1_END = 360; // 0-12s pain
const ACT_2_END = 870; // 12-29s reframe
const ACT_3_END = 1410; // 29-47s build
const ACT_4_END = 1860; // 47-62s reveal
const ACT_5_END = 2280; // 62-76s generators
const ACT_6_END = 2700; // 76-90s install + close

export const ShotkitExplainer: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill
      style={{
        backgroundColor: COLORS.cream,
        fontFamily: interFamily,
        color: COLORS.ink,
      }}
    >
      {frame < ACT_1_END && <Act1Pain frame={frame} />}
      {frame >= ACT_1_END && frame < ACT_2_END && (
        <Act2FiveLayers frame={frame - ACT_1_END} />
      )}
      {frame >= ACT_2_END && frame < ACT_3_END && (
        <Act3Build frame={frame - ACT_2_END} />
      )}
      {frame >= ACT_3_END && frame < ACT_4_END && (
        <Act4Reveal frame={frame - ACT_3_END} />
      )}
      {frame >= ACT_4_END && frame < ACT_5_END && (
        <Act5Generators frame={frame - ACT_4_END} />
      )}
      {frame >= ACT_5_END && frame < ACT_6_END && (
        <Act6Install frame={frame - ACT_5_END} />
      )}

      <Header />
      <Footer />
    </AbsoluteFill>
  );
};

// ============================================================================
// Act 1: Pain
// 0-12s. Brief types in, four generator pills appear with X marks, headline lands.
// ============================================================================

const BRIEF_LINES = [
  'One social video this week.',
  'Make it pop. Make it brandy.',
];
const BRIEF_TEXT = BRIEF_LINES.join('\n');

const GENERATORS = ['Midjourney', 'Flux', 'Ideogram', 'GPT Image'];

const Act1Pain: React.FC<{ frame: number }> = ({ frame }) => {
  // Phase 1 (0-90 frames): typewriter brief
  // Phase 2 (90-180 frames): generator pills appear
  // Phase 3 (180-360 frames): pain title fades in, brief and pills hold
  const charsTyped = Math.max(0, Math.min(BRIEF_TEXT.length, Math.floor(frame * (60 / 30))));
  const briefSlice = BRIEF_TEXT.slice(0, charsTyped);
  const briefDone = charsTyped >= BRIEF_TEXT.length;
  const cursorVisible = !briefDone || Math.floor(frame / 8) % 2 === 0;

  const pillsBaseFrame = 90;
  const titleFadeIn = interpolate(frame, [200, 260], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <>
      {/* BRIEF panel, top of content area */}
      <div
        style={{
          position: 'absolute',
          left: 360,
          top: 150,
          width: 560,
        }}
      >
        <PanelHeader>BRIEF</PanelHeader>
        <pre
          style={{
            margin: 0,
            marginTop: 18,
            fontFamily: monoFamily,
            fontSize: 18,
            lineHeight: 1.55,
            color: COLORS.ink,
            whiteSpace: 'pre-wrap',
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

      {/* Generator pills row, middle of content area */}
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          top: 290,
          display: 'flex',
          justifyContent: 'center',
          gap: 18,
        }}
      >
        {GENERATORS.map((name, i) => {
          const startFrame = pillsBaseFrame + i * 12;
          const local = frame - startFrame;
          const opacity = interpolate(local, [0, 16], [0, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          });
          const translateY = interpolate(local, [0, 20], [10, 0], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          });
          return (
            <div
              key={name}
              style={{
                opacity,
                transform: `translateY(${translateY}px)`,
                padding: '12px 18px',
                border: `1px solid ${COLORS.rule}`,
                borderRadius: 8,
                backgroundColor: '#FFFFFF',
                fontFamily: monoFamily,
                fontSize: 14,
                color: COLORS.ink,
                letterSpacing: '0.04em',
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                minWidth: 130,
                justifyContent: 'space-between',
              }}
            >
              <span>{name}</span>
              <span style={{ color: COLORS.coral, fontSize: 16 }}>×</span>
            </div>
          );
        })}
      </div>

      {/* Pain headline */}
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          top: 410,
          textAlign: 'center',
          opacity: titleFadeIn,
          padding: '0 80px',
        }}
      >
        <div
          style={{
            fontFamily: interFamily,
            fontWeight: 900,
            fontSize: 38,
            lineHeight: 1.15,
            color: COLORS.ink,
            letterSpacing: '-0.02em',
          }}
        >
          You don't have a content problem.
        </div>
        <div
          style={{
            fontFamily: interFamily,
            fontWeight: 900,
            fontSize: 38,
            lineHeight: 1.15,
            color: COLORS.ink,
            letterSpacing: '-0.02em',
            marginTop: 6,
          }}
        >
          You have a pre-production problem
          <span style={{ color: COLORS.coral }}>.</span>
        </div>
      </div>
    </>
  );
};

// ============================================================================
// Act 2: Five Layers
// 12-29s. Title, then five layer cards stagger in.
// ============================================================================

const FIVE_LAYERS = [
  { name: 'BRAND LOCK', sub: 'palette, type, mood, never list', accent: true },
  { name: 'SERIES LOCK', sub: 'character, environment, lighting' },
  { name: 'SHOT SPEC', sub: 'framing, angle, motion, subject' },
  { name: 'TEXT LAYER', sub: 'never in the prompt' },
  { name: 'GENERATOR ADAPTER', sub: 'midjourney, flux, ideogram, gpt-image, sora' },
];

const Act2FiveLayers: React.FC<{ frame: number }> = ({ frame }) => {
  const titleOpacity = interpolate(frame, [0, 30], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <>
      {/* Title at top of content area */}
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          top: 145,
          textAlign: 'center',
          opacity: titleOpacity,
        }}
      >
        <div
          style={{
            fontFamily: interFamily,
            fontWeight: 900,
            fontSize: 32,
            color: COLORS.ink,
            letterSpacing: '-0.02em',
          }}
        >
          Five layers. Locked top to bottom
          <span style={{ color: COLORS.coral }}>.</span>
        </div>
      </div>

      {/* Layer cards, stacked, fully within content zone */}
      <div
        style={{
          position: 'absolute',
          top: 200,
          left: 280,
          right: 280,
        }}
      >
        {FIVE_LAYERS.map((layer, i) => {
          const startFrame = 50 + i * 50;
          const local = frame - startFrame;
          const opacity = interpolate(local, [0, 24], [0, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          });
          const translateY = interpolate(local, [0, 30], [16, 0], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          });
          return (
            <div
              key={layer.name}
              style={{
                marginBottom: 10,
                padding: '12px 20px',
                border: `1px solid ${COLORS.rule}`,
                borderRadius: 8,
                backgroundColor: '#FFFFFF',
                opacity,
                transform: `translateY(${translateY}px)`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: 16,
                height: 56,
                boxSizing: 'border-box',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                <span
                  style={{
                    fontFamily: monoFamily,
                    fontSize: 13,
                    color: COLORS.muted,
                    letterSpacing: '0.08em',
                  }}
                >
                  {String(i + 1).padStart(2, '0')}
                </span>
                <div>
                  <div
                    style={{
                      fontFamily: monoFamily,
                      fontSize: 14,
                      letterSpacing: '0.08em',
                      color: COLORS.ink,
                      fontWeight: 700,
                    }}
                  >
                    {layer.name}
                  </div>
                  <div
                    style={{
                      fontFamily: interFamily,
                      fontWeight: 500,
                      fontSize: 12,
                      color: COLORS.muted,
                      marginTop: 2,
                    }}
                  >
                    {layer.sub}
                  </div>
                </div>
              </div>
              {layer.accent && (
                <div
                  style={{
                    width: 8,
                    height: 8,
                    borderRadius: 4,
                    backgroundColor: COLORS.coral,
                  }}
                />
              )}
            </div>
          );
        })}
      </div>
    </>
  );
};

// ============================================================================
// Act 3: Build
// 29-47s. Brief types into left panel, file tree assembles in right panel.
// ============================================================================

const BUILD_BRIEF_LINES = [
  '90-second explainer for shotkit.',
  'Pain reframe proof promise.',
  'Use brand-packs/whystrohm.md',
  'Aspect 16:9',
];
const BUILD_BRIEF_TEXT = BUILD_BRIEF_LINES.join('\n');

const FILE_TREE_ROWS = [
  { at: 60, text: 'output/' },
  { at: 75, text: '├── storyboard.md' },
  { at: 90, text: '├── shots.json' },
  { at: 105, text: '├── text-overlays.json' },
  { at: 120, text: '├── brand-lock.snapshot.md' },
  { at: 135, text: '├── prompts/' },
  { at: 150, text: '│   ├── midjourney.txt' },
  { at: 162, text: '│   ├── flux.txt' },
  { at: 174, text: '│   ├── ideogram.txt' },
  { at: 186, text: '│   ├── gpt-image.txt' },
  { at: 198, text: '│   ├── nano-banana.txt' },
  { at: 210, text: '│   ├── seedream.txt' },
  { at: 222, text: '│   └── runway-sora.txt' },
  { at: 240, text: '└── preview.html', coralDot: true },
];

const Act3Build: React.FC<{ frame: number }> = ({ frame }) => {
  const headerOpacity = interpolate(frame, [0, 20], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const charsTyped = Math.max(
    0,
    Math.min(BUILD_BRIEF_TEXT.length, Math.floor((frame - 20) * (50 / 30))),
  );
  const briefSlice = BUILD_BRIEF_TEXT.slice(0, charsTyped);
  const cursorVisible = Math.floor(frame / 8) % 2 === 0;

  const captionOpacity = interpolate(frame, [320, 380], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <>
      {/* Left: BRIEF */}
      <div
        style={{
          position: 'absolute',
          left: 100,
          top: 150,
          width: 460,
          opacity: headerOpacity,
        }}
      >
        <PanelHeader>BRIEF</PanelHeader>
        <pre
          style={{
            margin: 0,
            marginTop: 18,
            fontFamily: monoFamily,
            fontSize: 16,
            lineHeight: 1.55,
            color: COLORS.ink,
            whiteSpace: 'pre-wrap',
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

      {/* Right: OUTPUT file tree */}
      <div
        style={{
          position: 'absolute',
          left: 660,
          top: 150,
          width: 540,
          opacity: headerOpacity,
        }}
      >
        <PanelHeader>OUTPUT</PanelHeader>
        <div style={{ marginTop: 18 }}>
          {FILE_TREE_ROWS.map((row) => {
            const local = frame - row.at;
            const reveal = interpolate(local, [0, 8], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            });
            const translate = interpolate(local, [0, 8], [8, 0], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            });
            return (
              <div
                key={row.at}
                style={{
                  fontFamily: monoFamily,
                  fontSize: 14,
                  lineHeight: 1.6,
                  color: COLORS.ink,
                  opacity: reveal,
                  transform: `translateY(${translate}px)`,
                  display: 'flex',
                  alignItems: 'center',
                }}
              >
                <span style={{ whiteSpace: 'pre' }}>{row.text}</span>
                {row.coralDot && frame >= 250 && (
                  <span
                    style={{
                      marginLeft: 12,
                      width: 8,
                      height: 8,
                      borderRadius: 4,
                      backgroundColor: COLORS.coral,
                    }}
                  />
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Caption */}
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          top: 530,
          textAlign: 'center',
          opacity: captionOpacity,
        }}
      >
        <div
          style={{
            fontFamily: interFamily,
            fontWeight: 500,
            fontSize: 16,
            color: COLORS.muted,
            letterSpacing: '0.01em',
          }}
        >
          Brief in. Storyboard out. Audit trail included.
        </div>
      </div>
    </>
  );
};

// ============================================================================
// Act 4: Reveal
// 47-62s. Coral wipe expands, iframe scrolls through preview.html.
// ============================================================================

const Act4Reveal: React.FC<{ frame: number }> = ({ frame }) => {
  const wipeRadius = interpolate(frame, [0, 24], [0, 1100], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const scrollY = interpolate(frame, [30, 360], [0, 1400], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const captionOpacity = interpolate(frame, [330, 390], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <>
      <div
        style={{
          position: 'absolute',
          inset: 0,
          clipPath: `circle(${wipeRadius}px at 875px 480px)`,
        }}
      >
        <div
          style={{
            position: 'absolute',
            left: 60,
            top: 140,
            width: 1160,
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

      {/* Caption pill, sits over the iframe with cream background */}
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          top: 510,
          textAlign: 'center',
          opacity: captionOpacity,
        }}
      >
        <div
          style={{
            fontFamily: interFamily,
            fontWeight: 900,
            fontSize: 26,
            color: COLORS.ink,
            letterSpacing: '-0.02em',
            backgroundColor: COLORS.cream,
            display: 'inline-block',
            padding: '6px 18px',
            borderRadius: 6,
          }}
        >
          Files. Not panels
          <span style={{ color: COLORS.coral }}>.</span>
        </div>
      </div>
    </>
  );
};

// ============================================================================
// Act 5: Generators
// 62-76s. Center shot card, seven adapter labels fan out radially.
// ============================================================================

const ADAPTERS = [
  { name: 'Midjourney', angle: 0 },
  { name: 'Flux', angle: 51.4 },
  { name: 'Ideogram', angle: 102.8 },
  { name: 'GPT Image', angle: 154.2 },
  { name: 'Nano Banana', angle: 205.6 },
  { name: 'Seedream', angle: 257.0 },
  { name: 'Runway / Sora', angle: 308.4 },
];

const GENERATOR_CENTER = { cx: 640, cy: 370 };
const GENERATOR_RADIUS = 145;

const Act5Generators: React.FC<{ frame: number }> = ({ frame }) => {
  const titleOpacity = interpolate(frame, [0, 30], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const centerOpacity = interpolate(frame, [30, 60], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <>
      {/* Title */}
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          top: 142,
          textAlign: 'center',
          opacity: titleOpacity,
        }}
      >
        <div
          style={{
            fontFamily: interFamily,
            fontWeight: 900,
            fontSize: 24,
            color: COLORS.ink,
            letterSpacing: '-0.02em',
          }}
        >
          One shot. Seven generators. One spec
          <span style={{ color: COLORS.coral }}>.</span>
        </div>
      </div>

      {/* Connector lines */}
      <svg
        style={{
          position: 'absolute',
          left: 0,
          top: 0,
          width: 1280,
          height: 720,
          pointerEvents: 'none',
        }}
      >
        {ADAPTERS.map((adapter, i) => {
          const startFrame = 90 + i * 16;
          const local = frame - startFrame;
          const lineOpacity = interpolate(local, [0, 18], [0, 0.35], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          });
          const rad = (adapter.angle * Math.PI) / 180;
          const x = GENERATOR_CENTER.cx + Math.cos(rad) * GENERATOR_RADIUS;
          const y = GENERATOR_CENTER.cy + Math.sin(rad) * GENERATOR_RADIUS;
          return (
            <line
              key={adapter.name}
              x1={GENERATOR_CENTER.cx}
              y1={GENERATOR_CENTER.cy}
              x2={x}
              y2={y}
              stroke={COLORS.ink}
              strokeWidth={1}
              opacity={lineOpacity}
            />
          );
        })}
      </svg>

      {/* Center shot card */}
      <div
        style={{
          position: 'absolute',
          left: GENERATOR_CENTER.cx - 110,
          top: GENERATOR_CENTER.cy - 42,
          width: 220,
          height: 84,
          border: `1px solid ${COLORS.ink}`,
          borderRadius: 8,
          backgroundColor: '#FFFFFF',
          padding: 12,
          opacity: centerOpacity,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          gap: 4,
          boxSizing: 'border-box',
        }}
      >
        <div
          style={{
            fontFamily: monoFamily,
            fontSize: 11,
            letterSpacing: '0.08em',
            color: COLORS.muted,
          }}
        >
          SHOT_03
        </div>
        <div
          style={{
            fontFamily: interFamily,
            fontWeight: 500,
            fontSize: 13,
            color: COLORS.ink,
            textAlign: 'center',
            lineHeight: 1.35,
          }}
        >
          MCU eye-level push.
          <br />
          Founder, calm.
        </div>
      </div>

      {/* Adapter labels */}
      {ADAPTERS.map((adapter, i) => {
        const startFrame = 90 + i * 16;
        const local = frame - startFrame;
        const labelOpacity = interpolate(local, [0, 24], [0, 1], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        });
        const rad = (adapter.angle * Math.PI) / 180;
        const labelRadius = GENERATOR_RADIUS + 32;
        const x = GENERATOR_CENTER.cx + Math.cos(rad) * labelRadius;
        const y = GENERATOR_CENTER.cy + Math.sin(rad) * labelRadius;
        return (
          <div
            key={adapter.name}
            style={{
              position: 'absolute',
              left: x - 75,
              top: y - 14,
              width: 150,
              textAlign: 'center',
              opacity: labelOpacity,
              fontFamily: monoFamily,
              fontSize: 13,
              color: COLORS.ink,
              letterSpacing: '0.04em',
              backgroundColor: COLORS.cream,
              padding: '4px 8px',
              borderRadius: 4,
            }}
          >
            {adapter.name}
          </div>
        );
      })}
    </>
  );
};

// ============================================================================
// Act 6: Install + close
// 76-90s. Type-on install command, then tagline.
// ============================================================================

const INSTALL_LINES = [
  'git clone github.com/whystrohm/shotkit',
  'cd shotkit && ./install.sh',
];
const INSTALL_TEXT = INSTALL_LINES.join('\n');

const Act6Install: React.FC<{ frame: number }> = ({ frame }) => {
  const charsTyped = Math.max(0, Math.min(INSTALL_TEXT.length, Math.floor(frame * (50 / 30))));
  const installSlice = INSTALL_TEXT.slice(0, charsTyped);
  const cursorVisible = Math.floor(frame / 8) % 2 === 0;

  const taglineOpacity = interpolate(frame, [180, 240], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <>
      {/* Heading */}
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          top: 170,
          textAlign: 'center',
        }}
      >
        <div
          style={{
            fontFamily: interFamily,
            fontWeight: 900,
            fontSize: 30,
            color: COLORS.ink,
            letterSpacing: '-0.02em',
          }}
        >
          Install it
          <span style={{ color: COLORS.coral }}>.</span>
        </div>
      </div>

      {/* Install command block */}
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          top: 240,
          textAlign: 'center',
        }}
      >
        <pre
          style={{
            display: 'inline-block',
            margin: 0,
            padding: '20px 32px',
            border: `1px solid ${COLORS.ink}`,
            borderRadius: 8,
            backgroundColor: '#FFFFFF',
            fontFamily: monoFamily,
            fontSize: 18,
            lineHeight: 1.6,
            color: COLORS.ink,
            textAlign: 'left',
          }}
        >
          {installSlice}
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

      {/* Closing tagline */}
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          top: 460,
          textAlign: 'center',
          opacity: taglineOpacity,
        }}
      >
        <div
          style={{
            fontFamily: interFamily,
            fontStyle: 'italic',
            fontWeight: 500,
            fontSize: 18,
            color: COLORS.muted,
          }}
        >
          Pre-production for founder-led video at scale
          <span style={{ color: COLORS.coral, fontStyle: 'normal' }}>.</span>
        </div>
      </div>
    </>
  );
};

// ============================================================================
// Shared chrome
// ============================================================================

const PanelHeader: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div
    style={{
      fontFamily: monoFamily,
      fontSize: 13,
      letterSpacing: '0.08em',
      color: COLORS.ink,
      textTransform: 'uppercase',
    }}
  >
    {children}
  </div>
);

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
          fontSize: 44,
          color: COLORS.ink,
          letterSpacing: '-0.02em',
          marginLeft: 56,
          marginTop: -2,
        }}
      >
        shotkit
      </div>
      <div
        style={{
          fontFamily: interFamily,
          fontWeight: 500,
          fontSize: 13,
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
      EXPLAINER FILM / v.1.0
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
      <div>STORYBOARD PIPELINE EXPLAINER</div>
      <div>RUNTIME 90s</div>
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
        <span>WS-SK-EXP-001</span>
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
      pre-production for founder-led video at scale / open-sourced
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
