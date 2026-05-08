import React from 'react';
import { motion } from 'framer-motion';
import type { BuddyStats } from './BuddySpecies';
import type { ThemeConfig } from '../../types/theme';

interface BuddyStatsProps {
  stats: BuddyStats;
  theme: ThemeConfig;
  compact?: boolean;
}

const STAT_CONFIG = {
  debugging: {
    label: 'DEBUGGING',
    icon: '🔍',
    color: '#6c5ce7',
    description: 'Ability to find and fix bugs'
  },
  chaos: {
    label: 'CHAOS',
    icon: '⚡',
    color: '#e17055',
    description: 'Tendency to try unconventional approaches'
  },
  snark: {
    label: 'SNARK',
    icon: '💬',
    color: '#74b9ff',
    description: 'Sarcastic commentary level'
  },
  energy: {
    label: 'ENERGY',
    icon: '🔋',
    color: '#00b894',
    description: 'Current energy level'
  }
};

export const BuddyStatsPanel: React.FC<BuddyStatsProps> = ({
  stats,
  theme,
  compact = false
}) => {
  if (compact) {
    return (
      <div className="flex items-center gap-2">
        {Object.entries(STAT_CONFIG).slice(0, 3).map(([key, config]) => {
          const value = stats[key as keyof BuddyStats];
          return (
            <div key={key} className="flex items-center gap-1">
              <span>{config.icon}</span>
              <span className="text-xs font-mono" style={{ color: config.color }}>
                {value}
              </span>
            </div>
          );
        })}
      </div>
    );
  }

  return (
    <div 
      className="p-3 rounded-lg"
      style={{ 
        backgroundColor: theme.background + '80',
        border: `1px solid ${theme.primary}40`
      }}
    >
      <div className="text-xs font-bold mb-2" style={{ color: theme.foreground + '99' }}>
        BUDDY STATS
      </div>
      <div className="space-y-2">
        {Object.entries(STAT_CONFIG).map(([key, config]) => {
          const value = stats[key as keyof BuddyStats];
          const maxValue = key === 'energy' ? 100 : 10;
          const percentage = (value / maxValue) * 100;
          
          return (
            <div key={key} className="flex items-center gap-2">
              <span className="text-sm">{config.icon}</span>
              <div className="flex-1">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-bold" style={{ color: config.color }}>
                    {config.label}
                  </span>
                  <span className="text-xs font-mono" style={{ color: theme.foreground }}>
                    {value}
                  </span>
                </div>
                <div 
                  className="h-1 rounded-full overflow-hidden"
                  style={{ backgroundColor: theme.background }}
                >
                  <motion.div
                    className="h-full rounded-full"
                    style={{ backgroundColor: config.color }}
                    initial={{ width: 0 }}
                    animate={{ width: `${percentage}%` }}
                    transition={{ duration: 0.5, ease: 'easeOut' }}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default BuddyStatsPanel;