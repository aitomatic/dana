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
from ...common.utils.text_processor import TextProcessor

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
        self.parse_by_key = TextProcessor().parse_by_key

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
        if len(prev_signals) > 2:
            for i in range(2, len(prev_signals)):
                if prev_signals[i].type == ExecutionSignalType.DATA_RESULT:
                    prev_step_output += prev_signals[i].content["result"]["content"]
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
        
        
        if validation_node is not None:
            response = await self._execute_prosea_step_with_validation(node=node, context=context, validation_node=validation_node, original_problem=original_problem, prompt=prompt, prev_signals=prev_signals)
        else:
            response = await context.reasoning_llm.query({"prompt": prompt})
        return [ExecutionSignal(type=ExecutionSignalType.DATA_RESULT, content={
            "result": response,
            "node": node.node_id
        })]
    
    async def _validate_response(self, response: str, node: ExecutionNode, validation_node: ExecutionNode, context: ExecutionContext,
                                 original_problem: Optional[str] = None, additional_prompt: Optional[str] = None,
                                 prev_signals: Optional[List[ExecutionSignal]] = None) -> List[any]:
        """Validate the response against the validation node."""
        assert validation_node is not None
        assert original_problem is not None
        previous_step_output = ""
        if len(prev_signals) > 2:
            for i in range(2, len(prev_signals)):
                if prev_signals[i].type == ExecutionSignalType.DATA_RESULT:
                    previous_step_output += prev_signals[i].content["result"]["content"]
                    previous_step_output += "\n\n"
        
        prompt = f"""
        Initial analysis for the problem: {prev_signals[0].content["result"]["content"]}
        This is previous steps: {previous_step_output} \n\n
        This is the start prompt: {node.description}
        This is the additional prompt used in previous try: {additional_prompt}
        This is the output: {response}
        This is the expected information from output: {validation_node.description}

        First, please do reasoning and analysis on the output and expected information, then let me know if the output is matched with the expectation or not.
        If not, please do analysis and tell me that can you solve this problem only by continuing generate new prompt for the conversation to achieve the expectation?
        Do not assume the important if you are not sure and do not assume customized information (for example, different company will have different level ladder).
        
        Answer format:
        reasoning_analysis: Your reasoning and analysis on the output and expected information. You need to critique the output based on expected information. Always make sure that the information provided in the output is correct. If not, that's a big issue. If the criteria is gathering information, but output is how to gather information, then it's not correct. If expected output is nothing special, any output should be accepted. If there are information that matched with all requirement in the answer (even though the answer also has irrelevant information), the answer is also matched.
        is_matched: Specify if output is matched with criteria. Yes/No (just write Yes or No, no more). If the criteria is gathering information, but output is how to gather information or just give the questions or just give questions to get the information, then it's not correct and the answer is No. If expected output is nothing special, any output should be accepted and answer is Yes. f there are information that matched with all requirement in the answer (even though the answer has irrelevant information), the answer is also matched, please answer Yes.
        reasoning_for_contradicted: If the output is not matched with the expectation, given the start prompt, please do reasoning to check if the criteria for the output has any mistake that will make the output inaccurate. Point out the mistake. If criteria is accept anything, it means no contradict.
        is_contradicted: Specify if the criteria for the output has any mistake. Yes/No (just write Yes or No, no more). If the criteria is accept anything, it means no contradict and answer is No.
        refined_criteria: If the criteria for the output has any mistake, then let me know the refined criteria for the output here. Just tel me new criteria, do not say anything else.
        reasoning_analysis_solvable_by_continuing_prompt: Think carefully about if you can solve this problem by only ask a LLM and/or retrieve information from documents without interact with real world. If it's necessary to interact with real world or interact with device to get output, then you need to ask for more input from the user. If without input from user, the result will be unreliable, please ask user. If the answer can be achived by checking documents, continue prompt. If there is something need user's confirmation. You must ask user. Provide a clear analysis. Before asking user, is there anything from provided questions can replace the information you need? If require confirmation form human, you must ask user.
        is_solvable_by_continuing_prompt: Based on your above analysis, specify if you can solve this problem only by continuing generate new prompt to ask LLM (and/or retrieve information from documents) to achieve the expectation. Yes/No (just write Yes or No, no more). Yes means you can solve this problem only by continuing generate new prompt for the conversation (with RAG) to achieve the expectation or there is no need addtional input from user to process. No means you must ask for more input from the user. If require confirmation form human, you must ask user by saying Yes.
        
        Do not lack any key above.
        Do not forget the key and do not change the key format. Do not highlight the key.
        """
        response = await context.reasoning_llm.query({"prompt": prompt})
        response_text = response["content"]
        is_matched = "yes" in self.parse_by_key(response_text, "is_matched").lower()
        is_contradicted = "yes" in self.parse_by_key(response_text, "is_contradicted").lower()
        refined_criteria = self.parse_by_key(response_text, "refined_criteria")
        is_solvable_by_continuing_prompt = "yes" in self.parse_by_key(response_text, "is_solvable_by_continuing_prompt").lower()
        
        return is_matched, is_contradicted, refined_criteria, is_solvable_by_continuing_prompt    
        
    async def _execute_prosea_step_with_validation(self, node: ExecutionNode, context: ExecutionContext,
                              validation_node: Optional[ExecutionNode] = None,
                              original_problem: Optional[str] = None, prompt: str = None,
                              prev_signals: Optional[List[ExecutionSignal]] = None) -> List[ExecutionSignal]:
        """Execute PROSEA reasoning with validation."""
        assert context.reasoning_llm is not None
        is_matched = False
        print("Start validation")
        while not is_matched:
            response = await context.reasoning_llm.query({"prompt": prompt})
            response_text = response["content"]
            is_matched, is_contradicted, refined_criteria, is_solvable_by_continuing_prompt = await self._validate_response(response=response_text, node=node, validation_node=validation_node, context=context, original_problem=original_problem, additional_prompt=prompt, prev_signals=prev_signals)
            print("is_matched", is_matched)
        return response
        
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
