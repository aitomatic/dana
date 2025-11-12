"""
WilliamLearner2 - Enhanced learner with feedback-aware episodic learning.

This learner extends WilliamLearner with two modes:
- With feedback: When feedback folder exists, uses enhanced learning logic
- Without feedback: Falls back to standard WilliamLearner episodic learning
"""

from datetime import datetime

from .william_learner import WilliamLearner
from dana.common.protocols import DictParams
from dana.common.llm.types import LLMMessage
from dana.common.llm.debug_logger import get_debug_logger
from structlog import get_logger

logger = get_logger()


SYSTEM_PROMPT = """
You are the **HVAC-Learning Assistant**.
Convert every new **plan + execution feedback** cycle into concise Markdown **Learning Notes** that capture THIS system’s real-world behaviour and actionable rules.

## Your 5 Obligations  
1. **Pair each action with its feedback** (`action_index` → feedback block).  
2. **Compute fresh metrics** for the pair  
   • `cooling_rate = (start_temp_f – target_temp_f) / time_needed_minutes`  
   • `buffer_gap  = meeting_start_time – reached_time` (− = late)  
3. **Label outcome** (`success` / `failed`) and explain why.  
4. **Maintain value ranges & formulas**—expand or tighten as evidence grows.
5. **Write guidance** that would have prevented today’s failure next time. This should be a comprehensive guidance for the whole session, not just the current action with step by step advice when to use turbo mode, calculation formula and latest values like cooling rate (turbo/ non-turbo), buffer gap, etc.

### INPUT ORDER  
1. `<previous_learning> … </previous_learning>`  
2. CURRENT_ENVIRONMENT block  
3. PLAN block (array with `action_index`)  
4. `<feedback> … </feedback>`  

### OUTPUT — Markdown ONLY  
```
<updated_learning>

[Condition: …] Observation → Advice

…
</updated_learning>
```

<previous_learning>
{previous_learning}
</previous_learning>
"""

FEEDBACK_PROMPT = """
<feedback>
{feedback_content}
</feedback>
"""

LEARNING_PROMPT = """
Using the data above (plan, feedback, previous learning):

• Execute the 5-step process defined in SYSTEM_PROMPT.  
• Think silently first, then emit only the Markdown block required.

(Do not add narrative, JSON, or code.)
"""


class WilliamLearner3(WilliamLearner):
    """
    Enhanced learner with feedback-aware episodic learning.

    Overrides _reflect_episodic to check for feedback folder existence
    and implement different learning modes accordingly.
    """

    @property
    def _has_feedback(self) -> bool:
        """
        Check if feedback folder exists for current session.

        Returns:
            True if feedback folder exists, False otherwise
        """
        try:
            storage_path = self._get_feedback_storage_path()
            # Check if feedback folder exists and has content
            feedback_file = storage_path / "feedback.md"
            return (
                feedback_file.exists()
                and feedback_file.stat().st_size > 0
            )
        except Exception:
            return False

    def _reflect_episodic(self, trace_episodic: DictParams) -> DictParams:
        """
        Reflect on an episode with feedback-aware learning.

        Two modes:
        1. With feedback: If feedback folder exists, uses enhanced learning
        2. Without feedback: Falls back to parent's standard episodic learning

        Args:
            trace_episodic: Collection of experiences from the episode

        Returns:
            trace_learning: Learning insights from the episode
        """
        # Check if feedback exists
        if self._has_feedback:
            # Mode: WITH FEEDBACK
            # TODO: Implement enhanced learning logic using feedback
            return self._reflect_episodic_with_feedback(trace_episodic)
        else:
            # Mode: WITHOUT FEEDBACK
            # Use standard episodic learning from parent class
            return super()._reflect_episodic(trace_episodic)

    def _reflect_episodic_with_feedback(
        self, trace_episodic: DictParams
    ) -> DictParams:
        """
        Enhanced episodic learning when feedback is available.

        This method incorporates feedback into the learning analysis,
        allowing the agent to learn from both the interaction timeline
        and external feedback about performance.

        Args:
            trace_episodic: Collection of experiences from the episode

        Returns:
            trace_learning: Learning insights incorporating feedback
        """
        try:
            # Load feedback from feedback folder
            feedback_content = self._load_feedback()
            if not feedback_content:
                # Fall back to parent if feedback loading fails
                logger.warning("Feedback exists but could not be loaded")
                return super()._reflect_episodic(trace_episodic)

            # Load previous episodic learning (if exists)
            previous_learning = self._load_episodic_learning()

            messages = []

            # Enhanced system prompt: system-specific yet adaptable
            system_prompt = SYSTEM_PROMPT.format(previous_learning=previous_learning)

            messages.append(LLMMessage(role="system", content=system_prompt))

            # Include feedback with emphasis on system-specific learning



            timeline = self._agent._timeline
            timeline.timeline = list(timeline.read_since(checkpoint=-2))

            feedback_section = FEEDBACK_PROMPT.format(feedback_content=feedback_content)
            # Convert timeline to messages for learning context
            if timeline:
                timeline_messages = timeline.to_llm_messages(
                    separate_latest_user=False, max_tokens=40000
                )

                messages.extend(timeline_messages)

            learning_section = LEARNING_PROMPT
            
            messages.append(LLMMessage(role="user", content=f"{feedback_section}\n{learning_section}"))

            # Debug logging
            debug_logger = get_debug_logger()
            debug_logger.log_agent_interaction(
                agent_id=self._agent.object_id,
                agent_type=self._agent.agent_type,
                interaction_type=(
                    "build_session_learning_llm_request_with_feedback"
                ),
                content=f"Built {len(messages)} messages with feedback",
                metadata={
                    "message_count": len(messages),
                    "timeline_entries": (
                        len(timeline.timeline) if timeline else 0
                    ),
                    "has_feedback": True,
                    "feedback_length": len(feedback_content),
                },
            )

            llm_response = self._agent.llm_client.chat_response_sync(
                messages,
                agent_id=self._agent.object_id,
                agent_type=self._agent.agent_type,
                temperature=0.7,
            )

            episodic_content = (
                llm_response.content
                if hasattr(llm_response, "content")
                else str(llm_response)
            )

            episodic_content = episodic_content.replace("<updated_learning>", "")
            episodic_content = episodic_content.replace("</updated_learning>", "")

            # Keep in-memory for backward compatibility
            self.episodic_memory = episodic_content

            # Store episodic learning to disk
            self._store_episodic_learning(episodic_content)

            trace_learning = {
                "simple_summary": episodic_content,
                "learning_note": episodic_content,
                "timestamp": datetime.now().isoformat(),
                "reflection_context": (
                    f"Feedback-aware learning: {len(feedback_content)} chars"
                ),
            }

            return {"trace_learning": trace_learning}

        except Exception as e:
            # Log error but don't fail STAR loop
            logger.error(
                f"Episodic learning with feedback failed: {e}",
                exc_info=True
            )
            # Fall back to parent implementation on error
            return super()._reflect_episodic(trace_episodic)
