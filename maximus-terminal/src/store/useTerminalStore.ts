import { create } from 'zustand';
import type { TerminalLine, CommandHistory, AgentState } from '../types/terminal';
import type { ThemeConfig } from '../types/theme';
import { cyberpunkTheme } from '../types/theme';

interface Tab {
  id: string;
  title: string;
  sessionId: string;
  lines: TerminalLine[];
  commandHistory: CommandHistory;
  historyIndex: number;
  currentInput: string;
  agentState: AgentState;
  unreadCount: number;
}

interface TerminalStore {
  // Tab management
  tabs: Tab[];
  activeTabId: string | null;
  addTab: (title?: string) => void;
  closeTab: (tabId: string) => void;
  switchTab: (tabId: string) => void;
  updateTabTitle: (tabId: string, title: string) => void;
  updateActiveTab: (updates: Partial<Tab>) => void;

  // Current tab convenience getters
  lines: TerminalLine[];
  currentInput: string;
  commandHistory: CommandHistory;
  historyIndex: number;
  agentState: AgentState;
  isAgentRunning: boolean;

  // UI state (global)
  activeTheme: ThemeConfig;
  isFullscreen: boolean;
  showSettings: boolean;

  // Actions
  addLine: (line: TerminalLine) => void;
  setInput: (input: string) => void;
  executeCommand: (command: string) => void;
  navigateHistory: (direction: 'up' | 'down') => void;
  setAgentState: (state: Partial<AgentState>) => void;
  setTheme: (theme: ThemeConfig) => void;
  toggleFullscreen: () => void;
  toggleSettings: () => void;
  clearTerminal: () => void;
}

const createNewTab = (title: string, sessionId?: string): Tab => ({
  id: `tab_${Date.now()}`,
  title,
  sessionId: sessionId || `session_${Date.now()}`,
  lines: [],
  commandHistory: { commands: [], index: -1 },
  historyIndex: -1,
  currentInput: '',
  agentState: {
    state: 'idle',
    currentTool: null,
    progress: 0,
    message: '',
  },
  unreadCount: 0,
});

