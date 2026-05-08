import React from 'react';
import { Composition } from 'remotion';
import { ShotkitDemo } from './ShotkitDemo';
import { ShotkitExplainer } from './ShotkitExplainer';

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="ShotkitDemo"
        component={ShotkitDemo}
        durationInFrames={240}
        fps={30}
        width={1280}
        height={720}
      />
      <Composition
        id="ShotkitExplainer"
        component={ShotkitExplainer}
        durationInFrames={2700}
        fps={30}
        width={1280}
        height={720}
      />
    </>
  );
};
