import type { ThemeEffects } from './terminal';

export interface ThemeConfig {
  name: string;
  displayName: string;
  background: string;
  foreground: string;
  primary: string;
  secondary: string;
  accent: string;
  cursor: string;
  font: string;
  effects: ThemeEffects;
  gradient?: {
    from: string;
    to: string;
    direction: string;
  };
}

export const cyberpunkTheme: ThemeConfig = {
  name: 'cyberpunk',
  displayName: 'Cyberpunk Neon',
  background: '#0a0e27',
  foreground: '#00ff41',
  primary: '#00ff41',
  secondary: '#ff0080',
  accent: '#0080ff',
  cursor: '#00ff41',
  font: 'JetBrains Mono, monospace',
  effects: {
    scanlines: true,
    glitch: true,
    particles: true,
    crtCurve: false,
  },
  gradient: {
    from: '#0a0e27',
    to: '#1a1a2e',
    direction: '135deg',
  },
};

export const retroCRTTheme: ThemeConfig = {
  name: 'retro-crt',
  displayName: 'Retro CRT',
  background: '#001a00',
  foreground: '#00ff00',
  primary: '#00ff00',
  secondary: '#008000',
  accent: '#ffff00',
  cursor: '#00ff00',
  font: 'VT323, monospace',
  effects: {
    scanlines: true,
    glitch: false,
    particles: false,
    crtCurve: true,
  },
};

export const minimalistTheme: ThemeConfig = {
  name: 'minimalist',
  displayName: 'Minimalist',
  background: '#000000',
  foreground: '#ffffff',
  primary: '#ffffff',
  secondary: '#333333',
  accent: '#666666',
  cursor: '#ffffff',
  font: 'Inter, SF Mono, monospace',
  effects: {
    scanlines: false,
    glitch: false,
    particles: false,
    crtCurve: false,
  },
};

export const dataDrivenTheme: ThemeConfig = {
  name: 'data-driven',
  displayName: 'Data Driven',
  background: '#0d1117',
  foreground: '#c9d1d9',
  primary: '#3fb950',
  secondary: '#d29922',
  accent: '#58a6ff',
  cursor: '#3fb950',
  font: 'JetBrains Mono, monospace',
  effects: {
    scanlines: false,
    glitch: false,
    particles: true,
    crtCurve: false,
  },
};
