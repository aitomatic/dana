"""
WilliamLearner2 - Enhanced learner with feedback-aware episodic learning.

This learner extends WilliamLearner with two modes:
- With feedback: When feedback folder exists, uses enhanced learning logic
- Without feedback: Falls back to standard WilliamLearner episodic learning
"""

import json
from datetime import datetime

from .william_learner import WilliamLearner
from dana.common.protocols import DictParams
from dana.common.llm.types import LLMMessage
from dana.common.llm.debug_logger import get_debug_logger
from structlog import get_logger

logger = get_logger()

ANALYSIS_SYSTEM_PROMPT = """
You are the **HVAC-Analysis Assistant**.
Analyze the plan, feedback, and previous learning to determine if knowledge
should be updated.

### INPUT ORDER
1. Timeline messages containing the PLAN (with action_index, time_on, time_off,
   use_turbo, target_temp_f)
2. `<feedback> … </feedback>` (JSON with action_results, plan_success, etc.)
3. `<previous_learning> … </previous_learning>` (existing knowledge)

### Analysis Focus
You need to analyze the feedback, especially for:
1. **Late arrival errors**: Look for error messages containing "HVAC should
   have started earlier to reach target before meeting begins."
   - This indicates comfort failure (reached_time >= meeting_start_time)
   - Recommendation: Suggest starting earlier or using turbo mode
   - Adjust recommendation based on how late (minutes difference)

2. **Energy waste**: Look for "Wasted energy time: X min" when wasted time > 15
   minutes
   - This indicates excessive buffer_gap (reached_time much earlier than
     meeting_start_time)
   - Recommendation: Suggest starting later or using normal mode instead of
     turbo
   - Adjust recommendation based on how early (minutes difference)

3. **Cooling rate accuracy**: Compare actual time_needed_minutes vs estimated
   - If actual differs significantly from estimates in previous_learning,
     suggest updating cooling_rate_turbo or cooling_rate_normal values

### Decision Criteria
Return "knowledge_update": "no" if ALL of the following are true:
- `plan_success == "success"`
- All actions have `schedule_success == "success"`
- All actions have `is_comfort == true` (comfort achieved)
- No wasted time > 15 minutes for any action
- Cooling rates match previous estimates (within reasonable tolerance)

Otherwise, return "knowledge_update": "yes" and provide specific
recommendations.

### Output Format
Your answer MUST be valid JSON only (no markdown, no code blocks):
{{
    "analysis_result": "Detailed analysis of plan execution, feedback results,
     and comparison with previous learning. Identify specific issues: late
     arrivals, energy waste >15min, cooling rate discrepancies.",
    "knowledge_update": "yes" | "no",
    "knowledge_update_recommendation": "Specific recommendations for updating
     knowledge. If knowledge_update is 'yes', provide actionable guidance:
     - Timing adjustments (start X minutes earlier/later)
     - Mode recommendations (use turbo/normal mode)
     - Cooling rate corrections (update cooling_rate_turbo/normal values)
     - Buffer gap optimizations. If 'no', explain why current knowledge is
     sufficient."
}}

<previous_learning>
{previous_learning}
</previous_learning>
"""

