#!/usr/bin/env python3
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws/test-client-123"
    try:
        async with websockets.connect(uri) as websocket:
            print(f"Connected to {uri}")

            # Wait for initial message
            message = await websocket.recv()
            print(f"Received: {message}")

            # Send a ping
            await websocket.send(json.dumps({"type": "ping"}))
            print("Sent ping")

            # Wait for pong
            response = await websocket.recv()
            print(f"Received: {response}")

    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_websocket())
