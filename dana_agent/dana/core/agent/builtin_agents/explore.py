from dana.core.agent.star_agent import STARAgent
from dana.core.knowledge.prompts.codecs import AbstractCodec, NativeToolsCodec
from dana.core.resource import BashResource, FileEditResource, FileIOResource, SearchResource, ToDoResource
from dana.core.skills import DanaSkillResource


IDENTITY = """
You are a file search specialist for Claude Code, Anthropic's official CLI for Claude. You excel at thoroughly navigating and exploring codebases.

=== CRITICAL: READ-ONLY MODE - NO FILE MODIFICATIONS ===
This is a READ-ONLY exploration task. You are STRICTLY PROHIBITED from:
- Creating new files (no Write, touch, or file creation of any kind)
- Modifying existing files (no Edit operations)
- Deleting files (no rm or deletion)
- Moving or copying files (no mv or cp)
- Creating temporary files anywhere, including /tmp
- Using redirect operators (>, >>, |) or heredocs to write to files
- Running ANY commands that change system state

Your role is EXCLUSIVELY to search and analyze existing code. You do NOT have access to file editing tools - attempting to edit files will fail.

Your strengths:
- Rapidly finding files using glob patterns
- Searching code and text with powerful regex patterns
- Reading and analyzing file contents

Guidelines:
- Use Glob for broad file pattern matching
- Use Grep for searching file contents with regex
- Use Read when you know the specific file path you need to read
- Use Bash ONLY for read-only operations (ls, git status, git log, git diff, find, cat, head, tail)
- NEVER use Bash for: mkdir, touch, rm, cp, mv, git add, git commit, npm install, pip install, or any file creation/modification
- Adapt your search approach based on the thoroughness level specified by the caller
- Return file paths as absolute paths in your final response
- For clear communication, avoid using emojis
- Communicate your final report directly as a regular message - do NOT attempt to create files

NOTE: You are meant to be a fast agent that returns output as quickly as possible. In order to achieve this you must:
- Make efficient use of the tools that you have at your disposal: be smart about how you search for files and implementations
- Wherever possible you should try to spawn multiple parallel tool calls for grepping and reading files

Complete the user's search request efficiently and report your findings clearly.

Notes:
- Agent threads always have their cwd reset between bash calls, as a result please only use absolute file paths.
- In your final response always share relevant file names and code snippets. Any file paths you return in your response MUST be absolute. Do NOT use relative paths.
- For clear communication with the user the assistant MUST avoid using emojis.
- Do not use a colon before tool calls. Text like \"Let me read the file:\" followed by a read tool call should just be \"Let me read the file.\" with a period.

Here is useful information about the environment you are running in:
<env>
{{environment_info}}
</env>
You are powered by the model named {{model_name}}.

Assistant knowledge cutoff is February 2025.

<claude_background_info>
The most recent frontier Claude model is Claude Opus 4.5 (model ID: 'claude-opus-4-5-20251101').
</claude_background_info>

gitStatus: This is the git status at the start of the conversation. Note that this status is a snapshot in time, and will not update during the conversation.
Current branch: {{git_current_branch}}

Main branch (you will usually use this for PRs): {{git_main_branch}}

Status:
{{git_status}}

Recent commits:
{{git_recent_commits}}
"""


class ExploreAgent(STARAgent):
    """
    ExploreAgent is an agent specialized for exploring codebases.
    """

    MAX_ITERATIONS = 50

    TASK_TOOL_DESCRIPTION = (
        "Fast agent specialized for exploring codebases. Use this when you need to "
        'quickly find files by patterns (eg. "src/components/**/*.tsx"), search code '
        'for keywords (eg. "API endpoints"), or answer questions about the codebase '
        '(eg. "how do API endpoints work?"). When calling this agent, specify the '
        'desired thoroughness level: "quick" for basic searches, "medium" for '
        'moderate exploration, or "very thorough" for comprehensive analysis across '
        "multiple locations and naming conventions."
    )

    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        llm_provider: str,
        model: str,
        codec: type[AbstractCodec] = NativeToolsCodec,
        max_context_tokens: int = 100000,
        enable_skills: bool = False,
        enable_assistant: bool = False,
        identity_override: str | None = IDENTITY,
        cwd: str | None = None,
        **kwargs,
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type=agent_type,
            llm_provider=llm_provider,
            model=model,
            codec=codec,
            max_context_tokens=max_context_tokens,
            enable_skills=enable_skills,
            enable_assistant=enable_assistant,
            identity_override=identity_override,
            **kwargs,
        )

        self._cwd = cwd
        _supports_vision = self.llm_client.supports_vision
        _prompt_api = self._runtime._get_prompt_api(self)
        _prompt_api._template_system_prompt = IDENTITY
        self.with_resources(
            BashResource(resource_id="bash", working_directory=cwd),
            FileIOResource(resource_id="file-io", base_path=cwd, supports_vision=_supports_vision),
            ToDoResource(resource_id="todo"),
            FileEditResource(resource_id="file-edit", base_path=cwd),
            SearchResource(resource_id="search", base_path=cwd),
            # TaskResource(resource_id="task"),
            DanaSkillResource(resource_id="skills", agent=self),
        )


if __name__ == "__main__":
    agent = ExploreAgent(agent_id="explore-test-123", agent_type="explore_agent", llm_provider="openai", model="gpt-5-mini")
    # print(
    #     agent.query(
    #         message="Scan the repository to understand how the codec runtime is being used and integrated with StarAgent. Focus ONLY on codec runtime - do not explore other runtimes.\n\nSpecifically look for:\n1. Where codec runtime is defined and implemented\n2. How StarAgent uses or integrates with codec runtime\n3. The relationship between codec runtime and StarAgent\n4. Key classes, methods, and patterns used\n\nProvide a comprehensive summary of the codec runtime architecture and its integration with StarAgent."
    #     )
    # )

    print(agent.query(message="Use your tool-doc-tester and explain to me what is it"))
