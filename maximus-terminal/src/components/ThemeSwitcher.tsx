import React from 'react';
import { motion } from 'framer-motion';
import { type ThemeConfig } from '../types/theme';

interface ThemeSwitcherProps {
  themes: ThemeConfig[];
  activeTheme: ThemeConfig;
  onSelect: (theme: ThemeConfig) => void;
}

const ThemeSwitcher: React.FC<ThemeSwitcherProps> = ({ themes, activeTheme, onSelect }) => {
  return (
    <div className="space-y-2">
      <h3 className="text-sm font-bold mb-3">Select Theme</h3>

      <div className="grid grid-cols-2 gap-2">
        {themes.map((theme) => {
          const isActive = theme.name === activeTheme.name;

          return (
            <motion.div
              key={theme.name}
              className="relative rounded-lg p-3 cursor-pointer overflow-hidden"
              style={{
                background: theme.background,
                border: `2px solid ${isActive ? theme.primary : 'transparent'}`,
                color: theme.foreground,
              }}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => onSelect(theme)}
            >
              {/* Preview gradient */}
              <div
                className="absolute inset-0 opacity-20"
                style={{
                  background: theme.gradient
                    ? `linear-gradient(${theme.gradient.direction}, ${theme.gradient.from}, ${theme.gradient.to})`
                    : theme.background,
                }}
              />

              <div className="relative z-10">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-bold text-sm">{theme.displayName}</span>
                  {isActive && (
                    <motion.span
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      className="text-xs"
                      style={{ color: theme.primary }}
                    >
                      ✓ Active
                    </motion.span>
                  )}
                </div>

                {/* Color preview */}
                <div className="flex gap-2 mb-2">
                  <div
                    className="w-6 h-6 rounded"
                    style={{ background: theme.primary }}
                  />
                  <div
                    className="w-6 h-6 rounded"
                    style={{ background: theme.secondary }}
                  />
                  <div
                    className="w-6 h-6 rounded"
                    style={{ background: theme.accent }}
                  />
                </div>

                {/* Effects preview */}
                <div className="flex gap-1 flex-wrap">
                  {theme.effects.scanlines && (
                    <span className="text-xs px-1 rounded" style={{ background: theme.primary + '20' }}>
                      Scanlines
                    </span>
                  )}
                  {theme.effects.glitch && (
                    <span className="text-xs px-1 rounded" style={{ background: theme.primary + '20' }}>
                      Glitch
                    </span>
                  )}
                  {theme.effects.particles && (
                    <span className="text-xs px-1 rounded" style={{ background: theme.primary + '20' }}>
                      Particles
                    </span>
                  )}
                  {theme.effects.crtCurve && (
                    <span className="text-xs px-1 rounded" style={{ background: theme.primary + '20' }}>
                      CRT
                    </span>
                  )}
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
};

export default ThemeSwitcher;
