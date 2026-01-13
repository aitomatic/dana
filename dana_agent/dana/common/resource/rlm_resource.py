"""
RLM Resource - Recursive Language Model resource for querying large documents.

Implements the RLM pattern where an LLM writes Python code to explore
large documents that don't fit in context. The LLM iteratively writes
code, receives output, and continues until it finds the answer.
"""

import re
from datetime import datetime
from pathlib import Path

from dana.common.llm import LLM, LLMMessage
from dana.common.protocols.war import tool_use
from dana.core.agent.components.python_sandbox import PythonSandbox
from dana.core.resource.base_resource import BaseResource


# System prompt for RLM query pattern
RLM_SYSTEM_PROMPT = """You are an RLM agent with access to a Python REPL containing a large document.

Environment:
- `context`: str - The full document (may be very large, don't print it all)
- `llm_query(prompt, text)`: Query sub-LLM for semantic tasks (summarize, extract, etc.)
- Modules: re, json, math, collections, itertools, functools

Strategies:
1. Peek: `print(context[:3000])` to see structure
2. Search: `re.findall(pattern, context)` to find sections
3. Slice: `context[start:end]` to extract portions
4. Sub-query: `result = llm_query("summarize", chunk)` for semantic work
5. Accumulate: Store results in variables (they persist)

Output Python code. When done, output ONE of:
- FINAL(your_answer_string)
- FINAL_VAR(variable_name)

IMPORTANT: Output ONLY Python code or FINAL/FINAL_VAR. No explanations."""

# Maximum iterations for RLM loop
MAX_ITERATIONS = 20


class RLMResource(BaseResource):
    """RLM-backed resource for querying and writing to large context files.

    This resource enables querying large documents (500K+ tokens) by having
    an LLM write Python code to explore them programmatically, rather than
    stuffing everything into the context window.
    """

    def __init__(
        self,
        file: str = "context.md",
        llm_provider: str = "anthropic",
        llm_model: str = "claude-sonnet-4-20250514",
        **kwargs,
    ):
        """
        Initialize RLMResource.

        Args:
            file: Path to the context file (created if doesn't exist)
            llm_provider: LLM provider to use for queries
            llm_model: LLM model to use for queries
            **kwargs: Additional arguments passed to BaseResource
        """
        super().__init__(resource_type="rlm", **kwargs)
        self.file = Path(file)
        self.llm_provider = llm_provider
        self.llm_model = llm_model

        # Create file if it doesn't exist
        if not self.file.exists():
            self.file.parent.mkdir(parents=True, exist_ok=True)
            self.file.write_text("")

        # Initialize LLM
        self._llm = LLM(provider=llm_provider, model=llm_model)

    def _get_context(self) -> str:
        """Read the current context from file."""
        return self.file.read_text()

    def _llm_query_fn(self, prompt: str, text: str) -> str:
        """Sub-LLM query function for semantic tasks."""
        import asyncio

        async def _query():
            return await self._llm.ask(
                f"{prompt}\n\nText:\n{text}",
                system_prompt="You are a helpful assistant. Respond concisely.",
            )

        # Run async in sync context
        try:
            loop = asyncio.get_running_loop()
            # We're in an async context, create a task
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _query())
                return future.result()
        except RuntimeError:
            # No running loop, use asyncio.run
            return asyncio.run(_query())

    def _extract_final(self, response: str, sandbox: PythonSandbox) -> str | None:
        """Extract final answer from response if present."""
        # Check for FINAL(answer)
        final_match = re.search(r"FINAL\(([^)]+)\)", response)
        if final_match:
            return final_match.group(1).strip().strip("'\"")

        # Check for FINAL_VAR(variable_name)
        final_var_match = re.search(r"FINAL_VAR\(([^)]+)\)", response)
        if final_var_match:
            var_name = final_var_match.group(1).strip()
            if var_name in sandbox.namespace:
                return str(sandbox.namespace[var_name])
            return f"Error: Variable '{var_name}' not found in namespace"

        return None

    def _extract_code(self, response: str) -> str:
        """Extract Python code from response."""
        # Try to extract from code blocks first
        code_block_match = re.search(r"```(?:python)?\s*\n?(.*?)```", response, re.DOTALL)
        if code_block_match:
            return code_block_match.group(1).strip()

        # Otherwise, treat the whole response as code (after removing FINAL markers)
        code = response.strip()
        # Remove any FINAL markers that might be in the response
        code = re.sub(r"FINAL\([^)]+\)", "", code)
        code = re.sub(r"FINAL_VAR\([^)]+\)", "", code)
        return code.strip()

    @tool_use
    def query(self, question: str) -> str:
        """
        Query the context using RLM pattern.

        The LLM writes Python code to search/analyze the context document.
        It iterates until it finds the answer and outputs FINAL(answer)
        or FINAL_VAR(variable_name).

        Args:
            question: The question to answer about the context

        Returns:
            The answer extracted from the LLM's exploration
        """
        import asyncio

        async def _query_async():
            context = self._get_context()
            if not context.strip():
                return "Error: Context is empty. Use load_file() or append() to add content first."

            # Create sandbox with llm_query function
            sandbox = PythonSandbox(llm_query_fn=self._llm_query_fn)

            # Build conversation
            messages = [
                LLMMessage(role="system", content=RLM_SYSTEM_PROMPT),
                LLMMessage(
                    role="user",
                    content=f"Question: {question}\n\nThe context has {len(context)} characters. Start exploring.",
                ),
            ]

            for iteration in range(MAX_ITERATIONS):
                # Get LLM response
                response = await self._llm.chat(messages)

                # Check for final answer
                final_answer = self._extract_final(response, sandbox)
                if final_answer:
                    return final_answer

                # Extract and execute code
                code = self._extract_code(response)
                if not code:
                    # No code found, ask LLM to continue
                    messages.append(LLMMessage(role="assistant", content=response))
                    messages.append(
                        LLMMessage(
                            role="user",
                            content="Please output Python code to explore the context, or FINAL(answer) if you have the answer.",
                        )
                    )
                    continue

                # Execute code in sandbox
                output = sandbox.execute(code, context)

                # Add to conversation
                messages.append(LLMMessage(role="assistant", content=response))
                messages.append(LLMMessage(role="user", content=f"Output:\n{output}\n\nContinue exploring or output FINAL(answer)."))

            return "Error: Maximum iterations reached without finding answer"

        # Run async
        try:
            loop = asyncio.get_running_loop()
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _query_async())
                return future.result()
        except RuntimeError:
            return asyncio.run(_query_async())

    @tool_use
    def append(self, content: str, category: str = "note") -> str:
        """
        Append content to the context file with timestamp.

        Args:
            content: The content to append
            category: Category label for the entry (default: "note")

        Returns:
            Confirmation message
        """
        timestamp = datetime.now().isoformat()
        entry = f"\n\n## [{category}] {timestamp}\n\n{content}"

        with open(self.file, "a") as f:
            f.write(entry)

        return f"Appended {len(content)} characters as [{category}] at {timestamp}"

    @tool_use
    def load_file(self, path: str) -> str:
        """
        Load and append file contents to the context.

        Args:
            path: Path to the file to load

        Returns:
            Confirmation message with file size
        """
        source_path = Path(path)
        if not source_path.exists():
            return f"Error: File not found: {path}"

        content = source_path.read_text()
        timestamp = datetime.now().isoformat()
        entry = f"\n\n## [file: {source_path.name}] {timestamp}\n\n{content}"

        with open(self.file, "a") as f:
            f.write(entry)

        return f"Loaded {len(content)} characters from {source_path.name}"
