import openai
import json
import os
from typing import List, Dict, Any
from datetime import datetime

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ReActAgent:
    """
    ReAct (Reasoning and Acting) Agent using OpenAI's new Responses API.
    ReAct interleaves reasoning (Thought) with actions (Action) and observations.
    The Responses API is stateful and handles conversation management automatically.
    """
    
    def __init__(self, model: str = "gpt-4o"):
        self.model = model
        self.memory: List[Dict[str, Any]] = []
        self.conversation_history: List[Dict[str, str]] = []
        self.response_id = None  # Track previous response for conversation continuity
        
    def get_tools_config(self) -> List[Dict]:
        """Define custom tools for the agent"""
        return [
            {
                "type": "function",
                "name": "calculator",
                "description": "Performs basic arithmetic operations. Use this for any mathematical calculations.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "Mathematical expression to evaluate, e.g., '2 + 2' or '10 * 5'"
                        }
                    },
                    "required": ["expression"]
                }
            },
            {
                "type": "function",
                "name": "search_knowledge",
                "description": "Searches a knowledge base for information about various topics",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "type": "function",
                "name": "get_current_date",
                "description": "Returns the current date and time",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool and return the result as a JSON string"""
        
        if tool_name == "calculator":
            try:
                # Safe evaluation
                result = eval(arguments["expression"], {"__builtins__": {}}, {})
                return json.dumps({
                    "success": True,
                    "result": result,
                    "expression": arguments["expression"]
                })
            except Exception as e:
                return json.dumps({
                    "success": False,
                    "error": str(e)
                })
        
        elif tool_name == "search_knowledge":
            # Simulated knowledge base
            knowledge_base = {
                "python": "Python is a high-level programming language created by Guido van Rossum, first released in 1991. Known for its readability and versatility.",
                "ai": "Artificial Intelligence (AI) involves creating systems that can perform tasks requiring human intelligence, such as learning, reasoning, and problem-solving.",
                "openai": "OpenAI is an AI research company founded in 2015 that created GPT models, ChatGPT, and various AI tools.",
                "javascript": "JavaScript is a programming language commonly used for web development, created in 1995 by Brendan Eich.",
            }
            
            query = arguments["query"].lower()
            for key, value in knowledge_base.items():
                if key in query:
                    return json.dumps({
                        "found": True,
                        "topic": key,
                        "info": value
                    })
            
            return json.dumps({
                "found": False,
                "message": "No relevant information found in knowledge base"
            })
        
        elif tool_name == "get_current_date":
            current = datetime.now()
            return json.dumps({
                "date": current.strftime('%Y-%m-%d'),
                "time": current.strftime('%H:%M:%S'),
                "full_datetime": current.strftime('%Y-%m-%d %H:%M:%S'),
                "year": current.year
            })
        
        return json.dumps({"error": "Tool not found"})
    
    def get_system_instructions(self) -> str:
        """System instructions that implement the ReAct (Reasoning and Acting) pattern"""
        return """You are a helpful AI agent that uses the ReAct (Reasoning and Acting) framework.

CRITICAL: Follow this ReAct loop for EVERY request:

The ReAct pattern consists of repeating cycles of:
1. Thought: Reason about the current situation
2. Action: Take an action using available tools
3. Observation: Observe the result of the action

REACT LOOP:

**Thought**: Start by reasoning about what you need to do.
   - What is the current state?
   - What information do I have?
   - What do I need to find out next?
   - Which tool should I use?

**Action**: Take ONE specific action by calling a tool.
   - Call only ONE tool at a time
   - Be specific with tool arguments
   - Wait for the observation before proceeding

**Observation**: After receiving tool results, you will observe the outcome.
   - What did the tool return?
   - Does this answer the question?
   - What should I do next?

Repeat the Thought → Action → Observation cycle until you can answer the user's question.

**Final Answer**: When you have enough information, provide the final answer.
   - State your conclusion clearly
   - Reference the observations you made
   - Be concise and direct

IMPORTANT:
- Always start with a Thought before taking an Action
- Use tools one at a time - don't batch multiple tool calls
- After each tool result, think about what you learned
- Stop when you have enough information to answer confidently
- Be explicit about your reasoning in each Thought"""
    
    def run(self, user_query: str, store_conversation: bool = False) -> Dict[str, Any]:
        """
        Main agent loop using Responses API.
        
        Args:
            user_query: The user's question or request
            store_conversation: If True, OpenAI stores conversation state server-side
        """
        print(f"\n{'='*70}")
        print(f"USER QUERY: {user_query}")
        print(f"{'='*70}\n")
        
        iteration = 0
        max_iterations = 10
        
        # Prepare input - can be a simple string or list of messages
        input_data = user_query
        
        # If we have previous conversation history and not using server-side storage
        if self.conversation_history and not store_conversation:
            input_data = self.conversation_history + [
                {"role": "user", "content": user_query}
            ]
        
        while iteration < max_iterations:
            iteration += 1
            print(f"\n{'='*70}")
            print(f"ITERATION {iteration}")
            print(f"{'='*70}\n")
            
            try:
                # Create response with Responses API
                response_params = {
                    "model": self.model,
                    "input": input_data,
                    "instructions": self.get_system_instructions(),
                    "tools": self.get_tools_config(),
                    "store": store_conversation,  # Server-side conversation storage
                }
                
                # Include previous_response_id for conversation continuity only if using server-side storage
                if store_conversation and self.response_id:
                    response_params["previous_response_id"] = self.response_id
                
                response = client.responses.create(**response_params)
                
                # Store response ID for next iteration
                self.response_id = response.id
                
                # Process output items
                has_tool_calls = False
                assistant_message = ""
                tool_calls_to_execute = []

                print("🤖 REACT CYCLE:")

                for item in response.output:
                    # Handle message output (Thought)
                    if item.type == "message":
                        for content_item in item.content:
                            if hasattr(content_item, 'text'):
                                text = content_item.text
                                assistant_message += text
                                print(f"\n💭 Thought:\n{text}")

                    # Handle function calls
                    elif item.type == "function_call":
                        has_tool_calls = True
                        tool_calls_to_execute.append({
                            'id': item.call_id,
                            'name': item.name,
                            'arguments': json.loads(item.arguments)
                        })
                
                # Store this iteration in memory
                step = {
                    "iteration": iteration,
                    "thought": assistant_message,
                    "tool_calls": [],
                    "response_id": response.id
                }
                
                # Execute tool calls if any (Action step)
                if has_tool_calls:
                    print(f"\n{'='*70}")
                    print(f"⚡ ACTION: Executing {len(tool_calls_to_execute)} tool(s)")
                    print(f"{'='*70}")

                    tool_results = []

                    for tool_call in tool_calls_to_execute:
                        tool_name = tool_call['name']
                        tool_args = tool_call['arguments']
                        tool_id = tool_call['id']

                        print(f"\n  📌 Action: {tool_name}")
                        print(f"     Args: {json.dumps(tool_args, indent=6)}")

                        # Execute the tool
                        result = self.execute_tool(tool_name, tool_args)
                        print(f"\n  👁️  Observation: {result}")
                        
                        # Store in memory
                        step["tool_calls"].append({
                            "tool": tool_name,
                            "arguments": tool_args,
                            "result": result
                        })
                        
                        # Prepare result for next API call
                        tool_results.append({
                            "type": "function_call_output",
                            "call_id": tool_id,
                            "output": result
                        })
                    
                    # Update input for next iteration with tool results
                    # Just send tool results directly as input
                    input_data = tool_results
                    
                    step["status"] = "tools_executed"
                    self.memory.append(step)
                    
                    # Continue to next iteration to get model's response to tool results
                    continue
                
                else:
                    # No tool calls - we have the final answer
                    step["status"] = "completed"
                    self.memory.append(step)
                    
                    print(f"\n{'='*70}")
                    print("✅ TASK COMPLETED")
                    print(f"{'='*70}\n")
                    
                    # Extract final answer
                    final_answer = assistant_message
                    
                    return {
                        "answer": final_answer,
                        "reasoning_trace": self.memory,
                        "iterations": iteration,
                        "response_id": response.id,
                        "usage": {
                            "input_tokens": response.usage.input_tokens,
                            "output_tokens": response.usage.output_tokens,
                            "total_tokens": response.usage.total_tokens
                        }
                    }
            
            except Exception as e:
                print(f"\n❌ Error in iteration {iteration}: {str(e)}")
                return {
                    "answer": f"Error occurred: {str(e)}",
                    "reasoning_trace": self.memory,
                    "iterations": iteration,
                    "error": str(e)
                }
        
        # Max iterations reached
        print(f"\n⚠️ Max iterations ({max_iterations}) reached")
        return {
            "answer": "Task incomplete - max iterations reached",
            "reasoning_trace": self.memory,
            "iterations": iteration
        }
    
    def print_reasoning_trace(self):
        """Pretty print the complete ReAct trace"""
        print(f"\n{'='*70}")
        print("COMPLETE REACT TRACE")
        print(f"{'='*70}\n")

        for step in self.memory:
            print(f"📍 Cycle {step['iteration']} ({step['status']})")
            print(f"   Response ID: {step.get('response_id', 'N/A')}")

            if step['thought']:
                # Truncate long thoughts
                thought = step['thought']
                if len(thought) > 200:
                    thought = thought[:200] + "..."
                print(f"   💭 Thought: {thought}")

            if step['tool_calls']:
                print(f"   ⚡ Actions taken: {len(step['tool_calls'])}")
                for i, tool_call in enumerate(step['tool_calls'], 1):
                    print(f"      {i}. Action: {tool_call['tool']}({tool_call['arguments']})")
                    print(f"         👁️  Observation: {tool_call['result']}")

            print()
    
    def reset(self):
        """Reset conversation state"""
        self.memory = []
        self.conversation_history = []
        self.response_id = None


# Example usage
def main():
    print("\n" + "="*70)
    print("REACT AGENT WITH RESPONSES API")
    print("="*70)

    # Example 1: Multi-step reasoning with calculations
    print("\n" + "="*70)
    print("EXAMPLE 1: Multi-step mathematical problem")
    print("="*70)

    agent = ReActAgent(model="gpt-4o")
    
    result = agent.run(
        "If I have 15 apples and I buy 3 more bags with 8 apples each, "
        "then give away half of my apples, how many do I have left? "
        "Use the ReAct pattern: think about what you need to calculate, "
        "then use the calculator tool for each step.",
        store_conversation=True  # Use server-side conversation storage
    )
    
    print(f"\n{'='*70}")
    print("📊 FINAL RESULT")
    print(f"{'='*70}")
    print(f"Answer: {result['answer']}")
    print(f"Iterations: {result['iterations']}")
    print(f"Response ID: {result.get('response_id', 'N/A')}")
    if 'usage' in result:
        print(f"Tokens: {result['usage']['total_tokens']} "
              f"(in: {result['usage']['input_tokens']}, "
              f"out: {result['usage']['output_tokens']})")
    
    agent.print_reasoning_trace()
    
    # Example 2: Information gathering with multiple tools
    print("\n" + "="*70)
    print("EXAMPLE 2: Multi-tool information gathering")
    print("="*70)

    agent2 = ReActAgent(model="gpt-4o")

    result2 = agent2.run(
        "What is Python programming language? What's today's date? "
        "Then tell me: was Python created more than 30 years ago from today? "
        "Use the ReAct pattern to gather information step by step.",
        store_conversation=True
    )
    
    print(f"\n{'='*70}")
    print("📊 FINAL RESULT")
    print(f"{'='*70}")
    print(f"Answer: {result2['answer']}")
    print(f"Iterations: {result2['iterations']}")
    if 'usage' in result2:
        print(f"Tokens: {result2['usage']['total_tokens']}")
    
    agent2.print_reasoning_trace()
    
    # Example 3: Using server-side conversation storage
    print("\n" + "="*70)
    print("EXAMPLE 3: Server-side conversation storage")
    print("="*70)

    agent3 = ReActAgent(model="gpt-4o")

    result3 = agent3.run(
        "Calculate 15 + 27, then multiply the result by 3. "
        "Think, act, and observe at each step.",
        store_conversation=True  # Let OpenAI handle conversation state
    )
    
    print(f"\n{'='*70}")
    print("📊 FINAL RESULT")
    print(f"{'='*70}")
    print(f"Answer: {result3['answer']}")
    print(f"Stored Response ID: {result3.get('response_id')}")
    print("(This response ID can be used in future conversations)")


if __name__ == "__main__":
    main()