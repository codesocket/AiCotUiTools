# LLM Agent UI - Interactive Tool Calling Demo

A sophisticated React application demonstrating how an LLM can intelligently infer and execute both **UI tools** (frontend) and **backend tools** through a WebSocket connection.

## 🌟 Features

### Backend Tools
- **Calculator**: Perform arithmetic operations
- **Knowledge Search**: Search a built-in knowledge base
- **Date/Time**: Get current date and time

### UI Tools (Executed in Browser)
- **Change Theme Color**: Dynamically change the UI theme (8 colors available)
- **High Contrast Mode**: Toggle accessibility-friendly high contrast mode

### Key Capabilities
- ✨ **Real-time WebSocket communication** between React frontend and FastAPI backend
- 🧠 **LLM intelligently chooses** which tools to execute based on user prompts
- 🔄 **Live reasoning step visualization** - see the agent think in real-time
- 🎨 **Dynamic UI updates** when LLM calls UI tools
- 📊 **Tool execution tracking** with detailed arguments and results
- 🎯 **Chain of Thought reasoning** visible to users

## 🏗️ Architecture

```
React UI (Frontend)
    ↕️ WebSocket Connection
FastAPI Server (Backend)
    ↕️
ChainOfThoughtAgent
    ↕️
OpenAI API (GPT-4)
```

## 📁 Project Structure

```
webapp/
├── backend/
│   ├── server.py              # FastAPI WebSocket server
│   └── requirements.txt       # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.tsx           # Main React component
│   │   ├── main.tsx          # React entry point
│   │   ├── types.ts          # TypeScript interfaces
│   │   ├── index.css         # Tailwind CSS + custom styles
│   │   └── hooks/
│   │       └── useWebSocket.ts  # WebSocket client hook
│   ├── package.json          # Node dependencies
│   ├── vite.config.ts        # Vite configuration
│   ├── tailwind.config.js    # Tailwind CSS config
│   └── tsconfig.json         # TypeScript config
└── README.md                 # This file
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.12+** (for backend)
- **Node.js 18+** (for frontend)
- **OpenAI API Key** (set as `OPENAI_API_KEY` environment variable)

### 1. Set up Backend

```bash
cd webapp/backend

# Install Python dependencies
pip install -r requirements.txt

# Set your OpenAI API key
export OPENAI_API_KEY="your-api-key-here"

# Start the FastAPI server
python server.py
```

The backend will start on `http://localhost:8000`

### 2. Set up Frontend

```bash
cd webapp/frontend

# Install Node dependencies
npm install

# Start the development server
npm run dev
```

The frontend will start on `http://localhost:5173`

### 3. Open Your Browser

Navigate to `http://localhost:5173` and start chatting!

## 💬 Example Prompts

Try these to see the LLM intelligently choose tools:

### UI Tools
- "Change the theme to purple"
- "Enable high contrast mode"
- "Make the interface pink and enable high contrast"
- "Switch to a green theme"

### Backend Tools
- "What's 25 * 47?"
- "Search for information about Python"
- "What's the current date and time?"
- "Calculate 1234 + 5678"

### Mixed (UI + Backend)
- "Change the theme to orange and tell me the current date"
- "Enable high contrast and calculate 99 * 88"
- "Search for AI information and make the UI teal"

## 🔧 How It Works

### 1. Tool Registration

The backend registers all available tools (UI + backend) with the OpenAI API:

```python
{
  "name": "change_theme_color",
  "description": "Changes the UI theme color...",
  "parameters": {...}
}
```

### 2. LLM Decision Making

When you send a prompt like "Change the theme to purple and calculate 5 * 5":

1. OpenAI analyzes the prompt
2. Identifies it needs TWO tools: `change_theme_color` and `calculator`
3. Generates function calls with appropriate arguments

### 3. Tool Execution

- **Backend tools**: Executed on the server, results sent back
- **UI tools**: Server sends `ui_action` message, React updates UI immediately

### 4. Real-time Updates

The WebSocket connection streams:
- Reasoning steps (Chain of Thought)
- Tool calls with arguments
- Tool execution results
- UI action commands

## 🎨 UI Tools Implementation

UI tools are unique - they're defined on the backend but executed on the frontend:

```typescript
// Backend detects UI tool
if (tool_name === "change_theme_color") {
  return json.dumps({
    "type": "ui_action",
    "action": "change_theme",
    "color": color_map[color]
  })
}

// Frontend receives and executes
const handleUIAction = (action: string, payload: any) => {
  if (action === 'change_theme') {
    setUIState(prev => ({ ...prev, themeColor: payload.color }));
  }
};
```

## 📊 WebSocket Message Types

### Client → Server
- `query`: Send user query
- `reset`: Reset agent conversation
- `ping`: Keep-alive

### Server → Client
- `connected`: Initial connection confirmation
- `status`: Agent processing status
- `reasoning`: Chain of Thought step
- `tool_call`: Tool execution started
- `tool_result`: Tool execution completed
- `ui_action`: UI tool to execute on frontend
- `complete`: Query processing finished
- `error`: Error occurred

## 🎯 Key Technologies

### Backend
- **FastAPI**: Modern async Python web framework
- **WebSockets**: Real-time bidirectional communication
- **OpenAI API**: LLM with function calling
- **Chain of Thought Agent**: From the main AiCot project

### Frontend
- **React 18**: UI framework
- **TypeScript**: Type-safe JavaScript
- **Tailwind CSS**: Utility-first CSS framework
- **Vite**: Lightning-fast build tool
- **Lucide React**: Beautiful icon library

## 🔍 Advanced Features

### Real-time Reasoning Visualization
Watch the AI think! Each reasoning step is streamed and displayed in real-time with visual indicators.

### Tool Execution Tracking
See exactly which tools are called, with what arguments, and their results - all in a beautiful, color-coded UI.

### Accessibility
High contrast mode can be toggled both manually through settings AND by asking the AI to enable it.

### Dynamic Theming
8 beautiful color themes that can be changed on-the-fly, either manually or via AI commands.

## 🐛 Troubleshooting

### Backend won't start
- Ensure `OPENAI_API_KEY` is set
- Check Python version (`python --version` should be 3.12+)
- Verify all dependencies are installed

### Frontend won't connect
- Ensure backend is running on port 8000
- Check browser console for WebSocket errors
- Verify CORS settings in `server.py`

### Tools not executing
- Check browser console for errors
- Verify OpenAI API key has sufficient credits
- Check backend logs for error messages

## 🎓 Learning Points

This demo showcases:

1. **Tool Inference**: How LLMs understand natural language and map it to specific function calls
2. **Multi-tool Orchestration**: LLMs can call multiple tools in sequence or parallel
3. **Hybrid Execution**: Some tools execute server-side, others client-side
4. **Real-time Streaming**: WebSocket enables live updates as the agent reasons
5. **Separation of Concerns**: Tool definitions on backend, execution can be anywhere

## 📝 License

Part of the AiCot project - exploring LLM reasoning patterns.

## 🤝 Contributing

This is a demonstration project. Feel free to extend with:
- More UI tools (font size, layout changes, etc.)
- More backend tools (database queries, API calls, etc.)
- Different reasoning patterns (ReAct, Tree of Thought, etc.)

---

**Built with ❤️ to demonstrate the power of LLM tool calling**
