"""
WebSocket-enabled FastAPI server for LLM Agent with UI and Backend Tools
"""
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import os
import sys

from enhanced_agent import EnhancedAgent
from connection_manager import ConnectionManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add parent directory to path to import the agent
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, parent_dir)

try:
    from main import ChainOfThoughtAgent
except ImportError as e:
    logger.error(f"Error importing ChainOfThoughtAgent: {e}")
    logger.error(f"Python path: {sys.path}")
    logger.error(f"Current directory: {os.getcwd()}")
    logger.error(f"Parent directory: {parent_dir}")
    raise

app = FastAPI(title="LLM Agent WebSocket Server")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

manager = ConnectionManager()


@app.get("/")
async def root():
    return {
        "message": "LLM Agent WebSocket Server",
        "version": "1.0.0",
        "endpoints": {
            "websocket": "/ws/{client_id}",
            "health": "/health"
        }
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "active_connections": len(manager.active_connections)
    }


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    try:
        await manager.connect(websocket, client_id)
        logger.info(f"Client {client_id} connected successfully")

        # Send initial connection message
        await websocket.send_json({
            "type": "connected",
            "data": {
                "client_id": client_id,
                "message": "Connected to LLM Agent",
                "available_tools": {
                    "backend": ["calculator", "search_knowledge", "get_current_date"],
                    "ui": ["change_theme_color", "enable_high_contrast"]
                }
            },
            "timestamp": datetime.now().isoformat()
        })
        logger.info(f"Sent connection message to client {client_id}")

        while True:
            # Receive message from client
            data = await websocket.receive_json()
            message_type = data.get("type")
            logger.info(f"Received message from {client_id}: {message_type}")

            if message_type == "register_ui_tools":
                # Client is registering its UI tools
                tools = data.get("tools", [])
                agent = manager.get_agent(client_id)
                if agent:
                    agent.register_ui_tools(tools)
                    logger.info(f"Registered {len(tools)} UI tools for client {client_id}")

            elif message_type == "ui_tool_result":
                # Client is returning the result of a UI tool execution
                tool_name = data.get("tool")
                result = data.get("result")
                agent = manager.get_agent(client_id)
                if agent:
                    agent.set_ui_tool_result(tool_name, result)
                    logger.info(f"Received UI tool result for {tool_name}")

            elif message_type == "ui_tool_error":
                # Client had an error executing a UI tool
                tool_name = data.get("tool")
                error = data.get("error")
                agent = manager.get_agent(client_id)
                if agent:
                    error_result = json.dumps({"error": error})
                    agent.set_ui_tool_result(tool_name, error_result)
                    logger.error(f"UI tool error for {tool_name}: {error}")

            elif message_type == "query":
                query = data.get("query", "")
                agent = manager.get_agent(client_id)

                if agent and query:
                    # Process query with streaming updates
                    logger.info(f"Processing query: {query}")
                    await agent.process_with_chain_of_thought_streaming(query)

            elif message_type == "reset":
                agent = manager.get_agent(client_id)
                if agent:
                    agent.reset()
                    await websocket.send_json({
                        "type": "reset_complete",
                        "data": {"message": "Agent reset successfully"},
                        "timestamp": datetime.now().isoformat()
                    })

            elif message_type == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })

    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected normally")
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        manager.disconnect(client_id)


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting LLM Agent WebSocket Server...")
    logger.info("WebSocket endpoint: ws://localhost:8000/ws/{client_id}")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
