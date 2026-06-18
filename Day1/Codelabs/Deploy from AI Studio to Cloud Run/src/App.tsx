/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useEffect } from 'react';
import { EffectType, DensityLevel, SwayLevel } from './types';
import ParticleLayer from './components/ParticleLayer';
import StatusTracker from './components/StatusTracker';
import ControlPanel from './components/ControlPanel';
import { Sparkles, Info } from 'lucide-react';

export default function App() {
  const [activeEffect, setActiveEffect] = useState<EffectType | null>(null);
  const [timeLeft, setTimeLeft] = useState<number>(0);
  const [density, setDensity] = useState<DensityLevel>('standard');
  const [sway, setSway] = useState<SwayLevel>('gentle');
  
  // triggerId forces active particle regeneration and resets the 5-second timer immediately on quick successive button clicks.
  const [triggerId, setTriggerId] = useState<number>(0);

  // Elegant timed lifecycle for the 5-second active overlay duration
  useEffect(() => {
    if (!activeEffect) {
      setTimeLeft(0);
      return;
    }

    const durationMs = 5000;
    const intervalTickMs = 40; // High resolution 40ms interval for fluid 25fps progress updates
    setTimeLeft(durationMs);

    const timer = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= intervalTickMs) {
          clearInterval(timer);
          setActiveEffect(null);
          return 0;
        }
        return prev - intervalTickMs;
      });
    }, intervalTickMs);

    return () => {
      clearInterval(timer);
    };
  }, [activeEffect, triggerId]);

  const handleTriggerEffect = (effect: EffectType) => {
    setActiveEffect(effect);
    setTriggerId((prev) => prev + 1);
  };

  return (
    <div className="min-h-screen bg-white text-gray-900 font-sans flex flex-col justify-between selection:bg-gray-100 selection:text-gray-900 relative">
      {/* Dynamic full-screen particle overlay layer */}
      <ParticleLayer
        activeEffect={activeEffect}
        density={density}
        sway={sway}
        triggerId={triggerId}
      />

      {/* Main Container */}
      <main className="flex-1 flex items-center justify-center p-4 sm:p-6 md:p-8 z-10">
        <div className="w-full max-w-xl bg-white border border-gray-200/80 p-8 sm:p-12 text-center space-y-10 shadow-sm">
          {/* Elegant Minimal Header */}
          <div className="space-y-4">
            <p className="text-xs uppercase tracking-[0.4em] text-gray-400 font-semibold">
              System Interface
            </p>
            <h1 className="text-4xl sm:text-5xl font-light tracking-tight text-gray-900 font-display">
              Atmospheric Controls
            </h1>
            <div className="h-px w-24 bg-gray-200 mx-auto mt-8"></div>
          </div>

          <p className="text-gray-500 leading-relaxed text-sm max-w-md mx-auto">
            Select a sequence to initiate environmental visual feedback across the primary viewing sector. Active frames cascade elegantly for 5 seconds.
          </p>

          {/* Interactive controls and state updates */}
          <div className="space-y-8 text-left">
            <StatusTracker activeEffect={activeEffect} timeLeft={timeLeft} />

            <ControlPanel
              activeEffect={activeEffect}
              density={density}
              sway={sway}
              onTriggerEffect={handleTriggerEffect}
              onSetDensity={setDensity}
              onSetSway={setSway}
            />
          </div>
        </div>
      </main>

      {/* Minimalistic Footer */}
      <footer className="w-full py-8 text-center text-[10px] text-gray-400 uppercase tracking-widest z-10">
        Terminal Revision v2.4.0 — Formal Environment
      </footer>
    </div>
  );
}