export const useTerminalStore = create<TerminalStore>((set, get) => ({
  // Initial state with one default tab
  tabs: [createNewTab('Session 1')],
  activeTabId: null,

  addTab: (title) => {
    const newTab = createNewTab(title || `Session ${get().tabs.length + 1}`);
    set((state) => ({
      tabs: [...state.tabs, newTab],
      activeTabId: newTab.id,
    }));
  },

  closeTab: (tabId) => {
    set((state) => {
      const newTabs = state.tabs.filter((t) => t.id !== tabId);
      if (newTabs.length === 0) {
        // Always keep at least one tab
        const defaultTab = createNewTab('Session 1');
        return { tabs: [defaultTab], activeTabId: defaultTab.id };
      }
      const newActiveId = state.activeTabId === tabId ? newTabs[newTabs.length - 1].id : state.activeTabId;
      return { tabs: newTabs, activeTabId: newActiveId };
    });
  },

  switchTab: (tabId) => {
    set({ activeTabId: tabId });
    // Clear unread count for switched tab
    set((state) => ({
      tabs: state.tabs.map((t) => (t.id === tabId ? { ...t, unreadCount: 0 } : t)),
    }));
  },

  updateTabTitle: (tabId, title) => {
    set((state) => ({
      tabs: state.tabs.map((t) => (t.id === tabId ? { ...t, title } : t)),
    }));
  },

  updateActiveTab: (updates) => {
    const { activeTabId } = get();
    if (!activeTabId) return;
    set((state) => ({
      tabs: state.tabs.map((t) => (t.id === activeTabId ? { ...t, ...updates } : t)),
    }));
  },

  // Convenience getters for active tab
  get lines() {
    const { tabs, activeTabId } = get();
    const activeTab = tabs.find((t) => t.id === activeTabId) || tabs[0];
    return activeTab?.lines || [];
  },

  get currentInput() {
    const { tabs, activeTabId } = get();
    const activeTab = tabs.find((t) => t.id === activeTabId) || tabs[0];
    return activeTab?.currentInput || '';
  },

  get commandHistory() {
    const { tabs, activeTabId } = get();
    const activeTab = tabs.find((t) => t.id === activeTabId) || tabs[0];
    return activeTab?.commandHistory || { commands: [], index: -1 };
  },

  get historyIndex() {
    const { tabs, activeTabId } = get();
    const activeTab = tabs.find((t) => t.id === activeTabId) || tabs[0];
    return activeTab?.historyIndex ?? -1;
  },

  get agentState() {
    const { tabs, activeTabId } = get();
    const activeTab = tabs.find((t) => t.id === activeTabId) || tabs[0];
    return activeTab?.agentState || { state: 'idle', currentTool: null, progress: 0, message: '' };
  },

  get isAgentRunning() {
    const state = get().agentState.state;
    return state !== 'idle' && state !== 'error';
  },

  // Actions that update active tab
  addLine: (line) => {
    const { activeTabId } = get();
    if (!activeTabId) return;
    set((state) => ({
      tabs: state.tabs.map((t) => {
        if (t.id !== activeTabId) return t;
        return { ...t, lines: [...t.lines, line] };
      }),
    }));
  },

  setInput: (input) => {
    const { activeTabId } = get();
    if (!activeTabId) return;
    set((state) => ({
      tabs: state.tabs.map((t) => (t.id === activeTabId ? { ...t, currentInput: input } : t)),
    }));
  },

  executeCommand: (command) => {
    const { activeTabId } = get();
    if (!activeTabId) return;
    set((state) => ({
      tabs: state.tabs.map((t) => {
        if (t.id !== activeTabId) return t;
        return {
          ...t,
          lines: [
            ...t.lines,
            {
              id: Date.now().toString(),
              type: 'input' as const,
              content: command,
              timestamp: new Date(),
            },
          ],
          commandHistory: {
            commands: [...t.commandHistory.commands, command],
            index: t.commandHistory.commands.length,
          },
          currentInput: '',
          historyIndex: -1,
        };
      }),
    }));
  },

  navigateHistory: (direction) => {
    const { activeTabId, tabs } = get();
    if (!activeTabId) return;
    const tab = tabs.find((t) => t.id === activeTabId);
    if (!tab) return;

    const { commandHistory, historyIndex } = tab;
    const { commands } = commandHistory;

    if (commands.length === 0) return;

    let newIndex = historyIndex;
    if (direction === 'up' && historyIndex < commands.length - 1) {
      newIndex = historyIndex + 1;
    } else if (direction === 'down' && historyIndex > -1) {
      newIndex = historyIndex - 1;
    }

    const newInput = newIndex >= 0 ? commands[commands.length - 1 - newIndex] : '';
    set((state) => ({
      tabs: state.tabs.map((t) => (t.id === activeTabId ? { ...t, currentInput: newInput, historyIndex: newIndex } : t)),
    }));
  },

  setAgentState: (newState) => {
    const { activeTabId } = get();
    if (!activeTabId) return;
    set((state) => ({
      tabs: state.tabs.map((t) => {
        if (t.id !== activeTabId) return t;
        return { ...t, agentState: { ...t.agentState, ...newState } };
      }),
    }));
  },

  // Global UI state
  activeTheme: cyberpunkTheme,
  isFullscreen: false,
  showSettings: false,

  setTheme: (theme) => set({ activeTheme: theme }),
  toggleFullscreen: () => set((state) => ({ isFullscreen: !state.isFullscreen })),
  toggleSettings: () => set((state) => ({ showSettings: !state.showSettings })),

  clearTerminal: () => {
    const { activeTabId } = get();
    if (!activeTabId) return;
    set((state) => ({
      tabs: state.tabs.map((t) => (t.id === activeTabId ? { ...t, lines: [], currentInput: '', historyIndex: -1 } : t)),
    }));
  },
}));
