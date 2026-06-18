/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import { EffectType } from '../types';
import { Snowflake, Percent } from 'lucide-react';

interface StatusTrackerProps {
  activeEffect: EffectType | null;
  timeLeft: number; // millseconds remaining out of 5000
}

export default function StatusTracker({ activeEffect, timeLeft }: StatusTrackerProps) {
  const percentage = Math.max(0, Math.min(100, (timeLeft / 5000) * 100));
  const secondsLeft = (timeLeft / 1000).toFixed(1);

  return (
    <div className="w-full bg-gray-50/50 border border-gray-200 p-5 mb-6 transition-all duration-300">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
        <div className="flex items-center gap-3">
          <div className="relative flex h-2 w-2">
            {activeEffect ? (
              <>
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-gray-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-gray-700"></span>
              </>
            ) : (
              <span className="relative inline-flex rounded-full h-2 w-2 bg-gray-300"></span>
            )}
          </div>
          <div>
            <p className="text-[10px] uppercase font-mono tracking-widest text-gray-400">
              System State
            </p>
            <p className="text-xs font-semibold text-gray-700">
              {activeEffect ? (
                <span>
                  Presenting{' '}
                  <span className="capitalize text-gray-900 font-bold">
                    {activeEffect}
                  </span>
                </span>
              ) : (
                <span className="text-gray-400">Idle • Awaiting Sequence</span>
              )}
            </p>
          </div>
        </div>

        <div className="text-left sm:text-right">
          <p className="text-[10px] uppercase font-mono tracking-widest text-gray-400">
            Active Countdown
          </p>
          <p className="text-base font-mono font-bold text-gray-800">
            {activeEffect ? `${secondsLeft}s / 5.0s` : '0.0s'}
          </p>
        </div>
      </div>

      {/* Modern, elegant fluid animated progress track */}
      <div className="h-1 w-full bg-gray-100 overflow-hidden">
        <div
          className="h-full bg-gray-900 transition-all duration-100 ease-linear"
          style={{ width: `${activeEffect ? percentage : 0}%` }}
        ></div>
      </div>

      <div className="flex items-center justify-between mt-2.5 text-[9px] font-mono uppercase tracking-wider text-gray-400">
        <span>0.0s</span>
        <span>2.5s Midpoint</span>
        <span>5.0s Term</span>
      </div>
    </div>
  );
}
