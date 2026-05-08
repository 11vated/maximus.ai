import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { ThemeConfig } from '../types/theme';

interface DiffPreviewProps {
  filePath: string;
  originalContent: string;
  newContent: string;
  operation: 'write' | 'edit' | 'create';
  theme: ThemeConfig;
  onConfirm: () => void;
  onCancel: () => void;
  onCopyOriginal?: () => void;
  onCopyNew?: () => void;
}

interface DiffLine {
  type: 'unchanged' | 'added' | 'removed' | 'header';
  content: string;
  lineNumber?: number;
}

export const DiffPreview: React.FC<DiffPreviewProps> = ({
  filePath,
  originalContent,
  newContent,
  operation,
  theme,
  onConfirm,
  onCancel,
  onCopyOriginal,
  onCopyNew
}) => {
  const [activeTab, setActiveTab] = useState<'split' | 'new' | 'original'>('split');
  const [isCollapsed, setIsCollapsed] = useState(false);

  const diffLines = useMemo(() => {
    const originalLines = originalContent.split('\n');
    const newLines = newContent.split('\n');
    const result: DiffLine[] = [];

    // Simple diff algorithm
    const maxLines = Math.max(originalLines.length, newLines.length);
    
    for (let i = 0; i < maxLines; i++) {
      const origLine = originalLines[i];
      const newLine = newLines[i];

      if (origLine === newLine) {
        result.push({ type: 'unchanged', content: origLine, lineNumber: i + 1 });
      } else if (origLine === undefined) {
        result.push({ type: 'added', content: newLine, lineNumber: i + 1 });
      } else if (newLine === undefined) {
        result.push({ type: 'removed', content: origLine, lineNumber: i + 1 });
      } else {
        // Changed line - show both
        result.push({ type: 'removed', content: origLine, lineNumber: i + 1 });
        result.push({ type: 'added', content: newLine, lineNumber: i + 1 });
      }
    }

    return result;
  }, [originalContent, newContent]);

  const stats = useMemo(() => {
    let added = 0;
    let removed = 0;
    diffLines.forEach(line => {
      if (line.type === 'added') added++;
      if (line.type === 'removed') removed++;
    });
    return { added, removed };
  }, [diffLines]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: 20, scale: 0.95 }}
      className="rounded-lg border overflow-hidden"
      style={{
        backgroundColor: theme.background,
        borderColor: theme.primary + '60',
        boxShadow: `0 0 30px ${theme.primary}30`
      }}
    >
      {/* Header */}
      <div 
        className="flex items-center justify-between px-4 py-3 border-b"
        style={{ borderColor: theme.primary + '40' }}
      >
        <div className="flex items-center gap-3">
          <span className="text-xl">
            {operation === 'create' ? '✨' : operation === 'write' ? '📝' : '✏️'}
          </span>
          <div>
            <div className="font-mono font-bold" style={{ color: theme.foreground }}>
              {filePath}
            </div>
            <div className="text-xs" style={{ color: theme.foreground + '99' }}>
              {operation === 'create' ? 'New file' : 'Review changes before applying'}
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <span 
            className="text-xs px-2 py-1 rounded font-mono"
            style={{ backgroundColor: '#00b89430', color: '#00b894' }}
          >
            +{stats.added}
          </span>
          <span 
            className="text-xs px-2 py-1 rounded font-mono"
            style={{ backgroundColor: '#d6303130', color: '#d63031' }}
          >
            -{stats.removed}
          </span>
        </div>
      </div>

      {/* View tabs */}
      <div 
        className="flex border-b"
        style={{ borderColor: theme.primary + '30' }}
      >
        {(['split', 'new', 'original'] as const).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className="px-4 py-2 text-sm capitalize"
            style={{
              backgroundColor: activeTab === tab ? theme.primary + '20' : 'transparent',
              color: activeTab === tab ? theme.primary : theme.foreground + '99',
              borderBottom: activeTab === tab ? `2px solid ${theme.primary}` : 'none'
            }}
          >
            {tab === 'split' ? 'Split View' : tab === 'new' ? 'New' : 'Original'}
          </button>
        ))}
        <button 
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="ml-auto px-3 text-sm"
          style={{ color: theme.foreground + '99' }}
        >
          {isCollapsed ? '▼ Expand' : '▲ Collapse'}
        </button>
      </div>

      {/* Diff content */}
      <AnimatePresence>
        {!isCollapsed && (
          <motion.div
            initial={{ height: 0 }}
            animate={{ height: 'auto' }}
            exit={{ height: 0 }}
            className="overflow-auto"
            style={{ maxHeight: '400px' }}
          >
            {activeTab === 'split' ? (
              <div className="grid grid-cols-2 divide-x" style={{ borderColor: theme.primary + '30' }}>
                {/* Original */}
                <div className="p-2">
                  <div className="text-xs px-2 py-1 mb-2 rounded" style={{ 
                    backgroundColor: '#d6303130', 
                    color: '#d63031' 
                  }}>
                    Original
                  </div>
                  <pre 
                    className="text-xs font-mono whitespace-pre-wrap"
                    style={{ color: theme.foreground }}
                  >
                    {originalContent || '(empty)'}
                  </pre>
                  {onCopyOriginal && (
                    <button
                      onClick={onCopyOriginal}
                      className="mt-2 text-xs px-2 py-1 rounded"
                      style={{ backgroundColor: theme.primary + '20', color: theme.primary }}
                    >
                      📋 Copy Original
                    </button>
                  )}
                </div>
                
                {/* New */}
                <div className="p-2">
                  <div className="text-xs px-2 py-1 mb-2 rounded" style={{ 
                    backgroundColor: '#00b89430', 
                    color: '#00b894' 
                  }}>
                    New
                  </div>
                  <pre 
                    className="text-xs font-mono whitespace-pre-wrap"
                    style={{ color: theme.foreground }}
                  >
                    {newContent || '(empty)'}
                  </pre>
                  {onCopyNew && (
                    <button
                      onClick={onCopyNew}
                      className="mt-2 text-xs px-2 py-1 rounded"
                      style={{ backgroundColor: theme.primary + '20', color: theme.primary }}
                    >
                      📋 Copy New
                    </button>
                  )}
                </div>
              </div>
            ) : activeTab === 'new' ? (
              <div className="p-2">
                <pre 
                  className="text-xs font-mono whitespace-pre-wrap"
                  style={{ color: theme.foreground }}
                >
                  {newContent || '(empty)'}
                </pre>
              </div>
            ) : (
              <div className="p-2">
                <pre 
                  className="text-xs font-mono whitespace-pre-wrap"
                  style={{ color: theme.foreground }}
                >
                  {originalContent || '(empty)'}
                </pre>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Actions */}
      <div 
        className="flex items-center justify-end gap-3 px-4 py-3 border-t"
        style={{ borderColor: theme.primary + '30' }}
      >
        <button
          onClick={onCancel}
          className="px-4 py-2 rounded text-sm"
          style={{ 
            backgroundColor: 'transparent',
            border: `1px solid ${theme.primary}40`,
            color: theme.foreground
          }}
        >
          Cancel
        </button>
        <button
          onClick={onConfirm}
          className="px-4 py-2 rounded text-sm font-bold"
          style={{ 
            backgroundColor: theme.primary,
            color: '#fff'
          }}
        >
          {operation === 'create' ? 'Create File' : 'Apply Changes'}
        </button>
      </div>
    </motion.div>
  );
};

export default DiffPreview;