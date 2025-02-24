"""Reasoning executor implementation."""

from enum import Enum
from typing import List, cast, Optional
import asyncio

from ..execution_context import ExecutionContext
from ..execution_types import (
    ExecutionNode,
    ExecutionSignal,
    ExecutionSignalType,
    Objective
)
from ..execution_graph import ExecutionGraph
from ..executor import Executor
from .reasoning import Reasoning
from ..planning.plan import Plan
from ...common.graph import NodeType

class ReasoningStrategy(Enum):
    """Reasoning execution strategies."""
    DEFAULT = "DEFAULT"         # Simple LLM query
    CHAIN_OF_THOUGHT = "COT"    # Step by step reasoning
    OODA = "OODA"               # OODA loop pattern
    DANA = "DANA"               # DANA pattern
    PROSEA = "PROSEA"           # PROSEA pattern
    
class ReasoningExecutor(Executor):
    """Executes reasoning patterns."""

    def __init__(self, strategy: ReasoningStrategy = ReasoningStrategy.DEFAULT):
        super().__init__(depth=3)  # Child of plan
        self.strategy = strategy
        self.current_reasoning = None
        self.graph: Optional[ExecutionGraph] = None  # Add type annotation
        self.layer = "reasoning"
        self._configure_logger()

    async def execute(self, upper_graph: ExecutionGraph, context: ExecutionContext,
                      upper_signals: Optional[List[ExecutionSignal]] = None) -> List[ExecutionSignal]:
        """Execute using reasoning strategy."""
        # Create reasoning graph based on strategy
        plan = cast(Plan, upper_graph)
        reasoning = self._create_reasoning(plan, upper_graph.objective)

        # Update context with new reasoning
        context.current_reasoning = reasoning

        # Execute reasoning through base executor
        return await super().execute(upper_graph=reasoning, context=context, upper_signals=upper_signals)

    async def execute_node(self, node: ExecutionNode, context: ExecutionContext,
                           validation_node: Optional[ExecutionNode] = None,
                           original_problem: Optional[str] = None,
                           prev_signals: Optional[List[ExecutionSignal]] = None,
                           upper_signals: Optional[List[ExecutionSignal]] = None,
                           lower_signals: Optional[List[ExecutionSignal]] = None) -> List[ExecutionSignal]:
        """Execute a reasoning node using LLM."""
        if not context.reasoning_llm:
            raise ValueError("No reasoning LLM configured in context")

        # print(node.node_id)
        # print("\033[91mPrev signals:\033[0m", prev_signals)
        # print("\033[92mUpper signals:\033[0m", upper_signals)
        # print("\033[93mLower signals:\033[0m", lower_signals)
        
        # TODO: use upper_signals and prev_signals somehow?

        # Safety: make sure our graph is set
        if self.graph is None and context.current_reasoning:
            self.graph = context.current_reasoning

        if context.current_reasoning is None and self.graph:
            context.current_reasoning = cast(Reasoning, self.graph)

        if node.node_type in [NodeType.START, NodeType.END]:
            return []   # Start and end nodes just initialize/terminate flow

        if self.strategy == ReasoningStrategy.DEFAULT:
            return await self._execute_direct(node, context)
        if self.strategy == ReasoningStrategy.CHAIN_OF_THOUGHT:
            return await self._execute_cot(node, context)
        if self.strategy == ReasoningStrategy.OODA:
            return await self._execute_ooda(node, context)
        if self.strategy == ReasoningStrategy.DANA:
            return await self._execute_dana(node, context)
        if self.strategy == ReasoningStrategy.PROSEA:
            return await self._execute_prosea(node=node, context=context, validation_node=validation_node, original_problem=original_problem, prev_signals=prev_signals, upper_signals=upper_signals, lower_signals=lower_signals)
        raise ValueError(f"Unknown strategy: {self.strategy}")

    def _create_graph(self,
                       upper_graph: ExecutionGraph,
                       objective: Optional[Objective] = None,
                       context: Optional[ExecutionContext] = None) -> ExecutionGraph:
        """Create this layer's graph from the upper layer's graph."""
        reasoning = self._create_reasoning(cast(Plan, upper_graph), objective)
        assert context is not None
        context.current_reasoning = reasoning
        return cast(ExecutionGraph, reasoning)

    def _create_reasoning(self, plan: "Plan", objective: Optional[Objective] = None) -> Reasoning:
        """Create reasoning graph based on strategy."""
        reasoning = None
        objective = objective or plan.objective
        assert objective is not None

        if self.strategy == ReasoningStrategy.DEFAULT:
            if len(plan.nodes) == 2:
            # Simple single-node reasoning
                node = ExecutionNode(
                    node_id="DIRECT_REASONING",
                    node_type=NodeType.TASK,
                    description=objective.original
                )
                reasoning = self._create_execution_graph([node])
            if len(plan.nodes) > 2:
                nodes = []
                for node_id in plan.nodes.keys():
                    nodes.append(plan.nodes[node_id])
                    reasoning = self._create_execution_graph(nodes)
                    
        elif self.strategy == ReasoningStrategy.CHAIN_OF_THOUGHT:
            # Add nodes for each reasoning step
            node = ExecutionNode(
                node_id="cot_reasoning",
                node_type=NodeType.TASK,
                description=f"Let's solve this step by step:\n{objective.original}"
            )
            reasoning = self._create_execution_graph([node])
        # elif self.strategy == ReasoningStrategy.PROSEA:
            # nodes = []
            # print(plan.nodes)
            # for node_id in plan.nodes.keys():
            #     nodes.append(plan.nodes[node_id])
            # reasoning = self._create_execution_graph(nodes)
        
        if not reasoning:
            raise ValueError(f"Failed to create reasoning graph for strategy {self.strategy}")
        reasoning.objective = objective
        return cast(Reasoning, reasoning)

    async def _execute_prosea(self, node: ExecutionNode, context: ExecutionContext,
                              validation_node: Optional[ExecutionNode] = None,
                              original_problem: Optional[str] = None,
                              prev_signals: Optional[List[ExecutionSignal]] = None,
                              upper_signals: Optional[List[ExecutionSignal]] = None,
                              lower_signals: Optional[List[ExecutionSignal]] = None) -> List[ExecutionSignal]:
        """Execute PROSEA reasoning."""
        assert context.reasoning_llm is not None
        # print("\033[91mPrev signals\033[0m", prev_signals)
        prev_step_output = ""
        if prev_signals:
            for signal in prev_signals:
                if signal.type == ExecutionSignalType.DATA_RESULT:
                    prev_step_output += signal.content["result"]["content"]
                    prev_step_output += "\n\n"
        if "step_" in node.node_id:
            prompt = f"""
            These are the previous steps and their outputs:
            {prev_step_output}
            
            The original problem is:
            {original_problem}

            Now, based on the previous steps and the original problem, please solve the current step:
            {node.description}
            """
        elif "FINALIZE_ANSWER" in node.node_id:
            print("FINALIZE_ANSWER")
            prompt = node.description.replace("<reasoning_result>", prev_step_output)
        else:
            prompt = node.description
        response = await context.reasoning_llm.query({"prompt": prompt})
        return [ExecutionSignal(type=ExecutionSignalType.DATA_RESULT, content={
            "result": response,
            "node": node.node_id
        })]

    async def _execute_direct(self, node: ExecutionNode, context: ExecutionContext) -> List[ExecutionSignal]:
        """Execute direct LLM query."""
        self.logger.info(
            "Starting reasoning", 
            extra={
                'strategy': self.strategy.value,
                'layer': 'reasoning',
                'prompt': node.description[:50] + "...",
                'plan_step': getattr(context.agent_state, 'current_step_index', 0)
            }
        )
        assert context.reasoning_llm is not None
        response = await context.reasoning_llm.query({"prompt": node.description})
        self.logger.debug(
            "LLM response received",
            extra={
                'response_length': len(response),
                'node': node.node_id,
                'latency': getattr(context, 'llm_latency', 0)
            }
        )
        return [ExecutionSignal(
            type=ExecutionSignalType.DATA_RESULT,
            content={
                "result": response,
                "node": node.node_id
            }
        )]

    async def _execute_cot(self, node: ExecutionNode, context: ExecutionContext) -> List[ExecutionSignal]:
        """Execute chain-of-thought reasoning."""
        prompt = f"Let's solve this step by step:\nQuestion: {node.description}\nThought process:"
        assert context.reasoning_llm is not None
        response = await context.reasoning_llm.query({"prompt": prompt})
        return [ExecutionSignal(type=ExecutionSignalType.DATA_RESULT, content=response)]

    async def _execute_ooda(self, node: ExecutionNode, context: ExecutionContext) -> List[ExecutionSignal]:
        """Execute OODA loop reasoning."""
        stage = node.metadata.get("ooda_stage", 0)
        stages = ["observe", "orient", "decide", "act"]

        if stage >= len(stages):
            return []

        current_stage = stages[stage]
        prompt = f"{current_stage.capitalize()}: {node.description}"
        assert context.reasoning_llm is not None
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(context.reasoning_llm.query({"prompt": prompt}))

        node.metadata["ooda_stage"] = stage + 1
        return [ExecutionSignal(type=ExecutionSignalType.DATA_RESULT, content=response)]

    async def _execute_dana(self, node: ExecutionNode, context: ExecutionContext) -> List[ExecutionSignal]:
        """Execute DANA pattern reasoning."""
        # For now, same as direct
        return await self._execute_direct(node, context)
