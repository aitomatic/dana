"""
Learner: Handles the four learning phases of STAR reflection.

This component provides functionality for:
- ACQUISITIVE learning (immediate experience reflection)
- EPISODIC learning (episode-level reflection)
- INTEGRATIVE learning (multi-episode integration)
- RETENTIVE learning (long-term learning)
"""

import json
from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from structlog import get_logger

from dana.common.llm.types import LLMMessage
from dana.common.observable import observable
from dana.common.protocols import DictParams
from dana.common.protocols.types import LearningPhase
from dana.core.agent.components.learner import LearnerProtocol
from dana.common.llm.debug_logger import get_debug_logger
from dana.core.agent.timeline import TimelineEntry
from pathlib import Path
from rank_bm25 import BM25Okapi
import numpy as np

logger = get_logger()

if TYPE_CHECKING:
    from dana.core.agent.star_agent import STARAgent
    from dana.core.agent.timeline import Timeline
    from dana.repositories.repository_protocol import LearningRepositoryProtocol
    from dana.repositories.repository_factory import RepositoryFactory

class BM25SearchEngine:
    def __init__(self, corpus: list[str]):
        self._original_corpus = corpus
        self.corpus = [self.text_to_words(text) for text in corpus]
        self.bm25 = BM25Okapi(self.corpus)

    @staticmethod
    def text_to_words(text: str) -> list[str]:
        return [word.lower() for word in text.split(" ")]

    def search(self, query: str, n: int = 1) -> list[str]:
        top_n = self.get_top_n_indices(query, n)
        return [self._original_corpus[i] for i in top_n]

    def get_top_n_indices(self, query: str, n: int = 1) -> list[int]:
        scores = self.bm25.get_scores(self.text_to_words(query))
        return np.argsort(scores)[::-1][:n].tolist()




