import openai
import json
import os
from typing import List, Dict, Any
from datetime import datetime

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class TreeOfThoughtAgent:
    """
    Tree of Thought (ToT) Agent using OpenAI's new Responses API.
    ToT explores multiple reasoning paths simultaneously, evaluates them,
    and selects the most promising path to continue exploration.
    The Responses API is stateful and handles conversation management automatically.
    """

    def __init__(self, model: str = "gpt-4o", num_thoughts: int = 3, depth_limit: int = 3):
        self.model = model
        self.num_thoughts = num_thoughts  # Number of candidate thoughts to generate
        self.depth_limit = depth_limit    # Maximum depth of thought tree
        self.memory: List[Dict[str, Any]] = []
        self.thought_tree: Dict[str, Any] = {}  # Store the complete thought tree
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
    
    def get_system_instructions(self, mode: str = "generate") -> str:
        """System instructions that implement the Tree of Thought pattern"""
        if mode == "generate":
            return f"""You are a helpful AI agent that uses the Tree of Thought (ToT) framework.

CRITICAL: When asked to generate thoughts, provide {self.num_thoughts} DIFFERENT reasoning paths.

Your task is to generate {self.num_thoughts} distinct candidate thoughts for solving the problem.
Each thought should represent a different approach or next step.

Format your response as a JSON array with {self.num_thoughts} objects, each containing:
- "thought": A clear reasoning step or approach
- "reasoning": Why this approach might work
- "next_action": What tool to use next (if any)

Example format:
[
  {{
    "thought": "First approach...",
    "reasoning": "This works because...",
    "next_action": "calculator"
  }},
  {{
    "thought": "Second approach...",
    "reasoning": "This is better because...",
    "next_action": "search_knowledge"
  }},
  {{
    "thought": "Third approach...",
    "reasoning": "Alternative method...",
    "next_action": null
  }}
]

Be creative and explore different reasoning paths."""

        elif mode == "evaluate":
            return """You are an AI evaluator that scores different reasoning paths.

Your task is to evaluate the given thoughts and score each one based on:
1. **Correctness**: Is the reasoning sound?
2. **Efficiency**: Does it lead to the goal quickly?
3. **Completeness**: Does it address the full problem?

Rate each thought on a scale of 0-10 and provide brief justification.

Format your response as a JSON array:
[
  {
    "thought_id": 0,
    "score": 8.5,
    "justification": "Strong reasoning but could be more efficient"
  },
  ...
]"""

        else:  # execute mode
            return """You are a helpful AI agent executing a specific reasoning path.

Follow the selected thought path and use the available tools to gather information.
After using tools, provide your observation and determine if you can answer the question.

If you have enough information, provide the final answer.
If not, indicate what additional information is needed."""

    def generate_thoughts(self, context: str) -> List[Dict[str, Any]]:
        """Generate multiple candidate thoughts for the current state"""
        print(f"\n🌳 GENERATING {self.num_thoughts} CANDIDATE THOUGHTS...")

        prompt = f"""Current problem/context: {context}

Generate {self.num_thoughts} different reasoning paths to solve this problem.
Each path should explore a different approach or strategy."""

        try:
            response = client.responses.create(
                model=self.model,
                input=prompt,
                instructions=self.get_system_instructions(mode="generate"),
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
            # Look for JSON array in the response
            import re
            json_match = re.search(r'\[[\s\S]*\]', response_text)
            if json_match:
                thoughts = json.loads(json_match.group())
                print(f"✅ Generated {len(thoughts)} thoughts")
                for i, thought in enumerate(thoughts):
                    print(f"\n  Thought {i+1}:")
                    print(f"    - Path: {thought.get('thought', 'N/A')[:100]}...")
                    print(f"    - Reasoning: {thought.get('reasoning', 'N/A')[:100]}...")
                return thoughts
            else:
                print("⚠️ Could not parse JSON, using fallback")
                return [{"thought": response_text, "reasoning": "Direct response", "next_action": None}]

        except Exception as e:
            print(f"❌ Error generating thoughts: {e}")
            return [{"thought": f"Error: {e}", "reasoning": "Fallback", "next_action": None}]

    def evaluate_thoughts(self, thoughts: List[Dict[str, Any]], context: str) -> List[Dict[str, Any]]:
        """Evaluate and score the generated thoughts"""
        print(f"\n📊 EVALUATING {len(thoughts)} THOUGHTS...")

        thoughts_str = json.dumps(thoughts, indent=2)
        prompt = f"""Problem context: {context}

Candidate thoughts to evaluate:
{thoughts_str}

Evaluate each thought and provide scores."""

        try:
            response = client.responses.create(
                model=self.model,
                input=prompt,
                instructions=self.get_system_instructions(mode="evaluate")
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
            json_match = re.search(r'\[[\s\S]*\]', response_text)
            if json_match:
                evaluations = json.loads(json_match.group())
                print(f"✅ Evaluated {len(evaluations)} thoughts")
                for eval_item in evaluations:
                    print(f"  Thought {eval_item.get('thought_id', 'N/A')}: Score {eval_item.get('score', 0)}/10")
                    print(f"    Justification: {eval_item.get('justification', 'N/A')}")
                return evaluations
            else:
                # Fallback: assign equal scores
                return [{"thought_id": i, "score": 5.0, "justification": "Could not evaluate"}
                        for i in range(len(thoughts))]

        except Exception as e:
            print(f"❌ Error evaluating thoughts: {e}")
            return [{"thought_id": i, "score": 5.0, "justification": f"Error: {e}"}
                    for i in range(len(thoughts))]

    def select_best_thought(self, thoughts: List[Dict[str, Any]],
                           evaluations: List[Dict[str, Any]]) -> tuple:
        """Select the highest-scored thought"""
        best_eval = max(evaluations, key=lambda x: x.get('score', 0))
        best_idx = best_eval.get('thought_id', 0)
        best_thought = thoughts[best_idx] if best_idx < len(thoughts) else thoughts[0]

        print(f"\n🎯 SELECTED BEST THOUGHT (ID: {best_idx}, Score: {best_eval.get('score', 0)}/10)")
        print(f"   Path: {best_thought.get('thought', 'N/A')[:100]}...")

        return best_thought, best_eval

    def run(self, user_query: str, store_conversation: bool = False) -> Dict[str, Any]:
        """
        Main Tree of Thought agent loop using Responses API.

        Args:
            user_query: The user's question or request
            store_conversation: If True, OpenAI stores conversation state server-side
        """
        print(f"\n{'='*70}")
        print(f"USER QUERY: {user_query}")
        print(f"{'='*70}\n")

        depth = 0
        context = user_query
        selected_path = []

        # Initialize thought tree
        self.thought_tree = {
            "query": user_query,
            "depth_limit": self.depth_limit,
            "paths": []
        }

        while depth < self.depth_limit:
            depth += 1
            print(f"\n{'='*70}")
            print(f"TREE DEPTH: {depth}/{self.depth_limit}")
            print(f"{'='*70}\n")

            try:
                # Step 1: Generate multiple candidate thoughts
                thoughts = self.generate_thoughts(context)

                # Step 2: Evaluate the thoughts
                evaluations = self.evaluate_thoughts(thoughts, context)

                # Step 3: Select the best thought
                best_thought, best_eval = self.select_best_thought(thoughts, evaluations)

                # Store in tree
                tree_node = {
                    "depth": depth,
                    "context": context,
                    "candidates": thoughts,
                    "evaluations": evaluations,
                    "selected": best_thought,
                    "selected_score": best_eval.get('score', 0)
                }
                self.thought_tree["paths"].append(tree_node)
                selected_path.append(best_thought)

                # Step 4: Execute action if needed
                next_action = best_thought.get('next_action')
                if next_action and next_action in ['calculator', 'search_knowledge', 'get_current_date']:
                    print(f"\n⚡ EXECUTING ACTION: {next_action}")

                    # Use the model to determine the arguments for the tool
                    action_prompt = f"""Based on this reasoning path: {best_thought.get('thought')}

Execute the {next_action} tool. What arguments should be used?
Provide your response as a JSON object with the tool arguments.
For calculator: {{"expression": "..."}}
For search_knowledge: {{"query": "..."}}
For get_current_date: {{}}"""

                    response = client.responses.create(
                        model=self.model,
                        input=action_prompt,
                        instructions=self.get_system_instructions(mode="execute"),
                        tools=self.get_tools_config()
                    )

                    # Look for tool calls
                    tool_result = None
                    for item in response.output:
                        if item.type == "function_call" and item.name == next_action:
                            tool_args = json.loads(item.arguments)
                            print(f"  Args: {json.dumps(tool_args, indent=4)}")
                            tool_result = self.execute_tool(next_action, tool_args)
                            print(f"  Result: {tool_result}")
                            tree_node["action_result"] = tool_result
                            break

                    # Update context with the result
                    if tool_result:
                        context = f"{context}\n\nPrevious step: {best_thought.get('thought')}\nAction taken: {next_action}\nResult: {tool_result}"
                    else:
                        context = f"{context}\n\nPrevious step: {best_thought.get('thought')}"
                else:
                    # No action needed, might have the answer
                    print(f"\n✅ NO ACTION NEEDED - Checking if we have the answer...")

                    # Check if we have enough information to answer
                    check_prompt = f"""Original question: {user_query}

Reasoning path so far:
{json.dumps(selected_path, indent=2)}

Do you have enough information to answer the question? If yes, provide the final answer.
If no, explain what additional information is needed."""

                    response = client.responses.create(
                        model=self.model,
                        input=check_prompt,
                        instructions=self.get_system_instructions(mode="execute")
                    )

                    final_answer = ""
                    for item in response.output:
                        if item.type == "message":
                            for content_item in item.content:
                                if hasattr(content_item, 'text'):
                                    final_answer += content_item.text

                    # Check if this is truly final or we need more depth
                    if "final answer" in final_answer.lower() or depth >= self.depth_limit:
                        print(f"\n{'='*70}")
                        print("✅ TREE OF THOUGHT COMPLETED")
                        print(f"{'='*70}\n")

                        return {
                            "answer": final_answer,
                            "thought_tree": self.thought_tree,
                            "selected_path": selected_path,
                            "depth_reached": depth,
                            "response_id": response.id
                        }
                    else:
                        context = f"{context}\n\nPrevious step: {best_thought.get('thought')}\nAnalysis: {final_answer}"

            except Exception as e:
                print(f"\n❌ Error at depth {depth}: {str(e)}")
                return {
                    "answer": f"Error occurred: {str(e)}",
                    "thought_tree": self.thought_tree,
                    "selected_path": selected_path,
                    "depth_reached": depth,
                    "error": str(e)
                }

        # Max depth reached
        print(f"\n⚠️ Max depth ({self.depth_limit}) reached")
        return {
            "answer": "Reached maximum tree depth",
            "thought_tree": self.thought_tree,
            "selected_path": selected_path,
            "depth_reached": depth
        }
    
    def print_reasoning_trace(self):
        """Pretty print the complete Tree of Thought trace"""
        print(f"\n{'='*70}")
        print("COMPLETE TREE OF THOUGHT TRACE")
        print(f"{'='*70}\n")

        if not self.thought_tree.get("paths"):
            print("No reasoning trace available")
            return

        print(f"Original Query: {self.thought_tree.get('query', 'N/A')}")
        print(f"Depth Limit: {self.thought_tree.get('depth_limit', 'N/A')}\n")

        for node in self.thought_tree["paths"]:
            print(f"🌳 DEPTH {node['depth']}")
            print(f"   Context: {node['context'][:100]}...")
            print(f"\n   Generated {len(node['candidates'])} candidate thoughts:")

            for i, thought in enumerate(node['candidates']):
                eval_info = next((e for e in node['evaluations'] if e.get('thought_id') == i), {})
                score = eval_info.get('score', 'N/A')
                is_selected = (thought == node['selected'])

                marker = "🎯" if is_selected else "  "
                print(f"\n   {marker} Candidate {i+1} (Score: {score}/10):")
                print(f"      Thought: {thought.get('thought', 'N/A')[:80]}...")
                print(f"      Reasoning: {thought.get('reasoning', 'N/A')[:80]}...")
                print(f"      Next Action: {thought.get('next_action', 'None')}")

                if is_selected and 'action_result' in node:
                    print(f"      ⚡ Executed with result: {node['action_result'][:80]}...")

            print()

    def reset(self):
        """Reset conversation state"""
        self.memory = []
        self.thought_tree = {}
        self.conversation_history = []
        self.response_id = None


# Example usage
def main():
    print("\n" + "="*70)
    print("TREE OF THOUGHT AGENT WITH RESPONSES API")
    print("="*70)

    # Example 1: Multi-step reasoning with calculations
    print("\n" + "="*70)
    print("EXAMPLE 1: Multi-step mathematical problem with Tree of Thought")
    print("="*70)

    agent = TreeOfThoughtAgent(model="gpt-4o", num_thoughts=3, depth_limit=3)

    result = agent.run(
        "If I have 15 apples and I buy 3 more bags with 8 apples each, "
        "then give away half of my apples, how many do I have left?",
        store_conversation=True
    )

    print(f"\n{'='*70}")
    print("📊 FINAL RESULT")
    print(f"{'='*70}")
    print(f"Answer: {result['answer']}")
    print(f"Depth Reached: {result.get('depth_reached', 'N/A')}")
    print(f"Response ID: {result.get('response_id', 'N/A')}")

    agent.print_reasoning_trace()

    # Example 2: Information gathering with multiple tools
    print("\n" + "="*70)
    print("EXAMPLE 2: Multi-tool information gathering with ToT")
    print("="*70)

    agent2 = TreeOfThoughtAgent(model="gpt-4o", num_thoughts=3, depth_limit=2)

    result2 = agent2.run(
        "What is Python programming language? What's today's date? "
        "Then tell me: was Python created more than 30 years ago from today?",
        store_conversation=True
    )

    print(f"\n{'='*70}")
    print("📊 FINAL RESULT")
    print(f"{'='*70}")
    print(f"Answer: {result2['answer']}")
    print(f"Depth Reached: {result2.get('depth_reached', 'N/A')}")

    agent2.print_reasoning_trace()

    # Example 3: Complex problem requiring exploration
    print("\n" + "="*70)
    print("EXAMPLE 3: Complex problem exploration")
    print("="*70)

    agent3 = TreeOfThoughtAgent(model="gpt-4o", num_thoughts=4, depth_limit=3)

    result3 = agent3.run(
        "I need to plan a data science project. What are the key steps? "
        "Consider different approaches and select the best one.",
        store_conversation=True
    )

    print(f"\n{'='*70}")
    print("📊 FINAL RESULT")
    print(f"{'='*70}")
    print(f"Answer: {result3['answer']}")
    print(f"Depth Reached: {result3.get('depth_reached', 'N/A')}")
    print(f"Stored Response ID: {result3.get('response_id')}")

    # Show selected path
    if 'selected_path' in result3:
        print(f"\n📍 Selected reasoning path:")
        for i, step in enumerate(result3['selected_path'], 1):
            print(f"  {i}. {step.get('thought', 'N/A')[:60]}...")


if __name__ == "__main__":
    main()