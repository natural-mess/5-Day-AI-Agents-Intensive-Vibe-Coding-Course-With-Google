/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

export type EffectType = 'snowflakes' | 'balloons';

export type DensityLevel = 'low' | 'standard' | 'rich';

export type SwayLevel = 'none' | 'gentle' | 'flowing';

export interface Particle {
  id: string;
  type: 'snowflake' | 'balloon';
  left: number;       // Horizontal position (percentage from 2% to 98%)
  size: number;       // Dimension size in pixels
  duration: number;   // Travel duration (seconds)
  delay: number;      // Staggered starter delay (seconds)
  colorIndex?: number; // Chosen color theme index (for balloons)
  flakeChar?: string; // Snow unicode representation (for snowflakes)
  swayDuration: number; // Duration of side sway oscillation
}

export interface EffectState {
  activeEffect: EffectType | null;
  timeLeft: number;     // Remaining time (ms, up to 5000)
  density: DensityLevel;
  sway: SwayLevel;
}
