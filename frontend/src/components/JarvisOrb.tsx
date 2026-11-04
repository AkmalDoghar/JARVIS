"use client";

import React, { useRef, useEffect, useState, useMemo } from "react";
import { motion } from "framer-motion";

export interface JarvisOrbProps {
  status: "idle" | "listening" | "thinking" | "speaking";
  size?: "sm" | "md" | "lg";
  userName?: string;
  caption?: string;
  onClick?: () => void;
}

interface RadiationParticle {
  angle: number;
  dist: number;
  speed: number;
  size: number;
  opacity: number;
  life: number;
  maxLife: number;
}

export const JarvisOrb: React.FC<JarvisOrbProps> = ({
  status,
  size = "lg",
  userName = "Sir",
  caption,
  onClick,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  const isListening = status === "listening";
  const isThinking = status === "thinking";
  const isSpeaking = status === "speaking";

  // Dimension scaling
  const dim = size === "sm" ? 180 : size === "lg" ? 270 : 220;
  const coreRadius = dim * 0.22; // ~59px
  const maxRadius = dim * 0.48;  // ~130px

  // Controlled, subtle color scheme - NO blinding white glow
  const theme = useMemo(() => {
    if (isListening) {
      return {
        primary: "#a855f7",        // Neon Purple
        secondary: "#c084fc",
        dotColor: "168, 85, 247",
        coreBorder: "rgba(168, 85, 247, 0.45)",
        statusText: "LISTENING // AUDIO BUFFER ACTIVE",
        statusColor: "text-purple-300",
        badgeBg: "bg-purple-950/60 border-purple-500/40 text-purple-200",
        speedMultiplier: 1.4,
      };
    }
    if (isThinking) {
      return {
        primary: "#10b981",        // Cyber Emerald
        secondary: "#22d3ee",
        dotColor: "16, 185, 129",
        coreBorder: "rgba(16, 185, 129, 0.5)",
        statusText: "PROCESSING // NEURAL HEURISTICS",
        statusColor: "text-emerald-300",
        badgeBg: "bg-emerald-950/60 border-emerald-500/40 text-emerald-200",
        speedMultiplier: 1.8,
      };
    }
    if (isSpeaking) {
      return {
        primary: "#0ea5e9",        // Electric Sky Blue
        secondary: "#38bdf8",
        dotColor: "14, 165, 233",
        coreBorder: "rgba(14, 165, 233, 0.45)",
        statusText: "VOCALIZING // NEURAL SYNTHESIS",
        statusColor: "text-sky-300",
        badgeBg: "bg-sky-950/60 border-sky-500/40 text-sky-200",
        speedMultiplier: 1.6,
      };
    }
    // Idle state: Subtle Deep Cyan
    return {
      primary: "#06b6d4",
      secondary: "#0284c7",
      dotColor: "6, 182, 212",
      coreBorder: "rgba(6, 182, 212, 0.35)",
      statusText: caption ? (caption.length > 30 ? caption.slice(0, 28) + "..." : caption) : `ONLINE // READY, ${userName.toUpperCase()}`,
      statusColor: "text-cyan-300",
      badgeBg: "bg-cyan-950/50 border-cyan-500/30 text-cyan-200",
      speedMultiplier: 1.0,
    };
  }, [isListening, isThinking, isSpeaking, caption, userName]);

  // Subtle 3D mouse tilt tracking
  const [tilt, setTilt] = useState({ x: 0, y: 0 });

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const cx = rect.left + rect.width / 2;
    const cy = rect.top + rect.height / 2;
    const dx = (e.clientX - cx) / (rect.width / 2);
    const dy = (e.clientY - cy) / (rect.height / 2);
    setTilt({ x: -dy * 8, y: dx * 8 });
  };

  const handleMouseLeave = () => {
    setTilt({ x: 0, y: 0 });
  };

  // High-performance HTML5 Canvas Radiation Dots Engine
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animId: number;
    const dpr = window.devicePixelRatio || 1;
    const width = dim + 40;
    const height = dim + 40;

    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);

    const cx = width / 2;
    const cy = height / 2;

    // Initialize radiation particles
    const particleCount = 75;
    const particles: RadiationParticle[] = [];

    const spawnParticle = (): RadiationParticle => ({
      angle: Math.random() * Math.PI * 2,
      dist: coreRadius + Math.random() * 8,
      speed: (0.45 + Math.random() * 0.85) * theme.speedMultiplier,
      size: Math.random() * 1.8 + 0.8,
      opacity: Math.random() * 0.4 + 0.6,
      life: 0,
      maxLife: 60 + Math.random() * 40,
    });

    for (let i = 0; i < particleCount; i++) {
      const p = spawnParticle();
      // Distribute radially at start for smooth continuous loop
      p.dist = coreRadius + Math.random() * (maxRadius - coreRadius);
      particles.push(p);
    }

    // Expanding radiation ring shockwaves
    const shockwaves = [
      { r: coreRadius, alpha: 0.35, speed: 0.6 },
      { r: coreRadius + (maxRadius - coreRadius) * 0.5, alpha: 0.2, speed: 0.6 },
    ];

    const render = () => {
      ctx.clearRect(0, 0, width, height);

      // 1. Draw subtle expanding radiation wave rings
      for (let i = 0; i < shockwaves.length; i++) {
        const sw = shockwaves[i];
        sw.r += sw.speed * theme.speedMultiplier;
        const progress = (sw.r - coreRadius) / (maxRadius - coreRadius);
        sw.alpha = Math.max(0, (1 - progress) * 0.3);

        if (sw.r >= maxRadius) {
          sw.r = coreRadius;
          sw.alpha = 0.3;
        }

        ctx.beginPath();
        ctx.arc(cx, cy, sw.r, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(${theme.dotColor}, ${sw.alpha * 0.6})`;
        ctx.lineWidth = 1;
        ctx.stroke();
      }

      // 2. Draw radiating dots pushing outward from core to perimeter
      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];

        // Move outwards radially
        p.dist += p.speed * theme.speedMultiplier;
        p.life++;

        // Fade out as it approaches max boundary
        const distRatio = (p.dist - coreRadius) / (maxRadius - coreRadius);
        const fade = distRatio <= 0.2 ? distRatio / 0.2 : Math.max(0, 1 - distRatio);
        const currentOpacity = p.opacity * fade;

        // Position coordinates
        const px = cx + Math.cos(p.angle) * p.dist;
        const py = cy + Math.sin(p.angle) * p.dist;

        // Render dot
        ctx.beginPath();
        ctx.arc(px, py, p.size, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${theme.dotColor}, ${currentOpacity})`;
        ctx.fill();

        // Subtle laser glow for larger radiating particles
        if (p.size > 1.8 && currentOpacity > 0.4) {
          ctx.beginPath();
          ctx.arc(px, py, p.size * 1.8, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(${theme.dotColor}, ${currentOpacity * 0.25})`;
          ctx.fill();
        }

        // Reset if reached outer perimeter or life expired
        if (p.dist >= maxRadius || p.life >= p.maxLife) {
          particles[i] = spawnParticle();
        }
      }

      animId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animId);
    };
  }, [dim, coreRadius, maxRadius, theme.dotColor, theme.speedMultiplier]);

  return (
    <div
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className="relative flex flex-col items-center justify-center select-none group perspective-1000 py-1"
    >
      {/* 3D Gyroscopic Container */}
      <motion.div
        onClick={onClick}
        className="relative flex items-center justify-center cursor-pointer preserve-3d"
        style={{ width: `${dim + 30}px`, height: `${dim + 30}px` }}
        animate={{
          rotateX: tilt.x,
          rotateY: tilt.y,
        }}
        transition={{ type: "spring", stiffness: 240, damping: 24 }}
        title="Click to interact with JARVIS Voice"
      >
        {/* Layer 0A: Concentric Outward Radiating Shockwave Layers emitting from the orb */}
        {[0, 1, 2].map((i) => (
          <motion.div
            key={i}
            className="absolute rounded-full pointer-events-none z-0"
            style={{
              width: `${dim}px`,
              height: `${dim}px`,
              border: `1px solid rgba(${theme.dotColor}, 0.3)`,
              boxShadow: `0 0 18px rgba(${theme.dotColor}, 0.15)`,
            }}
            animate={{
              scale: [1, 1.4, 1.85],
              opacity: isSpeaking ? [0.55, 0.22, 0] : isThinking ? [0.5, 0.2, 0] : [0.35, 0.12, 0],
            }}
            transition={{
              duration: isThinking ? 2.0 : isSpeaking ? 2.4 : 3.8,
              delay: i * 1.0,
              repeat: Infinity,
              ease: "easeOut",
            }}
          />
        ))}

        {/* Layer 0B: HTML5 Canvas Radiating Dots & Waves */}
        <canvas
          ref={canvasRef}
          className="absolute inset-0 pointer-events-none z-10"
          style={{ width: `${dim + 40}px`, height: `${dim + 40}px` }}
        />

        {/* ========================================================================= */}
        {/* 4 CONCENTRIC BORDER LAYERS ROTATING IN OPPOSITE DIRECTIONS */}
        {/* ========================================================================= */}

        {/* BORDER LAYER 1 (Outermost - Clockwise) */}
        <motion.div
          className="absolute rounded-full pointer-events-none z-20 flex items-center justify-center"
          style={{ width: `${dim}px`, height: `${dim}px` }}
          animate={{ rotate: 360 }}
          transition={{
            duration: isThinking ? 14 : isSpeaking ? 22 : 32,
            repeat: Infinity,
            ease: "linear",
          }}
        >
          <svg className="w-full h-full overflow-visible" viewBox="0 0 100 100">
            {/* 6 Segmented Precision Outer Laser Arcs */}
            <circle
              cx="50"
              cy="50"
              r="48"
              fill="none"
              stroke={theme.primary}
              strokeWidth="1.2"
              strokeDasharray="24 10 12 8 36 14"
              strokeLinecap="round"
              opacity={0.8}
            />
            {/* Cardinal Alignment Dots */}
            {[0, 90, 180, 270].map((deg) => (
              <circle
                key={deg}
                cx={50 + 48 * Math.cos((deg * Math.PI) / 180)}
                cy={50 + 48 * Math.sin((deg * Math.PI) / 180)}
                r="1.2"
                fill={theme.secondary}
                opacity={0.9}
              />
            ))}
          </svg>
        </motion.div>

        {/* BORDER LAYER 2 (Middle-Outer - Counter-Clockwise [Opposite]) */}
        <motion.div
          className="absolute rounded-full pointer-events-none z-20 flex items-center justify-center"
          style={{ width: `${dim - 28}px`, height: `${dim - 28}px` }}
          animate={{ rotate: -360 }}
          transition={{
            duration: isThinking ? 11 : isSpeaking ? 18 : 26,
            repeat: Infinity,
            ease: "linear",
          }}
        >
          <svg className="w-full h-full overflow-visible" viewBox="0 0 100 100">
            {/* Fine Dotted Calibration Ring */}
            <circle
              cx="50"
              cy="50"
              r="48"
              fill="none"
              stroke={theme.secondary}
              strokeWidth="1.0"
              strokeDasharray="2 6"
              opacity={0.65}
            />
          </svg>
        </motion.div>

        {/* BORDER LAYER 3 (Middle-Inner - Clockwise [Opposite]) */}
        <motion.div
          className="absolute rounded-full pointer-events-none z-20 flex items-center justify-center"
          style={{ width: `${dim - 56}px`, height: `${dim - 56}px` }}
          animate={{ rotate: 360 }}
          transition={{
            duration: isThinking ? 8 : isSpeaking ? 14 : 20,
            repeat: Infinity,
            ease: "linear",
          }}
        >
          <svg className="w-full h-full overflow-visible" viewBox="0 0 100 100">
            {/* Segmented Tech Track with Angular Notches */}
            <circle
              cx="50"
              cy="50"
              r="48"
              fill="none"
              stroke={theme.primary}
              strokeWidth="1.2"
              strokeDasharray="14 14 6 8"
              strokeLinecap="round"
              opacity={0.7}
            />
          </svg>
        </motion.div>

        {/* BORDER LAYER 4 (Innermost framing the core - Counter-Clockwise [Opposite]) */}
        <motion.div
          className="absolute rounded-full pointer-events-none z-20 flex items-center justify-center"
          style={{ width: `${dim - 84}px`, height: `${dim - 84}px` }}
          animate={{ rotate: -360 }}
          transition={{
            duration: isThinking ? 6 : isSpeaking ? 10 : 16,
            repeat: Infinity,
            ease: "linear",
          }}
        >
          <svg className="w-full h-full overflow-visible" viewBox="0 0 100 100">
            {/* Razor-sharp aperture boundary ring */}
            <circle
              cx="50"
              cy="50"
              r="48"
              fill="none"
              stroke={theme.secondary}
              strokeWidth="0.9"
              strokeDasharray="4 4"
              opacity={0.6}
            />
          </svg>
        </motion.div>

        {/* ========================================================================= */}
        {/* CENTER CORE: SUBTLE, DARK METALLIC TECH IRIS (Controlled glow, NOT blinding) */}
        {/* ========================================================================= */}
        <motion.div
          className="relative rounded-full flex items-center justify-center overflow-hidden z-30 shadow-xl"
          style={{
            width: `${dim - 110}px`,
            height: `${dim - 110}px`,
            // Dark obsidian titanium gradient - NO blinding white blowout
            background: "radial-gradient(circle at 50% 50%, #06152a 0%, #030a16 60%, #01040a 100%)",
            border: `1.5px solid ${theme.coreBorder}`,
            boxShadow: `0 0 16px rgba(${theme.dotColor}, 0.25), inset 0 0 12px rgba(0, 0, 0, 0.9)`,
          }}
          animate={{
            scale: isThinking
              ? [0.96, 1.04, 0.96]
              : isSpeaking
              ? [0.97, 1.03, 0.97]
              : isListening
              ? [0.98, 1.02, 0.98]
              : [0.99, 1.01, 0.99],
          }}
          transition={{
            duration: isThinking ? 0.8 : isSpeaking ? 0.6 : 2.2,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        >
          {/* Internal Geometric Aperture Blades (Subtle Tech Grid) */}
          <div className="absolute inset-1.5 rounded-full border border-cyan-500/20 flex items-center justify-center opacity-60 pointer-events-none">
            {[0, 60, 120].map((deg) => (
              <div
                key={deg}
                className="absolute w-full h-[1px]"
                style={{
                  transform: `rotate(${deg}deg)`,
                  background: `linear-gradient(90deg, transparent 20%, rgba(${theme.dotColor}, 0.35) 50%, transparent 80%)`,
                }}
              />
            ))}
          </div>

          {/* Central Controlled Micro Energy Node */}
          <motion.div
            className="relative z-10 w-6 h-6 rounded-full flex items-center justify-center border"
            style={{
              borderColor: `rgba(${theme.dotColor}, 0.6)`,
              backgroundColor: "#030c18",
              boxShadow: `0 0 8px rgba(${theme.dotColor}, 0.4)`,
            }}
            animate={{
              scale: isThinking ? [0.85, 1.15, 0.85] : [0.92, 1.08, 0.92],
            }}
            transition={{
              duration: isThinking ? 0.6 : 1.6,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          >
            {/* Crisp Central Dot */}
            <div
              className="w-2 h-2 rounded-full shadow-[0_0_6px_currentColor]"
              style={{ backgroundColor: theme.primary }}
            />
          </motion.div>
        </motion.div>

        {/* Precision HUD Reticle Crosshairs (Faint, sleek) */}
        <div className="absolute inset-0 pointer-events-none flex items-center justify-center opacity-20">
          <div className="w-[80%] h-[1px] bg-gradient-to-r from-transparent via-cyan-400 to-transparent" />
          <div className="absolute h-[80%] w-[1px] bg-gradient-to-b from-transparent via-cyan-400 to-transparent" />
        </div>
      </motion.div>

      {/* Sleek Minimalist Tactical Status Tag Below */}
      <div
        onClick={onClick}
        className={`mt-2 px-3.5 py-1 rounded-full border text-[10px] font-mono font-bold tracking-wider backdrop-blur-md shadow-md transition-all duration-300 cursor-pointer flex items-center gap-2 ${theme.badgeBg} hover:scale-105 active:scale-95 z-20`}
        title="Click to activate voice input or interrupt JARVIS"
      >
        <span className="w-1.5 h-1.5 rounded-full bg-current animate-ping" />
        <span>{theme.statusText}</span>
      </div>
    </div>
  );
};