SYSTEM_PROMPT = """
You are the **HVAC-Learning Assistant**.
Convert every new **plan + execution feedback** cycle into concise
Markdown **Learning Notes** that capture THIS system's real-world
behaviour and actionable rules.

**IMPORTANT**: If feedback indicates optimal performance (comfort achieved
AND energy efficiency is optimal/acceptable), return minimal output
indicating no updates are needed. Only generate learning notes when there
are issues to address or improvements to make.

## Dual Optimization Objectives
Your learning must optimize for TWO equally critical goals:

1. **User Comfort** (Primary Priority):
   - Temperature MUST reach the expected target BEFORE the meeting starts
   - Success criterion: `reached_time < meeting_start_time`
   - Late arrival = comfort failure (user discomfort)
   - Comfort is non-negotiable: it's better to waste energy than fail comfort

2. **Energy Efficiency** (Secondary Priority):
   - Temperature should reach the target as CLOSE as possible to meeting start
   - Minimize `buffer_gap = meeting_start_time - reached_time`
   - Optimal buffer: 1-3 minutes (comfort margin without waste)
   - Large positive buffer_gap (>5 min) = wasted energy
   - Negative buffer_gap = comfort failure (highest priority to avoid)

**Ideal outcome**: reached_time is 1-3 minutes before meeting_start_time
(comfort achieved + minimal energy waste).

**Decision Framework**: When in doubt, prioritize comfort over energy.
Energy can be optimized once comfort is guaranteed.

## Your 5 Obligations
1. **Pair each action with its feedback**
   (`action_index` → feedback block).

2. **Compute fresh metrics** for the pair:
   • `cooling_rate = (start_temp_f – target_temp_f) / time_needed_minutes`
   • `buffer_gap = meeting_start_time – reached_time`
     (positive = early/energy waste, negative = late/comfort failure)
   • `comfort_achieved = reached_time < meeting_start_time` (boolean)
   • `energy_efficiency_score = max(0, 1 - buffer_gap / optimal_buffer)`
     where optimal_buffer = 2-3 minutes
   • `comfort_score = 1.0 if comfort_achieved else 0.0`
   • `combined_score = 0.7 * comfort_score + 0.3 * energy_efficiency_score`

3. **Label outcome** with dual assessment:
   - `comfort`: `success` if reached_time < meeting_start_time,
     `failed` if late
   - `efficiency`: `optimal` if buffer_gap is 1-3 min,
     `wasteful` if buffer_gap > 5 min, `risky` if buffer_gap < 1 min,
     `acceptable` if buffer_gap is 3-5 min
   - Overall: `success` only if comfort achieved AND efficiency is
     optimal/acceptable
   - If comfort failed, mark as `failed` regardless of efficiency

4. **Maintain value ranges & formulas**—expand or tighten as evidence grows.
   Track cooling rates for both turbo and non-turbo modes separately.
   Build cumulative knowledge without referencing specific previous runs.

5. **Write guidance** that balances both objectives. Generate comprehensive,
   standalone knowledge that doesn't reference previous outputs. Include:
   - Step-by-step advice on when to use turbo mode vs normal mode
   - Calculation formulas with latest learned values
     (cooling_rate_turbo, cooling_rate_normal, typical_buffer_gap)
   - Timing strategies: "Start cooling X minutes before meeting to reach
     target 2-3 minutes early"
   - Trade-off guidance: "If buffer_gap > 5 min, start later next time.
     If buffer_gap < 0 (late), start earlier or use turbo mode."
   - Comfort-first principle: "Always ensure comfort is achieved first,
     then optimize for energy efficiency"

### INPUT ORDER
1. `<previous_learning> … </previous_learning>` (for context only)
2. CURRENT_ENVIRONMENT block
3. PLAN block (array with `action_index`)
4. `<feedback> … </feedback>`

### OUTPUT — Markdown ONLY
Generate fresh, standalone knowledge. Do NOT reference previous runs or
outputs. Write as if this is the first time documenting these insights.

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

ANALYSIS_PROMPT = """
Using the data above (plan from timeline, feedback, previous learning):

1. **Extract the plan** from the timeline messages:
   - Identify all HVAC actions with their action_index, time_on, time_off,
     use_turbo, and target_temp_f values

2. **Analyze each action's feedback**:
   - Match each action in the plan with its corresponding result in
     feedback.action_results (by action_index)
   - Check for late arrival: Look for error messages containing "HVAC should
     have started earlier" or check if `reached_time >= meeting_start_time`
   - Check for energy waste: Look for "Wasted energy time: X min" in error
     messages or check the `wasted` field when > 15 minutes
   - Calculate actual cooling_rate = (start_temp_f - target_temp_f) /
     time_needed_minutes for each action

3. **Compare with previous learning**:
   - Check if actual cooling rates match previous estimates
   - Verify if timing strategies from previous learning were followed
   - Identify discrepancies between expected and actual performance

4. **Determine if update is needed**:
   - If all actions succeeded, comfort achieved, and no significant waste
     (>15 min), return "knowledge_update": "no"
   - Otherwise, return "knowledge_update": "yes" with specific
     recommendations

