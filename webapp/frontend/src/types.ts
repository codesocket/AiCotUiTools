export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  toolCalls?: ToolCall[];
  reasoningSteps?: ReasoningStep[];
}

export interface ToolCall {
  tool: string;
  arguments: Record<string, any>;
  result?: string;
  timestamp?: Date;
}

export interface ReasoningStep {
  type: 'reasoning' | 'tool_call';
  text?: string;
  data?: any;
  timestamp?: Date;
}

export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
}

export interface UIState {
  themeColor: string;
  highContrast: boolean;
}

export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

export interface AgentStatus {
  message: string;
  stage: 'start' | 'api_call' | 'processing' | 'thinking' | 'executing' | 'completed';
}
