"""
Learner: Handles the four learning phases of STAR reflection.

This component provides functionality for:
- ACQUISITIVE learning (immediate experience reflection)
- EPISODIC learning (episode-level reflection)
- INTEGRATIVE learning (multi-episode integration)
- RETENTIVE learning (long-term learning)
"""

import inspect
import re
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, Any
from uuid import uuid4

from structlog import get_logger

from dana.common.llm.types import LLMMessage
from dana.common.observable import observable
from dana.common.protocols import DictParams
from dana.common.protocols.types import LearningPhase
logger = get_logger()


if TYPE_CHECKING:
    from dana.core.agent.star_agent import STARAgent
    from dana.core.agent.timeline import Timeline

class LearnerProtocol(Protocol):
    def _reflect_acquisitive(self, trace_acquisitive: DictParams) -> DictParams:
        ...

    def _reflect_episodic(self, trace_episodic: DictParams) -> DictParams:
        ...

    def _reflect_integrative(self, trace_integrative: DictParams) -> DictParams:
        ...

    def _reflect_retentive(self, trace_retentive: DictParams) -> DictParams:
        ...

    def _load_acquisitive(self) -> list[str]:
        ...

    def _load_episodic(self) -> str | None:
        ...

    def query_learnings(self, query: str, phase: LearningPhase | None = None) -> str | None:
        ...

    def _load_feedback(self) -> Any:
        ...

    def save_feedback(self, feedback: Any) -> None:
        ...
class Learner:
    """Component providing STAR learning phase implementations."""

    def __init__(self, agent: "STARAgent"):
        """
        Initialize the component with a reference to the agent.

        Args:
            agent: The agent instance this component belongs to
        """
        self._agent = agent

    # ============================================================================
    # LEARNING PHASES (STAR REFLECTION IMPLEMENTATIONS)
    # ============================================================================

    @observable
    def _reflect_acquisitive(
        self, trace_acquisitive: DictParams
    ) -> DictParams:
        """
        Reflect on the acquisitions (immediate learning phase).

        Args:
            trace_acquisitive from the ACT phase containing tool_results

        Returns:
            trace_learning: Learning insights from the acquisitions
        """
        tool_results = trace_acquisitive.get("tool_results", [])

        trace_learning = {
            "acquisitions_summary": (
                f"Processed acquisitions with {len(tool_results)} tool results"
            ),
            "timestamp": datetime.now().isoformat(),
            "tool_results": tool_results,
        }
        return {"trace_learning": trace_learning}

    @observable
    def _reflect_episodic(self, trace_episodic: DictParams) -> DictParams:
        """
        Reflect on an episode (collection of experiences).

        Args:
            trace_episodic: Collection of experiences from the episode

        Returns:
            trace_learning: Learning insights from the episode
        """
        # Basic episode reflection - can be overridden by subclasses
        trace_learning = {
            "episode_summary": (
                f"Processed episode with {len(trace_episodic)} interactions"
            ),
            "timestamp": datetime.now().isoformat(),
        }
        return {"trace_learning": trace_learning}

    @observable
    def _reflect_integrative(
        self, trace_integrative: DictParams
    ) -> DictParams:
        """
        Reflect on integration (collection of episodes).

        Args:
            trace_integrative: Collection of episodes to integrate

        Returns:
            trace_learning: Integrated learning insights
        """
        # Basic integration reflection - can be overridden by subclasses
        trace_learning = {
            "integrative_summary": (
                "Integrated learning from multiple episodes"
            ),
            "timestamp": datetime.now().isoformat(),
        }
        return {"trace_learning": trace_learning}

    @observable
    def _reflect_retentive(self, trace_retentive: DictParams) -> DictParams:
        """
        Reflect on retention (long-term learning).

        Args:
            trace_retentive: Long-term learning data

        Returns:
            trace_learning: Retained learning insights
        """
        # Basic retention reflection - can be overridden by subclasses
        trace_learning = {
            "retentive_summary": "Long-term learning retention",
            "timestamp": datetime.now().isoformat(),
        }
        return {"trace_learning": trace_learning}

    def _load_acquisitive(self) -> list[str]:
        return []

    def _load_episodic(self) -> str | None:
        return None

    def query_learnings(self, query: str, phase: LearningPhase | None = None) -> str | None:
        return None

    def _load_feedback(self) -> Any:
        return None

    def save_feedback(self, feedback: Any) -> None:
        pass

