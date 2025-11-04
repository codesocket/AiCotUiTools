import openai
import json
import os
from typing import List, Dict, Any
from datetime import datetime

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ChainOfThoughtAgent:
    """
    Chain of Thought Agent using OpenAI's Responses API.
    This pattern encourages the model to reason step-by-step, showing its thinking process
    before arriving at a final answer. It breaks down complex reasoning into explicit,
    sequential steps that are visible to the user.
    The Responses API is stateful and handles conversation management automatically.
    """

    def __init__(self, model: str = "gpt-4o"):
        self.model = model
        self.memory: List[Dict[str, Any]] = []
        self.reasoning_steps: List[Dict[str, Any]] = []  # Store the reasoning chain
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
        """System instructions that implement the Chain of Thought pattern"""
        return """You are a helpful AI agent that uses Chain of Thought reasoning to solve problems.

When given a problem or question, you should:

1. Think step-by-step, showing your reasoning process explicitly
2. Break down complex problems into clear, logical steps
3. Use available tools when needed for calculations, information lookup, or getting current data
4. Show intermediate results and how they lead to the next step
5. Explain your thought process as you work through the problem
6. Arrive at a final answer based on your step-by-step reasoning

Format your response to clearly show:
- Each step of your reasoning (numbered or clearly marked)
- What you're thinking at each step
- When and why you're using tools
- How intermediate results connect to the final answer

Example structure:
"Let me think through this step by step:

Step 1: [Identify what we need to find]
Step 2: [Gather necessary information using tools if needed]
Step 3: [Perform calculations or analysis]
Step 4: [Draw conclusions from the results]

Therefore, the final answer is..."

Be clear, logical, and thorough in your reasoning. Show your work!"""

    def process_with_chain_of_thought(self, user_query: str) -> Dict[str, Any]:
        """
        Process the query using Chain of Thought reasoning.
        The agent will think step-by-step and use tools as needed.
        """
        print(f"\n🧠 APPLYING CHAIN OF THOUGHT REASONING...")

        prompt = f"""Let's solve this problem step by step: {user_query}

Think through this carefully, showing your reasoning at each step. Use the available tools when you need to calculate, search for information, or get the current date."""

        try:
            response = client.responses.create(
                model=self.model,
                input=prompt,
                instructions=self.get_system_instructions(),
                tools=self.get_tools_config()
            )

            reasoning_output = ""
            tool_calls_made = []
            step_number = 0

            # Process the response - may include multiple tool calls and reasoning
            for item in response.output:
                if item.type == "function_call":
                    step_number += 1
                    tool_name = item.name
                    tool_args = json.loads(item.arguments)

                    print(f"\n  📍 Step {step_number}: Using tool '{tool_name}'")
                    print(f"     Arguments: {json.dumps(tool_args, indent=4)}")

                    tool_result = self.execute_tool(tool_name, tool_args)
                    print(f"     Result: {tool_result}")

                    tool_calls_made.append({
                        "step": step_number,
                        "tool": tool_name,
                        "arguments": tool_args,
                        "result": tool_result
                    })

                    self.reasoning_steps.append({
                        "type": "tool_call",
                        "step": step_number,
                        "tool": tool_name,
                        "arguments": tool_args,
                        "result": tool_result
                    })

                elif item.type == "message":
                    for content_item in item.content:
                        if hasattr(content_item, 'text'):
                            reasoning_output += content_item.text

            # Store the reasoning text as well
            if reasoning_output:
                self.reasoning_steps.append({
                    "type": "reasoning",
                    "content": reasoning_output
                })

            print(f"\n✅ Chain of Thought reasoning completed with {len(tool_calls_made)} tool calls")

            return {
                "reasoning": reasoning_output,
                "tool_calls": tool_calls_made,
                "steps": len(self.reasoning_steps)
            }

        except Exception as e:
            print(f"❌ Error in Chain of Thought reasoning: {e}")
            return {
                "reasoning": f"Error occurred: {e}",
                "tool_calls": [],
                "error": str(e)
            }

    def run(self, user_query: str, store_conversation: bool = False) -> Dict[str, Any]:
        """
        Main Chain of Thought agent loop using Responses API.

        Args:
            user_query: The user's question or request
            store_conversation: If True, OpenAI stores conversation state server-side
        """
        print(f"\n{'='*70}")
        print(f"USER QUERY: {user_query}")
        print(f"{'='*70}\n")

        try:
            # Process the query with Chain of Thought reasoning
            result = self.process_with_chain_of_thought(user_query)

            if "error" in result:
                return {
                    "answer": result.get("reasoning", "Error occurred"),
                    "reasoning_steps": self.reasoning_steps,
                    "tool_calls": result.get("tool_calls", []),
                    "error": result["error"]
                }

            print(f"\n{'='*70}")
            print("✅ CHAIN OF THOUGHT REASONING COMPLETED")
            print(f"{'='*70}\n")

            return {
                "answer": result["reasoning"],
                "reasoning_steps": self.reasoning_steps,
                "tool_calls": result["tool_calls"],
                "num_steps": result["steps"]
            }

        except Exception as e:
            print(f"\n❌ Error in Chain of Thought reasoning: {str(e)}")
            return {
                "answer": f"Error occurred: {str(e)}",
                "reasoning_steps": self.reasoning_steps,
                "tool_calls": [],
                "error": str(e)
            }

    def print_execution_trace(self):
        """Pretty print the complete Chain of Thought reasoning trace"""
        print(f"\n{'='*70}")
        print("COMPLETE CHAIN OF THOUGHT REASONING TRACE")
        print(f"{'='*70}\n")

        if not self.reasoning_steps:
            print("No reasoning steps available")
            return

        print(f"🧠 Total Reasoning Steps: {len(self.reasoning_steps)}\n")

        for i, step in enumerate(self.reasoning_steps, 1):
            if step["type"] == "tool_call":
                print(f"Step {step['step']}: Tool Call - {step['tool']}")
                print(f"  Arguments: {json.dumps(step['arguments'], indent=2)}")
                print(f"  Result: {step['result']}\n")
            elif step["type"] == "reasoning":
                print(f"Reasoning Output:")
                print(f"  {step['content']}\n")

    def reset(self):
        """Reset conversation state"""
        self.memory = []
        self.reasoning_steps = []
        self.conversation_history = []
        self.response_id = None


