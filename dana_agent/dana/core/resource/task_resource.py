"""
{
      "name": "Task",
      "description": "Launch a new agent to handle complex, multi-step tasks autonomously. \n\nThe Task tool launches specialized agents (subprocesses) that autonomously handle complex tasks. Each agent type has specific capabilities and tools available to it.\n\nAvailable agent types and the tools they have access to:\n- Bash: Command execution specialist for running bash commands. Use this for git operations, command execution, and other terminal tasks. (Tools: Bash)\n- general-purpose: General-purpose agent for researching complex questions, searching for code, and executing multi-step tasks. When you are searching for a keyword or file and are not confident that you will find the right match in the first few tries use this agent to perform the search for you. (Tools: *)\n- statusline-setup: Use this agent to configure the user's Claude Code status line setting. (Tools: Read, Edit)\n- Explore: Fast agent specialized for exploring codebases. Use this when you need to quickly find files by patterns (eg. \"src/components/**/*.tsx\"), search code for keywords (eg. \"API endpoints\"), or answer questions about the codebase (eg. \"how do API endpoints work?\"). When calling this agent, specify the desired thoroughness level: \"quick\" for basic searches, \"medium\" for moderate exploration, or \"very thorough\" for comprehensive analysis across multiple locations and naming conventions. (Tools: All tools except Task, ExitPlanMode, Edit, Write, NotebookEdit)\n- Plan: Software architect agent for designing implementation plans. Use this when you need to plan the implementation strategy for a task. Returns step-by-step plans, identifies critical files, and considers architectural trade-offs. (Tools: All tools except Task, ExitPlanMode, Edit, Write, NotebookEdit)\n- claude-code-guide: Use this agent when the user asks questions (\"Can Claude...\", \"Does Claude...\", \"How do I...\") about: (1) Claude Code (the CLI tool) - features, hooks, slash commands, MCP servers, settings, IDE integrations, keyboard shortcuts; (2) Claude Agent SDK - building custom agents; (3) Claude API (formerly Anthropic API) - API usage, tool use, Anthropic SDK usage. **IMPORTANT:** Before spawning a new agent, check if there is already a running or recently completed claude-code-guide agent that you can resume using the \"resume\" parameter. (Tools: Glob, Grep, Read, WebFetch, WebSearch)\n- prompt-optimizer: Use this agent when you need to create, optimize, or enhance LLM prompts for agent systems. This includes improving system prompts, refining instruction clarity, applying prompt engineering best practices, or analyzing existing prompts for weaknesses. The agent will first understand the codebase structure to ensure optimizations align with the existing architecture.\n\nExamples:\n\n<example>\nContext: User wants to improve an existing interview agent prompt that isn't generating good follow-up questions.\nuser: \"The interview agent isn't asking good follow-up questions. Can you optimize its prompt?\"\nassistant: \"I'll use the prompt-optimizer agent to analyze the current prompt structure and enhance it with better follow-up generation techniques.\"\n<Task tool call to launch prompt-optimizer agent>\n</example>\n\n<example>\nContext: User is creating a new code review agent and needs a well-crafted system prompt.\nuser: \"I need to create a system prompt for a code review agent\"\nassistant: \"Let me use the prompt-optimizer agent to craft an optimized system prompt that follows best practices for code review agents.\"\n<Task tool call to launch prompt-optimizer agent>\n</example>\n\n<example>\nContext: User notices an agent is not following instructions consistently.\nuser: \"My documentation agent keeps ignoring the formatting requirements I specified\"\nassistant: \"I'll launch the prompt-optimizer agent to analyze the current prompt and restructure it for better instruction adherence.\"\n<Task tool call to launch prompt-optimizer agent>\n</example>\n\n<example>\nContext: User wants to apply advanced prompt engineering techniques to an existing prompt.\nuser: \"Can you make this prompt use chain-of-thought reasoning?\"\nassistant: \"I'll use the prompt-optimizer agent to enhance the prompt with chain-of-thought and other advanced prompting techniques.\"\n<Task tool call to launch prompt-optimizer agent>\n</example> (Tools: All tools)\n- software-architect: Use this agent when you need to design, review, or refactor code architecture for Python or React projects. This includes designing new features with proper separation of concerns, evaluating existing code structure against clean architecture principles, identifying violations of SOLID or DRY principles, planning module/package organization, and making architectural decisions about dependencies and boundaries.\n\nExamples:\n\n<example>\nContext: User is starting a new feature and wants to structure it properly.\nuser: \"I need to add a user authentication system to our Python backend\"\nassistant: \"Before implementing, let me consult the software-architect agent to design a clean architecture for this authentication system.\"\n<Task tool call to software-architect agent>\nThe architect recommends the following layered structure with clear separation between auth logic, data access, and API endpoints...\n</example>\n\n<example>\nContext: User has written code and wants architectural feedback.\nuser: \"I just finished the payment processing module, can you check if it follows good practices?\"\nassistant: \"I'll use the software-architect agent to review the architecture of your payment processing module.\"\n<Task tool call to software-architect agent>\nThe architectural review identified several concerns: the PaymentService class is violating Single Responsibility by handling both validation and external API calls...\n</example>\n\n<example>\nContext: User is refactoring and needs guidance on code organization.\nuser: \"Our React components folder has 50+ components and it's getting hard to manage\"\nassistant: \"Let me bring in the software-architect agent to propose a better organization structure for your React components.\"\n<Task tool call to software-architect agent>\nBased on clean architecture principles for React, I recommend restructuring into feature-based modules with shared components extracted...\n</example>\n\n<example>\nContext: User is making a design decision.\nuser: \"Should I use inheritance or composition for these data models?\"\nassistant: \"This is an important architectural decision. Let me consult the software-architect agent for a principled recommendation.\"\n<Task tool call to software-architect agent>\nApplying SOLID principles, specifically the Liskov Substitution Principle and favoring composition over inheritance...\n</example> (Tools: All tools)\n- code-simplifier: Use this agent when Claude has just generated code and you want to review it for unnecessary complexity, over-engineering, or violations of KISS/YAGNI principles. This agent should be called proactively after generating any non-trivial code block.\n\nExamples:\n\n<example>\nContext: Claude just generated a function with multiple abstraction layers\nuser: \"Write a function to fetch user data from an API\"\nassistant: \"Here is the function to fetch user data:\"\n```python\nclass UserFetcher:\n    def __init__(self, api_client_factory):\n        self.api_client = api_client_factory.create()\n    \n    def fetch(self, user_id, options=None):\n        options = options or FetchOptions()\n        return self._execute_fetch(user_id, options)\n    \n    def _execute_fetch(self, user_id, options):\n        # ... 40 more lines\n```\nassistant: \"Now let me use the code-simplifier agent to review this for unnecessary complexity.\"\n<commentary>\nSince code was just generated, use the code-simplifier agent to check if the abstraction layers and factory pattern are actually needed for this use case.\n</commentary>\n</example>\n\n<example>\nContext: Claude generated a utility with many configurable options\nuser: \"Create a logging helper\"\nassistant: \"Here's a comprehensive logging solution:\"\n```python\nclass LoggerConfig:\n    # ... 100+ lines with multiple formatters, handlers, rotation policies\n```\nassistant: \"Let me run the code-simplifier agent to ensure we're not over-engineering this.\"\n<commentary>\nThe generated logger has extensive configuration that the user didn't ask for. Use the code-simplifier agent to strip it down to essentials.\n</commentary>\n</example>\n\n<example>\nContext: User explicitly asks for simplification\nuser: \"This code feels too complex, can you simplify it?\"\nassistant: \"I'll use the code-simplifier agent to analyze and streamline this code.\"\n<commentary>\nDirect request for simplification - use the code-simplifier agent to provide structured analysis and refactoring.\n</commentary>\n</example> (Tools: All tools)\n- preference-learner: Use this agent when the user provides feedback, corrections, or expresses preferences about how tasks should be done. This agent should be triggered proactively whenever:\n\n<example>\nContext: User corrects the assistant's approach to solving a problem\nuser: \"No, don't implement the entire feature at once. I prefer you to outline the structure first and get my approval before coding.\"\nassistant: \"I understand. Let me use the preference-learner agent to capture this workflow preference and check if it should be added to your global instructions.\"\n<commentary>\nThe user expressed a clear preference about development workflow. Use the preference-learner agent to analyze if this is a high-level preference worth persisting to ~/.claude/CLAUDE.md.\n</commentary>\n</example>\n\n<example>\nContext: User expresses frustration with assistant behavior\nuser: \"You keep agreeing with everything I say. I need you to push back more and tell me when my ideas are bad.\"\nassistant: \"That's valuable feedback. Let me use the preference-learner agent to evaluate this collaboration preference against your existing guidelines.\"\n<commentary>\nThe user is providing meta-feedback about interaction style. This is a high-level collaboration preference that the preference-learner agent should analyze and potentially persist.\n</commentary>\n</example>\n\n<example>\nContext: User praises a particular approach\nuser: \"Yes! This is exactly what I want - showing me the interface first before the implementation details.\"\nassistant: \"I'm glad this approach works for you. Let me use the preference-learner agent to capture this as a potential workflow preference.\"\n<commentary>\nPositive feedback indicates a preference worth learning. Use the preference-learner agent to determine if this should be generalized and added to global instructions.\n</commentary>\n</example> (Tools: All tools)\n\nWhen using the Task tool, you must specify a subagent_type parameter to select which agent type to use.\n\nWhen NOT to use the Task tool:\n- If you want to read a specific file path, use the Read or Glob tool instead of the Task tool, to find the match more quickly\n- If you are searching for a specific class definition like \"class Foo\", use the Glob tool instead, to find the match more quickly\n- If you are searching for code within a specific file or set of 2-3 files, use the Read tool instead of the Task tool, to find the match more quickly\n- Other tasks that are not related to the agent descriptions above\n\n\nUsage notes:\n- Always include a short description (3-5 words) summarizing what the agent will do\n- Launch multiple agents concurrently whenever possible, to maximize performance; to do that, use a single message with multiple tool uses\n- When the agent is done, it will return a single message back to you. The result returned by the agent is not visible to the user. To show the user the result, you should send a text message back to the user with a concise summary of the result.\n- You can optionally run agents in the background using the run_in_background parameter. When an agent runs in the background, the tool result will include an output_file path. To check on the agent's progress or retrieve its results, use the Read tool to read the output file, or use Bash with `tail` to see recent output. You can continue working while background agents run.\n- Agents can be resumed using the `resume` parameter by passing the agent ID from a previous invocation. When resumed, the agent continues with its full previous context preserved. When NOT resuming, each invocation starts fresh and you should provide a detailed task description with all necessary context.\n- When the agent is done, it will return a single message back to you along with its agent ID. You can use this ID to resume the agent later if needed for follow-up work.\n- Provide clear, detailed prompts so the agent can work autonomously and return exactly the information you need.\n- Agents with \"access to current context\" can see the full conversation history before the tool call. When using these agents, you can write concise prompts that reference earlier context (e.g., \"investigate the error discussed above\") instead of repeating information. The agent will receive all prior messages and understand the context.\n- The agent's outputs should generally be trusted\n- Clearly tell the agent whether you expect it to write code or just to do research (search, file reads, web fetches, etc.), since it is not aware of the user's intent\n- If the agent description mentions that it should be used proactively, then you should try your best to use it without the user having to ask for it first. Use your judgement.\n- If the user specifies that they want you to run agents \"in parallel\", you MUST send a single message with multiple Task tool use content blocks. For example, if you need to launch both a build-validator agent and a test-runner agent in parallel, send a single message with both tool calls.\n\nExample usage:\n\n<example_agent_descriptions>\n\"test-runner\": use this agent after you are done writing code to run tests\n\"greeting-responder\": use this agent when to respond to user greetings with a friendly joke\n</example_agent_description>\n\n<example>\nuser: \"Please write a function that checks if a number is prime\"\nassistant: Sure let me write a function that checks if a number is prime\nassistant: First let me use the Write tool to write a function that checks if a number is prime\nassistant: I'm going to use the Write tool to write the following code:\n<code>\nfunction isPrime(n) {\n  if (n <= 1) return false\n  for (let i = 2; i * i <= n; i++) {\n    if (n % i === 0) return false\n  }\n  return true\n}\n</code>\n<commentary>\nSince a significant piece of code was written and the task was completed, now use the test-runner agent to run the tests\n</commentary>\nassistant: Now let me use the test-runner agent to run the tests\nassistant: Uses the Task tool to launch the test-runner agent\n</example>\n\n<example>\nuser: \"Hello\"\n<commentary>\nSince the user is greeting, use the greeting-responder agent to respond with a friendly joke\n</commentary>\nassistant: \"I'm going to use the Task tool to launch the greeting-responder agent\"\n</example>\n",
      "input_schema": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
          "description": {
            "description": "A short (3-5 word) description of the task",
            "type": "string"
          },
          "prompt": {
            "description": "The task for the agent to perform",
            "type": "string"
          },
          "subagent_type": {
            "description": "The type of specialized agent to use for this task",
            "type": "string"
          },
          "model": {
            "description": "Optional model to use for this agent. If not specified, inherits from parent. Prefer haiku for quick, straightforward tasks to minimize cost and latency.",
            "type": "string",
            "enum": [
              "sonnet",
              "opus",
              "haiku"
            ]
          },
          "resume": {
            "description": "Optional agent ID to resume from. If provided, the agent will continue from the previous execution transcript.",
            "type": "string"
          },
          "run_in_background": {
            "description": "Set to true to run this agent in the background. The tool result will include an output_file path - use Read tool or Bash tail to check on output.",
            "type": "boolean"
          },
          "max_turns": {
            "description": "Maximum number of agentic turns (API round-trips) before stopping. Used internally for warmup.",
            "type": "integer",
            "exclusiveMinimum": 0,
            "maximum": 9007199254740991
          }
        },
        "required": [
          "description",
          "prompt",
          "subagent_type"
        ],
        "additionalProperties": false
      }
    },
    {
      "name": "TaskOutput",
      "description": "- Retrieves output from a running or completed task (background shell, agent, or remote session)\n- Takes a task_id parameter identifying the task\n- Returns the task output along with status information\n- Use block=true (default) to wait for task completion\n- Use block=false for non-blocking check of current status\n- Task IDs can be found using the /tasks command\n- Works with all task types: background shells, async agents, and remote sessions",
      "input_schema": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
          "task_id": {
            "description": "The task ID to get output from",
            "type": "string"
          },
          "block": {
            "description": "Whether to wait for completion",
            "default": true,
            "type": "boolean"
          },
          "timeout": {
            "description": "Max wait time in ms",
            "default": 30000,
            "type": "number",
            "minimum": 0,
            "maximum": 600000
          }
        },
        "required": [
          "task_id",
          "block",
          "timeout"
        ],
        "additionalProperties": false
      }
    }
"""

from dana.common.protocols.war import named_tool
from dana.core.resource.base_resource import BaseResource


class TaskResource(BaseResource):
    """Resource for launching tasks."""

    def __init__(self, resource_id: str, **kwargs):
        """Initialize the TaskResource.

        Args:
            resource_id: Unique identifier for this resource instance.
            **kwargs: Additional arguments passed to the base resource.
        """
        super().__init__(resource_id=resource_id, **kwargs)

    @named_tool(name="Task")
    async def task(
        self,
        description: str,
        prompt: str,
        subagent_type: str,
        model: str | None = None,
        resume: str | None = None,
        run_in_background: bool = False,
        max_turns: int = 50,
    ) -> str:
        """ """
        pass

    @named_tool(name="TaskOutput")
    async def task_output(self, task_id: str, block: bool = True, timeout: int = 30000) -> str:
        """ """
        pass
