"""
Copyright © 2025 Aitomatic, Inc.

This source code is licensed under the license found in the LICENSE file in the root directory of this source tree

Defines the interface for the DANA Compiler (NL-to-Program).
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from opendxa.dana.parser.ast import Program
    from opendxa.dana.sandbox.sandbox_context import SandboxContext


class CompilerInterface(ABC):
    """Interface for the Compiler responsible for generating DANA programs from NL objectives."""

    # This corresponds to the GMA concept

    @abstractmethod
    async def compile(self, objective: str, context: "SandboxContext") -> "Program":
        """Compiles a natural language objective into a DANA program AST, using the provided context."""
        pass


# Example Placeholder Implementation (e.g., using an LLM)
# from opendxa.agent.resource import LLMResource # Assuming LLMResource exists
# from ..language.parser import parse_program # Assuming a parser exists

# class LLMCompiler(CompilerInterface):
#     def __init__(self, llm: LLMResource, prompt_template: str):
#         self.llm = llm
#         self.prompt_template = prompt_template # Template for building the prompt

#     async def compile(self, objective: str, context: 'RuntimeContext') -> 'Program':
#         """Uses an LLM to generate and then parse the program."""
#         prompt = self._build_prompt(objective, context)
#         program_dsl_str = await self.llm.generate(prompt)
#         try:
#             program_ast = parse_program(program_dsl_str) # Call the parser
#             # TODO: Add validation step using language.validator
#             return program_ast
#         except Exception as e:
#             # from ..exceptions import ProgramParsingError
#             # raise ProgramParsingError(f"Failed to parse LLM output: {e}\nOutput:\n{program_dsl_str}")
#             raise ValueError(f"Failed to parse LLM output: {e}") # Simple error for now

#     def _build_prompt(self, objective: str, context: 'RuntimeContext') -> str:
#         # Construct a detailed prompt using the template.
#         # Include objective, context state (agent, world, execution),
#         # available resources/tools (context.resources.list()),
#         # and the target DSL syntax/format.
#         full_context_state = context.get_full_state()
#         available_tools = context.resources.list()
#         # Use self.prompt_template.format(...) or similar
#         prompt = f"Objective: {objective}\nContext: {full_context_state}\nTools: {available_tools}\n---\nGenerate DANA program:"
#         return prompt
