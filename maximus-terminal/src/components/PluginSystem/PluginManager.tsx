import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { type ThemeConfig } from '../../types/theme';

interface Plugin {
  id: string;
  name: string;
  description: string;
  version: string;
  author: string;
  installed: boolean;
  enabled: boolean;
  icon: string;
}

interface PluginManagerProps {
  theme: ThemeConfig;
  onClose: () => void;
}

const samplePlugins: Plugin[] = [
  {
    id: 'code-highlighter',
    name: 'Code Highlighter',
    description: 'Enhanced syntax highlighting with custom themes',
    version: '1.2.0',
    author: 'Maximus Team',
    installed: true,
    enabled: true,
    icon: '🎨',
  },
  {
    id: 'data-viz',
    name: 'Data Visualizer',
    description: 'Create charts and graphs from command output',
    version: '2.0.1',
    author: 'Maximus Team',
    installed: true,
    enabled: false,
    icon: '📊',
  },
  {
    id: 'git-integration',
    name: 'Git Integration',
    description: 'Enhanced git status, diff, and branch visualization',
    version: '1.0.0',
    author: 'Maximus Team',
    installed: false,
    enabled: false,
    icon: '🔀',
  },
];

const PluginManager: React.FC<PluginManagerProps> = ({ theme, onClose }) => {
  const [plugins, setPlugins] = useState<Plugin[]>(samplePlugins);
  const [filter, setFilter] = useState<'all' | 'installed' | 'available'>('all');

  const togglePlugin = (id: string) => {
    setPlugins(prev =>
      prev.map(p => (p.id === id ? { ...p, enabled: !p.enabled } : p))
    );
  };

  const installPlugin = (id: string) => {
    setPlugins(prev =>
      prev.map(p => (p.id === id ? { ...p, installed: true } : p))
    );
  };

  const filteredPlugins = plugins.filter(p => {
    if (filter === 'installed') return p.installed;
    if (filter === 'available') return !p.installed;
    return true;
  });

  return (
    <motion.div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />

      <motion.div
        className="relative z-10 w-full max-w-2xl rounded-xl overflow-hidden"
        style={{
          background: theme.background + 'f5',
          border: `1px solid ${theme.primary}40`,
          boxShadow: `0 20px 60px ${theme.primary}30`,
        }}
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
      >
        {/* Header */}
        <div
          className="flex items-center justify-between p-4 border-b"
          style={{ borderColor: theme.primary + '40' }}
        >
          <h2 className="text-lg font-bold" style={{ color: theme.primary }}>
            🔌 Plugin Manager
          </h2>
          <button
            onClick={onClose}
            className="text-2xl hover:opacity-70"
            style={{ color: theme.foreground }}
          >
            ×
          </button>
        </div>

        {/* Filter tabs */}
        <div className="flex gap-2 p-4 pb-0">
          {(['all', 'installed', 'available'] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className="px-3 py-1 rounded capitalize text-sm"
              style={{
                background: filter === f ? theme.primary : theme.primary + '20',
                color: filter === f ? theme.background : theme.foreground,
              }}
            >
              {f}
            </button>
          ))}
        </div>

        {/* Plugin list */}
        <div className="p-4 space-y-3 max-h-96 overflow-y-auto">
          {filteredPlugins.map((plugin, idx) => (
            <motion.div
              key={plugin.id}
              className="p-3 rounded-lg border"
              style={{
                borderColor: theme.primary + '20',
                background: plugin.enabled ? theme.primary + '10' : 'transparent',
              }}
              initial={{ x: -20, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ delay: idx * 0.05 }}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3">
                  <span className="text-2xl">{plugin.icon}</span>
                  <div>
                    <h3 className="font-bold text-sm" style={{ color: theme.foreground }}>
                      {plugin.name}
                      <span className="ml-2 text-xs" style={{ color: theme.secondary }}>
                        v{plugin.version}
                      </span>
                    </h3>
                    <p className="text-xs mt-1" style={{ color: theme.secondary }}>
                      {plugin.description}
                    </p>
                    <p className="text-xs mt-1 opacity-50" style={{ color: theme.secondary }}>
                      by {plugin.author}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  {plugin.installed ? (
                    <button
                      onClick={() => togglePlugin(plugin.id)}
                      className="px-3 py-1 rounded text-xs"
                      style={{
                        background: plugin.enabled ? theme.primary : theme.secondary + '20',
                        color: plugin.enabled ? theme.background : theme.foreground,
                      }}
                    >
                      {plugin.enabled ? 'Enabled' : 'Disabled'}
                    </button>
                  ) : (
                    <button
                      onClick={() => installPlugin(plugin.id)}
                      className="px-3 py-1 rounded text-xs"
                      style={{
                        background: theme.accent,
                        color: theme.background,
                      }}
                    >
                      Install
                    </button>
                  )}
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Footer */}
        <div
          className="p-4 border-t text-xs"
          style={{
            borderColor: theme.primary + '40',
            color: theme.secondary,
          }}
        >
          {plugins.filter(p => p.installed).length} plugins installed •
          {' '}
          {plugins.filter(p => p.enabled).length} enabled
        </div>
      </motion.div>
    </motion.div>
  );
};

export default PluginManager;
