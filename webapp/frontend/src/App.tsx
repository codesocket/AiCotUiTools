import { useState, useRef, useEffect, useMemo } from 'react';
import { useWebSocket } from './hooks/useWebSocket';
import { Message, ToolCall, ReasoningStep, UIState } from './types';
import {
  Send,
  Loader2,
  Wifi,
  WifiOff,
  Sparkles,
  Settings,
  Palette,
  Contrast,
  RotateCcw,
  Zap,
  Brain,
  CheckCircle2
} from 'lucide-react';

const THEME_COLORS = {
  blue: '#3b82f6',
  purple: '#a855f7',
  green: '#10b981',
  red: '#ef4444',
  orange: '#f97316',
  pink: '#ec4899',
  indigo: '#6366f1',
  teal: '#14b8a6'
};

function App() {
  const [inputValue, setInputValue] = useState('');
  const [uiState, setUIState] = useState<UIState>({
    themeColor: THEME_COLORS.blue,
    highContrast: false
  });
  const [showSettings, setShowSettings] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const handleUIAction = (tool: string, args: any) => {
    switch (tool) {
      case 'change_theme_color':
        const colorMap: Record<string, string> = {
          blue: '#3b82f6',
          purple: '#a855f7',
          green: '#10b981',
          red: '#ef4444',
          orange: '#f97316',
          pink: '#ec4899',
          indigo: '#6366f1',
          teal: '#14b8a6'
        };
        setUIState(prev => ({ ...prev, themeColor: colorMap[args.color] || '#3b82f6' }));
        break;
      case 'enable_high_contrast':
        setUIState(prev => ({ ...prev, highContrast: args.enabled }));
        break;
      // Legacy support
      case 'change_theme':
        setUIState(prev => ({ ...prev, themeColor: args.color }));
        break;
      case 'toggle_high_contrast':
        setUIState(prev => ({ ...prev, highContrast: args.enabled }));
        break;
    }
  };

  // Create a stable client ID that doesn't change on re-renders
  const clientId = useMemo(() => 'client-' + Date.now(), []);

  const {
    connectionStatus,
    messages,
    currentToolCalls,
    currentReasoningSteps,
    agentStatus,
    sendQuery,
    resetAgent
  } = useWebSocket(clientId, handleUIAction);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, currentReasoningSteps, currentToolCalls]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim() && connectionStatus === 'connected') {
      sendQuery(inputValue.trim());
      setInputValue('');
    }
  };

  const handleReset = () => {
    resetAgent();
  };

  const ConnectionIndicator = () => {
    const statusConfig = {
      connecting: { icon: Loader2, color: 'text-yellow-500', text: 'Connecting...', spinning: true },
      connected: { icon: Wifi, color: 'text-green-500', text: 'Connected', spinning: false },
      disconnected: { icon: WifiOff, color: 'text-gray-400', text: 'Disconnected', spinning: false },
      error: { icon: WifiOff, color: 'text-red-500', text: 'Error', spinning: false }
    };

    const config = statusConfig[connectionStatus];
    const Icon = config.icon;

    return (
      <div className="flex items-center gap-2 text-sm">
        <Icon className={`w-4 h-4 ${config.color} ${config.spinning ? 'animate-spin' : ''}`} />
        <span className={config.color}>{config.text}</span>
      </div>
    );
  };

  const ToolCallDisplay = ({ toolCall }: { toolCall: ToolCall }) => (
    <div className="bg-gradient-to-r from-purple-50 to-pink-50 border-l-4 border-purple-400 rounded-lg p-4 mb-2">
      <div className="flex items-start gap-2">
        <Zap className="w-5 h-5 text-purple-600 mt-0.5 flex-shrink-0" />
        <div className="flex-1">
          <div className="font-semibold text-purple-900 flex items-center gap-2">
            {toolCall.tool}
            {toolCall.result && <CheckCircle2 className="w-4 h-4 text-green-600" />}
          </div>
          <div className="text-sm text-purple-700 mt-1">
            <span className="font-medium">Args:</span> {JSON.stringify(toolCall.arguments)}
          </div>
          {toolCall.result && (
            <div className="text-sm text-green-700 mt-2 bg-green-50 rounded p-2">
              <span className="font-medium">Result:</span> {toolCall.result}
            </div>
          )}
        </div>
      </div>
    </div>
  );

  const ReasoningStepDisplay = ({ step }: { step: ReasoningStep }) => {
    if (step.type === 'reasoning' && step.text) {
      return (
        <div className="bg-blue-50 border-l-4 border-blue-400 rounded-lg p-4 mb-2">
          <div className="flex items-start gap-2">
            <Brain className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
            <div className="text-sm text-blue-900 whitespace-pre-wrap">{step.text}</div>
          </div>
        </div>
      );
    }
    return null;
  };

  const MessageDisplay = ({ message }: { message: Message }) => {
    const isUser = message.role === 'user';
    const isSystem = message.role === 'system';

    if (isSystem) {
      const isWarning = message.content.includes('⚠️');
      return (
        <div className="flex justify-center my-4">
          <div className={`text-sm rounded-lg px-6 py-4 max-w-2xl ${
            isWarning
              ? 'bg-yellow-50 border-2 border-yellow-300 text-yellow-900'
              : 'bg-gray-100 text-gray-600 rounded-full px-4 py-2 max-w-md text-center'
          }`}>
            <div className={isWarning ? 'text-left whitespace-pre-wrap' : ''}>
              {message.content}
            </div>
          </div>
        </div>
      );
    }

    return (
      <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
        <div className={`max-w-3xl ${isUser ? 'ml-12' : 'mr-12'}`}>
          <div
            className={`rounded-2xl px-6 py-4 ${
              isUser
                ? 'text-white shadow-lg'
                : 'bg-white border border-gray-200 shadow-sm'
            }`}
            style={isUser ? { backgroundColor: uiState.themeColor } : {}}
          >
            {isUser ? (
              <div className="whitespace-pre-wrap">{message.content}</div>
            ) : (
              <div>
                {message.reasoningSteps && message.reasoningSteps.length > 0 && (
                  <div className="space-y-2 mb-4">
                    {message.reasoningSteps.map((step, idx) => (
                      <ReasoningStepDisplay key={idx} step={step} />
                    ))}
                  </div>
                )}

                {message.toolCalls && message.toolCalls.length > 0 && (
                  <div className="space-y-2 mb-4">
                    {message.toolCalls.map((toolCall, idx) => (
                      <ToolCallDisplay key={idx} toolCall={toolCall} />
                    ))}
                  </div>
                )}

                {message.content && (
                  <div className="text-gray-800 whitespace-pre-wrap">{message.content}</div>
                )}
              </div>
            )}
          </div>
          <div className={`text-xs text-gray-400 mt-1 ${isUser ? 'text-right' : 'text-left'}`}>
            {message.timestamp.toLocaleTimeString()}
          </div>
        </div>
      </div>
    );
  };

  const CurrentActivityDisplay = () => {
    if (!agentStatus && currentToolCalls.length === 0 && currentReasoningSteps.length === 0) {
      return null;
    }

    return (
      <div className="mb-4 mr-12">
        <div className="max-w-3xl bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-200 rounded-2xl px-6 py-4 shadow-sm">
          {agentStatus && (
            <div className="flex items-center gap-2 text-indigo-700 mb-3">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span className="text-sm font-medium">{agentStatus.message}</span>
            </div>
          )}

          {currentReasoningSteps.length > 0 && (
            <div className="space-y-2 mb-3">
              {currentReasoningSteps.map((step, idx) => (
                <ReasoningStepDisplay key={idx} step={step} />
              ))}
            </div>
          )}

          {currentToolCalls.length > 0 && (
            <div className="space-y-2">
              {currentToolCalls.map((toolCall, idx) => (
                <ToolCallDisplay key={idx} toolCall={toolCall} />
              ))}
            </div>
          )}
        </div>
      </div>
    );
  };

  const SettingsPanel = () => {
    if (!showSettings) return null;

    return (
      <div className="absolute top-16 right-4 bg-white border border-gray-200 rounded-lg shadow-xl p-4 w-80 z-10">
        <h3 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
          <Settings className="w-4 h-4" />
          UI Settings
        </h3>

        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium text-gray-700 flex items-center gap-2 mb-2">
              <Palette className="w-4 h-4" />
              Theme Color
            </label>
            <div className="grid grid-cols-4 gap-2">
              {Object.entries(THEME_COLORS).map(([name, color]) => (
                <button
                  key={name}
                  onClick={() => setUIState(prev => ({ ...prev, themeColor: color }))}
                  className={`w-full h-10 rounded-lg border-2 transition-all ${
                    uiState.themeColor === color ? 'border-gray-800 scale-110' : 'border-gray-200'
                  }`}
                  style={{ backgroundColor: color }}
                  title={name}
                />
              ))}
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-gray-700 flex items-center gap-2 mb-2">
              <Contrast className="w-4 h-4" />
              High Contrast Mode
            </label>
            <button
              onClick={() => setUIState(prev => ({ ...prev, highContrast: !prev.highContrast }))}
              className={`w-full py-2 px-4 rounded-lg border-2 transition-all ${
                uiState.highContrast
                  ? 'bg-gray-900 text-white border-gray-900'
                  : 'bg-white text-gray-800 border-gray-300'
              }`}
            >
              {uiState.highContrast ? 'Disable' : 'Enable'} High Contrast
            </button>
          </div>
        </div>

        <div className="mt-4 pt-4 border-t border-gray-200">
          <p className="text-xs text-gray-500">
            Try asking the AI to change these settings!
            <br />
            Example: "Change the theme to purple" or "Enable high contrast mode"
          </p>
        </div>
      </div>
    );
  };

  return (
    <div className={`min-h-screen flex flex-col ${uiState.highContrast ? 'high-contrast' : ''}`}>
      {/* Header */}
      <header
        className="border-b shadow-sm transition-colors duration-300"
        style={{
          backgroundColor: uiState.highContrast ? '#000' : uiState.themeColor,
          borderColor: uiState.highContrast ? '#fff' : 'transparent'
        }}
      >
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Sparkles className="w-8 h-8 text-white" />
            <div>
              <h1 className="text-2xl font-bold text-white">LLM Agent UI</h1>
              <p className="text-sm text-white/80">Interactive Tool Calling Demo</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <ConnectionIndicator />
            <button
              onClick={handleReset}
              className="flex items-center gap-2 px-4 py-2 bg-white/20 hover:bg-white/30 text-white rounded-lg transition-colors"
              title="Reset conversation"
            >
              <RotateCcw className="w-4 h-4" />
              Reset
            </button>
            <button
              onClick={() => setShowSettings(!showSettings)}
              className="flex items-center gap-2 px-4 py-2 bg-white/20 hover:bg-white/30 text-white rounded-lg transition-colors"
            >
              <Settings className="w-4 h-4" />
              Settings
            </button>
          </div>
        </div>
        <SettingsPanel />
      </header>

      {/* Messages Area */}
      <main className="flex-1 overflow-y-auto bg-gray-50 custom-scrollbar">
        <div className="max-w-7xl mx-auto px-4 py-6">
          {messages.length === 0 && !agentStatus ? (
            <div className="flex items-center justify-center h-full min-h-[400px]">
              <div className="text-center">
                <Sparkles className="w-16 h-16 mx-auto mb-4" style={{ color: uiState.themeColor }} />
                <h2 className="text-2xl font-bold text-gray-800 mb-2">Welcome to LLM Agent UI</h2>
                <p className="text-gray-600 mb-6 max-w-md">
                  This demo showcases how an LLM can intelligently choose and execute both UI and backend tools.
                </p>
                <div className="bg-white rounded-lg shadow-md p-6 max-w-2xl mx-auto text-left">
                  <h3 className="font-semibold text-gray-800 mb-3">Try these examples:</h3>
                  <ul className="space-y-2 text-sm text-gray-600">
                    <li className="flex items-start gap-2">
                      <span className="text-purple-500">•</span>
                      <span>"Change the theme to purple and enable high contrast"</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-blue-500">•</span>
                      <span>"What's 25 * 47?"</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-green-500">•</span>
                      <span>"Search for information about Python"</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-orange-500">•</span>
                      <span>"What's the current date and time?"</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-pink-500">•</span>
                      <span>"Make the UI pink and calculate 100 / 5"</span>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          ) : (
            <>
              {messages.map((message) => (
                <MessageDisplay key={message.id} message={message} />
              ))}
              <CurrentActivityDisplay />
              <div ref={messagesEndRef} />
            </>
          )}
        </div>
      </main>

      {/* Input Area */}
      <footer className="border-t bg-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <form onSubmit={handleSubmit} className="flex gap-3">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Ask me to change UI settings, calculate, search knowledge, or get the date..."
              className="flex-1 px-4 py-3 border-2 border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 transition-colors"
              disabled={connectionStatus !== 'connected'}
            />
            <button
              type="submit"
              disabled={connectionStatus !== 'connected' || !inputValue.trim()}
              className="px-6 py-3 text-white rounded-lg font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 shadow-md hover:shadow-lg"
              style={{ backgroundColor: connectionStatus === 'connected' ? uiState.themeColor : '#9ca3af' }}
            >
              <Send className="w-5 h-5" />
              Send
            </button>
          </form>
        </div>
      </footer>
    </div>
  );
}

export default App;
