/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import { EffectType, DensityLevel, SwayLevel } from '../types';
import { Snowflake, Sliders, Play, Layers, Sparkles } from 'lucide-react';

interface ControlPanelProps {
  activeEffect: EffectType | null;
  density: DensityLevel;
  sway: SwayLevel;
  onTriggerEffect: (type: EffectType) => void;
  onSetDensity: (density: DensityLevel) => void;
  onSetSway: (sway: SwayLevel) => void;
}

export default function ControlPanel({
  activeEffect,
  density,
  sway,
  onTriggerEffect,
  onSetDensity,
  onSetSway,
}: ControlPanelProps) {
  return (
    <div className="space-y-6">
      {/* Prime Action Buttons Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Snowflakes Selector Button */}
        <button
          id="btn-snowflakes"
          onClick={() => onTriggerEffect('snowflakes')}
          className={`relative overflow-hidden w-full py-5 border transition-all duration-300 flex flex-col items-center justify-center gap-2 cursor-pointer text-xs font-semibold uppercase tracking-widest active:scale-95 shadow-xs ${
            activeEffect === 'snowflakes'
              ? 'border-gray-950 bg-gray-50 text-gray-950'
              : 'border-gray-200 bg-white hover:bg-gray-50 text-gray-500'
          }`}
        >
          <div className="p-1 rounded-full">
            <Snowflake className={`w-4 h-4 ${activeEffect === 'snowflakes' ? 'text-gray-900' : 'text-gray-400'}`} />
          </div>
          <span>Snowflakes</span>
        </button>

        {/* Balloons Selector Button */}
        <button
          id="btn-balloons"
          onClick={() => onTriggerEffect('balloons')}
          className={`relative overflow-hidden w-full py-5 border transition-all duration-300 flex flex-col items-center justify-center gap-2 cursor-pointer text-xs font-semibold uppercase tracking-widest active:scale-95 shadow-xs ${
            activeEffect === 'balloons'
              ? 'border-gray-950 bg-gray-50 text-gray-950'
              : 'border-gray-200 bg-white hover:bg-gray-50 text-gray-500'
          }`}
        >
          <div className="p-1 rounded-full">
            {/* Custom Balloon Inline Icon */}
            <svg
              viewBox="0 0 24 24"
              className={`w-4 h-4 fill-none stroke-2 ${
                activeEffect === 'balloons' ? 'stroke-gray-900' : 'stroke-gray-400'
              }`}
            >
              <ellipse cx="12" cy="10" rx="5" ry="6" />
              <polygon points="12,16 13,17 11,17" />
              <path d="M12,17 L12,21" />
            </svg>
          </div>
          <span>Balloons</span>
        </button>
      </div>

      {/* Advanced Fine Tuning Controls */}
      <div className="border border-gray-150 p-5 bg-gray-50/40 space-y-5">
        <div className="flex items-center gap-2 mb-1">
          <Sliders className="w-3.5 h-3.5 text-gray-400" />
          <h3 className="text-[10px] uppercase font-mono tracking-widest font-semibold text-gray-400">
            System Tuning & Sway
          </h3>
        </div>

        {/* Density Selectors */}
        <div className="space-y-2">
          <label className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider flex items-center justify-between">
            <span>Payload Density</span>
            <span className="text-[9px] font-mono tracking-normal bg-gray-100 text-gray-600 px-1.5 py-0.5">
              {density === 'low' ? '20 particles' : density === 'standard' ? '40 particles' : '75 particles'}
            </span>
          </label>
          <div className="grid grid-cols-3 gap-2">
            {(['low', 'standard', 'rich'] as DensityLevel[]).map((level) => (
              <button
                key={level}
                onClick={() => onSetDensity(level)}
                className={`py-2 text-[10px] font-semibold tracking-wider uppercase border transition-all duration-200 cursor-pointer ${
                  density === level
                    ? 'bg-gray-950 border-gray-950 text-white shadow-xs'
                    : 'bg-white border-gray-200 text-gray-500 hover:bg-gray-50'
                }`}
              >
                {level}
              </button>
            ))}
          </div>
        </div>

        {/* Sway Intensity Selectors */}
        <div className="space-y-2">
          <label className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider flex items-center justify-between">
            <span>Wind Sway</span>
            <span className="text-[9px] font-mono tracking-normal bg-gray-100 text-gray-600 px-1.5 py-0.5">
              {sway === 'none' ? 'None' : `${sway}`}
            </span>
          </label>
          <div className="grid grid-cols-3 gap-2">
            {(['none', 'gentle', 'flowing'] as SwayLevel[]).map((level) => (
              <button
                key={level}
                onClick={() => onSetSway(level)}
                className={`py-2 text-[10px] font-semibold tracking-wider uppercase border transition-all duration-200 cursor-pointer ${
                  sway === level
                    ? 'bg-gray-950 border-gray-950 text-white shadow-xs'
                    : 'bg-white border-gray-200 text-gray-500 hover:bg-gray-50'
                }`}
              >
                {level}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
