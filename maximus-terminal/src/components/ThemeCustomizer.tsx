import React, { useState } from 'react';
import { motion } from 'framer-motion';
import type { ThemeConfig } from '../types/theme';

interface ThemeCustomizerProps {
  activeTheme: ThemeConfig;
  onSaveTheme: (theme: ThemeConfig) => void;
  onImportTheme: (theme: ThemeConfig) => void;
}

interface ColorPickerProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
}

const ColorPicker: React.FC<ColorPickerProps> = ({ label, value, onChange }) => (
  <div className="flex items-center gap-2">
    <input
      type="color"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="w-8 h-8 rounded cursor-pointer"
    />
    <span className="text-xs text-gray-400">{label}</span>
  </div>
);

const Toggle: React.FC<{ checked: boolean; onChange: (v: boolean) => void }> = ({ checked, onChange }) => (
  <button
    onClick={() => onChange(!checked)}
    className={`w-10 h-5 rounded-full transition-colors ${checked ? 'bg-green-500' : 'bg-gray-600'}`}
  >
    <motion.div
      className="w-4 h-4 bg-white rounded-full"
      animate={{ x: checked ? 20 : 2 }}
      transition={{ type: 'spring', stiffness: 500, damping: 30 }}
    />
  </button>
);

export const ThemeCustomizer: React.FC<ThemeCustomizerProps> = ({
  activeTheme,
  onSaveTheme,
  onImportTheme
}) => {
  const [editedTheme, setEditedTheme] = useState<ThemeConfig>({ ...activeTheme });
  const [showExport, setShowExport] = useState(false);
  const [exportCode, setExportCode] = useState('');
  const [customName, setCustomName] = useState('');

  const updateTheme = (path: string, value: any) => {
    const newTheme = { ...editedTheme };
    const keys = path.split('.');
    let obj: any = newTheme;
    for (let i = 0; i < keys.length - 1; i++) {
      obj = obj[keys[i]] = { ...obj[keys[i]] };
    }
    obj[keys[keys.length - 1]] = value;
    setEditedTheme(newTheme);
  };

  const handleSave = () => {
    const themed = { 
      ...editedTheme, 
      name: customName || editedTheme.name || 'Custom Theme' 
    };
    onSaveTheme(themed);
    
    // Save to localStorage
    const savedThemes = JSON.parse(localStorage.getItem('customThemes') || '[]');
    savedThemes.push(themed);
    localStorage.setItem('customThemes', JSON.stringify(savedThemes));
  };

  const handleExport = () => {
    const code = JSON.stringify(editedTheme, null, 2);
    setExportCode(code);
    setShowExport(true);
  };

  const handleImport = () => {
    try {
      const imported = JSON.parse(exportCode);
      onImportTheme(imported);
      setShowExport(false);
    } catch {
      alert('Invalid JSON format');
    }
  };

  return (
    <div className="p-4 space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-bold" style={{ color: editedTheme.foreground }}>
          Theme Customizer
        </h3>
        <input
          type="text"
          placeholder="Theme name..."
          value={customName}
          onChange={(e) => setCustomName(e.target.value)}
          className="px-2 py-1 rounded text-sm"
          style={{ 
            backgroundColor: editedTheme.background,
            border: `1px solid ${editedTheme.primary}40`,
            color: editedTheme.foreground
          }}
        />
      </div>

      {/* Basic Colors */}
      <div>
        <h4 className="text-sm font-bold mb-3" style={{ color: editedTheme.foreground + '99' }}>
          Colors
        </h4>
        <div className="grid grid-cols-2 gap-4">
          <ColorPicker
            label="Primary"
            value={editedTheme.primary}
            onChange={(v) => updateTheme('primary', v)}
          />
          <ColorPicker
            label="Background"
            value={editedTheme.background}
            onChange={(v) => updateTheme('background', v)}
          />
          <ColorPicker
            label="Foreground"
            value={editedTheme.foreground}
            onChange={(v) => updateTheme('foreground', v)}
          />
          <ColorPicker
            label="Secondary"
            value={editedTheme.secondary || editedTheme.primary}
            onChange={(v) => updateTheme('secondary', v)}
          />
        </div>
      </div>

      {/* Effects */}
      <div>
        <h4 className="text-sm font-bold mb-3" style={{ color: editedTheme.foreground + '99' }}>
          Visual Effects
        </h4>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm" style={{ color: editedTheme.foreground }}>Particles</span>
            <Toggle 
              checked={editedTheme.effects?.particles || false}
              onChange={(v) => updateTheme('effects.particles', v)}
            />
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm" style={{ color: editedTheme.foreground }}>Scanlines</span>
            <Toggle 
              checked={editedTheme.effects?.scanlines || false}
              onChange={(v) => updateTheme('effects.scanlines', v)}
            />
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm" style={{ color: editedTheme.foreground }}>Glitch</span>
            <Toggle 
              checked={editedTheme.effects?.glitch || false}
              onChange={(v) => updateTheme('effects.glitch', v)}
            />
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm" style={{ color: editedTheme.foreground }}>CRT Curve</span>
            <Toggle 
              checked={editedTheme.effects?.crtCurve || false}
              onChange={(v) => updateTheme('effects.crtCurve', v)}
            />
          </div>
        </div>
      </div>

      {/* Gradient */}
      <div>
        <h4 className="text-sm font-bold mb-3" style={{ color: editedTheme.foreground + '99' }}>
          Background Gradient
        </h4>
        <div className="space-y-2">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={editedTheme.gradient?.enabled || false}
              onChange={(e) => updateTheme('gradient.enabled', e.target.checked)}
            />
            <span className="text-sm" style={{ color: editedTheme.foreground }}>Enable Gradient</span>
          </label>
          {editedTheme.gradient?.enabled && (
            <div className="grid grid-cols-2 gap-2 ml-6">
              <ColorPicker
                label="From"
                value={editedTheme.gradient?.from || '#000000'}
                onChange={(v) => updateTheme('gradient.from', v)}
              />
              <ColorPicker
                label="To"
                value={editedTheme.gradient?.to || '#000000'}
                onChange={(v) => updateTheme('gradient.to', v)}
              />
            </div>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-2 pt-4 border-t" style={{ borderColor: editedTheme.primary + '30' }}>
        <button
          onClick={handleSave}
          className="px-4 py-2 rounded text-sm font-bold"
          style={{ backgroundColor: editedTheme.primary, color: '#fff' }}
        >
          Save Theme
        </button>
        <button
          onClick={handleExport}
          className="px-4 py-2 rounded text-sm"
          style={{ 
            backgroundColor: 'transparent', 
            border: `1px solid ${editedTheme.primary}40`,
            color: editedTheme.foreground 
          }}
        >
          Export
        </button>
        <button
          onClick={() => setShowExport(true)}
          className="px-4 py-2 rounded text-sm"
          style={{ 
            backgroundColor: 'transparent', 
            border: `1px solid ${editedTheme.primary}40`,
            color: editedTheme.foreground 
          }}
        >
          Import
        </button>
      </div>

      {/* Export/Import Modal */}
      {showExport && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="fixed inset-0 bg-black/80 flex items-center justify-center z-50"
          onClick={() => setShowExport(false)}
        >
          <motion.div
            initial={{ scale: 0.9 }}
            animate={{ scale: 1 }}
            className="p-4 rounded-lg max-w-lg w-full"
            style={{ backgroundColor: editedTheme.background }}
            onClick={(e) => e.stopPropagation()}
          >
            <h4 className="font-bold mb-2" style={{ color: editedTheme.foreground }}>
              {exportCode ? 'Export Theme' : 'Import Theme'}
            </h4>
            {exportCode ? (
              <>
                <textarea
                  value={exportCode}
                  readOnly
                  className="w-full h-40 p-2 rounded text-xs font-mono"
                  style={{ 
                    backgroundColor: editedTheme.background,
                    color: editedTheme.foreground,
                    border: `1px solid ${editedTheme.primary}40`
                  }}
                />
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(exportCode);
                    alert('Copied to clipboard!');
                  }}
                  className="mt-2 px-3 py-1 rounded text-sm"
                  style={{ backgroundColor: editedTheme.primary + '30', color: editedTheme.primary }}
                >
                  Copy to Clipboard
                </button>
              </>
            ) : (
              <textarea
                value={exportCode}
                onChange={(e) => setExportCode(e.target.value)}
                placeholder="Paste theme JSON here..."
                className="w-full h-40 p-2 rounded text-xs font-mono"
                style={{ 
                  backgroundColor: editedTheme.background,
                  color: editedTheme.foreground,
                  border: `1px solid ${editedTheme.primary}40`
                }}
              />
            )}
            <div className="flex gap-2 mt-4">
              {!exportCode && (
                <button
                  onClick={handleImport}
                  className="px-4 py-2 rounded text-sm font-bold"
                  style={{ backgroundColor: editedTheme.primary, color: '#fff' }}
                >
                  Import
                </button>
              )}
              <button
                onClick={() => {
                  setShowExport(false);
                  setExportCode('');
                }}
                className="px-4 py-2 rounded text-sm"
                style={{ 
                  backgroundColor: 'transparent', 
                  border: `1px solid ${editedTheme.primary}40`,
                  color: editedTheme.foreground 
                }}
              >
                Close
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </div>
  );
};

export default ThemeCustomizer;