#!/bin/bash

echo "🚀 Starting LLM Agent Backend Server..."
echo ""

# Check if OPENAI_API_KEY is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ Error: OPENAI_API_KEY environment variable is not set"
    echo "Please set it with: export OPENAI_API_KEY='your-api-key-here'"
    exit 1
fi

# Navigate to backend directory
cd "$(dirname "$0")/backend"

# Check if requirements are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "📦 Installing backend dependencies..."
    pip install -r requirements.txt
fi

echo "✅ Starting FastAPI server on http://localhost:8000"
echo "📡 WebSocket endpoint: ws://localhost:8000/ws/{client_id}"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
python server.py
