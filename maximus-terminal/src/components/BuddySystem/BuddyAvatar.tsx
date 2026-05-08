import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MOOD_COLORS, MOOD_EMOJIS, type BuddyState } from './BuddySpecies';
import type { ThemeConfig } from '../../types/theme';

interface BuddyAvatarProps {
  buddy: BuddyState;
  theme: ThemeConfig;
  onInteraction?: (type: string) => void;
  size?: 'small' | 'medium' | 'large';
}

const SIZES = {
  small: 48,
  medium: 80,
  large: 120
};

const MOOD_ANIMATIONS = {
  idle: {
    y: [0, -5, 0],
    transition: { repeat: Infinity, duration: 3 }
  },
  thinking: {
    scale: [1, 1.05, 1],
    rotate: [0, 5, -5, 0],
    transition: { repeat: Infinity, duration: 2 }
  },
  working: {
    scale: [1, 1.1, 1],
    transition: { repeat: Infinity, duration: 0.5 }
  },
  happy: {
    y: [0, -10, 0],
    rotate: [0, 10, -10, 0],
    transition: { repeat: Infinity, duration: 1 }
  },
  sad: {
    y: 5,
    scale: 0.95,
    transition: { repeat: Infinity, duration: 2 }
  },
  excited: {
    scale: [1, 1.2, 1],
    rotate: [0, 15, -15, 0],
    transition: { repeat: Infinity, duration: 0.3 }
  },
  confused: {
    rotate: [0, 10, -10, 5, -5, 0],
    transition: { repeat: Infinity, duration: 2 }
  },
  error: {
    x: [-5, 5, -5, 5, 0],
    transition: { repeat: Infinity, duration: 0.2 }
  }
};

export const BuddyAvatar: React.FC<BuddyAvatarProps> = ({
  buddy,
  theme,
  onInteraction,
  size = 'medium'
}) => {
  const [showTooltip, setShowTooltip] = useState(false);
  const [floatingEmojis, setFloatingEmojis] = useState<{id: number, emoji: string}[]>([]);
  
  const dimensions = SIZES[size];
  const moodColor = MOOD_COLORS[buddy.mood];
  const moodEmoji = MOOD_EMOJIS[buddy.mood];
  
  const handleClick = () => {
    onInteraction?.('click');
    // Add floating emoji
    const emoji = ['✨', '❤️', '🎵', '⭐', '💫'][Math.floor(Math.random() * 5)];
    setFloatingEmojis(prev => [...prev, { id: Date.now(), emoji }]);
    setTimeout(() => {
      setFloatingEmojis(prev => prev.filter(e => e.id !== Date.now()));
    }, 1000);
  };
  
  const handleHover = () => {
    setShowTooltip(true);
    onInteraction?.('hover');
  };

  return (
    <div className="relative inline-flex items-center justify-center">
      <motion.div
        className="relative cursor-pointer"
        style={{ width: dimensions, height: dimensions }}
        onClick={handleClick}
        onMouseEnter={handleHover}
        onMouseLeave={() => setShowTooltip(false)}
        animate={MOOD_ANIMATIONS[buddy.mood]}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.95 }}
      >
        {/* Main avatar circle */}
        <div
          className="absolute inset-0 rounded-full flex items-center justify-center"
          style={{
            background: `linear-gradient(135deg, ${buddy.species.primaryColor}40, ${buddy.species.secondaryColor}40)`,
            border: `3px solid ${moodColor}`,
            boxShadow: `0 0 20px ${moodColor}60, inset 0 0 20px ${buddy.species.primaryColor}30`
          }}
        >
          <span style={{ fontSize: dimensions * 0.5 }}>{buddy.species.emoji}</span>
        </div>
        
        {/* Mood indicator ring */}
        <motion.div
          className="absolute inset-[-4px] rounded-full border-2 border-dashed"
          style={{ borderColor: moodColor }}
          animate={{ rotate: 360 }}
          transition={{ repeat: Infinity, duration: 10, ease: 'linear' }}
        />
        
        {/* Energy indicator */}
        <div
          className="absolute bottom-0 right-0 w-3 h-3 rounded-full"
          style={{
            backgroundColor: buddy.stats.energy > 50 ? '#00b894' : '#e17055',
            boxShadow: `0 0 8px ${buddy.stats.energy > 50 ? '#00b894' : '#e17055'}`
          }}
        />
        
        {/* Floating emojis on interaction */}
        <AnimatePresence>
          {floatingEmojis.map(f => (
            <motion.span
              key={f.id}
              initial={{ opacity: 1, y: 0, scale: 0.5 }}
              animate={{ opacity: 0, y: -40, scale: 1.5 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 flex items-center justify-center pointer-events-none"
              style={{ fontSize: dimensions * 0.4 }}
            >
              {f.emoji}
            </motion.span>
          ))}
        </AnimatePresence>
      </motion.div>
      
      {/* Tooltip */}
      <AnimatePresence>
        {showTooltip && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            className="absolute top-full mt-2 p-3 rounded-lg z-50 min-w-[200px]"
            style={{
              backgroundColor: theme.background + 'f0',
              border: `1px solid ${theme.primary}`,
              backdropFilter: 'blur(8px)'
            }}
          >
            <div className="flex items-center gap-2 mb-2">
              <span style={{ fontSize: 24 }}>{buddy.species.emoji}</span>
              <div>
                <div className="font-bold" style={{ color: theme.foreground }}>
                  {buddy.species.name}
                </div>
                <div className="text-xs" style={{ color: theme.foreground + '99' }}>
                  Level {buddy.level} • {buddy.stats.energy}% energy
                </div>
              </div>
            </div>
            <div className="text-xs" style={{ color: theme.foreground }}>
              {buddy.species.description}
            </div>
            <div className="mt-2 flex items-center gap-2">
              <span style={{ color: moodColor }}>{moodEmoji}</span>
              <span className="text-xs capitalize" style={{ color: theme.foreground }}>
                {buddy.mood}
              </span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default BuddyAvatar;