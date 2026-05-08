import React from 'react';
import { motion } from 'framer-motion';
import type { ThemeConfig } from '../types/theme';

interface AgentState {
  state: string;
  currentTool: string | null;
  progress: number;
  message: string;
}

interface AgentVisualizerProps {
  agentState: AgentState;
  theme: ThemeConfig;
  mode?: 'compact' | 'galaxy' | 'minimal';
}

interface StatePlanet {
  id: string;
  name: string;
  color: string;
  orbitRadius: number;
  size: number;
  description: string;
}

const COGNITIVE_STATES: StatePlanet[] = [
  { id: 'init', name: 'INIT', color: '#ffffff', orbitRadius: 30, size: 12, description: 'Initialize task' },
  { id: 'plan', name: 'PLAN', color: '#f0e68c', orbitRadius: 50, size: 14, description: 'Plan approach' },
  { id: 'act', name: 'ACT', color: '#ff6b6b', orbitRadius: 70, size: 16, description: 'Execute actions' },
  { id: 'observe', name: 'OBSERVE', color: '#4dabf7', orbitRadius: 90, size: 14, description: 'Observe results' },
  { id: 'reflect', name: 'REFLECT', color: '#cc5de8', orbitRadius: 110, size: 15, description: 'Reflect on outcomes' },
  { id: 'adapt', name: 'ADAPT', color: '#51cf66', orbitRadius: 130, size: 13, description: 'Adapt strategy' },
  { id: 'commit', name: 'COMMIT', color: '#ffa94d', orbitRadius: 150, size: 14, description: 'Commit results' },
  { id: 'pause', name: 'PAUSE', color: '#22b8cf', orbitRadius: 170, size: 12, description: 'Pause & wait' },
];

const getCurrentStateIndex = (state: string): number => {
  const index = COGNITIVE_STATES.findIndex(s => s.id === state.toLowerCase());
  return index >= 0 ? index : 0;
};

export const AgentVisualizer: React.FC<AgentVisualizerProps> = ({
  agentState,
  theme,
  mode = 'galaxy'
}) => {
  const currentIndex = getCurrentStateIndex(agentState.state);
  const progress = agentState.progress / 100;

  // Galaxy mode - rotating solar system
  if (mode === 'galaxy') {
    return (
      <GalaxyVisualizer 
        states={COGNITIVE_STATES}
        currentIndex={currentIndex}
        theme={theme}
        progress={progress}
      />
    );
  }

  // Compact mode - inline text
  if (mode === 'compact') {
    return (
      <div className="flex items-center gap-2 text-xs">
        <span 
          className="px-2 py-1 rounded font-mono"
          style={{ 
            backgroundColor: COGNITIVE_STATES[currentIndex].color + '30',
            color: COGNITIVE_STATES[currentIndex].color
          }}
        >
          {agentState.state.toUpperCase()}
        </span>
        {agentState.currentTool && (
          <span style={{ color: theme.foreground + '99' }}>
            → {agentState.currentTool}
          </span>
        )}
      </div>
    );
  }

  // Minimal mode - just progress bar
  return (
    <div className="flex items-center gap-2">
      <div 
        className="h-1 rounded-full"
        style={{ 
          width: '60px',
          backgroundColor: theme.background
        }}
      >
        <motion.div
          className="h-full rounded-full"
          style={{ backgroundColor: COGNITIVE_STATES[currentIndex].color }}
          animate={{ width: `${progress * 100}%` }}
        />
      </div>
    </div>
  );
};

