/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useEffect, useState } from 'react';
import { Particle, EffectType, DensityLevel, SwayLevel } from '../types';

interface ParticleLayerProps {
  activeEffect: EffectType | null;
  density: DensityLevel;
  sway: SwayLevel;
  triggerId: number; // Incrementing counter to force regenerate even if clicking the same effect multiple times
}

export const BALLOON_COLORS = [
  { name: 'Burgundy Crimson', primary: '#e11d48', dark: '#9f1239' }, // deep luxury crimson
  { name: 'Satin Teal', primary: '#0d9488', dark: '#115e59' },      // deep warm teal
  { name: 'Royal Sapphire', primary: '#2563eb', dark: '#1e3a8a' },  // royal blue
  { name: 'Golden Amber', primary: '#d97706', dark: '#78350f' },    // rich bronze gold
  { name: 'Amethyst Velvet', primary: '#7c3aed', dark: '#4c1d95' }, // deep purple
  { name: 'Vibrant Tangerine', primary: '#ea580c', dark: '#9a3412' } // warm formal orange
];

const SNOW_CHARS = ['❄', '❅', '❆'];

export default function ParticleLayer({ activeEffect, density, sway, triggerId }: ParticleLayerProps) {
  const [particles, setParticles] = useState<Particle[]>([]);

  useEffect(() => {
    if (!activeEffect) {
      setParticles([]);
      return;
    }

    // Determine target quantity based on density controls
    let count = 40;
    if (density === 'low') count = 20;
    if (density === 'rich') count = 75;

    const generated: Particle[] = [];

    for (let i = 0; i < count; i++) {
      // Stagger start delay over first 1.8 seconds so the flow is organic throughout the 5-second session.
      const delay = Math.random() * 1.8;
      
      // Compute travel duration. Falling/floating takes around 3.0 to 4.2 seconds.
      const duration = 2.8 + Math.random() * 1.4;

      // Select size in the medium band (20px to 36px) as requested.
      const size = activeEffect === 'snowflakes'
        ? 20 + Math.floor(Math.random() * 12)  // 20px - 32px
        : 28 + Math.floor(Math.random() * 14); // 28px - 42px

      // Compute sway oscillation speed
      let swayDuration = 2 + Math.random() * 3; // 2s - 5s
      if (sway === 'none') swayDuration = 0;
      else if (sway === 'flowing') swayDuration = 1.5 + Math.random() * 1.5; // faster sway

      generated.push({
        id: `p-${triggerId}-${i}`,
        type: activeEffect === 'snowflakes' ? 'snowflake' : 'balloon',
        left: 2 + Math.random() * 96, // 2% to 98% horizontal dispersion
        size,
        duration,
        delay,
        colorIndex: Math.floor(Math.random() * BALLOON_COLORS.length),
        flakeChar: SNOW_CHARS[Math.floor(Math.random() * SNOW_CHARS.length)],
        swayDuration,
      });
    }

    setParticles(generated);
  }, [activeEffect, density, sway, triggerId]);

  if (!activeEffect || particles.length === 0) return null;

  return (
    <div className="fixed inset-0 pointer-events-none z-50 overflow-hidden select-none">
      {particles.map((p) => {
        // Build style blocks using CSS variables to handle durations and delays flawlessly
        const travelAnimation = p.type === 'snowflake' ? 'fall' : 'rise';
        const swayAnimation = p.type === 'snowflake' ? 'snow-sway' : 'balloon-sway';

        const containerStyle: React.CSSProperties = {
          position: 'absolute',
          left: `${p.left}%`,
          width: `${p.size}px`,
          height: p.type === 'snowflake' ? `${p.size}px` : `${p.size * 2}px`, // Balloons are tall
          animationName: p.swayDuration > 0 ? swayAnimation : 'none',
          animationDuration: `${p.swayDuration}s`,
          animationIterationCount: 'infinite',
          animationTimingFunction: 'ease-in-out',
          animationDelay: `${p.delay * 0.4}s`, // slightly desynced starting position
          willChange: 'transform',
        };

        const particleStyle: React.CSSProperties = {
          width: '100%',
          height: '100%',
          animationName: travelAnimation,
          animationDuration: `${p.duration}s`,
          animationDelay: `${p.delay}s`,
          animationTimingFunction: 'linear',
          animationFillMode: 'both',
          willChange: 'transform',
        };

        return (
          <div key={p.id} style={containerStyle}>
            <div style={particleStyle}>
              {p.type === 'snowflake' ? (
                <div
                  className="flex items-center justify-center text-slate-700/85 filter drop-shadow-[0_2px_4px_rgba(255,255,255,0.9)] dark:text-zinc-300 dark:drop-shadow-[0_2px_6px_rgba(0,0,0,0.5)]"
                  style={{
                    fontSize: `${p.size}px`,
                    lineHeight: 1,
                    transform: 'translate3d(0, 0, 0)',
                  }}
                >
                  {p.flakeChar}
                </div>
              ) : (
                <div className="relative w-full h-full" style={{ transform: 'translate3d(0, 0, 0)' }}>
                  {/* Balloon design using high fidelity inline SVG coordinates */}
                  <svg
                    viewBox="0 0 40 90"
                    className="w-full h-full"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <defs>
                      <radialGradient
                        id={`grad-${p.id}`}
                        cx="35%"
                        cy="30%"
                        r="60%"
                      >
                        <stop offset="0%" stopColor="#ffffff" stopOpacity="0.6" />
                        <stop offset="60%" stopColor={BALLOON_COLORS[p.colorIndex || 0].primary} />
                        <stop offset="100%" stopColor={BALLOON_COLORS[p.colorIndex || 0].dark} />
                      </radialGradient>
                    </defs>
                    
                    {/* Primary thread/string */}
                    <path
                      d="M20,44 Q17,58 23,71 T20,90"
                      stroke="#94a3b8"
                      strokeWidth="1.5"
                      fill="none"
                      strokeLinecap="round"
                    />

                    {/* Balloon balloon-knot connector triangle */}
                    <polygon
                      points="17,44 23,44 20,40"
                      fill={BALLOON_COLORS[p.colorIndex || 0].dark}
                    />

                    {/* Glossy Balloon Base Egg Shape */}
                    <ellipse
                      cx="20"
                      cy="25"
                      rx="15"
                      ry="19"
                      fill={`url(#grad-${p.id})`}
                      filter="drop-shadow(0 3px 6px rgba(0,0,0,0.15))"
                    />
                  </svg>
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