5. **Generate recommendations** (if update needed):
   - For late arrivals: Calculate how many minutes late, recommend starting
     that many minutes earlier, or suggest turbo mode if normal mode was used
   - For energy waste >15 min: Calculate wasted minutes, recommend starting
     that many minutes later, or suggest normal mode if turbo was used
   - For cooling rate discrepancies: Suggest updated values based on actual
     observed rates

Return ONLY valid JSON (no markdown formatting, no code blocks, no
explanatory text outside the JSON).
"""

LEARNING_PROMPT = """
Using the data above (plan, feedback, previous learning):

**FIRST: Evaluate if feedback is good**
Check if ALL of the following conditions are met:
1. `plan_success == "success"`
2. All actions have `schedule_success == "success"` (no failed actions)
3. **Comfort achieved**: `reached_time < meeting_start_time` for all actions
4. **Energy efficiency is optimal or acceptable**: `buffer_gap` is between 1-5
   minutes (1-3 min = optimal, 3-5 min = acceptable)

**IF FEEDBACK IS GOOD** (all conditions above are met):
- Return ONLY: `<updated_learning>\n\nNo updates needed. System performing
  optimally.</updated_learning>`
- Do NOT generate new learning notes or update formulas
- Do NOT modify previous learning content

**IF FEEDBACK IS NOT GOOD** (any condition above fails):
- Execute the 5-step process defined in SYSTEM_PROMPT
- Apply the dual optimization framework: prioritize user comfort first,
  then optimize for energy efficiency
- For each action-feedback pair, explicitly evaluate BOTH dimensions:
  - **Comfort Assessment**: Was comfort achieved?
    (`reached_time < meeting_start_time`)
    If not, this is a critical failure that must be addressed.
  - **Energy Assessment**: Was energy used efficiently?
    (`buffer_gap` between 1-3 minutes is optimal, 3-5 minutes is acceptable,
    >5 minutes is wasteful)
  - **Combined Analysis**: What timing adjustment would improve the next
    attempt while ensuring comfort is never compromised?
- Generate fresh, standalone knowledge. Do NOT reference previous run
  outputs, previous learning notes, or specific past executions. Write as
  cumulative knowledge that stands on its own.

• Think silently first, then emit only the Markdown block required.

You must not mention the action feedback in the knowledge you generate.

