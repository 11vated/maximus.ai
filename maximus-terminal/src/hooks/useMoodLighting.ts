import { useState, useEffect, useCallback } from 'react';
import { useTerminalStore } from '../store/useTerminalStore';

// Mood colors based on cognitive states
const MOOD_COLORS: Record<string, string> = {
  init: '#ffffff',     // White - fresh start
  plan: '#f0e68c',    // Yellow - thinking
  act: '#ff6b6b',     // Red - active execution
  observe: '#4dabf7', // Blue - observation
  reflect: '#cc5de8', // Purple - reflection
  adapt: '#51cf66',   // Green - adaptation
  commit: '#ffa94d', // Orange - commitment
  pause: '#22b8cf',  // Cyan - waiting
  idle: '#636e72',   // Gray - idle
  error: '#d63031',  // Red - error
};

interface MoodLightingOptions {
  enabled?: boolean;
  transitionDuration?: number;
  intensity?: number; // 0-1
}

export function useMoodLighting(options: MoodLightingOptions = {}) {
  const { enabled = true, transitionDuration = 500, intensity = 0.3 } = options;
  const { agentState } = useTerminalStore();
  const [currentMoodColor, setCurrentMoodColor] = useState<string>('#636e72');

  const updateMoodColor = useCallback((state: string) => {
    if (!enabled) return;
    
    const newColor = MOOD_COLORS[state.toLowerCase()] || MOOD_COLORS.idle;
    setCurrentMoodColor(newColor);
  }, [enabled]);

  useEffect(() => {
    updateMoodColor(agentState.state);
  }, [agentState.state, updateMoodColor]);

  // Return color with intensity applied
  const getMoodAdjustedColor = useCallback((baseColor: string): string => {
    // If intensity is 0, return base color unchanged
    if (intensity === 0) return baseColor;
    
    // Parse the mood color
    const moodRgb = hexToRgb(currentMoodColor);
    const baseRgb = hexToRgb(baseColor);
    
    if (!moodRgb || !baseRgb) return baseColor;
    
    // Blend the colors
    const blended = {
      r: Math.round(baseRgb.r * (1 - intensity) + moodRgb.r * intensity),
      g: Math.round(baseRgb.g * (1 - intensity) + moodRgb.g * intensity),
      b: Math.round(baseRgb.b * (1 - intensity) + moodRgb.b * intensity),
    };
    
    return rgbToHex(blended.r, blended.g, blended.b);
  }, [currentMoodColor, intensity]);

  // Get CSS transition style for smooth color changes
  const getTransitionStyle = () => ({
    transition: `color ${transitionDuration}ms ease, background-color ${transitionDuration}ms ease, border-color ${transitionDuration}ms ease`,
  });

  return {
    currentMoodColor,
    getMoodAdjustedColor,
    getTransitionStyle,
    state: agentState.state
  };
}

// Utility functions
function hexToRgb(hex: string): { r: number; g: number; b: number } | null {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result ? {
    r: parseInt(result[1], 16),
    g: parseInt(result[2], 16),
    b: parseInt(result[3], 16)
  } : null;
}

function rgbToHex(r: number, g: number, b: number): string {
  return '#' + [r, g, b].map(x => {
    const hex = x.toString(16);
    return hex.length === 1 ? '0' + hex : hex;
  }).join('');
}

export default useMoodLighting;