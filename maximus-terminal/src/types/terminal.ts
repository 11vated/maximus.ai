export interface TerminalLine {
  id: string;
  type: 'input' | 'output' | 'error' | 'system' | 'agent' | 'tool';
  content: string;
  timestamp: Date;
  metadata?: Record<string, unknown>;
  toolName?: string;
}

export interface CommandHistory {
  commands: string[];
  index: number;
}

export interface Theme {
  name: string;
  background: string;
  foreground: string;
  primary: string;
  secondary: string;
  accent: string;
  cursor: string;
  font: string;
  effects: ThemeEffects;
}

export interface ThemeEffects {
  scanlines: boolean;
  glitch: boolean;
  particles: boolean;
  crtCurve: boolean;
}

export type CognitiveState = 'init' | 'thinking' | 'acting' | 'observing' | 'reflecting' | 'idle' | 'error' | 'done';

export interface AgentState {
  state: CognitiveState;
  currentTool?: string | null;
  progress?: number;
  message: string;
  sessionId?: string;
}
