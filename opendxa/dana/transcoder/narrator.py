"""
Copyright © 2025 Aitomatic, Inc.

This source code is licensed under the license found in the LICENSE file in the root directory of this source tree

Defines the interface for the DANA Narrator (Program-to-NL)."""

from abc import ABC, abstractmethod

from opendxa.dana.parser.ast import Program


class NarratorInterface(ABC):
    """Interface for the Narrator responsible for generating natural language from DANA programs."""

    @abstractmethod
    async def narrate(self, program: Program) -> str:
        """Generate a natural language description of the given DANA program."""
        pass
