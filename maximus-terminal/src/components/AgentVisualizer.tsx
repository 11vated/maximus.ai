interface AgentVisualizerProps {
  agentState: any;
  theme: any;
}

const stateConfig: Record<string, { label: string; color: string; icon: string }> = {
  init: { label: 'INIT', color: '#6b7280', icon: '⚡' },
  plan: { label: 'PLAN', color: '#3b82f6', icon: '🧠' },
  act: { label: 'ACT', color: '#10b981', icon: '⚙' },
  observe: { label: 'OBSERVE', color: '#8b5cf6', icon: '👁' },
  reflect: { label: 'REFLECT', color: '#f59e0b', icon: '🤔' },
  adapt: { label: 'ADAPT', color: '#ec4899', icon: '🔧' },
  commit: { label: 'COMMIT', color: '#14b8a6', icon: '✎' },
  pause: { label: 'PAUSE', color: '#6b7280', icon: '⏸' },
};

export function AgentVisualizer({ agentState, theme }: AgentVisualizerProps) {
  const state = agentState?.state || 'idle';
  const config = stateConfig[state] || stateConfig.init;

  return (
    <div className="flex items-center justify-center gap-4 p-2 border-b" style={{ borderColor: theme?.primary + '40' }}>
      <div className="flex items-center gap-2">
        <span className="text-xs opacity-70">State:</span>
        <span
          className="px-2 py-1 rounded text-xs font-bold"
          style={{ background: config.color + '20', color: config.color }}
        >
          {config.icon} {config.label}
        </span>
      </div>

      {agentState?.currentTool && (
        <div className="flex items-center gap-2">
          <span className="text-xs opacity-70">Tool:</span>
          <span className="text-xs" style={{ color: theme?.primary }}>
            {agentState.currentTool}
          </span>
        </div>
      )}

      {agentState?.message && (
        <div className="flex-1 text-center">
          <span className="text-xs opacity-70">{agentState.message}</span>
        </div>
      )}

      {agentState?.progress !== undefined && (
        <div className="w-32 h-1 bg-gray-700 rounded-full overflow-hidden">
          <div
            className="h-full transition-all duration-300"
            style={{ width: `${agentState.progress}%`, background: theme?.primary }}
          />
        </div>
      )}
    </div>
  );
}