// Galaxy Visualization - rotating planets in orbit
const GalaxyVisualizer: React.FC<{
  states: StatePlanet[];
  currentIndex: number;
  theme: ThemeConfig;
  progress: number;
}> = ({ states, currentIndex, theme, progress }) => {
  const [rotation, setRotation] = React.useState(0);

  React.useEffect(() => {
    const interval = setInterval(() => {
      setRotation(r => r + 0.5);
    }, 50);
    return () => clearInterval(interval);
  }, []);

  return (
    <div 
      className="relative flex items-center justify-center py-2 overflow-hidden"
      style={{ height: '80px' }}
    >
      {/* Center star */}
      <motion.div
        className="absolute rounded-full"
        style={{
          width: 20,
          height: 20,
          background: `radial-gradient(circle, ${theme.primary}, ${theme.primary}40)`,
          boxShadow: `0 0 20px ${theme.primary}, 0 0 40px ${theme.primary}60`
        }}
        animate={{
          scale: [1, 1.2, 1],
          boxShadow: [
            `0 0 20px ${theme.primary}`,
            `0 0 40px ${theme.primary}`,
            `0 0 20px ${theme.primary}`
          ]
        }}
        transition={{ duration: 2, repeat: Infinity }}
      />

      {/* Orbital paths */}
      {states.map((state, idx) => (
        <div
          key={state.id}
          className="absolute rounded-full border"
          style={{
            width: state.orbitRadius * 2,
            height: state.orbitRadius * 2,
            borderColor: theme.primary + '20',
            borderStyle: 'dashed',
            transform: `rotate(${rotation + idx * 15}deg)`
          }}
        />
      ))}

      {/* State planets */}
      {states.map((state, idx) => {
        const angle = (idx * 360 / states.length) - rotation;
        const isActive = idx === currentIndex;
        
        // 3D positioning - planets further back are smaller and dimmer
        const radian = (angle * Math.PI) / 180;
        const x = Math.sin(radian) * state.orbitRadius;
        const z = Math.cos(radian); // z-index for depth
        const scale = 0.5 + (z + 1) * 0.25;
        const opacity = 0.4 + (z + 1) * 0.3;
        
        return (
          <motion.div
            key={state.id}
            className="absolute flex items-center justify-center rounded-full cursor-pointer"
            style={{
              width: state.size * scale,
              height: state.size * scale,
              backgroundColor: state.color,
              left: `calc(50% + ${x}px - ${state.size * scale / 2}px)`,
              top: `calc(50% - ${state.size * scale / 2}px)`,
              opacity: isActive ? 1 : opacity,
              boxShadow: isActive 
                ? `0 0 15px ${state.color}, 0 0 30px ${state.color}80`
                : `0 0 5px ${state.color}40`,
              zIndex: Math.floor(z * 100),
              transform: `scale(${scale})`
            }}
            whileHover={{ scale: scale * 1.3 }}
            title={state.description}
          >
            {/* Active ring */}
            {isActive && (
              <motion.div
                className="absolute rounded-full border-2"
                style={{
                  width: state.size * scale * 1.5,
                  height: state.size * scale * 1.5,
                  borderColor: state.color,
                  opacity: 0.5
                }}
                animate={{ scale: [1, 1.3, 1], opacity: [0.5, 0.2, 0.5] }}
                transition={{ duration: 1.5, repeat: Infinity }}
              />
            )}
            
            {/* Planet label for active state */}
            {isActive && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="absolute top-full mt-1 text-[8px] font-mono whitespace-nowrap"
                style={{ color: state.color }}
              >
                {state.name}
              </motion.div>
            )}
          </motion.div>
        );
      })}

      {/* Progress indicator */}
      <div 
        className="absolute bottom-0 flex items-center gap-1 text-[10px]"
        style={{ color: theme.foreground + '99' }}
      >
        <span>Task Progress:</span>
        <div 
          className="h-1 rounded-full"
          style={{ width: '80px', backgroundColor: theme.background }}
        >
          <motion.div
            className="h-full rounded-full"
            style={{ backgroundColor: theme.primary }}
            animate={{ width: `${progress * 100}%` }}
          />
        </div>
        <span>{Math.round(progress * 100)}%</span>
      </div>
    </div>
  );
};

export default AgentVisualizer;