import { useState, useCallback, useEffect } from 'react';

export type VimMode = 'normal' | 'insert' | 'visual' | 'command';

interface VimState {
  mode: VimMode;
  register: string;
  count: number;
  lastOperator: string | null;
  commandBuffer: string;
  visualStart: number;
}

interface VimResult {
  value: string;
  displayMode: string;
  cursorPosition: number;
}

const initialState: VimState = {
  mode: 'normal',
  register: '',
  count: 1,
  lastOperator: null,
  commandBuffer: '',
  visualStart: 0
};

export function useVimMode(
  initialValue: string = '',
  onExecute?: (cmd: string) => void
) {
  const [value, setValue] = useState(initialValue);
  const [vimState, setVimState] = useState<VimState>(initialState);
  const [cursorPosition, setCursorPosition] = useState(0);

  const getDisplayMode = (mode: VimMode, buffer: string): string => {
    if (mode === 'command') return `:${buffer}`;
    return mode.toUpperCase();
  };

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    const key = e.key;
    
    // Always allow escape to normal mode
    if (key === 'Escape') {
      setVimState(prev => ({ ...prev, mode: 'normal', commandBuffer: '' }));
      return { value, displayMode: 'NORMAL', cursorPosition };
    }

    const currentMode = vimState.mode;
    const buffer = vimState.commandBuffer;

    if (currentMode === 'normal') {
      if (key === 'i') {
        setVimState(prev => ({ ...prev, mode: 'insert' }));
        return { value, displayMode: 'INSERT', cursorPosition };
      }
      if (key === 'v') {
        setVimState(prev => ({ ...prev, mode: 'visual', visualStart: cursorPosition }));
        return { value, displayMode: 'VISUAL', cursorPosition };
      }
      if (key === ':') {
        setVimState(prev => ({ ...prev, mode: 'command' }));
        return { value, displayMode: ':', cursorPosition };
      }
      // Basic navigation
      if (key === 'h' && cursorPosition > 0) {
        setCursorPosition(p => p - 1);
        return { value, displayMode: 'NORMAL', cursorPosition: cursorPosition - 1 };
      }
      if (key === 'l' && cursorPosition < value.length) {
        setCursorPosition(p => p + 1);
        return { value, displayMode: 'NORMAL', cursorPosition: cursorPosition + 1 };
      }
      if (key === 'w' && cursorPosition < value.length) {
        const nextSpace = value.indexOf(' ', cursorPosition);
        const newPos = nextSpace === -1 ? value.length : nextSpace + 1;
        setCursorPosition(newPos);
        return { value, displayMode: 'NORMAL', cursorPosition: newPos };
      }
      if (key === 'b' && cursorPosition > 0) {
        const prevSpace = value.lastIndexOf(' ', cursorPosition - 2);
        const newPos = prevSpace === -1 ? 0 : prevSpace + 1;
        setCursorPosition(newPos);
        return { value, displayMode: 'NORMAL', cursorPosition: newPos };
      }
      if (key === '0') {
        setCursorPosition(0);
        return { value, displayMode: 'NORMAL', cursorPosition: 0 };
      }
      if (key === '$') {
        setCursorPosition(value.length);
        return { value, displayMode: 'NORMAL', cursorPosition: value.length };
      }
      return { value, displayMode: 'NORMAL', cursorPosition };
    }

    if (currentMode === 'insert') {
      if (key === 'Enter') {
        const newVal = value.slice(0, cursorPosition) + '\n' + value.slice(cursorPosition);
        setValue(newVal);
        setCursorPosition(cursorPosition + 1);
        return { value: newVal, displayMode: 'INSERT', cursorPosition: cursorPosition + 1 };
      }
      if (key === 'Backspace' && cursorPosition > 0) {
        const newVal = value.slice(0, cursorPosition - 1) + value.slice(cursorPosition);
        setValue(newVal);
        setCursorPosition(cursorPosition - 1);
        return { value: newVal, displayMode: 'INSERT', cursorPosition: cursorPosition - 1 };
      }
      if (key === 'ArrowLeft' && cursorPosition > 0) {
        setCursorPosition(p => p - 1);
        return { value, displayMode: 'INSERT', cursorPosition: cursorPosition - 1 };
      }
      if (key === 'ArrowRight' && cursorPosition < value.length) {
        setCursorPosition(p => p + 1);
        return { value, displayMode: 'INSERT', cursorPosition: cursorPosition + 1 };
      }
      if (key.length === 1) {
        const newVal = value.slice(0, cursorPosition) + key + value.slice(cursorPosition);
        setValue(newVal);
        setCursorPosition(cursorPosition + 1);
        return { value: newVal, displayMode: 'INSERT', cursorPosition: cursorPosition + 1 };
      }
      return { value, displayMode: 'INSERT', cursorPosition };
    }

    if (currentMode === 'visual') {
      if (key === 'Escape' || key === 'v') {
        setVimState(prev => ({ ...prev, mode: 'normal' }));
        return { value, displayMode: 'NORMAL', cursorPosition };
      }
      if (key === 'y') {
        const start = Math.min(vimState.visualStart, cursorPosition);
        const end = Math.max(vimState.visualStart, cursorPosition);
        const selected = value.slice(start, end);
        setVimState(prev => ({ ...prev, register: selected, mode: 'normal' }));
        return { value, displayMode: 'NORMAL', cursorPosition };
      }
      if (key === 'd') {
        const start = Math.min(vimState.visualStart, cursorPosition);
        const end = Math.max(vimState.visualStart, cursorPosition);
        const newVal = value.slice(0, start) + value.slice(end);
        setValue(newVal);
        setVimState(prev => ({ ...prev, mode: 'normal' }));
        setCursorPosition(start);
        return { value: newVal, displayMode: 'NORMAL', cursorPosition: start };
      }
      // Visual movement
      if (key === 'h' && cursorPosition > 0) {
        setCursorPosition(p => p - 1);
        return { value, displayMode: 'VISUAL', cursorPosition: cursorPosition - 1 };
      }
      if (key === 'l' && cursorPosition < value.length) {
        setCursorPosition(p => p + 1);
        return { value, displayMode: 'VISUAL', cursorPosition: cursorPosition + 1 };
      }
      return { value, displayMode: 'VISUAL', cursorPosition };
    }

    if (currentMode === 'command') {
      if (key === 'Enter') {
        const cmd = buffer;
        setVimState(prev => ({ ...prev, mode: 'normal', commandBuffer: '' }));
        
        if (cmd === 'w' || cmd === 'write') {
          onExecute?.(value);
        }
        
        return { value, displayMode: 'NORMAL', cursorPosition };
      }
      if (key === 'Backspace' && buffer.length > 0) {
        setVimState(prev => ({ ...prev, commandBuffer: buffer.slice(0, -1) }));
        return { value, displayMode: `:${buffer.slice(0, -1)}`, cursorPosition };
      }
      if (key.length === 1) {
        setVimState(prev => ({ ...prev, commandBuffer: buffer + key }));
        return { value, displayMode: `:${buffer + key}`, cursorPosition };
      }
      return { value, displayMode: `:${buffer}`, cursorPosition };
    }

    return { value, displayMode: getDisplayMode(currentMode, buffer), cursorPosition };
  }, [value, vimState, cursorPosition, onExecute]);

  // Sync cursor position with value changes
  useEffect(() => {
    if (cursorPosition > value.length) {
      setCursorPosition(value.length);
    }
  }, [value.length, cursorPosition]);

  const result: VimResult = {
    value,
    displayMode: getDisplayMode(vimState.mode, vimState.commandBuffer),
    cursorPosition
  };

  return {
    ...result,
    mode: vimState.mode,
    commandBuffer: vimState.commandBuffer,
    handleKeyDown,
    setValue: (v: string) => {
      setValue(v);
      setCursorPosition(v.length);
    },
    setMode: (mode: VimMode) => setVimState(prev => ({ ...prev, mode })),
    vimState
  };
}