# Example usage
def main():
    print("\n" + "="*70)
    print("CHAIN OF THOUGHT AGENT WITH RESPONSES API")
    print("="*70)

    # Example 1: Multi-step reasoning with calculations
    print("\n" + "="*70)
    print("EXAMPLE 1: Multi-step mathematical problem with Chain of Thought")
    print("="*70)

    agent = ChainOfThoughtAgent(model="gpt-4o")

    result = agent.run(
        "If I have 15 apples and I buy 3 more bags with 8 apples each, "
        "then give away half of my apples, how many do I have left?",
        store_conversation=True
    )

    print(f"\n{'='*70}")
    print("📊 FINAL RESULT")
    print(f"{'='*70}")
    print(f"Answer: {result['answer']}")
    print(f"Number of Reasoning Steps: {result.get('num_steps', 'N/A')}")
    print(f"Tool Calls Made: {len(result.get('tool_calls', []))}")

    agent.print_execution_trace()

    # Example 2: Information gathering with multiple tools
    print("\n" + "="*70)
    print("EXAMPLE 2: Multi-tool information gathering with Chain of Thought")
    print("="*70)

    agent2 = ChainOfThoughtAgent(model="gpt-4o")

    result2 = agent2.run(
        "What is Python programming language? What's today's date? "
        "Then tell me: was Python created more than 30 years ago from today?",
        store_conversation=True
    )

    print(f"\n{'='*70}")
    print("📊 FINAL RESULT")
    print(f"{'='*70}")
    print(f"Answer: {result2['answer']}")
    print(f"Number of Reasoning Steps: {result2.get('num_steps', 'N/A')}")
    print(f"Tool Calls Made: {len(result2.get('tool_calls', []))}")

    agent2.print_execution_trace()

    # Example 3: Complex problem requiring step-by-step reasoning
    print("\n" + "="*70)
    print("EXAMPLE 3: Complex problem with Chain of Thought reasoning")
    print("="*70)

    agent3 = ChainOfThoughtAgent(model="gpt-4o")

    result3 = agent3.run(
        "A store has a sale where everything is 20% off. If I buy a laptop for $800, "
        "a mouse for $25, and headphones for $75, what's my total after the discount? "
        "Also, if I pay with a $1000 bill, how much change do I get?",
        store_conversation=True
    )

    print(f"\n{'='*70}")
    print("📊 FINAL RESULT")
    print(f"{'='*70}")
    print(f"Answer: {result3['answer']}")
    print(f"Number of Reasoning Steps: {result3.get('num_steps', 'N/A')}")
    print(f"Tool Calls Made: {len(result3.get('tool_calls', []))}")

    # Show reasoning trace
    agent3.print_execution_trace()


if __name__ == "__main__":
    main()
