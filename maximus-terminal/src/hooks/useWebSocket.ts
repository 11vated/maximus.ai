import { useEffect, useRef, useState, useCallback } from 'react';
import { useTerminalStore } from '../store/useTerminalStore';

interface WebSocketMessage {
  type: string;
  session_id?: string;
  data?: any;
  message?: string;
  [key: string]: any;
}

interface UseWebSocketOptions {
  url?: string;
  sessionId?: string;
  onMessage?: (message: WebSocketMessage) => void;
  onError?: (error: Event) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const { url = 'ws://localhost:8000/api/ws/agent', onMessage, onError, onConnect, onDisconnect } = options;

  const ws = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  const connect = useCallback(() => {
    try {
      ws.current = new WebSocket(url);

      ws.current.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        reconnectAttempts.current = 0;
        onConnect?.();
      };

      ws.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setLastMessage(message);
          onMessage?.(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        onError?.(error);
      };

      ws.current.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        onDisconnect?.();

        // Attempt to reconnect
        if (reconnectAttempts.current < maxReconnectAttempts) {
          reconnectAttempts.current += 1;
          setTimeout(connect, 1000 * reconnectAttempts.current);
        }
      };
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
    }
  }, [url, onMessage, onError, onConnect, onDisconnect]);

  const disconnect = useCallback(() => {
    if (ws.current) {
      ws.current.close();
      ws.current = null;
    }
  }, []);

  const sendMessage = useCallback((message: any) => {
    if (ws.current && isConnected) {
      ws.current.send(JSON.stringify(message));
      return true;
    }
    return false;
  }, [isConnected]);

  // Connect on mount
  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return {
    isConnected,
    lastMessage,
    sendMessage,
    connect,
    disconnect,
  };
}

// Hook for agent commands via WebSocket with tab support
export function useAgentWebSocket() {
  const { activeTabId, tabs, addLine, updateActiveTab } = useTerminalStore();
  const activeTab = tabs.find(t => t.id === activeTabId);
  const sessionId = activeTab?.sessionId;

  const handleMessage = useCallback((message: WebSocketMessage) => {
    const { type, data, message: msg } = message;

    switch (type) {
      case 'start':
        updateActiveTab({
          agentState: { state: 'init' as any, message: 'Agent starting...', currentTool: null, progress: 0 }
        });
        addLine({
          id: Date.now().toString(),
          type: 'system',
          content: `Agent started: ${msg || 'Processing command'}`,
          timestamp: new Date(),
        });
        break;

      case 'thinking':
        updateActiveTab({ agentState: { state: 'thinking' as any, currentTool: null, progress: 0, message: msg || 'Thinking...' } });
        break;

      case 'acting':
        updateActiveTab({
          agentState: { state: 'acting' as any, currentTool: data?.tool || null, progress: 50, message: msg || 'Executing...' }
        });
        if (data?.tool) {
          addLine({
            id: Date.now().toString(),
            type: 'tool',
            content: `Using tool: ${data.tool}`,
            timestamp: new Date(),
            toolName: data.tool,
          });
        }
        break;

      case 'observing':
        updateActiveTab({ agentState: { state: 'observing' as any, currentTool: null, progress: 75, message: 'Processing result...' } });
        break;

      case 'reflecting':
        updateActiveTab({ agentState: { state: 'reflecting' as any, currentTool: null, progress: 85, message: 'Reflecting...' } });
        break;

      case 'done':
        updateActiveTab({ agentState: { state: 'idle' as any, currentTool: null, progress: 100, message: 'Task completed' } });
        addLine({
          id: Date.now().toString(),
          type: 'system',
          content: 'Agent finished',
          timestamp: new Date(),
        });
        break;

      case 'error':
        updateActiveTab({ agentState: { state: 'error' as any, currentTool: null, progress: 0, message: msg || 'An error occurred' } });
        addLine({
          id: Date.now().toString(),
          type: 'error',
          content: `Error: ${msg || 'Unknown error'}`,
          timestamp: new Date(),
        });
        break;

      default:
        // Handle tool output or other messages
        if (data && type !== 'pong') {
          addLine({
            id: Date.now().toString(),
            type: 'output',
            content: typeof data === 'string' ? data : JSON.stringify(data, null, 2),
            timestamp: new Date(),
          });
        }
    }
  }, [updateActiveTab, addLine]);

  const ws = useWebSocket({
    url: 'ws://localhost:8000/api/ws/agent',
    sessionId,
    onMessage: handleMessage,
  });

  const sendCommand = useCallback((command: string, model = 'qwen2.5-coder:7b', workdir = '.') => {
    if (!sessionId) return false;
    return ws.sendMessage({
      command,
      model,
      workdir,
      session_id: sessionId,
    });
  }, [ws.sendMessage, sessionId]);

  return {
    ...ws,
    sessionId,
    sendCommand,
  };
}
