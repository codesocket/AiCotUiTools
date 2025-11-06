"""
WebSocket Connection Manager
"""
import logging
from typing import Dict, Optional
from fastapi import WebSocket

from enhanced_agent import EnhancedAgent

# Configure logging
logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manage WebSocket connections and their associated agents"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.agents: Dict[str, EnhancedAgent] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept a new WebSocket connection and create an agent for it"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.agents[client_id] = EnhancedAgent(websocket=websocket)
        logger.info(f"Client {client_id} connected")

    def disconnect(self, client_id: str):
        """Remove a client connection and its agent"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.agents:
            del self.agents[client_id]
        logger.info(f"Client {client_id} disconnected")

    def get_agent(self, client_id: str) -> Optional[EnhancedAgent]:
        """Get the agent associated with a client ID"""
        return self.agents.get(client_id)
