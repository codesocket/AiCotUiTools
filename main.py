import openai
import json
import os
from typing import List, Dict, Any
from datetime import datetime

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class TaskDecompositionAgent:
    """
    Task Decomposition Agent using OpenAI's Responses API.
    This pattern breaks down complex problems into smaller, manageable subtasks,
    executes them sequentially, and combines results to solve the original problem.
    The Responses API is stateful and handles conversation management automatically.
    """

    def __init__(self, model: str = "gpt-4o", max_subtasks: int = 5):
        self.model = model
        self.max_subtasks = max_subtasks  # Maximum number of subtasks to decompose into
        self.memory: List[Dict[str, Any]] = []
        self.task_plan: Dict[str, Any] = {}  # Store the complete task decomposition plan
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

    def get_system_instructions(self, mode: str = "decompose") -> str:
        """System instructions that implement the Task Decomposition pattern"""
        if mode == "decompose":
            return f"""You are a helpful AI agent that uses Task Decomposition to solve complex problems.

Your task is to break down the given problem into a sequence of {self.max_subtasks} or fewer subtasks.
Each subtask should be:
1. Clear and specific
2. Achievable with available tools or reasoning
3. Build upon previous subtasks sequentially

Format your response as a JSON object:
{{
  "analysis": "Brief analysis of the problem",
  "subtasks": [
    {{
      "id": 1,
      "description": "Clear description of the subtask",
      "tool_needed": "calculator|search_knowledge|get_current_date|reasoning",
      "depends_on": []
    }},
    {{
      "id": 2,
      "description": "Next subtask",
      "tool_needed": "calculator",
      "depends_on": [1]
    }}
  ],
  "final_step": "How to combine results to answer the original question"
}}

Be logical and efficient in your decomposition."""

        elif mode == "execute":
            return """You are a helpful AI agent executing a specific subtask.

Use the available tools to complete the subtask.
Provide clear output about what you've done and what result you obtained.
If the subtask requires reasoning without tools, provide your analysis."""

        else:  # synthesize mode
            return """You are a helpful AI agent synthesizing results from multiple subtasks.

Review the completed subtasks and their results.
Combine them to provide a comprehensive final answer to the original question.
Ensure your answer is clear, complete, and addresses all aspects of the question."""

    def decompose_task(self, user_query: str) -> Dict[str, Any]:
        """Decompose the user's query into subtasks"""
        print(f"\n📋 DECOMPOSING TASK INTO SUBTASKS...")

        prompt = f"""Problem to solve: {user_query}

Break this problem down into a sequence of subtasks that can be executed step by step.
Consider what information is needed and in what order."""

        try:
            response = client.responses.create(
                model=self.model,
                input=prompt,
                instructions=self.get_system_instructions(mode="decompose"),
                tools=self.get_tools_config()
            )

            # Extract the response text
            response_text = ""
            for item in response.output:
                if item.type == "message":
                    for content_item in item.content:
                        if hasattr(content_item, 'text'):
                            response_text += content_item.text

            # Try to parse JSON from response
            import re
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                task_plan = json.loads(json_match.group())
                print(f"✅ Decomposed into {len(task_plan.get('subtasks', []))} subtasks")
                print(f"\n📊 Analysis: {task_plan.get('analysis', 'N/A')}")

                for subtask in task_plan.get('subtasks', []):
                    print(f"\n  Subtask {subtask.get('id')}:")
                    print(f"    - Description: {subtask.get('description')}")
                    print(f"    - Tool needed: {subtask.get('tool_needed', 'N/A')}")
                    print(f"    - Depends on: {subtask.get('depends_on', [])}")

                print(f"\n  Final step: {task_plan.get('final_step', 'N/A')}")
                return task_plan
            else:
                print("⚠️ Could not parse JSON, using fallback")
                return {
                    "analysis": "Could not decompose properly",
                    "subtasks": [{
                        "id": 1,
                        "description": user_query,
                        "tool_needed": "reasoning",
                        "depends_on": []
                    }],
                    "final_step": "Provide direct answer"
                }

        except Exception as e:
            print(f"❌ Error decomposing task: {e}")
            return {
                "analysis": f"Error: {e}",
                "subtasks": [],
                "final_step": "Error occurred"
            }

    def execute_subtask(self, subtask: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single subtask"""
        subtask_id = subtask.get('id', 0)
        description = subtask.get('description', '')
        tool_needed = subtask.get('tool_needed', 'reasoning')

        print(f"\n⚡ EXECUTING SUBTASK {subtask_id}: {description}")

        # Build context from previous subtasks
        context_str = "Previous results:\n"
        for prev_id, prev_result in context.items():
            context_str += f"Subtask {prev_id}: {prev_result.get('output', 'N/A')}\n"

        prompt = f"""Execute this subtask: {description}

{context_str}

Use the appropriate tool or provide reasoning to complete this subtask."""

        try:
            response = client.responses.create(
                model=self.model,
                input=prompt,
                instructions=self.get_system_instructions(mode="execute"),
                tools=self.get_tools_config()
            )

            result = {
                "subtask_id": subtask_id,
                "description": description,
                "output": "",
                "tool_used": None,
                "tool_result": None
            }

            # Process response - look for tool calls and text
            for item in response.output:
                if item.type == "function_call":
                    tool_name = item.name
                    tool_args = json.loads(item.arguments)
                    print(f"  🔧 Using tool: {tool_name}")
                    print(f"  📝 Arguments: {json.dumps(tool_args, indent=4)}")

                    tool_result = self.execute_tool(tool_name, tool_args)
                    print(f"  ✅ Result: {tool_result}")

                    result["tool_used"] = tool_name
                    result["tool_result"] = tool_result
                    result["output"] = tool_result

                elif item.type == "message":
                    for content_item in item.content:
                        if hasattr(content_item, 'text'):
                            result["output"] += content_item.text

            if not result["output"]:
                result["output"] = "No output generated"

            print(f"  ✅ Subtask {subtask_id} completed")
            return result

        except Exception as e:
            print(f"  ❌ Error executing subtask {subtask_id}: {e}")
            return {
                "subtask_id": subtask_id,
                "description": description,
                "output": f"Error: {e}",
                "error": str(e)
            }

    def synthesize_results(self, user_query: str, task_plan: Dict[str, Any],
                          results: List[Dict[str, Any]]) -> str:
        """Synthesize all subtask results into a final answer"""
        print(f"\n🔄 SYNTHESIZING FINAL ANSWER...")

        results_str = json.dumps(results, indent=2)

        prompt = f"""Original question: {user_query}

Task decomposition plan:
{json.dumps(task_plan, indent=2)}

Completed subtasks and their results:
{results_str}

Based on all the subtask results, provide a comprehensive final answer to the original question."""

        try:
            response = client.responses.create(
                model=self.model,
                input=prompt,
                instructions=self.get_system_instructions(mode="synthesize")
            )

            final_answer = ""
            for item in response.output:
                if item.type == "message":
                    for content_item in item.content:
                        if hasattr(content_item, 'text'):
                            final_answer += content_item.text

            print(f"✅ Final answer synthesized")
            return final_answer

        except Exception as e:
            print(f"❌ Error synthesizing results: {e}")
            return f"Error synthesizing results: {e}"

    def run(self, user_query: str, store_conversation: bool = False) -> Dict[str, Any]:
        """
        Main Task Decomposition agent loop using Responses API.

        Args:
            user_query: The user's question or request
            store_conversation: If True, OpenAI stores conversation state server-side
        """
        print(f"\n{'='*70}")
        print(f"USER QUERY: {user_query}")
        print(f"{'='*70}\n")

        try:
            # Step 1: Decompose the task into subtasks
            task_plan = self.decompose_task(user_query)
            self.task_plan = task_plan

            if not task_plan.get('subtasks'):
                return {
                    "answer": "Could not decompose task into subtasks",
                    "task_plan": task_plan,
                    "results": [],
                    "error": "No subtasks generated"
                }

            # Step 2: Execute subtasks sequentially
            print(f"\n{'='*70}")
            print(f"EXECUTING {len(task_plan['subtasks'])} SUBTASKS")
            print(f"{'='*70}\n")

            results = []
            context = {}  # Store results of completed subtasks

            for subtask in task_plan['subtasks']:
                result = self.execute_subtask(subtask, context)
                results.append(result)
                context[subtask.get('id')] = result

            # Step 3: Synthesize final answer
            print(f"\n{'='*70}")
            print("SYNTHESIS PHASE")
            print(f"{'='*70}\n")

            final_answer = self.synthesize_results(user_query, task_plan, results)

            print(f"\n{'='*70}")
            print("✅ TASK DECOMPOSITION COMPLETED")
            print(f"{'='*70}\n")

            return {
                "answer": final_answer,
                "task_plan": task_plan,
                "results": results,
                "num_subtasks": len(task_plan['subtasks'])
            }

        except Exception as e:
            print(f"\n❌ Error in task decomposition: {str(e)}")
            return {
                "answer": f"Error occurred: {str(e)}",
                "task_plan": self.task_plan,
                "results": [],
                "error": str(e)
            }

    def print_execution_trace(self):
        """Pretty print the complete Task Decomposition trace"""
        print(f"\n{'='*70}")
        print("COMPLETE TASK DECOMPOSITION TRACE")
        print(f"{'='*70}\n")

        if not self.task_plan:
            print("No task plan available")
            return

        print(f"📋 Task Plan Analysis: {self.task_plan.get('analysis', 'N/A')}\n")

        print(f"📝 Decomposed Subtasks ({len(self.task_plan.get('subtasks', []))}):")
        for subtask in self.task_plan.get('subtasks', []):
            print(f"\n  {subtask.get('id')}. {subtask.get('description')}")
            print(f"     Tool needed: {subtask.get('tool_needed', 'N/A')}")
            print(f"     Dependencies: {subtask.get('depends_on', [])}")

        print(f"\n🎯 Final Step: {self.task_plan.get('final_step', 'N/A')}")

    def reset(self):
        """Reset conversation state"""
        self.memory = []
        self.task_plan = {}
        self.conversation_history = []
        self.response_id = None


# Example usage
def main():
    print("\n" + "="*70)
    print("TASK DECOMPOSITION AGENT WITH RESPONSES API")
    print("="*70)

    # Example 1: Multi-step reasoning with calculations
    print("\n" + "="*70)
    print("EXAMPLE 1: Multi-step mathematical problem with Task Decomposition")
    print("="*70)

    agent = TaskDecompositionAgent(model="gpt-4o", max_subtasks=5)

    result = agent.run(
        "If I have 15 apples and I buy 3 more bags with 8 apples each, "
        "then give away half of my apples, how many do I have left?",
        store_conversation=True
    )

    print(f"\n{'='*70}")
    print("📊 FINAL RESULT")
    print(f"{'='*70}")
    print(f"Answer: {result['answer']}")
    print(f"Number of Subtasks: {result.get('num_subtasks', 'N/A')}")

    agent.print_execution_trace()

    # Example 2: Information gathering with multiple tools
    print("\n" + "="*70)
    print("EXAMPLE 2: Multi-tool information gathering with Task Decomposition")
    print("="*70)

    agent2 = TaskDecompositionAgent(model="gpt-4o", max_subtasks=5)

    result2 = agent2.run(
        "What is Python programming language? What's today's date? "
        "Then tell me: was Python created more than 30 years ago from today?",
        store_conversation=True
    )

    print(f"\n{'='*70}")
    print("📊 FINAL RESULT")
    print(f"{'='*70}")
    print(f"Answer: {result2['answer']}")
    print(f"Number of Subtasks: {result2.get('num_subtasks', 'N/A')}")

    agent2.print_execution_trace()

    # Example 3: Complex problem requiring systematic breakdown
    print("\n" + "="*70)
    print("EXAMPLE 3: Complex problem with systematic task breakdown")
    print("="*70)

    agent3 = TaskDecompositionAgent(model="gpt-4o", max_subtasks=6)

    result3 = agent3.run(
        "I need to plan a data science project. What are the key steps? "
        "Break it down systematically and provide a comprehensive plan.",
        store_conversation=True
    )

    print(f"\n{'='*70}")
    print("📊 FINAL RESULT")
    print(f"{'='*70}")
    print(f"Answer: {result3['answer']}")
    print(f"Number of Subtasks: {result3.get('num_subtasks', 'N/A')}")

    # Show task plan
    if 'task_plan' in result3 and 'subtasks' in result3['task_plan']:
        print(f"\n📍 Task decomposition breakdown:")
        for subtask in result3['task_plan']['subtasks']:
            print(f"  {subtask.get('id')}. {subtask.get('description')}")


if __name__ == "__main__":
    main()