(Do not add narrative, JSON, or code. Do not mention "previous run" or
"last time".)
"""


class WilliamLearner_demo(WilliamLearner):
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

            print("[ANALYSIS] Starting analysis step...")
            prev_learning_len = (
                len(previous_learning) if previous_learning else 0
            )
            print(f"[ANALYSIS] Previous learning length: {prev_learning_len}")

            feedback_section = FEEDBACK_PROMPT.format(
                feedback_content=feedback_content
            )

            analysis_messages = []
            analysis_messages.append(
                LLMMessage(
                    role="system",
                    content=ANALYSIS_SYSTEM_PROMPT.format(
                        previous_learning=previous_learning
                    ),
                ),
            )
            analysis_messages.append(
                LLMMessage(
                    role="user",
                    content=ANALYSIS_PROMPT + feedback_section,
                ),
            )

            print("[ANALYSIS] Calling LLM for analysis...")
            analysis_response = self._agent.llm_client.chat_response_sync(
                analysis_messages,
                agent_id=self._agent.object_id,
                agent_type=self._agent.agent_type,
                temperature=0.0,
            )

            print("[ANALYSIS] Received analysis response")

            # Parse analysis response
            analysis_content = (
                analysis_response.content
                if hasattr(analysis_response, "content")
                else str(analysis_response)
            )

            # Debug output - use both print and logger
            print(f"[ANALYSIS] Analysis content: {analysis_content}")
            logger.info(f"Analysis content: {analysis_content}")

            # Try to parse JSON response
            try:
                # Remove markdown code blocks if present
                analysis_content_clean = analysis_content.strip()
                if analysis_content_clean.startswith("```"):
                    # Extract JSON from code block
                    lines = analysis_content_clean.split("\n")
                    analysis_content_clean = "\n".join(
                        lines[1:-1]
                        if lines[-1].strip() == "```"
                        else lines[1:]
                    )
                elif analysis_content_clean.startswith("```json"):
                    lines = analysis_content_clean.split("\n")
                    analysis_content_clean = "\n".join(
                        lines[1:-1]
                        if lines[-1].strip() == "```"
                        else lines[1:]
                    )

                analysis_result = json.loads(analysis_content_clean)
                knowledge_update = analysis_result.get(
                    "knowledge_update", "yes"
                )
                knowledge_update_recommendation = analysis_result.get(
                    "knowledge_update_recommendation", ""
                )
                print(
                    f"[ANALYSIS] Parsed JSON - "
                    f"knowledge_update: {knowledge_update}"
                )
                rec_len = len(knowledge_update_recommendation)
                print(f"[ANALYSIS] Recommendation length: {rec_len}")
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(
                    f"Failed to parse analysis response as JSON: {e}. "
                    f"Content: {analysis_content[:200]}"
                )
                # Default to updating if parsing fails
                knowledge_update = "yes"
                knowledge_update_recommendation = (
                    "Analysis response could not be parsed. "
                    "Proceeding with standard learning update."
                )

            # If knowledge_update is "no", return previous learning
            if knowledge_update.lower() == "no":
                print(
                    "[ANALYSIS] Knowledge update: NO - "
                    "returning previous learning"
                )
                episodic_content = (
                    previous_learning
                    or "No previous learning available."
                )
                logger.info(
                    "Analysis determined no knowledge update needed. "
                    "Returning previous learning."
                )
            else:
                print(
                    "[ANALYSIS] Knowledge update: YES - "
                    "proceeding with 2nd LLM call"
                )
                # Proceed with 2nd LLM call using
                # knowledge_update_recommendation
                messages = []

                # Enhanced system prompt: system-specific yet adaptable
                system_prompt = SYSTEM_PROMPT.format(
                    previous_learning=previous_learning
                )

                messages.append(
                    LLMMessage(role="system", content=system_prompt)
                )

                timeline = self._agent._timeline
                timeline.timeline = list(timeline.read_since(checkpoint=-2))

                # Convert timeline to messages for learning context
                if timeline:
                    timeline_messages = timeline.to_llm_messages(
                        separate_latest_user=False, max_tokens=40000
                    )
                    messages.extend(timeline_messages)

                # Include knowledge_update_recommendation in learning prompt
                learning_section = (
                    f"**Knowledge Update Recommendation from Analysis:**\n"
                    f"{knowledge_update_recommendation}\n\n"
                    f"Use this recommendation to guide your learning "
                    f"update.\n\n"
                    f"{LEARNING_PROMPT}"
                )

                messages.append(
                    LLMMessage(
                        role="user",
                        content=f"{feedback_section}\n{learning_section}",
                    ),
                )

                # Debug logging
                debug_logger = get_debug_logger()
                debug_logger.log_agent_interaction(
                    agent_id=self._agent.object_id,
                    agent_type=self._agent.agent_type,
                    interaction_type=(
                        "build_session_learning_llm_request_with_feedback"
                    ),
                    content=(
                        f"Built {len(messages)} messages with feedback and "
                        f"knowledge update recommendation"
                    ),
                    metadata={
                        "message_count": len(messages),
                        "timeline_entries": (
                            len(timeline.timeline) if timeline else 0
                        ),
                        "has_feedback": True,
                        "feedback_length": len(feedback_content),
                        "knowledge_update": knowledge_update,
                    },
                )

                llm_response = self._agent.llm_client.chat_response_sync(
                    messages,
                    agent_id=self._agent.object_id,
                    agent_type=self._agent.agent_type,
                    temperature=0.0,
                )

                episodic_content = (
                    llm_response.content
                    if hasattr(llm_response, "content")
                    else str(llm_response)
                )

                episodic_content = episodic_content.replace(
                    "<updated_learning>", ""
                )
                episodic_content = episodic_content.replace(
                    "</updated_learning>", ""
                )

            # Keep in-memory for backward compatibility
            self.episodic_memory = episodic_content

            # Store episodic learning to disk
            self._store_episodic_learning(episodic_content)

            trace_learning = {
                "simple_summary": episodic_content,
                "learning_note": episodic_content,
                "timestamp": datetime.now().isoformat(),
                "reflection_context": (
                    f"Feedback-aware learning: "
                    f"{len(feedback_content)} chars"
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
