import { useState, useEffect, useRef, useCallback } from 'react';
import { ConnectionStatus, WebSocketMessage, Message, ToolCall, ReasoningStep, AgentStatus } from '../types';
import { getUIToolDefinitions, executeUITool } from '../tools/uiTools';

const WS_URL = 'ws://localhost:8000/ws';

interface UseWebSocketReturn {
  connectionStatus: ConnectionStatus;
  messages: Message[];
  currentToolCalls: ToolCall[];
  currentReasoningSteps: ReasoningStep[];
  agentStatus: AgentStatus | null;
  sendQuery: (query: string) => void;
  resetAgent: () => void;
  executeUIAction: (action: string, payload: any) => void;
}

export function useWebSocket(clientId: string, onUIAction: (action: string, payload: any) => void): UseWebSocketReturn {
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('connecting');
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentToolCalls, setCurrentToolCalls] = useState<ToolCall[]>([]);
  const [currentReasoningSteps, setCurrentReasoningSteps] = useState<ReasoningStep[]>([]);
  const [agentStatus, setAgentStatus] = useState<AgentStatus | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const currentMessageRef = useRef<Message | null>(null);

  const connect = useCallback(() => {
    try {
      setConnectionStatus('connecting');
      const ws = new WebSocket(`${WS_URL}/${clientId}`);

      ws.onopen = () => {
        console.log('WebSocket connected');
        setConnectionStatus('connected');

        // Send UI tool definitions to backend
        const uiTools = getUIToolDefinitions();
        ws.send(JSON.stringify({
          type: 'register_ui_tools',
          tools: uiTools
        }));
        console.log('Sent UI tool definitions:', uiTools);
      };

      ws.onmessage = (event) => {
        try {
          const wsMessage: WebSocketMessage = JSON.parse(event.data);
          handleWebSocketMessage(wsMessage);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionStatus('error');
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setConnectionStatus('disconnected');

        // Attempt to reconnect after 3 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log('Attempting to reconnect...');
          connect();
        }, 3000);
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Error connecting to WebSocket:', error);
      setConnectionStatus('error');
    }
  }, [clientId]);

  const handleWebSocketMessage = (wsMessage: WebSocketMessage) => {
    const { type, data } = wsMessage;

    switch (type) {
      case 'connected':
        console.log('Connected to agent:', data);
        setMessages([{
          id: Date.now().toString(),
          role: 'system',
          content: `Connected to LLM Agent! Available tools:\n• Backend: ${data.available_tools.backend.join(', ')}\n• UI: ${data.available_tools.ui.join(', ')}`,
          timestamp: new Date()
        }]);
        break;

      case 'status':
        setAgentStatus(data);
        break;

      case 'reasoning':
        const reasoningStep: ReasoningStep = {
          type: 'reasoning',
          text: data.text,
          timestamp: new Date()
        };
        setCurrentReasoningSteps(prev => [...prev, reasoningStep]);

        // Update current message content
        if (currentMessageRef.current) {
          currentMessageRef.current.content += data.text + '\n';
          setMessages(prev => {
            const updated = [...prev];
            const lastIndex = updated.length - 1;
            if (lastIndex >= 0 && updated[lastIndex].id === currentMessageRef.current?.id) {
              updated[lastIndex] = { ...currentMessageRef.current! };
            }
            return updated;
          });
        }
        break;

      case 'tool_call':
        const toolCall: ToolCall = {
          tool: data.tool,
          arguments: data.arguments,
          timestamp: new Date()
        };
        setCurrentToolCalls(prev => [...prev, toolCall]);
        setAgentStatus({ message: `Executing ${data.tool}...`, stage: 'executing' });
        break;

      case 'tool_result':
        setCurrentToolCalls(prev => {
          const updated = [...prev];
          const lastCall = updated[updated.length - 1];
          if (lastCall && lastCall.tool === data.tool) {
            lastCall.result = data.result;
          }
          return updated;
        });
        break;

      case 'execute_ui_tool':
        // Backend is requesting UI tool execution
        console.log('UI Tool execution request:', data);
        executeUITool(data.tool, data.arguments)
          .then(result => {
            // Send result back to backend
            if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
              wsRef.current.send(JSON.stringify({
                type: 'ui_tool_result',
                tool: data.tool,
                result: result
              }));
            }

            // Execute the UI action
            onUIAction(data.tool, data.arguments);
          })
          .catch(error => {
            console.error('Error executing UI tool:', error);
            if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
              wsRef.current.send(JSON.stringify({
                type: 'ui_tool_error',
                tool: data.tool,
                error: error.message
              }));
            }
          });
        break;

      case 'ui_action':
        // Legacy: Execute UI action immediately
        console.log('UI Action received:', data);
        onUIAction(data.action, data);

        // Add to current tool calls for display
        setCurrentToolCalls(prev => {
          const updated = [...prev];
          const lastCall = updated[updated.length - 1];
          if (lastCall && !lastCall.result) {
            lastCall.result = data.message;
          }
          return updated;
        });
        break;

      case 'no_tools_used':
        // Show a helpful message when no tools matched the query
        console.log('No tools were used:', data);
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          role: 'system',
          content: `⚠️ ${data.message}\n${data.available_capabilities.map((cap: string) => `  • ${cap}`).join('\n')}`,
          timestamp: new Date()
        }]);
        break;

      case 'complete':
        // Finalize the assistant message
        if (currentMessageRef.current) {
          currentMessageRef.current.toolCalls = [...currentToolCalls];
          currentMessageRef.current.reasoningSteps = [...currentReasoningSteps];
          setMessages(prev => {
            const updated = [...prev];
            const lastIndex = updated.length - 1;
            if (lastIndex >= 0 && updated[lastIndex].id === currentMessageRef.current?.id) {
              updated[lastIndex] = { ...currentMessageRef.current! };
            }
            return updated;
          });
        }

        // Reset current state
        setCurrentToolCalls([]);
        setCurrentReasoningSteps([]);
        setAgentStatus(null);
        currentMessageRef.current = null;
        break;

      case 'error':
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          role: 'system',
          content: `Error: ${data.message}`,
          timestamp: new Date()
        }]);
        setAgentStatus(null);
        setCurrentToolCalls([]);
        setCurrentReasoningSteps([]);
        currentMessageRef.current = null;
        break;

      case 'reset_complete':
        setMessages([{
          id: Date.now().toString(),
          role: 'system',
          content: 'Agent reset successfully',
          timestamp: new Date()
        }]);
        break;
    }
  };

  const sendQuery = useCallback((query: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      // Add user message
      const userMessage: Message = {
        id: Date.now().toString(),
        role: 'user',
        content: query,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, userMessage]);

      // Create placeholder for assistant message
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '',
        timestamp: new Date(),
        toolCalls: [],
        reasoningSteps: []
      };
      setMessages(prev => [...prev, assistantMessage]);
      currentMessageRef.current = assistantMessage;

      // Reset current state
      setCurrentToolCalls([]);
      setCurrentReasoningSteps([]);

      // Send query to server
      wsRef.current.send(JSON.stringify({
        type: 'query',
        query
      }));
    }
  }, []);

  const resetAgent = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'reset'
      }));
      setCurrentToolCalls([]);
      setCurrentReasoningSteps([]);
      setAgentStatus(null);
      currentMessageRef.current = null;
    }
  }, []);

  const executeUIAction = useCallback((action: string, payload: any) => {
    // This is called from the parent component
    // WebSocket already handles UI actions via the ui_action message type
  }, []);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  return {
    connectionStatus,
    messages,
    currentToolCalls,
    currentReasoningSteps,
    agentStatus,
    sendQuery,
    resetAgent,
    executeUIAction
  };
}