class DefaultLearner(LearnerProtocol):
    """Component providing STAR learning phase implementations."""

    def __init__(self, agent: "STARAgent"):
        """
        Initialize the component with a reference to the agent.

        Args:
            agent: The agent instance this component belongs to
        """
        self._agent = agent

    # ============================================================================
    # LEARNING PHASES (STAR REFLECTION IMPLEMENTATIONS)
    # ============================================================================

    @observable
    def _reflect_acquisitive(self, trace_acquisitive: DictParams) -> DictParams:
        """
        Reflect on the acquisitions (immediate learning phase) using LLM analysis.

        Args:
            trace_acquisitive: Data from the ACT phase containing:
              - caller_message (str): Original caller message
              - response (str): Response from THINK phase
              - reasoning (str): Reasoning from THINK phase
              - tool_calls (list[DictParams]): Tool calls made
              - tool_results (list[DictParams]): Tool results received

        Returns:
            trace_learning: Learning insights from the acquisitions
        """
        try:
            # Generate loop ID
            loop_id = str(uuid4())
            timestamp = datetime.now()

            # Get timeline context
            timeline = getattr(self._agent, "_timeline", None)
            timeline_context = []
            if timeline:
                timeline_context = self._get_timeline_context_for_loop(timeline)

            # Load previous learning markdown (if exists)
            previous_learning_markdown = self._load_acquisitive_learning_markdown()

            # Build analysis context for LLM
            try:
                available_tools = self._agent._prompt_engineer.available_tools_prompt
            except Exception as e:
                logger.error(f"Error getting available tools: {e}", exc_info=True)
                available_tools = "Tools' schema is not available"
            context = self._build_analysis_context(trace_acquisitive, timeline_context)

            # Call LLM for markdown analysis (with previous learning if exists)
            llm_markdown = self._call_llm_for_analysis(context, available_tools, previous_learning_markdown)

            # Store learning markdown (replaces old file)
            self._store_acquisitive_learning_markdown(llm_markdown)

            trace_learning = {
                "loop_id": loop_id,
                "timestamp": timestamp.isoformat(),
                "llm_analysis_markdown": llm_markdown,
                "is_first_loop": previous_learning_markdown is None,
            }
            return {"trace_learning": trace_learning}

        except Exception as e:
            # Log error but don't fail STAR loop
            logger.error(f"Acquisitive learning failed: {e}", exc_info=True)
            trace_learning = {
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
            return {"trace_learning": trace_learning}

    def _get_timeline_context_for_loop(self, timeline: "Timeline", max_entries: int = 5) -> list[dict]:
        """
        Extract timeline context for the current loop.

        Finds the latest user_message entry and includes a few entries before it
        for context.

        Args:
            timeline: Timeline object
            max_entries: Maximum number of entries before user message to include

        Returns:
            List of timeline entries with type, content, timestamp
        """
        from dana.core.agent.timeline import TimelineEntryType

        timeline_context = []

        # Find latest user_message entry
        user_message_index = None
        for i in range(len(timeline.timeline) - 1, -1, -1):
            entry = timeline.timeline[i]
            if entry.entry_type == TimelineEntryType.USER_MESSAGE:
                user_message_index = i
                break

        if user_message_index is None:
            # No user message found, return empty context
            return timeline_context

        # Extract entries from max(0, index - max_entries) to index + 1
        start_index = max(0, user_message_index - max_entries)
        end_index = user_message_index + 1

        for i in range(start_index, end_index):
            entry = timeline.timeline[i]
            timeline_context.append({
                "type": entry.entry_type.value,
                "content": entry.content,
                "timestamp": entry.timestamp.isoformat(),
                "metadata": entry.metadata,
            })

        return timeline_context

    def _load_acquisitive_learning_markdown(self) -> str | None:
        """
        Load existing acquisitive learning markdown from disk.

        Returns:
            Learning markdown string if exists, None otherwise
        """
        try:
            storage_path = self._get_acquisitive_storage_path()
            learnings_file = storage_path / "learnings.md"

            if not learnings_file.exists():
                return None

            return learnings_file.read_text()
        except Exception as e:
            logger.warning(f"Failed to load acquisitive learning markdown: {e}")
            return None

    def _get_acquisitive_storage_path(self) -> Path:
        """
        Get acquisitive learning storage path following EventLog pattern.

        Path: {codec.__qualname__}/{agent.__class__.__qualname__}__{filename}/learnings/acquisitive

        Returns:
            Path to acquisitive learning storage directory
        """
        from dana.config.storage_config import FileStorageConfig

        storage_config = FileStorageConfig()
        base_path = Path(storage_config.workspace_folder)

        # Follow EventLog pattern
        filepath = inspect.getfile(self._agent.__class__)
        filename = Path(filepath).stem

        # Get codec from agent
        codec = getattr(self._agent, "_codec", None)
        if codec is None or "magic" in str(codec.__qualname__):
            # Try to get from prompt_engineer if available
            prompt_engineer = getattr(self._agent, "_prompt_engineer", None)
            if prompt_engineer:
                codec = getattr(prompt_engineer, "_codec", None)

        codec_name = codec.__qualname__ if codec else "default"

        relative_path = f"{codec_name}/{self._agent.__class__.__qualname__}__{filename}/learnings/acquisitive"
        storage_path = base_path / relative_path
        storage_path.mkdir(parents=True, exist_ok=True)
        return storage_path

    def _build_analysis_context(self, trace_acquisitive: DictParams, timeline_context: list[dict]) -> str:
        """
        Build context string for LLM analysis.

        Args:
            trace_acquisitive: Data from ACT phase
            timeline_context: Timeline entries for context

        Returns:
            Formatted context string
        """
        context_parts = []

        # Add timeline context
        if timeline_context:
            context_parts.append("=== Timeline Context ===")
            for entry in timeline_context:
                try:
                    context_parts.append(f"[{entry['type']}] {entry['content'][:500]}...")
                except Exception as e:
                    logger.error(f"Error adding timeline context: {e}", exc_info=True)
            context_parts.append("")

        # Add caller message
        caller_message = trace_acquisitive.get("caller_message", "")
        if caller_message:
            context_parts.append(f"=== User Request ===\n{caller_message}\n")

        # Add reasoning
        reasoning = trace_acquisitive.get("reasoning", "")
        if reasoning:
            context_parts.append(f"=== Agent Reasoning ===\n{reasoning[:500]}...\n")

        # Add response
        response = trace_acquisitive.get("response", "")
        if response:
            context_parts.append(f"=== Agent Response ===\n{response[:500]}...\n")

        # Add tool calls
        tool_calls = trace_acquisitive.get("tool_calls", [])
        if tool_calls:
            context_parts.append(f"=== Tool Calls ({len(tool_calls)}) ===")
            for i, tool_call in enumerate(tool_calls, 1):
                function = tool_call.get("function", "unknown")
                arguments = tool_call.get("arguments", {})
                context_parts.append(f"{i}. {function}")
                context_parts.append(f"   Arguments: {str(arguments)[:300]}...")
            context_parts.append("")

        # Add tool results
        tool_results = trace_acquisitive.get("tool_results", [])
        if tool_results:
            context_parts.append(f"=== Tool Results ({len(tool_results)}) ===")
            for i, result in enumerate(tool_results, 1):
                result_type = result.get("type", "unknown")
                result_content = str(result.get("result", ""))[:500]
                context_parts.append(f"{i}. [{result_type}] {result_content}...")
            context_parts.append("")

        return "\n".join(context_parts)

    def _call_llm_for_analysis(self, context: str, available_tools: str, previous_learning_markdown: str | None = None) -> str:
        """
        Call LLM to analyze the STAR loop execution.

        Args:
            context: Formatted context string
            available_tools: Available tools schema
            previous_learning_markdown: Previous accumulated learning markdown (if exists)

        Returns:
            LLM markdown response
        """
        system_prompt = f"""You are a learning reflection assistant analyzing agent STAR loop executions.

You are given the following tools' schemas:
<schemas>
{available_tools}
</schemas>


Analyze the agent's interaction and provide insights in markdown format with the following sections:

## What Worked Well
- [List successful patterns, effective tool usage, good parameter choices]

## Tool Call Failures
For each failed or problematic tool call:
- **Tool**: [tool name]
- **Parameters**: [parameters used]
- **Issue**: [description of the problem]
- **Improvement**: [suggestion for improvement]

## Tool Selection
- **Correct Tools**: [Yes/No]
- **Selected Tools**: [list of tools used]
- **Alternative Tools**: [suggested alternatives if any]
- **Reasoning**: [explanation]

## Implied Patterns
- [Pattern 1]
- [Pattern 2]
- ...

## Suggestions for Future Iterations
- [Suggestion 1]
- [Suggestion 2]
- ..."""

        if previous_learning_markdown:
            # Subsequent loop: include previous learning and generate updated version
            user_prompt = f"""Generate the latest version of accumulated learning insights that includes information from previous loops and this new loop execution.

=== Previous Accumulated Learning ===
{previous_learning_markdown}

=== Current Loop Execution ===
{context}

Provide your updated analysis in the markdown format specified above. 
The new version should consolidate insights from previous loops and this new loop, 
removing duplicates and refining patterns based on accumulated evidence. 
Make sure to include all relevant information from the previous version while 
incorporating new insights from the current loop execution."""
        else:
            # First loop: analyze current loop only
            user_prompt = f"""Analyze this agent STAR loop execution:

{context}

Provide your analysis in the markdown format specified above."""

        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_prompt),
        ]

        try:
            llm_response = self._agent.llm_client.chat_response_sync(
                messages,
                agent_id=self._agent.object_id,
                agent_type=self._agent.agent_type,
            )

            # Extract markdown text from response
            markdown_text = (
                llm_response.content
                if hasattr(llm_response, "content")
                else str(llm_response)
            )
            return markdown_text
        except Exception as e:
            logger.error(f"LLM call failed for acquisitive learning: {e}")
            return f"Error: LLM analysis failed: {str(e)}"

    def _parse_markdown_insights(self, markdown_text: str) -> dict:
        """
        Parse markdown insights using regex to extract structured data.

        Args:
            markdown_text: LLM markdown response

        Returns:
            Dictionary with parsed insights
        """
        insights = {
            "what_worked_well": [],
            "tool_failures": [],
            "tool_selection": {},
            "patterns": [],
            "suggestions": [],
        }

        try:
            # Extract "What Worked Well" section
            worked_well_match = re.search(
                r"##\s+What Worked Well\s*\n(.*?)(?=\n##|$)",
                markdown_text,
                re.DOTALL | re.IGNORECASE,
            )
            if worked_well_match:
                worked_well_text = worked_well_match.group(1)
                list_items = re.findall(r"-\s+(.+?)(?=\n-|\n##|$)", worked_well_text, re.DOTALL)
                insights["what_worked_well"] = [item.strip() for item in list_items]

            # Extract "Tool Call Failures" section
            failures_match = re.search(
                r"##\s+Tool Call Failures\s*\n(.*?)(?=\n##|$)",
                markdown_text,
                re.DOTALL | re.IGNORECASE,
            )
            if failures_match:
                failures_text = failures_match.group(1)
                # Extract each failure entry
                failure_pattern = r"\*\*Tool\*\*:\s*(.+?)\n\*\*Parameters\*\*:\s*(.+?)\n\*\*Issue\*\*:\s*(.+?)\n\*\*Improvement\*\*:\s*(.+?)(?=\n\*\*|\n##|$)"
                failures = re.findall(failure_pattern, failures_text, re.DOTALL)
                for failure in failures:
                    insights["tool_failures"].append({
                        "tool": failure[0].strip(),
                        "parameters": failure[1].strip(),
                        "issue": failure[2].strip(),
                        "improvement": failure[3].strip(),
                    })

            # Extract "Tool Selection" section
            selection_match = re.search(
                r"##\s+Tool Selection\s*\n(.*?)(?=\n##|$)",
                markdown_text,
                re.DOTALL | re.IGNORECASE,
            )
            if selection_match:
                selection_text = selection_match.group(1)
                # Extract fields
                correct_match = re.search(r"\*\*Correct Tools\*\*:\s*(.+?)(?=\n|$)", selection_text, re.IGNORECASE)
                selected_match = re.search(r"\*\*Selected Tools\*\*:\s*(.+?)(?=\n|$)", selection_text, re.IGNORECASE)
                alternative_match = re.search(r"\*\*Alternative Tools\*\*:\s*(.+?)(?=\n|$)", selection_text, re.IGNORECASE)
                reasoning_match = re.search(r"\*\*Reasoning\*\*:\s*(.+?)(?=\n##|$)", selection_text, re.DOTALL | re.IGNORECASE)

                insights["tool_selection"] = {
                    "correct_tools": correct_match.group(1).strip() if correct_match else None,
                    "selected_tools": selected_match.group(1).strip() if selected_match else None,
                    "alternative_tools": alternative_match.group(1).strip() if alternative_match else None,
                    "reasoning": reasoning_match.group(1).strip() if reasoning_match else None,
                }

            # Extract "Implied Patterns" section
            patterns_match = re.search(
                r"##\s+Implied Patterns\s*\n(.*?)(?=\n##|$)",
                markdown_text,
                re.DOTALL | re.IGNORECASE,
            )
            if patterns_match:
                patterns_text = patterns_match.group(1)
                list_items = re.findall(r"-\s+(.+?)(?=\n-|\n##|$)", patterns_text, re.DOTALL)
                insights["patterns"] = [item.strip() for item in list_items]

            # Extract "Suggestions for Future Iterations" section
            suggestions_match = re.search(
                r"##\s+Suggestions for Future Iterations\s*\n(.*?)(?=\n##|$)",
                markdown_text,
                re.DOTALL | re.IGNORECASE,
            )
            if suggestions_match:
                suggestions_text = suggestions_match.group(1)
                suggestions_list_items = re.findall(r"-\s+(.+?)(?=\n-|\n##|$)", suggestions_text, re.DOTALL)
                insights["suggestions"] = [item.strip() for item in suggestions_list_items]

        except Exception as e:
            logger.warning(f"Failed to parse markdown insights: {e}")
            # Return partial insights if parsing fails

        return insights

    def _store_acquisitive_learning_markdown(self, markdown_content: str) -> None:
        """
        Store acquisitive learning markdown to disk.

        Args:
            markdown_content: LLM-generated markdown with accumulated insights
        """
        try:
            storage_path = self._get_acquisitive_storage_path()
            learnings_file = storage_path / "learnings.md"

            # Write markdown file (replaces old file)
            learnings_file.write_text(markdown_content)

            logger.info(f"Stored acquisitive learning markdown: {learnings_file}")

        except Exception as e:
            logger.error(f"Failed to store acquisitive learning markdown: {e}", exc_info=True)

    @observable
    def _reflect_episodic(self, trace_episodic: DictParams) -> DictParams:
        """
        Reflect on an episode (collection of experiences).

        Args:
            trace_episodic: Collection of experiences from the episode

        Returns:
            trace_learning: Learning insights from the episode
        """
        # Basic episode reflection - can be overridden by subclasses
        trace_learning = {
            "episode_summary": f"Processed episode with {len(trace_episodic)} interactions",
            "timestamp": datetime.now().isoformat(),
        }
        return {"trace_learning": trace_learning}

    @observable
    def _reflect_integrative(self, trace_integrative: DictParams) -> DictParams:
        """
        Reflect on integration (collection of episodes).

        Args:
            trace_integrative: Collection of episodes to integrate

        Returns:
            trace_learning: Integrated learning insights
        """
        # Basic integration reflection - can be overridden by subclasses
        trace_learning = {"integrative_summary": "Integrated learning from multiple episodes", "timestamp": datetime.now().isoformat()}
        return {"trace_learning": trace_learning}

    @observable
    def _reflect_retentive(self, trace_retentive: DictParams) -> DictParams:
        """
        Reflect on retention (long-term learning).

        Args:
            trace_retentive: Long-term learning data

        Returns:
            trace_learning: Retained learning insights
        """
        # Basic retention reflection - can be overridden by subclasses
        trace_learning = {
            "retentive_summary": "Long-term learning retention",
            "timestamp": datetime.now().isoformat(),
        }
        return {"trace_learning": trace_learning}

    def _load_acquisitive(self) -> list[str]:
        return []

    def _load_episodic(self) -> str | None:
        return None

    def query_learnings(self, query: str, phase: LearningPhase | None = None) -> str | None:
        return None

    def _load_feedback(self) -> Any:
        return None

    def save_feedback(self, feedback: Any) -> None:
        pass