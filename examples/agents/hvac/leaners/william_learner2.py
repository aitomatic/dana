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


class WilliamLearner2(WilliamLearner):
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
            return feedback_file.exists() and feedback_file.stat().st_size > 0
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

    def _reflect_episodic_with_feedback(self, trace_episodic: DictParams) -> DictParams:
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
            system_prompt = """You are a learning and knowledge extraction
assistant with access to performance feedback.
Your role is to extract actionable advice from feedback that captures
the specific system/device/context's actual characteristics, while
formulating adaptable rules that work for this system across variations.

CRITICAL BALANCE:
- Extract THIS system/device/context's actual characteristics from
  feedback (observed rates, patterns, thresholds, behaviors, values)
- Calculate THIS system's specific performance metrics from feedback
  (e.g., rate = observed_change / observed_time)
- Extract value ranges and approximate values when they're useful and
  informative (e.g., "this system typically needs X-Y time units buffer")
- Formulate rules as formulas/patterns/ranges that capture THIS system's
  characteristics but adapt to different scenarios (different inputs,
  times, conditions)
- Make advice work perfectly for THIS system based on observed feedback,
  while remaining adaptable to variations within this context

Guidelines for VALUE EXTRACTION:
- Extract specific values and ranges from feedback when they're useful
  (e.g., "this system processes at rate ~X-Y units/time based on feedback")
- Express values as ranges, approximations, or formulas rather than
  exact single constants (e.g., "typically X-Y range" not "exactly X")
- Frame specific values as THIS system's observed characteristics that
  inform formulas (e.g., "based on feedback, use rate ≈ X-Y, so
   time_needed = change / rate")
- Include value ranges when they help distinguish THIS system from
  generic advice, but frame them as adaptable parameters

Guidelines for FORMULA CREATION:
- Use feedback to calculate THIS system's actual performance metrics
  (rates, patterns, timing relationships) from observed data
- Create formulas that incorporate THIS system's observed characteristics
  (e.g., "this system performs at rate X-Y based on feedback, so use
   formula: time_needed = change / rate")
- Extract THIS system's specific thresholds and patterns from feedback
  (e.g., "this system needs buffer Y-Z based on observed failures")
- Formulate adaptable rules that work for THIS system across different
  scenarios (not generic rules that could apply to any system)

The learning must capture THIS specific system's characteristics from
feedback (including useful value ranges), but express them as adaptable
formulas/ranges that work for this system across variations."""

            messages.append(LLMMessage(role="system", content=system_prompt))

            # Include feedback with emphasis on system-specific learning
            feedback_section = f"""=== PERFORMANCE FEEDBACK ===
{feedback_content}
=== END FEEDBACK ===

This feedback contains THIS system/device/context's actual observed
performance:
- Actual rates, patterns, and timing relationships observed (calculate
  from feedback: rate = observed_change / observed_time)
- Actual performance characteristics specific to THIS setup
- THIS system's observed thresholds, failure modes, and success patterns
- Concrete measurements that reveal THIS system's specific behavior

CRITICAL: Extract THIS system/device/context's specific characteristics:
- Calculate actual performance metrics from feedback observations
  (e.g., performance_rate = observed_change / observed_time_taken)
- Extract value ranges and approximate values when useful
  (e.g., "this system typically exhibits rate X-Y based on observed cases")
- Identify THIS system's observed patterns from feedback
  (e.g., "this system processes at ~A-B units/time in mode X, ~C-D
   units/time in mode Y, based on feedback observations")
- Determine THIS system's specific thresholds and formulas from feedback
  (e.g., "this system needs buffer Y-Z time units based on observed
   failures where timing was insufficient by W time units")
- Capture THIS system's failure modes and success patterns from feedback
- Frame specific values as ranges/approximations that inform formulas,
  not as fixed constants (e.g., "typically X-Y range" helps generalization)

The learning must work perfectly for THIS system based on observed feedback
data, while formulating rules as formulas/ranges that adapt to different
scenarios (different inputs, times, conditions) within this context.
Include specific value ranges when they're informative and help distinguish
THIS system's characteristics, but express them as adaptable parameters."""

            timeline = self._agent._timeline
            timeline.timeline = list(timeline.read_since(checkpoint=-100))

            # Convert timeline to messages for learning context
            if timeline:
                timeline_messages = timeline.to_llm_messages(separate_latest_user=False, max_tokens=40000)

                if timeline_messages:
                    # Include previous learning if available
                    if previous_learning:
                        messages.append(
                            LLMMessage(
                                role="user",
                                content=(
                                    f"=== Previous Accumulated Learning ===\n"
                                    f"{previous_learning}\n\n"
                                    f"Now analyze the current session "
                                    f"timeline considering the feedback "
                                    f"above:"
                                ),
                            )
                        )

                    # Wrap timeline in structured format for learning
                    timeline_lines = [
                        "<SESSION_TIMELINE>",
                        "Analyze the following agent interaction timeline:",
                        "",
                    ]

                    for msg in timeline_messages:
                        role_indicator = "USER" if msg.role == "user" else "AGENT"
                        content_tag = f"<{role_indicator}>{msg.content}</{role_indicator}>"
                        timeline_lines.append(content_tag)

                    timeline_lines.append("</SESSION_TIMELINE>")
                    timeline_content = "\n".join(timeline_lines)
                    messages.append(LLMMessage(role="user", content=timeline_content))

                    messages.append(LLMMessage(role="user", content=feedback_section))

                    # Learning prompt: system-specific characteristics
                    if previous_learning:
                        learning_prompt = """Based on the agent action and feedback data above,
previous accumulated learning, and the current session timeline above,
You need to consider the following:
1. THIS system/device/context's specific performance characteristics
   (calculate actual rates, patterns, timing relationships from feedback)
2. THIS system's successful strategies (validated by observed feedback)
3. THIS system's failure modes and improvement areas (from observed feedback)
4. THIS system's specific thresholds, formulas, and patterns (from feedback)
5. Relationships between inputs, actions, and outcomes for THIS system

CRITICAL: Extract THIS system/device/context's specific characteristics:
- Calculate actual performance metrics from feedback observations
  (e.g., performance_rate = observed_change / observed_time_needed)
- Extract value ranges and approximate values when they're useful
  (e.g., "this system typically processes at rate ~X-Y units/time based
   on feedback")
- Use THIS system's observed patterns to create formulas
  (e.g., "this system performs at rate X-Y based on feedback, so use
   formula: time_needed = change / rate")
- Identify THIS system's specific thresholds from feedback
  (e.g., "this system needs buffer Y-Z time units based on observed
   failures where timing was insufficient")
- Include specific value ranges when informative and help distinguish
  THIS system from generic advice, but express them as adaptable ranges
- Make advice work perfectly for THIS system while adapting to different
  scenarios (different inputs, times, conditions) within this context

You need to learn from the whole session, incorporating THIS system's
observed feedback characteristics (including useful value ranges), and
extract the knowledge note to perform better for THIS specific system/
device/context in future scenarios.
Format: [Condition] [Advice of what should do]

Update your accumulated learning by consolidating insights from
previous learning, this new session, and THIS system's observed feedback."""
                    else:
                        learning_prompt = """Based on the assistant action, feedback data above
and the session timeline above,
You need to consider the following:
1. THIS system/device/context's specific performance characteristics
   (calculate actual rates, patterns, timing relationships from feedback)
2. THIS system's successful strategies (validated by observed feedback)
3. THIS system's failure modes and improvement areas (from observed feedback)
4. THIS system's specific thresholds, formulas, and patterns (from feedback)
5. Relationships between inputs, actions, and outcomes for THIS system

CRITICAL: Extract THIS system/device/context's specific characteristics:
- Calculate actual performance metrics from feedback observations
  (e.g., performance_rate = observed_change / observed_time_needed)
- Extract value ranges and approximate values when they're useful
  (e.g., "this system typically processes at rate ~X-Y units/time based
   on feedback")
- Use THIS system's observed patterns to create formulas
  (e.g., "this system performs at rate X-Y based on feedback, so use
   formula: time_needed = change / rate")
- Identify THIS system's specific thresholds from feedback
  (e.g., "this system needs buffer Y-Z time units based on observed
   failures where timing was insufficient")
- Include specific value ranges when informative and help distinguish
  THIS system from generic advice, but express them as adaptable ranges
- Make advice work perfectly for THIS system while adapting to different
  scenarios (different inputs, times, conditions) within this context

You need to learn from the whole session, incorporating THIS system's
observed feedback characteristics (including useful value ranges), and
extract the knowledge note to perform better for THIS specific system/
device/context in future scenarios.
Format: [Condition] [Advice of what should do]"""

                    messages.append(LLMMessage(role="user", content=learning_prompt))
                else:
                    # No timeline content, but still use feedback
                    messages.append(LLMMessage(role="user", content=feedback_section))
                    messages.append(
                        LLMMessage(
                            role="user",
                            content=(
                                "No session timeline available, but feedback "
                                "is provided. Analyze THIS system/device/"
                                "context's feedback data to calculate actual "
                                "performance metrics (rates, patterns, timing "
                                "relationships) and extract THIS system's "
                                "specific characteristics, including useful "
                                "value ranges when informative. Create "
                                "formulas that incorporate THIS system's "
                                "observed behavior (expressed as adaptable "
                                "ranges) but adapt to different scenarios "
                                "within this context."
                            ),
                        )
                    )

            # Debug logging
            debug_logger = get_debug_logger()
            debug_logger.log_agent_interaction(
                agent_id=self._agent.object_id,
                agent_type=self._agent.agent_type,
                interaction_type=("build_session_learning_llm_request_with_feedback"),
                content=f"Built {len(messages)} messages with feedback",
                metadata={
                    "message_count": len(messages),
                    "timeline_entries": (len(timeline.timeline) if timeline else 0),
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

            episodic_content = llm_response.content if hasattr(llm_response, "content") else str(llm_response)

            # Keep in-memory for backward compatibility
            self.episodic_memory = episodic_content

            # Store episodic learning to disk
            self._store_episodic_learning(episodic_content)

            trace_learning = {
                "simple_summary": episodic_content,
                "learning_note": episodic_content,
                "timestamp": datetime.now().isoformat(),
                "reflection_context": (f"Feedback-aware learning: {len(feedback_content)} chars"),
            }

            return {"trace_learning": trace_learning}

        except Exception as e:
            # Log error but don't fail STAR loop
            logger.error(f"Episodic learning with feedback failed: {e}", exc_info=True)
            # Fall back to parent implementation on error
            return super()._reflect_episodic(trace_episodic)
