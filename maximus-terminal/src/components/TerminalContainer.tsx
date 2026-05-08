import React, { useEffect, useRef } from 'react';
import { useTerminalStore } from '../store/useTerminalStore';
import { useBuddyStore } from '../store/useBuddyStore';
import CommandLine from './CommandLine';
import OutputDisplay from './OutputDisplay';
import ThemeSwitcher from './ThemeSwitcher';
import { AgentVisualizer } from './AgentVisualizer';
import { TabBar } from './TabBar';
import { ParticleBackground } from './ParticleBackground';
import { BuddyAvatar } from './BuddySystem/BuddyAvatar';
import { BuddyStatsPanel } from './BuddySystem/BuddyStats';
import { cyberpunkTheme, retroCRTTheme, minimalistTheme, dataDrivenTheme } from '../types/theme';

interface TerminalContainerProps {
  className?: string;
}

const TerminalContainer: React.FC<TerminalContainerProps> = ({ className = '' }) => {
  const {
    lines,
    currentInput,
    activeTheme,
    agentState,
    isFullscreen,
    showSettings,
    setInput,
    executeCommand,
    setTheme,
    toggleFullscreen,
    toggleSettings,
    clearTerminal,
  } = useTerminalStore();

  const { buddy, interact } = useBuddyStore();

  const terminalRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [lines]);

  const handleCommand = (cmd: string) => {
    executeCommand(cmd);
  };

  const themes = [cyberpunkTheme, retroCRTTheme, minimalistTheme, dataDrivenTheme];

  return (
    <div
      className={`relative h-screen w-full overflow-hidden ${className}`}
      style={{
        background: activeTheme.gradient
          ? `linear-gradient(${activeTheme.gradient.direction}, ${activeTheme.gradient.from}, ${activeTheme.gradient.to})`
          : activeTheme.background,
        color: activeTheme.foreground,
        fontFamily: activeTheme.font,
      }}
    >
      {/* Particle background */}
      <ParticleBackground theme={activeTheme} enabled={activeTheme.effects?.particles} />

      {/* Scanline overlay */}
      {activeTheme.effects?.scanlines && (
        <div className="pointer-events-none absolute inset-0 z-10 opacity-10">
          <div className="h-full w-full" style={{
            background: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.3) 2px, rgba(0,0,0,0.3) 4px)',
          }} />
        </div>
      )}

      {/* Glitch effect overlay */}
      {activeTheme.effects?.glitch && (
        <div className="pointer-events-none absolute inset-0 z-10 glitch-overlay" />
      )}

      {/* Main terminal window */}
      <div className={`relative z-20 flex h-full flex-col ${isFullscreen ? '' : 'm-4 rounded-lg border'}`}
        style={{
          borderColor: activeTheme.primary + '40',
          boxShadow: `0 0 20px ${activeTheme.primary}20`,
        }}
      >
        {/* Title bar with tabs */}
        <div
          className="flex items-center justify-between border-b px-4 py-2"
          style={{ borderColor: activeTheme.primary + '40' }}
        >
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="h-3 w-3 rounded-full bg-red-500" />
              <div className="h-3 w-3 rounded-full bg-yellow-500" />
              <div className="h-3 w-3 rounded-full bg-green-500" />
              <span className="ml-2 text-sm opacity-70">Maximus.ai Terminal</span>
            </div>
            
            {/* Buddy System */}
            <div className="flex items-center gap-2 ml-4">
              <BuddyAvatar 
                buddy={buddy} 
                theme={activeTheme} 
                onInteraction={(type) => interact(type as any)}
                size="small"
              />
              <div className="hidden md:block">
                <BuddyStatsPanel 
                  stats={buddy.stats} 
                  theme={activeTheme} 
                  compact 
                />
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={toggleSettings}
              className="rounded px-2 py-1 text-xs hover:opacity-80"
              style={{ color: activeTheme.primary }}
            >
              ⚙ Themes
            </button>
            <button
              onClick={toggleFullscreen}
              className="rounded px-2 py-1 text-xs hover:opacity-80"
              style={{ color: activeTheme.primary }}
            >
              {isFullscreen ? '🗗 Exit' : '⛶ Full'}
            </button>
            <button
              onClick={clearTerminal}
              className="rounded px-2 py-1 text-xs hover:opacity-80"
              style={{ color: activeTheme.primary }}
            >
              🗑 Clear
            </button>
          </div>
        </div>

        {/* Tab bar */}
        <TabBar />

        {/* Agent state indicator */}
        <AgentVisualizer agentState={agentState} theme={activeTheme} />

        {/* Output area */}
        <div
          ref={terminalRef}
          className="flex-1 overflow-y-auto p-4"
        >
          <OutputDisplay lines={lines} theme={activeTheme} />
        </div>

        {/* Command input */}
        <div
          className="border-t p-4"
          style={{ borderColor: activeTheme.primary + '40' }}
        >
          <CommandLine
            value={currentInput}
            onChange={setInput}
            onExecute={handleCommand}
            theme={activeTheme}
          />
        </div>
      </div>

      {/* Settings panel */}
      {showSettings && (
        <div className="absolute right-4 top-16 z-30 w-80 rounded-lg border p-4 backdrop-blur"
          style={{
            background: activeTheme.background + 'f0',
            borderColor: activeTheme.primary + '40',
          }}
        >
          <ThemeSwitcher
            themes={themes}
            activeTheme={activeTheme}
            onSelect={setTheme}
          />
        </div>
      )}

      {/* CRT curvature effect */}
      {activeTheme.effects?.crtCurve && (
        <div
          className="pointer-events-none absolute inset-0 z-40"
          style={{
            background: 'radial-gradient(ellipse at center, transparent 50%, rgba(0,0,0,0.3) 100%)',
            borderRadius: '20%',
          }}
        />
      )}
    </div>
  );
};

export default TerminalContainer;
