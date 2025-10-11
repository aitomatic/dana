"""
Clean BaseSTARAgent implementation with minimal STAR pattern contract.

This module provides the core STAR (See-Think-Act-Reflect) pattern contract
without implementation details like LLM integration or rich state management.
"""

from abc import abstractmethod

from adana.common.observable import observable
from adana.common.protocols import DictParams, STARAgentProtococol
from adana.core.agent.base_agent import BaseAgent


EXIT_STAR_LOOP_FLAG = "EXIT_STAR_LOOP_FLAG"


class BaseSTARAgent(BaseAgent, STARAgentProtococol):
    """
        Minimal base class defining the STAR (See-Think-Act-Reflect) pattern contract.

        Provides core STAR pattern orchestration and basic agent identity without
        implementation details like LLM integration or rich state management.

        This class contains only the essential elements that define what it means to be
        a STAR agent: the four abstract methods and the loop orchestration logic.

        Schema for SYSTEM_PROMPT:
    <SYSTEM_PROMPT_SCHEMA>

    <IDENTITY>
      <!-- Who the coordinator is and how it behaves -->
      You are Dana — a general-purpose coordinating agent. You understand goals, plan concise next steps,
      and either answer directly (if trivial) or delegate via XML ToolCalls to agents, resources, or workflows.
      You keep all actions transparent, reproducible, and traceable.
    </IDENTITY>

    <THINKING>
      <!-- STAR loop and crisp rules for reasoning and action -->
      <Loop>SEE → THINK → ACT → REFLECT</Loop>
      <Rules>
        <Rule>Use ToolCalls for any external action, lookup, computation, or delegation.</Rule>
        <Rule>For conversational or final replies, omit ToolCalls.</Rule>
        <Rule>Ask at most one clarifying question if ambiguous; otherwise apply reasonable defaults.</Rule>
        <Rule>Do not invent agents, resources, workflows, or capabilities that don’t exist.</Rule>
        <Rule>Wait for tool results before continuing and handle errors gracefully.</Rule>
      </Rules>
    </THINKING>

    <RESPONSE_SCHEMA>
      <!-- Mandatory shape for every message you output -->
      <Envelope>
        <Response>
          <ResponseType>in_progress | final</ResponseType>
          <Reasoning>1–3 lines; concise internal rationale</Reasoning>
          <Status>working | success | failure</Status>
          <Content><!-- Markdown for humans; JSON for agents --></Content>
          <ToolCalls>
            <ToolCall>
              <TargetType>agent | resource | workflow</TargetType>
              <TargetId>unique-id</TargetId>
              <Function>invoke | method-name</Function>
              <Arguments><!-- XML parameters only --></Arguments>
            </ToolCall>
            <!-- Optional additional ToolCall blocks -->
          </ToolCalls>
        </Response>
      </Envelope>
      <Constraints>
        <Constraint>For ResponseType=final, omit ToolCalls.</Constraint>
        <Constraint>Arguments must be XML (no JSON).</Constraint>
        <Constraint>Never describe an action without including ToolCalls.</Constraint>
        <Constraint>When replying to another agent, Content must be valid JSON.</Constraint>
        <Constraint>Maintain tag order and close all tags exactly as defined.</Constraint>
      </Constraints>
    </RESPONSE_SCHEMA>

    <CONVENTIONS>
      <!-- Global structural and behavioral standards -->
      <Ids>lowercase-kebab-case</Ids>
      <ResponseTypes>in_progress, final</ResponseTypes>
      <Statuses>working, success, failure</Statuses>
      <ContentModes>markdown_for_users, json_for_agents</ContentModes>
      <Arguments>xml_only</Arguments>
      <ToolCallMechanism>xml_only</ToolCallMechanism>
      <NoStructuredAPI>Structured tool_call API is disabled; XML only.</NoStructuredAPI>
    </CONVENTIONS>

    <DOMAIN_KNOWLEDGE>
      <!-- Optional: stable org-wide facts or runtime-injected domain knowledge -->
      <Fact id="example-fact-1" v="2025.09">Short, vetted statement here.</Fact>
      <Ref id="kb-doc-1" v="2025.07">kb://path/to/doc</Ref>
    </DOMAIN_KNOWLEDGE>

    <KNOWLEDGE_RULES>
      <!-- How to apply, prioritize, and trust knowledge -->
      <Precedence>request_knowledge &gt; tool_results(newer) &gt; domain_knowledge &gt; model_prior</Precedence>
      <Freshness prefer_newer_than_days="400"/>
      <Citations required="true"/>
      <ConflictResolution>Prefer newer timestamp; else higher trust tier.</ConflictResolution>
      <TrustTiers>
        <Tier1>official_stats, regulators, primary_sources</Tier1>
        <Tier2>reputable_press, major_industry_reports</Tier2>
        <Tier3>blogs, forums, user_generated</Tier3>
      </TrustTiers>
    </KNOWLEDGE_RULES>

    <AGENTS_SECTION>
      <!-- Existing agents: must accept XML Arguments -->
      <AVAILABLE_AGENTS>
        <Agent id="web-research-001">Web research, synthesis, and data extraction.</Agent>
        <Agent id="research-001">Cross-source information gathering and synthesis.</Agent>
        <Agent id="analysis-001">Data interpretation and trend identification.</Agent>
        <Agent id="verifier-001">Accuracy and completeness verification.</Agent>
      </AVAILABLE_AGENTS>
      <Conventions>
        <FunctionForAgents>invoke</FunctionForAgents>
      </Conventions>
    </AGENTS_SECTION>

    <RESOURCES_SECTION>
      <!-- Simple or computational utilities -->
      <AVAILABLE_RESOURCES>
        <Resource id="task-manager" class="ToDoResource">
          Structured task tracking for multi-step work.
        </Resource>
      </AVAILABLE_RESOURCES>
    </RESOURCES_SECTION>

    <WORKFLOWS_SECTION>
      <!-- Multi-step orchestration definitions -->
      <AVAILABLE_WORKFLOWS>
        <!-- Add as available -->
      </AVAILABLE_WORKFLOWS>
      <Conventions>
        <DefaultFunction>execute</DefaultFunction>
      </Conventions>
    </WORKFLOWS_SECTION>

    </SYSTEM_PROMPT_SCHEMA>
    """

    # ============================================================================
    # CORE STAR PATTERN CONTRACT (Abstract Methods)
    # ============================================================================

    @abstractmethod
    def _see(self, trace_inputs: DictParams) -> DictParams:
        """
        SEE: See the inputs and produce percepts.

        Args:
            trace_inputs (DictParams): any new user/agent inputs

        Returns:
            - bool: True if the agent should continue the loop, False otherwise.
            - trace_percepts (DictParams): the percepts produced by this SEE phase.
        """
        result = {"trace_percepts": trace_inputs}
        self.broadcast(result)
        return result

    @abstractmethod
    def _think(self, trace_percepts: DictParams) -> DictParams:
        """
        THINK: Think about the percepts and produce thoughts.

        Args:
            trace_percepts (DictParams): the percepts produced by this SEE phase.

        Returns:
            - bool: True if the agent should continue the loop, False otherwise.
            - trace_thoughts (DictParams): the thoughts produced by this THINK phase.
        """
        result = {"trace_thoughts": trace_percepts}
        self.broadcast(result)
        return result

    @abstractmethod
    def _act(self, trace_thoughts: DictParams) -> DictParams:
        """
        ACT: Act on the thoughts and produce outputs.

        TODO: this is a good place to send feedback to the user if we are about to make tool calls

        Args:
            trace_thoughts (DictParams): the thoughts produced by this THINK phase.

        Returns:
            - bool: True if the agent should continue the loop, False otherwise.
            - trace_outputs (DictParams): the outputs produced by this ACT phase.
        """
        result = {"trace_outputs": trace_thoughts}
        self.broadcast(result)
        return result

    @abstractmethod
    def _reflect(self, trace_outputs: DictParams) -> DictParams:
        """
        REFLECT: Reflect on the outputs for learning.

        Args:
            trace_outputs (DictParams): the outputs produced by this ACT phase.

        Returns:
            - bool: True if the agent should continue the loop, False otherwise.
            - trace_learning (DictParams): the learning produced by this REFLECT phase.
        """
        result = {"trace_learning": trace_outputs}
        self.broadcast(result)
        return result

    # ============================================================================
    # EXIT STAR LOOP FLAG
    # ============================================================================

    def _mark_star_loop_exit(self, trace: DictParams | None = None) -> DictParams:
        if not trace:
            trace = {}

        trace[EXIT_STAR_LOOP_FLAG] = True
        return trace

    def _do_exit_star_loop(self, trace: DictParams) -> bool:
        return trace.get(EXIT_STAR_LOOP_FLAG, False) if trace else True

    # ============================================================================
    # STAR LOOP ORCHESTRATION
    # ============================================================================

    def query(self, **kwargs) -> DictParams:
        """Main entry point - orchestrates the STAR loop."""

        @observable(name=f"Dana {self.agent_type}-agent-query")
        def _do_query(trace_inputs: DictParams) -> DictParams:
            trace_outputs: DictParams = {}

            MAX_ITERATIONS = 10
            for _ in range(MAX_ITERATIONS):
                try:
                    trace_percepts = self._see(trace_inputs.get("trace_inputs", {}))
                    trace_thoughts = self._think(trace_percepts.get("trace_percepts", {}))
                    trace_outputs = self._act(trace_thoughts.get("trace_thoughts", {}))
                    # trace_learning = self._reflect(trace_outputs["trace_outputs"], continue_flag)
                    # trace_episode[datetime.now().isoformat()] = trace_learning

                    outputs = trace_outputs.get("trace_outputs", {})

                    # On next loop, agent will continue reasoning on the outputs (and any timeline)
                    trace_inputs["trace_inputs"] = outputs

                    if self._do_exit_star_loop(outputs):
                        break

                except Exception as e:
                    # print(f"Error in STAR loop: {e}")
                    # break
                    raise e

            # trace_episode["phase"] = LearningPhase.EPISODIC
            # _trace_trajectory = self._reflect(do_continue, trace_episode)

            return trace_outputs

        try:
            result = _do_query(trace_inputs={"trace_inputs": kwargs})
            result = result.get("trace_outputs", {}) if result else {}

        except Exception as e:
            print(f"Error in query: {e}")
            result = {"error": e}

        return result

    # ============================================================================
    # UTILITIES
    # ============================================================================

    def __str__(self) -> str:
        """String representation of the agent."""
        return f"BaseSTARAgent(type={self.agent_type}, id={self.object_id})"

    def __repr__(self) -> str:
        """Detailed string representation of the agent."""
        return f"BaseSTARAgent(agent_type='{self.agent_type}', object_id='{self.object_id}')"
