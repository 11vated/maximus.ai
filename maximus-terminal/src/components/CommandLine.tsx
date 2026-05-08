import React, { useState, useRef, useEffect } from 'react';
import { type ThemeConfig } from '../types/theme';
import { useVimMode } from '../hooks/useVimMode';

interface CommandLineProps {
  value: string;
  onChange: (value: string) => void;
  onExecute: (command: string) => void;
  theme: ThemeConfig;
  vimEnabled?: boolean;
}

const CommandLine: React.FC<CommandLineProps> = ({ value, onChange, onExecute, theme, vimEnabled = false }) => {
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const inputRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Vim mode
  const { 
    value: vimValue, 
    displayMode, 
    handleKeyDown: vimHandleKeyDown,
    setValue: setVimValue,
    mode: vimMode
  } = useVimMode(value, onExecute);

  const commands = [
    'help', 'clear', 'run', 'chat', 'status', 'analyze',
    'branch', 'stance', 'theme', 'history', 'exit',
  ];

  // Focus the contentEditable div
  const focusInput = () => {
    if (inputRef.current) {
      inputRef.current.focus();
      // Move cursor to end
      const range = document.createRange();
      range.selectNodeContents(inputRef.current);
      range.collapse(false);
      const sel = window.getSelection();
      sel?.removeAllRanges();
      sel?.addRange(range);
    }
  };

  // Setup click handler on container
  useEffect(() => {
    const container = containerRef.current;
    if (container) {
      container.addEventListener('click', focusInput);
      return () => container.removeEventListener('click', focusInput);
    }
  }, []);

  // Focus on mount
  useEffect(() => {
    setTimeout(focusInput, 100);
  }, []);

  // Handle input - reads text from contentEditable div
  const handleInput = () => {
    if (inputRef.current) {
      const text = inputRef.current.textContent || '';
      onChange(text);
    }
  };

  // Handle keydown - use vim handler when vim is enabled
  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (vimEnabled) {
      const result = vimHandleKeyDown(e);
      if (result.value !== value) {
        onChange(result.value);
        if (inputRef.current) {
          inputRef.current.textContent = result.value;
        }
      }
      
      // Execute on Enter in normal mode with content
      if (e.key === 'Enter' && vimMode === 'normal' && vimValue.trim()) {
        onExecute(vimValue);
        if (inputRef.current) {
          inputRef.current.textContent = '';
        }
        setVimValue('');
        onChange('');
      }
      return;
    }

    // Original handler
    if (e.key === 'Enter') {
      e.preventDefault();
      if (value.trim()) {
        onExecute(value);
        // Clear the div
        if (inputRef.current) {
          inputRef.current.textContent = '';
        }
        onChange('');
      }
      setShowSuggestions(false);
    } else if (e.key === 'Tab') {
      e.preventDefault();
      if (suggestions.length > 0) {
        onChange('/' + suggestions[0]);
        setShowSuggestions(false);
        // Update the div text
        if (inputRef.current) {
          inputRef.current.textContent = '/' + suggestions[0];
        }
      }
    } else if (e.key === 'Escape') {
      setShowSuggestions(false);
    }
  };

  // Update div text when value changes externally
  useEffect(() => {
    if (inputRef.current && inputRef.current.textContent !== value) {
      inputRef.current.textContent = value;
    }
  }, [value]);

  // Filter suggestions
  useEffect(() => {
    if (value.startsWith('/')) {
      const query = value.slice(1).toLowerCase();
      const matches = commands.filter(cmd => cmd.includes(query));
      setSuggestions(matches);
      setShowSuggestions(matches.length > 0);
    } else {
      setShowSuggestions(false);
    }
  }, [value]);

  const handleSuggestionClick = (suggestion: string) => {
    onChange('/' + suggestion);
    setShowSuggestions(false);
    focusInput();
    if (inputRef.current) {
      inputRef.current.textContent = '/' + suggestion;
    }
  };

  return (
    <div ref={containerRef} className="relative cursor-text">
      <div className="flex items-center gap-2">
        <span style={{ color: theme.primary }} className="font-bold">
          ❯
        </span>
        
        {/* Vim Mode Indicator */}
        {vimEnabled && (
          <div className="flex items-center gap-1">
            <span 
              className="text-xs px-2 py-0.5 rounded font-mono"
              style={{ 
                backgroundColor: vimMode === 'insert' ? '#00b894' : 
                                vimMode === 'visual' ? '#e17055' :
                                vimMode === 'command' ? '#6c5ce7' :
                                theme.primary + '40',
                color: vimMode === 'insert' ? '#fff' : theme.foreground
              }}
            >
              {displayMode}
            </span>
          </div>
        )}
        
        <div
          ref={inputRef}
          contentEditable
          suppressContentEditableWarning
          onInput={handleInput}
          onKeyDown={handleKeyDown}
          className="flex-1 bg-transparent outline-none border-none"
          style={{
            color: theme.foreground,
            fontFamily: theme.font,
            caretColor: theme.primary,
            minHeight: '1.5em',
          }}
          data-placeholder="Type a command... (Tab for suggestions)"
          onFocus={() => {
            // Show placeholder logic via CSS
          }}
        />
        <button
          onClick={(e) => {
            e.stopPropagation();
            if (value.trim()) onExecute(value);
          }}
          className="rounded px-3 py-1 text-sm hover:opacity-80"
          style={{
            background: theme.primary,
            color: theme.background,
          }}
        >
          Execute
        </button>
      </div>

      {/* Suggestions dropdown */}
      {showSuggestions && (
        <div
          className="absolute left-0 right-0 top-full z-50 mt-1 rounded border p-2"
          style={{
            background: theme.background,
            borderColor: theme.primary + '40',
          }}
        >
          {suggestions.map((sug, idx) => (
            <div
              key={idx}
              onClick={() => handleSuggestionClick(sug)}
              className="cursor-pointer rounded px-2 py-1 hover:opacity-80"
              style={{ color: theme.foreground }}
              onMouseEnter={(e) => (e.currentTarget.style.background = theme.primary + '20')}
              onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
            >
              /{sug}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default CommandLine;