class WilliamLearner(LearnerProtocol):
    """Component providing STAR learning phase implementations."""

    def __init__(self, agent: "STARAgent", repository: "LearningRepositoryProtocol | None" = None, repository_factory: "RepositoryFactory | None" = None):
        """
        Initialize the component with a reference to the agent.

        Args:
            agent: The agent instance this component belongs to
            repository: Learning repository (if None and agent provided, creates default via factory)
            repository_factory: Optional repository factory (uses DEFAULT_REPOSITORY_FACTORY if not provided)
        """
        # NOTE : self._agent will be set by the agent when it is initialized the agent
        self._agent = agent
        self.acquisitive_memory = []
        self.episodic_memory = None

        # Initialize repository if provided, otherwise create default from agent using factory
        if repository:
            self._repository = repository
        elif agent:
            from dana.repositories.repository_factory import DEFAULT_REPOSITORY_FACTORY, RepositoryType
            factory = repository_factory or DEFAULT_REPOSITORY_FACTORY
            self._repository = factory.create(RepositoryType.LEARNING, agent=agent)
        else:
            self._repository = None

    # ============================================================================
    # LEARNING PHASES (STAR REFLECTION IMPLEMENTATIONS)
    # ============================================================================

    @observable
    def query_learnings(self, query: str, phase: LearningPhase | None = None) -> str | None:
        if phase == LearningPhase.ACQUISITIVE:
            if not self.acquisitive_memory:
                self.acquisitive_memory = self._load_acquisitive()
            if not self.acquisitive_memory:
                return None
            # SIMPLE RETRIEVAL FIRST
            engine = BM25SearchEngine(self.acquisitive_memory)
            results = engine.search(query, n=3)
            return "\n".join(results)
        elif phase == LearningPhase.EPISODIC:
            if not self.episodic_memory:
                self.episodic_memory = self._load_episodic()
            return self.episodic_memory
        else:
            return None


    @property
    def session_id(self) -> str | None:
        # Get session_id from agent if available
        if hasattr(self._agent, "_session_id") and "magic" not in str(self._agent._session_id):
            return self._agent._session_id
        _event_log = getattr(self._agent, "_event_log", None)
        if _event_log is None or "magic" in str(_event_log):
            # Try to get from timeline or other sources
            session_id = None
        else:
            session_id = _event_log._current_session_id
        return session_id

    def _get_episodic_storage_path(self) -> Path:
        return self._repository._base_storage_path / "learnings" / self.session_id / "episodic"

    def _get_acquisitive_storage_path(self) -> Path:
        return self._repository._base_storage_path / "learnings" / self.session_id / "acquisitive"


    def _reflect_acquisitive(
        self, trace_acquisitive: DictParams
    ) -> DictParams:
        """
        Reflect on the acquisitions (immediate learning phase).

        Args:
            trace_acquisitive from the ACT phase containing:
              - caller_message (str): Original caller message
              - response (str): Response from THINK phase
              - reasoning (str): Reasoning from THINK phase
              - tool_calls (list[DictParams]): Tool calls made
              - tool_results (list[DictParams]): Tool results received

        Returns:
            trace_learning: Learning insights from the acquisitions
        """
        # return {"trace_learning": {}}
        try:
            # Generate loop ID
            loop_id = str(uuid4())
            timestamp = datetime.now()

            # Get timeline context
            timeline = getattr(self._agent, "_timeline", None)
            timeline_context = []
            if timeline:
                timeline_context = self._get_timeline_context_for_loop(timeline)

            # Call _reflect_action() to get learning_note
            result = self._reflect_action(trace_acquisitive)
            learning_note = result["trace_learning"].get("learning_note", "")
            reflection_context = result["trace_learning"].get("reflection_context", "")
            
            # Keep in-memory for backward compatibility
            self.acquisitive_memory.append(learning_note)

            

            # Build complete JSON structure
            loop_data = {
                "loop_id": loop_id,
                "timestamp": timestamp.isoformat(),
                "session_id": self.session_id,
                "query_id": None,  # Can be set if available
                "timeline_context": timeline_context,
                "caller_message": trace_acquisitive.get("caller_message", ""),
                "response": trace_acquisitive.get("response", ""),
                "reasoning": trace_acquisitive.get("reasoning", ""),
                "tool_calls": trace_acquisitive.get("tool_calls", []),
                "tool_results": trace_acquisitive.get("tool_results", []),
                "insights": {},  # Can be populated if structured insights are available
                "learning_note": learning_note,
            }

            # Store as JSON file
            self._store_acquisitive_loop_json(loop_data, loop_id, timestamp)

            trace_learning = {
                "loop_id": loop_id,
                "timestamp": timestamp.isoformat(),
                "learning_note": learning_note,
                "simple_summary": result["trace_learning"].get("simple_summary", ""),
                "reflection_context": reflection_context,
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

    @observable
    def _reflect_episodic(self, trace_episodic: DictParams) -> DictParams:
        """
        Reflect on an episode (collection of experiences).

        Args:
            trace_episodic: Collection of experiences from the episode

        Returns:
            trace_learning: Learning insights from the episode
        """
        try:
            # Load previous episodic learning (if exists)
            previous_learning = self._load_episodic_learning()

            messages = []

            # System prompt for learning/knowledge extraction
            system_prompt = """You are a learning and knowledge extraction
assistant.
Your role is to analyze agent interactions and extract:
1. Patterns and recurring themes
2. What worked well and what didn't
3. Key insights and learnings
4. Actionable knowledge for future improvements
5. Relationships between actions and outcomes

Be analytical, concise, and focus on extracting actionable
knowledge."""

            messages.append(LLMMessage(role="system", content=system_prompt))
            timeline = self._agent._timeline
            timeline.timeline = list(timeline.read_since(checkpoint=-100))
            # Convert timeline to messages for learning context
            if timeline:
                timeline_messages = timeline.to_llm_messages(
                    separate_latest_user=False, max_tokens=40000
                )

                if timeline_messages:
                    # Include previous learning if available
                    if previous_learning:
                        messages.append(
                            LLMMessage(
                                role="user",
                                content=f"=== Previous Accumulated Learning ===\n{previous_learning}\n\nNow analyze the current session timeline:",
                            )
                        )

                    # Wrap timeline in structured format for learning analysis
                    timeline_lines = [
                        "<SESSION_TIMELINE>",
                        "Analyze the following agent interaction timeline:",
                        "",
                    ]

                    for msg in timeline_messages:
                        role_indicator = (
                            "USER" if msg.role == "user" else "AGENT"
                        )
                        timeline_lines.append(
                            f"<{role_indicator}>{msg.content}</{role_indicator}>"
                        )

                    timeline_lines.append("</SESSION_TIMELINE>")
                    timeline_content = "\n".join(timeline_lines)
                    messages.append(
                        LLMMessage(role="user", content=timeline_content)
                    )

                    # Add learning request
                    if previous_learning:
                        learning_prompt = """Based on the previous accumulated learning and the current session timeline above,
You need to consider the following:
1. Key patterns and recurring behaviors
2. Successful strategies and approaches
3. Areas for improvement
4. Actionable insights for future interactions

You need to learn from the whole session and extract the knowledge note to perform better in the future for this task or similar tasks.
Format: [Condition] [Advice of what should do]

Update your accumulated learning by consolidating insights from previous learning and this new session."""
                    else:
                        learning_prompt = """Based on the session timeline above,
You need to consider the following:
1. Key patterns and recurring behaviors
2. Successful strategies and approaches
3. Areas for improvement
4. Actionable insights for future interactions

You need to learn from the whole session and extract the knowledge note to perform better in the future for this task or similar tasks.
Format: [Condition] [Advice of what should do]"""
                    messages.append(
                        LLMMessage(role="user", content=learning_prompt)
                    )
                else:
                    # No timeline content, provide default learning request
                    messages.append(
                        LLMMessage(
                            role="user",
                            content=(
                                "No session timeline available. "
                                "Provide general learning insights "
                                "for agent improvement."
                            ),
                        )
                    )

            # Debug logging
            debug_logger = get_debug_logger()
            debug_logger.log_agent_interaction(
                agent_id=self._agent.object_id,
                agent_type=self._agent.agent_type,
                interaction_type="build_session_learning_llm_request",
                content=f"Built {len(messages)} messages for learning",
                metadata={
                    "message_count": len(messages),
                    "timeline_entries": (
                        len(timeline.timeline) if timeline else 0
                    ),
                },
            )

            llm_response = self._agent.llm_client.chat_response_sync(
                messages,
                agent_id=self._agent.object_id,
                agent_type=self._agent.agent_type,
            )

            episodic_content = (
                llm_response.content
                if hasattr(llm_response, "content")
                else str(llm_response)
            )

            # Keep in-memory for backward compatibility
            self.episodic_memory = episodic_content

            # Store episodic learning to disk
            self._store_episodic_learning(episodic_content)

            trace_learning = {
                "simple_summary": episodic_content,
                "learning_note": episodic_content,
                "timestamp": datetime.now().isoformat(),
                "reflection_context": "",
            }
            
            return {"trace_learning": trace_learning}

        except Exception as e:
            # Log error but don't fail STAR loop
            logger.error(f"Episodic learning failed: {e}", exc_info=True)
            trace_learning = {
                "error": str(e),
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

    def _reflect_action(self, trace_action: DictParams) -> DictParams:
        """
        Reflect on action using LLM to generate insights.

        Args:
            trace_action: Action data from the ACT phase
              - response (str): Response from the THINK phase
              - tool_calls (list[DictParams]): Tool calls made
              - tool_results (list[DictParams]): Tool results received
              - caller_message (str): Original caller message

        Returns:
            trace_learning: Action insights from LLM reflection
        """
        # Build reflection prompt
        response = trace_action.get("response", "")
        tool_calls = trace_action.get("tool_calls", [])
        tool_results = trace_action.get("tool_results", [])
        caller_message = trace_action.get("caller_message", "")

        # Construct reflection context
        reflection_context = []
        if caller_message:
            reflection_context.append(f"User Request: {caller_message}")
        if response:
            reflection_context.append(f"Agent Response: {response}")
        if tool_calls:
            reflection_context.append(f"Tool Calls Made: {len(tool_calls)}")
            for i, tool_call in enumerate(tool_calls, 1):
                tool_type = tool_call.get("type", "unknown")
                tool_id = tool_call.get("target", {}).get("id", "unknown")
                reflection_context.append(f"  {i}. {tool_type} - {tool_id}")
        if tool_results:
            reflection_context.append(
                f"Tool Results Received: {len(tool_results)}"
            )
            for i, result in enumerate(tool_results, 1):
                result_summary = str(result.get("result", ""))[:100]
                reflection_context.append(f"  {i}. {result_summary}...")

        context_text = (
            "\n".join(reflection_context)
            if reflection_context
            else "No context available"
        )

        # Build LLM messages for reflection
        system_prompt = """You are a learning reflection assistant.
Analyze the agent's interaction and provide insights on:
1. What worked well
2. What could be improved
3. Key learnings or patterns observed
4. Suggestions for future interactions

If work well, you can return no advice.
Just return the advice only, no other analysis.
Format: [Condition] [Advice of what should do]"""

        user_prompt = f"""Reflect on this agent interaction:

{context_text}

Provide a brief reflection (2-3 sentences) on what the agent
learned from this interaction."""

        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_prompt),
        ]

        # Make LLM call
        llm_response = self._agent.llm_client.chat_response_sync(
            messages,
            agent_id=self._agent.object_id,
            agent_type=self._agent.agent_type,
        )

        # Extract reflection text from response
        reflection_text = (
            llm_response.content
            if hasattr(llm_response, "content")
            else str(llm_response)
        )

        trace_learning = {
            "simple_summary": reflection_text,
            "learning_note": reflection_text,
            "timestamp": datetime.now().isoformat(),
            "reflection_context": context_text,
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

    def _store_acquisitive_loop_json(self, loop_data: dict, loop_id: str, timestamp: datetime) -> None:
        """
        Store single acquisitive loop as JSON file with proper naming.

        Filename pattern: loop_{YYYYMMDD}_{HHMMSS}_{microseconds}_{loop_id_short}.json

        Args:
            loop_data: Complete loop data dictionary to store
            loop_id: Full UUID string
            timestamp: Datetime object for the loop
        """
        if self._repository is None:
            raise ValueError("Cannot store acquisitive loop: repository is None. Initialize WilliamLearner with repository or agent.")

        session_id = self.session_id
        if session_id is None:
            raise ValueError("Cannot store acquisitive loop: session_id is None. Set session_id on agent first.")

        try:
            self._repository.save_acquisitive_loop(session_id, loop_data, loop_id, timestamp)
        except Exception as e:
            logger.error(f"Failed to store acquisitive loop JSON: {e}", exc_info=True)

    def _load_episodic_learning(self) -> str | None:
        """
        Load existing episodic learning from disk.

        Returns:
            Episodic learning content string if exists, None otherwise
        """
        if self._repository is None:
            logger.warning("Cannot load episodic learning: repository is None")
            return None

        session_id = self.session_id
        if session_id is None:
            logger.warning("Cannot load episodic learning: session_id is None")
            return None

        try:
            return self._repository.load_episodic_learning(session_id)
        except Exception as e:
            logger.warning(f"Failed to load episodic learning: {e}")
            return None

    def _store_episodic_learning(self, content: str) -> None:
        """
        Store episodic learning to disk.

        Args:
            content: Episodic learning content to store
        """
        if self._repository is None:
            raise ValueError("Cannot store episodic learning: repository is None. Initialize WilliamLearner with repository or agent.")

        session_id = self.session_id
        if session_id is None:
            raise ValueError("Cannot store episodic learning: session_id is None. Set session_id on agent first.")

        try:
            self._repository.save_episodic_learning(session_id, content)
        except Exception as e:
            logger.error(f"Failed to store episodic learning: {e}", exc_info=True)

    def _load_acquisitive(self) -> list[str]:
        """
        Load acquisitive learning from disk.

        Loads all learning_note values from all JSON files in the acquisitive folder.

        Returns:
            list[str]: Acquisitive learning notes
        """
        if self._repository is None:
            logger.warning("Cannot load acquisitive learning: repository is None")
            return []

        session_id = self.session_id
        if session_id is None:
            logger.warning("Cannot load acquisitive learning: session_id is None")
            return []

        try:
            return self._repository.load_acquisitive_loops(session_id)
        except Exception as e:
            logger.warning(f"Failed to load acquisitive learning: {e}")
            return []

    def _load_episodic(self) -> str | None:
        """
        Load episodic learning from disk.

        Returns:
            Episodic learning content string if exists, None otherwise
        """
        try:
            return self._load_episodic_learning()
        except Exception as e:
            logger.warning(f"Failed to load episodic learning: {e}")
            return None

    def save_feedback(self, feedback: Any) -> None:
        if self._repository is None:
            raise ValueError("Cannot store feedback: repository is None. Initialize WilliamLearner with repository or agent.")

        session_id = self.session_id
        if session_id is None:
            raise ValueError("Cannot store feedback: session_id is None. Set session_id on agent first.")

        try:
            self._repository.save_feedback(session_id, str(feedback))
        except Exception as e:
            logger.error(f"Failed to store feedback: {e}", exc_info=True)

    def _load_feedback(self) -> Any:
        if self._repository is None:
            logger.warning("Cannot load feedback: repository is None")
            return None

        session_id = self.session_id
        if session_id is None:
            logger.warning("Cannot load feedback: session_id is None")
            return None

        try:
            return self._repository.load_feedback(session_id)
        except Exception as e:
            logger.warning(f"Failed to load feedback: {e}")
            return None

    def _get_timeline_entries(self, checkpoint: int = -100) -> list["TimelineEntry"]:
        timeline = self._agent._timeline
        return list(timeline.read_since(checkpoint=checkpoint))