"""Clean Reasoning Agent Implementation in LangGraph - Real LLM Only."""

import asyncio
import operator
import os
from dataclasses import dataclass
from typing import Annotated, TypedDict

from langchain_core.messages import HumanMessage, ToolMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph


# Define the state structure for the agent
class ReasoningState(TypedDict):
    messages: Annotated[list, operator.add]
    question: str
    reasoning_result: str
    mcp_tools_available: bool
    tool_results: dict


@dataclass
class AgentConfig:
    """Agent configuration matching DANA's system variables."""

    agent_name: str = "Reasoning Agent"
    agent_description: str = "A reasoning agent that can reason about the world and make decisions."
    mcp_servers: dict = None

    def __post_init__(self):
        if self.mcp_servers is None:
            self.mcp_servers = {
                "weather": {
                    "url": "http://127.0.0.1:8000/mcp/",
                    "transport": "streamable_http",
                }
            }


class ReasoningAgent:
    """Clean LangGraph implementation using real LLM only."""

    def __init__(self, config: AgentConfig | None = None):
        self.config = config or AgentConfig()
        self.llm = self._initialize_llm()
        self.mcp_client = MultiServerMCPClient(self.config.mcp_servers)
        self.tools = []
        self.graph = self._build_graph()

    def _initialize_llm(self):
        """Initialize the real LLM."""
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY environment variable is required. Please set your OpenAI API key to use this agent.")
        return ChatOpenAI(model="gpt-4", temperature=0)

    async def _setup_mcp_tools(self):
        """Setup MCP tools from the configured servers."""
        try:
            self.tools = await self.mcp_client.get_tools()
            print(f"✅ Loaded {len(self.tools)} MCP tools")
        except Exception as e:
            print(f"⚠️  Failed to load MCP tools: {e}")
            print("🔄 Continuing without MCP tools")
            self.tools = []

    def _build_graph(self):
        """Build the LangGraph reasoning workflow."""
        workflow = StateGraph(ReasoningState)

        # Add nodes for each step of reasoning
        workflow.add_node("setup_tools", self._setup_tools)
        workflow.add_node("reason_with_tools", self._reason_with_tools)
        workflow.add_node("execute_tools", self._execute_tools)
        workflow.add_node("final_response", self._final_response)
        workflow.add_node("format_response", self._format_response)

        # Define the flow
        workflow.set_entry_point("setup_tools")
        workflow.add_edge("setup_tools", "reason_with_tools")
        workflow.add_edge("reason_with_tools", "execute_tools")
        workflow.add_edge("execute_tools", "final_response")
        workflow.add_edge("final_response", "format_response")
        workflow.add_edge("format_response", END)

        return workflow.compile()

    async def _setup_tools(self, state: ReasoningState) -> ReasoningState:
        """Setup MCP tools for reasoning."""
        # Initialize MCP tools if not already done
        if not self.tools:
            await self._setup_mcp_tools()

        tools_available = len(self.tools) > 0
        print(f"🔧 Tools setup complete: {len(self.tools)} tools available")

        return {**state, "mcp_tools_available": tools_available, "tool_results": {}}

    async def _reason_with_tools(self, state: ReasoningState) -> ReasoningState:
        """Initial reasoning step - let LLM decide on tool usage."""
        question = state["question"]
        tools_available = state.get("mcp_tools_available", False)

        print(f"🤔 Processing question: {question}")
        print(f"🔗 Tools available: {tools_available}")

        try:
            # Bind tools to the LLM if available
            if tools_available and self.tools:
                llm_with_tools = self.llm.bind_tools(self.tools)
                print(f"🔗 Bound {len(self.tools)} tools to LLM")
            else:
                llm_with_tools = self.llm
                print("⚠️  No tools bound to LLM")

            # Create the reasoning prompt
            messages = [HumanMessage(content=question)]
            print(f"💬 Sending to LLM: {question}")

            response = await llm_with_tools.ainvoke(messages)
            print(f"✅ LLM initial response: {len(response.content)} characters")

            # Store the response and prepare for tool execution
            new_messages = state.get("messages", []) + [HumanMessage(content=question), response]

            return {
                "messages": new_messages,
                "question": state["question"],
                "reasoning_result": response.content,
                "mcp_tools_available": state["mcp_tools_available"],
                "tool_results": {},
            }

        except Exception as e:
            error_msg = f"Error during initial reasoning: {str(e)}"
            print(f"❌ {error_msg}")

            return {
                "messages": state.get("messages", []),
                "question": state["question"],
                "reasoning_result": f"I apologize, but I encountered an error: {str(e)}",
                "mcp_tools_available": state.get("mcp_tools_available", False),
                "tool_results": {},
            }

    async def _execute_tools(self, state: ReasoningState) -> ReasoningState:
        """Execute any tool calls from the LLM response."""
        messages = state.get("messages", [])
        if not messages:
            return state

        last_message = messages[-1]
        tool_results = {}

        # Check if there are tool calls to execute
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            print(f"🛠️  Processing {len(last_message.tool_calls)} tool calls")

            # Execute each tool call and add results to messages
            for tool_call in last_message.tool_calls:
                tool_name = tool_call.get("name", "unknown")
                print(f"🔧 Executing tool: {tool_name}")

                # For now, we'll simulate tool execution
                # In a real implementation, you'd call the actual tool
                result = f"Tool {tool_name} executed successfully with mock data"
                tool_results[tool_name] = result

                # Add tool message to conversation
                tool_message = ToolMessage(content=result, tool_call_id=tool_call.get("id", ""))
                messages.append(tool_message)
        else:
            print("ℹ️  No tool calls to execute")

        return {**state, "messages": messages, "tool_results": tool_results}

    async def _final_response(self, state: ReasoningState) -> ReasoningState:
        """Get final response from LLM after tool execution."""
        messages = state.get("messages", [])

        # If we have tool results, ask LLM to synthesize final answer
        if state.get("tool_results"):
            print("🎯 Getting final response after tool execution")

            # Add a prompt for final synthesis
            synthesis_prompt = "Please provide a comprehensive answer based on the tool results above."
            messages.append(HumanMessage(content=synthesis_prompt))

            try:
                final_response = await self.llm.ainvoke(messages)
                print(f"✅ Final response: {len(final_response.content)} characters")

                return {**state, "messages": messages + [final_response], "reasoning_result": final_response.content}
            except Exception as e:
                print(f"❌ Error getting final response: {e}")
                return {**state, "reasoning_result": "I was able to gather information but had trouble providing a final response."}
        else:
            # No tools were used, return the original response
            print("ℹ️  No tools used, using original response")
            return state

    async def _format_response(self, state: ReasoningState) -> ReasoningState:
        """Format the final response."""
        result = state["reasoning_result"]
        if not result or result.strip() == "":
            result = "No response generated."

        formatted_result = f"[{self.config.agent_name}] {result}"
        print(f"✨ Formatted response: {len(formatted_result)} characters")

        return {**state, "reasoning_result": formatted_result}

    async def solve(self, question: str) -> str:
        """Solve a question using the agent."""
        print("\n🚀 Starting LangGraph Reasoning Agent")
        print(f"❓ Question: {question}")

        initial_state: ReasoningState = {
            "messages": [],
            "question": question,
            "reasoning_result": "",
            "mcp_tools_available": False,
            "tool_results": {},
        }

        result = await self.graph.ainvoke(initial_state)
        print("✅ Agent completed processing")
        return result["reasoning_result"]


# Synchronous wrapper for easier usage
def solve_sync(question: str) -> str:
    """Synchronous wrapper for the solve function."""
    agent = ReasoningAgent()
    return asyncio.run(agent.solve(question))


async def main():
    """Demonstrate the LangGraph reasoning agent."""
    # Test questions
    test_questions = [
        "What is the weather in Tokyo?",
        "Explain the concept of machine learning in simple terms",
        "What are the benefits of renewable energy?",
    ]

    agent = ReasoningAgent()

    for i, question in enumerate(test_questions, 1):
        print(f"\n{'=' * 50}")
        print(f"TEST {i}: {question}")
        print(f"{'=' * 50}")

        try:
            answer = await agent.solve(question)
            print("\n📝 ANSWER:")
            print(answer)
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    # Example usage
    try:
        question = "What is the weather in Tokyo?"
        print("Testing LangGraph implementation with real LLM...")
        result = solve_sync(question)
        print("\n📝 FINAL RESULT:")
        print(result)
    except ValueError as e:
        print(f"Configuration Error: {e}")
    except Exception as e:
        print(f"Error: {e}")

    # Uncomment to run full test suite
    # asyncio.run(main())
