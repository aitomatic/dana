"""Domain expertise definitions for DXA.

This module defines the foundational structures for representing domain expertise,
enabling agents to:
- Define specialized knowledge domains
- Specify expert capabilities and requirements
- Match queries to appropriate expert resources
- Validate expertise requirements
- Store domain-specific knowledge notes

The DomainExpertise class serves as a blueprint for creating specialized expert 
resources with well-defined capabilities and requirements.

Classes:
    DomainExpertise: Defines a knowledge domain and its capabilities

Example:
    >>> finance_expert = DomainExpertise(
    ...     name="finance",
    ...     description="Expert in financial analysis and planning",
    ...     capabilities=["stock analysis", "risk assessment"],
    ...     keywords=["investment", "portfolio", "risk"],
    ...     requirements=["financial data", "time period"],
    ...     example_queries=["Analyze risk for AAPL stock"]
    ... )
    >>> finance_expert.add_note("Always check market conditions before analysis")
    >>> finance_expert.add_note("Consider both technical and fundamental factors")
    >>> finance_expert.add_note("Risk metrics: Beta, Sharpe ratio, VaR")
"""

from dataclasses import dataclass, field
from typing import List, Set, Union
from pathlib import Path

@dataclass
class DomainExpertise:
    """Definition of a domain of expertise.
    
    This class encapsulates all the information needed to define an expert's
    domain of knowledge, capabilities, and requirements. It serves as a
    blueprint for creating specialized expert resources.
    
    Attributes:
        name (str): Domain identifier (e.g., "mathematics")
        description (str): Detailed description of the expert's knowledge domain
        capabilities (List[str]): Specific abilities and skills this expert has
        keywords (List[str]): Trigger words/phrases that indicate this expertise is needed
        requirements (List[str]): Required information or context for queries in this domain
        example_queries (List[str]): Sample questions demonstrating proper usage
        notes (Set[str]): Set of domain-specific knowledge notes and best practices
        
    Example:
        >>> math_expert = DomainExpertise(
        ...     name="mathematics",
        ...     description="Expert in algebra and calculus",
        ...     capabilities=["equation solving", "differentiation"],
        ...     keywords=["solve", "calculate", "equation"],
        ...     requirements=["mathematical expression"],
        ...     example_queries=["solve x^2 + 2x + 1 = 0"]
        ... )
        >>> math_expert.add_note("Check for special cases (quadratic, linear)")
        >>> math_expert.add_note("Verify solutions by substitution")
    """
    name: str                    # e.g., "mathematics"
    description: str = ""        # What this expert knows
    capabilities: List[str] = field(default_factory=list)  # What this expert can do
    keywords: List[str] = field(default_factory=list)      # Trigger words/phrases
    requirements: List[str] = field(default_factory=list)  # What input this expert needs
    example_queries: List[str] = field(default_factory=list)  # Example questions
    notes: Set[str] = field(default_factory=set)  # Domain-specific knowledge notes

    def add_note(self, note: str) -> None:
        """Add a note to the domain expertise.
        
        Args:
            note: Knowledge note or best practice to add
            
        Example:
            >>> expertise.add_note("Always validate input ranges")
        """
        if not note.strip():
            return
        self.notes.add(note.strip())

    def add_note_from_file(self, file_path: Union[str, Path]) -> None:
        """Add contents of a text file as a single note.
        
        The entire file content will be added as one note,
        preserving all formatting and line breaks.
        
        Args:
            file_path: Path to text file containing the note
            
        Raises:
            FileNotFoundError: If file does not exist
            UnicodeDecodeError: If file is not valid UTF-8
            
        Example:
            >>> expertise.add_note_from_file("math_theory.txt")
        """
        path = Path(file_path)
        try:
            content = path.read_text(encoding='utf-8')
            self.add_note(content)
        except (FileNotFoundError, UnicodeDecodeError) as e:
            raise e from None

    @property
    def long_description(self) -> str:
        """Get detailed description of the domain expertise.
        
        Returns:
            Detailed description including all non-empty fields except notes.
            Sections with empty lists are omitted.
        """
        sections = [f"Domain: {self.name}"]
        
        if self.description:
            sections.append(f"\nDescription: {self.description}")
            
        if self.capabilities:
            sections.extend([
                "\nCapabilities:",
                *[f"- {cap}" for cap in self.capabilities]
            ])
            
        if self.keywords:
            sections.extend([
                "\nKeywords:",
                *[f"- {kw}" for kw in self.keywords]
            ])
            
        if self.requirements:
            sections.extend([
                "\nRequirements:",
                *[f"- {req}" for req in self.requirements]
            ])
            
        if self.example_queries:
            sections.extend([
                "\nExample Queries:",
                *[f"- {q}" for q in self.example_queries]
            ])
            
        return "\n".join(sections)
