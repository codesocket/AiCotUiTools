"""
Enhanced Agent with UI tool support and WebSocket streaming
"""
import json
import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime
from fastapi import WebSocket
from openai import OpenAI
import os
import sys

# Configure logging
logger = logging.getLogger(__name__)

# Add parent directory to path to import the agent
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, parent_dir)

try:
    from main import ChainOfThoughtAgent
except ImportError as e:
    logger.error(f"Error importing ChainOfThoughtAgent: {e}")
    raise


class EnhancedAgent(ChainOfThoughtAgent):
    """Extended agent with UI tool support and WebSocket streaming"""

    def __init__(self, websocket: Optional[WebSocket] = None, model: str = "gpt-4o"):
        super().__init__(model)
        self.websocket = websocket
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.ui_tools: List[Dict] = []  # UI tools registered by client
        self.ui_tool_results: Dict[str, asyncio.Future] = {}  # Pending UI tool executions
        self.ui_state = {
            "theme_color": "#3b82f6",  # Default blue
            "high_contrast": False
        }

    def register_ui_tools(self, tools: List[Dict]):
        """Register UI tools sent from the frontend"""
        self.ui_tools = tools
        logger.info(f"Registered {len(tools)} UI tools: {[t['name'] for t in tools]}")

    async def send_message(self, message_type: str, data: Dict):
        """Send real-time updates via WebSocket"""
        if self.websocket:
            try:
                await self.websocket.send_json({
                    "type": message_type,
                    "data": data,
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error sending WebSocket message: {e}")

    def get_tools_config(self) -> List[Dict]:
        """Extended tools including dynamically registered UI tools"""
        backend_tools = super().get_tools_config()

        # Include UI tools registered by the client
        return backend_tools + self.ui_tools

    async def execute_tool_async(self, tool_name: str, arguments: Dict) -> str:
        """Execute both backend and UI tools (async version)"""

        # Check if this is a UI tool
        ui_tool_names = [tool['name'] for tool in self.ui_tools]
        if tool_name in ui_tool_names:
            # This is a UI tool - request execution from client
            logger.info(f"Requesting UI tool execution: {tool_name}")

            # Create a future to wait for the result
            result_future = asyncio.Future()
            self.ui_tool_results[tool_name] = result_future

            # Send execution request to client
            await self.send_message("execute_ui_tool", {
                "tool": tool_name,
                "arguments": arguments
            })

            # Wait for result from client (with timeout)
            try:
                result = await asyncio.wait_for(result_future, timeout=10.0)
                return result
            except asyncio.TimeoutError:
                return json.dumps({"error": f"UI tool '{tool_name}' execution timed out"})
            finally:
                # Clean up
                if tool_name in self.ui_tool_results:
                    del self.ui_tool_results[tool_name]

        # Backend tools - use parent class implementation
        else:
            return super().execute_tool(tool_name, arguments)

    def execute_tool(self, tool_name: str, arguments: Dict) -> str:
        """Execute both backend and UI tools (sync version for compatibility)"""
        logger.info(f"execute_tool called: {tool_name} with args: {arguments}")
        # This method is called by the parent class synchronously
        # For UI tools, we need to use the async version
        # Check if this is a UI tool
        ui_tool_names = [tool['name'] for tool in self.ui_tools]
        if tool_name in ui_tool_names:
            logger.info(f"{tool_name} is a UI tool, executing async")
            # Run async version in event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.execute_tool_async(tool_name, arguments))
            finally:
                loop.close()
        else:
            logger.info(f"{tool_name} is a backend tool, calling parent execute_tool")
            result = super().execute_tool(tool_name, arguments)
            logger.info(f"Backend tool {tool_name} returned: {result[:100]}...")
            return result

    def set_ui_tool_result(self, tool_name: str, result: str):
        """Set the result of a UI tool execution"""
        if tool_name in self.ui_tool_results:
            future = self.ui_tool_results[tool_name]
            if not future.done():
                future.set_result(result)

    async def process_with_chain_of_thought_streaming(self, query: str) -> Dict:
        """Process query with real-time WebSocket updates"""

        await self.send_message("status", {"message": "Processing query...", "stage": "start"})

        self.reasoning_steps = []
        system_instructions = self.get_system_instructions()
        tools = self.get_tools_config()

        try:
            # Add query to conversation history
            self.conversation_history.append({
                "role": "user",
                "content": query
            })

            await self.send_message("status", {"message": "Calling OpenAI API...", "stage": "api_call"})

            # Call OpenAI API
            response = self.client.responses.create(
                model=self.model,
                input=query,
                instructions=system_instructions,
                tools=tools
            )

            self.response_id = response.id
            reasoning_text = ""
            tool_calls_made = []

            await self.send_message("status", {"message": "Processing response...", "stage": "processing"})

            # Collect function call outputs to submit back
            function_outputs = []

            # Process response outputs
            for item in response.output:
                logger.info(f"Processing output item: {item.type}")
                if item.type == "function_call":
                    tool_name = item.name
                    call_id = item.id  # Get the call ID for submitting the result
                    logger.info(f"Function call detected: {tool_name} (call_id: {call_id})")
                    try:
                        arguments = json.loads(item.arguments)
                    except json.JSONDecodeError:
                        arguments = {"raw": item.arguments}

                    logger.info(f"Parsed arguments: {arguments}")

                    await self.send_message("tool_call", {
                        "tool": tool_name,
                        "arguments": arguments,
                        "stage": "executing"
                    })

                    # Execute tool (use async version for UI tools)
                    ui_tool_names = [tool['name'] for tool in self.ui_tools]
                    if tool_name in ui_tool_names:
                        logger.info(f"Executing UI tool: {tool_name}")
                        result = await self.execute_tool_async(tool_name, arguments)
                    else:
                        logger.info(f"Executing backend tool: {tool_name}")
                        result = self.execute_tool(tool_name, arguments)

                    logger.info(f"Tool execution result: {result[:200]}...")

                    # Check if it's a UI action
                    try:
                        result_json = json.loads(result)
                        if result_json.get("type") == "ui_action":
                            await self.send_message("ui_action", result_json)
                    except:
                        pass

                    tool_call_info = {
                        "tool": tool_name,
                        "arguments": arguments,
                        "result": result
                    }

                    tool_calls_made.append(tool_call_info)
                    self.reasoning_steps.append({
                        "type": "tool_call",
                        "data": tool_call_info
                    })

                    await self.send_message("tool_result", {
                        "tool": tool_name,
                        "result": result,
                        "stage": "completed"
                    })

                    # Collect function output to submit back to OpenAI
                    function_outputs.append({
                        "call_id": call_id,
                        "output": result
                    })

                elif item.type == "message":
                    if hasattr(item, 'content'):
                        for content_item in item.content:
                            if hasattr(content_item, 'text'):
                                text = content_item.text
                                reasoning_text += text + "\n"

                                self.reasoning_steps.append({
                                    "type": "reasoning",
                                    "text": text
                                })

                                await self.send_message("reasoning", {
                                    "text": text,
                                    "stage": "thinking"
                                })

            # If we have function outputs, we need to make a follow-up call with the results
            if function_outputs:
                logger.info(f"Making follow-up call with {len(function_outputs)} function results")
                await self.send_message("status", {"message": "Processing function results...", "stage": "continuing"})

                # Build a follow-up message with the function results
                follow_up_prompt = f"I called the tools and got these results:\n"
                for tc in tool_calls_made:
                    follow_up_prompt += f"\nTool: {tc['tool']}\nResult: {tc['result']}\n"
                follow_up_prompt += f"\nBased on these results, please provide a complete answer to: {query}"

                logger.info(f"Follow-up prompt: {follow_up_prompt[:200]}...")

                # Make another API call with the function results
                follow_up_response = self.client.responses.create(
                    model=self.model,
                    input=follow_up_prompt,
                    instructions=system_instructions,
                    tools=tools
                )

                # Process the follow-up response
                for item in follow_up_response.output:
                    logger.info(f"Processing follow-up output item: {item.type}")
                    if item.type == "message":
                        if hasattr(item, 'content'):
                            for content_item in item.content:
                                if hasattr(content_item, 'text'):
                                    text = content_item.text
                                    reasoning_text += text + "\n"

                                    self.reasoning_steps.append({
                                        "type": "reasoning",
                                        "text": text
                                    })

                                    await self.send_message("reasoning", {
                                        "text": text,
                                        "stage": "final_answer"
                                    })

            # Add assistant response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": reasoning_text.strip()
            })

            # Check if no tools were used
            no_tools_used = len(tool_calls_made) == 0
            if no_tools_used:
                logger.info("No tools were used for this query")
                await self.send_message("no_tools_used", {
                    "message": "I couldn't find any tools that match your request. I can help you with:",
                    "available_capabilities": [
                        "Calculations (e.g., 'What is 25 * 47?')",
                        "Knowledge search (e.g., 'Tell me about Python')",
                        "Current date/time (e.g., 'What's today's date?')",
                        "UI customization (e.g., 'Change theme to purple', 'Enable high contrast')"
                    ]
                })

            result = {
                "answer": reasoning_text.strip(),
                "reasoning_steps": self.reasoning_steps,
                "tool_calls": tool_calls_made,
                "num_steps": len(self.reasoning_steps),
                "ui_state": self.ui_state,
                "no_tools_used": no_tools_used
            }

            await self.send_message("complete", result)

            return result

        except Exception as e:
            error_msg = f"Error during processing: {str(e)}"
            await self.send_message("error", {"message": error_msg})
            return {
                "answer": "",
                "reasoning_steps": self.reasoning_steps,
                "tool_calls": [],
                "num_steps": len(self.reasoning_steps),
                "error": error_msg
            }
