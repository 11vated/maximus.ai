import React from 'react';
import { type TerminalLine } from '../types/terminal';
import { type ThemeConfig } from '../types/theme';

interface OutputDisplayProps {
  lines: TerminalLine[];
  theme: ThemeConfig;
}

const OutputDisplay: React.FC<OutputDisplayProps> = ({ lines, theme }) => {
  const getLineColor = (type: string) => {
    switch (type) {
      case 'input': return theme.primary;
      case 'error': return '#ff0000';
      case 'system': return theme.secondary;
      case 'agent': return theme.accent;
      default: return theme.foreground;
    }
  };

  const getLinePrefix = (type: string) => {
    switch (type) {
      case 'input': return '❯';
      case 'error': return '✗';
      case 'system': return 'ℹ';
      case 'agent': return '🤖';
      default: return ' ';
    }
  };

  return (
    <div className="space-y-1 font-mono text-sm">
      {lines.map((line) => (
        <div key={line.id} className="group flex gap-2">
          <span
            className="shrink-0 opacity-50"
            style={{ color: theme.primary }}
          >
            {getLinePrefix(line.type)}
          </span>
          <span
            className="break-all"
            style={{ color: getLineColor(line.type) }}
          >
            {line.content}
          </span>
          <span className="ml-auto shrink-0 text-xs opacity-30">
            {line.timestamp.toLocaleTimeString()}
          </span>
        </div>
      ))}

      {lines.length === 0 && (
        <div className="py-8 text-center opacity-50" style={{ color: theme.secondary }}>
          <p className="text-lg mb-2">Welcome to Maximus.ai Terminal</p>
          <p className="text-sm">Type /help for available commands</p>
        </div>
      )}
    </div>
  );
};

export default OutputDisplay;
