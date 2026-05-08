import React from 'react';
import { Composition } from 'remotion';
import { ShotkitDemo } from './ShotkitDemo';

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="ShotkitDemo"
      component={ShotkitDemo}
      durationInFrames={240}
      fps={30}
      width={1280}
      height={720}
    />
  );
};
