"use client";

import React, { useMemo } from 'react';
import { motion } from 'framer-motion';

export interface DnaWaveProps {
  status?: 'idle' | 'listening' | 'thinking' | 'speaking';
}

export const DnaWaveBackground: React.FC<DnaWaveProps> = ({ status = 'idle' }) => {
  const isListening = status === 'listening';
  const isThinking = status === 'thinking';
  const isSpeaking = status === 'speaking';
  const isIdle = status === 'idle';

  const PERIOD = 600; // Exact repeating wavelength in pixels
  const TOTAL_WIDTH = PERIOD * 2; // 2 full periods for seamless loop
  const HEIGHT = 200;
  const MID = HEIGHT / 2; // 100
  const AMP = isSpeaking ? 58 : isListening ? 52 : isThinking ? 62 : 46;

  // Pre-calculate smooth mathematical sine wave paths and DNA rungs
  const { path1, path2, rungs, particles } = useMemo(() => {
    let p1 = `M 0 ${MID}`;
    let p2 = `M 0 ${MID}`;
    const rungsList: { x: number; y1: number; y2: number }[] = [];
    const particlesList: { x: number; y: number }[] = [];

    // Dense curve generation (step = 4px) for silky smooth bezier curves
    for (let x = 0; x <= TOTAL_WIDTH; x += 4) {
      const theta = (x / PERIOD) * 2 * Math.PI;
      const y1 = MID - AMP * Math.sin(theta);
      const y2 = MID + AMP * Math.sin(theta);
      p1 += ` L ${x.toFixed(1)} ${y1.toFixed(1)}`;
      p2 += ` L ${x.toFixed(1)} ${y2.toFixed(1)}`;

      // Center harmonic particle line
      if (x % 40 === 0) {
        const harmonicY = MID + 14 * Math.sin(theta * 2);
        particlesList.push({ x, y: harmonicY });
      }
    }

    // Generate DNA base pair rungs every 28px
    for (let x = 14; x < TOTAL_WIDTH; x += 28) {
      // Skip exact crossover nodes to prevent zero-height rungs
      if (Math.abs(x % (PERIOD / 2)) < 10) continue;
      const theta = (x / PERIOD) * 2 * Math.PI;
      const y1 = MID - AMP * Math.sin(theta);
      const y2 = MID + AMP * Math.sin(theta);
      rungsList.push({ x, y1, y2 });
    }

    return { path1: p1, path2: p2, rungs: rungsList, particles: particlesList };
  }, [AMP, PERIOD, TOTAL_WIDTH, MID]);

  // Dynamic animation speeds depending on JARVIS core status
  const duration = isThinking ? 5.5 : isListening ? 7.5 : isSpeaking ? 9.0 : 15.0;

  // Theme colors
  const strand1Color = isListening
    ? '#c084fc' // Purple
    : isThinking
    ? '#22d3ee' // Quantum Cyan
    : isSpeaking
    ? '#38bdf8' // Electric Sky
    : '#06b6d4'; // Deep Cyan

  const strand2Color = isListening
    ? '#a855f7' // Violet
    : isThinking
    ? '#34d399' // Emerald
    : isSpeaking
    ? '#6366f1' // Indigo
    : '#2563eb'; // Royal Blue

  return (
    <div
      className="absolute inset-0 pointer-events-none overflow-hidden flex items-center justify-center opacity-75 select-none"
      style={{
        maskImage: 'linear-gradient(to right, transparent 0%, black 18%, black 82%, transparent 100%)',
        WebkitMaskImage: 'linear-gradient(to right, transparent 0%, black 18%, black 82%, transparent 100%)'
      }}
    >
      <motion.div
        className="flex shrink-0 relative h-[200px]"
        style={{ width: `${TOTAL_WIDTH}px` }}
        animate={{ x: [0, -PERIOD] }}
        transition={{
          repeat: Infinity,
          repeatType: "loop",
          duration: duration,
          ease: "linear",
        }}
      >
        <svg
          width={TOTAL_WIDTH}
          height={HEIGHT}
          viewBox={`0 0 ${TOTAL_WIDTH} ${HEIGHT}`}
          fill="none"
          className="w-full h-full overflow-visible"
        >
          <defs>
            {/* Holographic Glowing Filters */}
            <filter id="dna-glow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="3.5" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            
            {/* Gradient along Strand 1 */}
            <linearGradient id="strand1-grad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor={strand1Color} stopOpacity="0.8" />
              <stop offset="50%" stopColor="#38bdf8" stopOpacity="0.9" />
              <stop offset="100%" stopColor={strand1Color} stopOpacity="0.8" />
            </linearGradient>

            {/* Gradient along Strand 2 */}
            <linearGradient id="strand2-grad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor={strand2Color} stopOpacity="0.7" />
              <stop offset="50%" stopColor="#818cf8" stopOpacity="0.85" />
              <stop offset="100%" stopColor={strand2Color} stopOpacity="0.7" />
            </linearGradient>
          </defs>

          {/* 1. Center Reference Horizontal Laser Baseline */}
          <line
            x1="0"
            y1={MID}
            x2={TOTAL_WIDTH}
            y2={MID}
            stroke="rgba(14, 165, 233, 0.15)"
            strokeDasharray="4 8"
            strokeWidth="1"
          />

          {/* 2. Harmonic Center Particles */}
          {particles.map((p, idx) => (
            <circle
              key={idx}
              cx={p.x}
              cy={p.y}
              r="1.2"
              fill={strand1Color}
              opacity="0.4"
            />
          ))}

          {/* 3. DNA Base-Pair Hydrogen Rungs (Vertical bridges with glowing node beads) */}
          {rungs.map((rung, idx) => (
            <g key={idx} opacity={isIdle ? 0.35 : 0.65} className="transition-opacity duration-500">
              {/* Connecting Bridge Line */}
              <line
                x1={rung.x}
                y1={rung.y1}
                x2={rung.x}
                y2={rung.y2}
                stroke="url(#strand1-grad)"
                strokeWidth="1.2"
                strokeDasharray="2 3"
              />
              {/* Node Bead on Strand 1 */}
              <circle
                cx={rung.x}
                cy={rung.y1}
                r="2.2"
                fill={strand1Color}
                filter="url(#dna-glow)"
              />
              {/* Node Bead on Strand 2 */}
              <circle
                cx={rung.x}
                cy={rung.y2}
                r="2.2"
                fill={strand2Color}
                filter="url(#dna-glow)"
              />
            </g>
          ))}

          {/* 4. Strand 1 (Cyan/Sky Sine Helix) */}
          <path
            d={path1}
            fill="none"
            stroke="url(#strand1-grad)"
            strokeWidth={isSpeaking || isListening ? "2.5" : "1.8"}
            strokeLinecap="round"
            filter="url(#dna-glow)"
            className="transition-all duration-300"
          />

          {/* 5. Strand 2 (Indigo/Purple Counter-Helix) */}
          <path
            d={path2}
            fill="none"
            stroke="url(#strand2-grad)"
            strokeWidth={isSpeaking || isListening ? "2.5" : "1.8"}
            strokeLinecap="round"
            filter="url(#dna-glow)"
            className="transition-all duration-300"
          />
        </svg>
      </motion.div>
    </div>
  );
};
