#!/bin/bash

echo "🎨 Starting LLM Agent Frontend..."
echo ""

# Navigate to frontend directory
cd "$(dirname "$0")/frontend"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

echo "✅ Starting Vite development server on http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the development server
npm run dev
