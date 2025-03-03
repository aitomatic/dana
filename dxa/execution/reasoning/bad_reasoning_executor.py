"""Reasoning executor implementation."""

from enum import Enum
from typing import List, cast, Optional, Dict

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

class BadReasoningStrategy(Enum):
    """Reasoning execution strategies."""
    DEFAULT = "DEFAULT"         # Simple LLM query
    CHAIN_OF_THOUGHT = "CHAIN_OF_THOUGHT"    # Step by step reasoning
    OODA = "OODA"               # OODA loop pattern
    DANA = "DANA"               # DANA pattern
    PROSEA = "PROSEA"           # PROSEA pattern
    
class BadReasoningExecutor(Executor):
    """Executes reasoning patterns."""

    def __init__(self, strategy: BadReasoningStrategy = BadReasoningStrategy.DEFAULT):
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
                           agent_role: Optional[str] = None,
                           prev_signals: Optional[List[ExecutionSignal]] = None,
                           upper_signals: Optional[List[ExecutionSignal]] = None,
                           lower_signals: Optional[List[ExecutionSignal]] = None) -> List[ExecutionSignal]:
        """Execute node based on its type and strategy."""
        # Get agent role from context if not provided
        if agent_role is None and context.current_workflow:
            agent_role = context.current_workflow.metadata.get("role", "Agent")

        # Execute based on strategy
        if self.strategy == ReasoningStrategy.DEFAULT:
            return await self._execute_direct(node=node, context=context)
        if self.strategy == ReasoningStrategy.CHAIN_OF_THOUGHT:
            return await self._execute_cot(node=node, context=context)
        if self.strategy == ReasoningStrategy.OODA:
            return await self._execute_ooda(node=node, context=context)
        if self.strategy == ReasoningStrategy.DANA:
            return await self._execute_dana(node=node, context=context)
        if self.strategy == ReasoningStrategy.PROSEA:
            return await self._execute_prosea(node=node, context=context, validation_node=validation_node, 
                                              original_problem=original_problem, agent_role=agent_role, prev_signals=prev_signals, 
                                              upper_signals=upper_signals, lower_signals=lower_signals)
        raise ValueError(f"Unknown strategy: {self.strategy}")

    def _create_graph(self,
                       upper_graph: ExecutionGraph,
                       objective: Optional[Objective] = None,
                       context: Optional[ExecutionContext] = None) -> ExecutionGraph:
        """Create reasoning graph from plan."""
        # Create reasoning based on strategy
        if not isinstance(upper_graph, Plan):
            raise ValueError(f"Expected Plan, got {type(upper_graph)}")
        
        plan = cast(Plan, upper_graph)
        
        # Use objective from plan if not provided
        if objective is None and plan.objective:
            objective = plan.objective
            
        # Create reasoning based on strategy
        reasoning = self._create_reasoning(plan, objective)
        
        # Ensure metadata from plan is properly copied to reasoning
        if plan.metadata:
            reasoning.metadata.update(plan.metadata)
            
        # Copy context if provided
        if context:
            reasoning.context = context
            
        return reasoning

    def _create_reasoning(self, plan: "Plan", objective: Optional[Objective] = None) -> Reasoning:
        """Create reasoning graph from plan."""
        # Create a new reasoning with the same objective
        reasoning = Reasoning(objective or plan.objective)
        
        if self.strategy == ReasoningStrategy.DEFAULT:
            if len(plan.nodes) == 2:
                # Simple single-node reasoning
                node = ExecutionNode(
                    node_id="DIRECT_REASONING",
                    node_type=NodeType.TASK,
                    description=objective.current if objective else "Direct reasoning",
                    # Copy metadata from plan if available
                    metadata=plan.metadata.copy() if plan.metadata else {}
                )
                reasoning.add_node(node)
                reasoning.add_edge(Edge(source="START", target="DIRECT_REASONING"))
                reasoning.add_edge(Edge(source="DIRECT_REASONING", target="END"))
            else:
                # Copy nodes from plan to reasoning, preserving structure
                for node_id, node in plan.nodes.items():
                    # Skip START and END nodes, they'll be added automatically
                    if node.node_type in [NodeType.START, NodeType.END]:
                        continue
                        
                    # Create a new reasoning node with the same properties
                    reasoning_node = ExecutionNode(
                        node_id=node_id,
                        node_type=node.node_type,
                        description=node.description,
                        # Copy metadata to preserve prompts and other settings
                        metadata=node.metadata.copy() if node.metadata else {}
                    )
                    
                    # Add the node to the reasoning
                    reasoning.add_node(reasoning_node)
                
                # Copy edges to maintain the same structure
                for edge in plan.edges:
                    # Skip edges connected to START or END if they'll be recreated
                    if (edge.source == "START" or edge.target == "END") and \
                       not (edge.source in reasoning.nodes and edge.target in reasoning.nodes):
                        continue
                        
                    # Create a new edge with the same properties
                    reasoning_edge = Edge(
                        source=edge.source,
                        target=edge.target,
                        metadata=edge.metadata.copy() if edge.metadata else {}
                    )
                    
                    # Add the edge to the reasoning
                    reasoning.add_edge(reasoning_edge)
        
        # Add other reasoning strategies as needed
        
        return reasoning

    async def _execute_prosea(self, node: ExecutionNode, context: ExecutionContext,
                              validation_node: Optional[ExecutionNode] = None,
                              original_problem: Optional[str] = None,
                              agent_role: Optional[str] = None,
                              prev_signals: Optional[List[ExecutionSignal]] = None,
                              upper_signals: Optional[List[ExecutionSignal]] = None,
                              lower_signals: Optional[List[ExecutionSignal]] = None) -> List[ExecutionSignal]:
        """Execute PROSEA reasoning."""
        assert context.reasoning_llm is not None
        # print("\033[91mPrev signals\033[0m", prev_signals)
        prev_step_output = await self._get_previous_steps(prev_signals) if prev_signals else ""
        
        # Use the prompt template from metadata if available, otherwise fall back to description
        prompt_template = node.metadata.get("prompt", node.description)
        
        # Format the prompt with any available variables
        formatted_prompt = prompt_template
        
        # If we have an objective, format it into the prompt
        if context.current_workflow and context.current_workflow.objective:
            objective = context.current_workflow.objective.current
            formatted_prompt = formatted_prompt.replace("{objective}", objective)
        
        if "step_" in node.node_id:
            prompt = f"""
            {formatted_prompt}
            
            Previous steps: {prev_step_output}
            """
        else:
            prompt = formatted_prompt
        
        if validation_node is not None:
            response = await self._execute_prosea_step_with_validation(node=node, context=context, validation_node=validation_node, 
                                                                       original_problem=original_problem, agent_role=agent_role,
                                                                       prompt=prompt, prev_signals=prev_signals)
        else:
            conclusion_messages = [
                {"role": "system", "content": f"You are a {agent_role} expert."},
                {"role": "user", "content": prompt}
            ]
            response = await context.reasoning_llm.conversational_query(conclusion_messages)
            
        return [ExecutionSignal(
            type=ExecutionSignalType.DATA_RESULT,
            content={
                "result": response,
                "node": node.node_id,
                "type": ExecutionSignalType.DATA_RESULT
            }
        )]
    
    async def _get_previous_steps(self, prev_signals: List[ExecutionSignal]) -> str:
        """Get the previous steps."""
        previous_step_output = ""
        if len(prev_signals) > 2:
            for i in range(2, len(prev_signals)):
                if prev_signals[i].type == ExecutionSignalType.DATA_RESULT:
                    previous_step_output += prev_signals[i].content["result"]["content"]
                    previous_step_output += "\n\n"
        return previous_step_output
    
    async def _validate_response(self, response: str, node: ExecutionNode, validation_node: ExecutionNode, context: ExecutionContext,
                                 original_problem: Optional[str] = None, additional_prompt: Optional[str] = None,
                                 prev_signals: Optional[List[ExecutionSignal]] = None, agent_role: Optional[str] = None) -> List[any]:
        """Validate the response against the validation node."""
        assert validation_node is not None
        assert original_problem is not None
        previous_step_output = await self._get_previous_steps(prev_signals)
        validation_messages = [
            {"role": "system", "content": f"You are a {agent_role} expert."},
        ]
        
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
        validation_messages = self._update_messages(validation_messages, prompt)
        response = await context.reasoning_llm.conversational_query(validation_messages)
        response_text = response["content"]
        is_matched = "yes" in self.parse_by_key(response_text, "is_matched").lower()
        is_contradicted = "yes" in self.parse_by_key(response_text, "is_contradicted").lower()
        refined_criteria = self.parse_by_key(response_text, "refined_criteria")
        is_solvable_by_continuing_prompt = "yes" in self.parse_by_key(response_text, "is_solvable_by_continuing_prompt").lower()
        
        return is_matched, is_contradicted, refined_criteria, is_solvable_by_continuing_prompt    
    
    async def _adjust_criteria(self, validation_node: ExecutionNode, new_criteria: str) -> str:
        """Adjust the criteria based on the validation node."""
        validation_node.description = new_criteria
        return validation_node
    
    async def _adjust_prompt(self, previous_steps: str, step_prompt: str, step_expectation: str, 
                             previous_tried_prompt: str, previous_tried_output: str, context: ExecutionContext, agent_role: Optional[str] = None) -> str:
        """Adjust the prompt based on the validation node."""
        prompt_to_agent_for_next_prompt = f"""
                                    This is previous steps: {previous_steps} \n\n
                                    
                                    Let me remind you about the task you need to do is: {step_prompt}, 
                                    and the criteria need to achieve is {step_expectation}. 
                                    This is the previous prompt you wrote: {previous_tried_prompt}, and it doesn't work.
                                    I got this answer from that prompt: {previous_tried_output}
                                    
                                    First, analyze the reason why the previous prompt doesn't work, then generate a new prompt to achieve the expectation.
                                    
                                    Please generate a new prompt to achieve the expectation. Prompt must be direct and concise.
                                    Do not assume the important if you are not sure 
                                    and do not assume customized information (for example, different company will have different level ladder).
                                    If you assume something, please explain there reason why you chose that value before assume.
                                    
                                    Answer format:
                                    old_answer_analysis: Look at previous answer, analyze the reason why the previous answer is not matched to criteria.
                                    old_prompt_analysis: Look at previous prompt, analyze the reason why the previous prompt cannot get the correct answer.
                                    strategy_for_new_prompt: Based on the analysis above, let me know what do we need to change from the previous prompt to make it work.
                            
                                    additional_prompt: Based on the method to adjust prompt above, write a new prompt that can achieve the expectation here. New prompt need to be different with previous prompt.
                                    
                                    Do not forget the key and do not change the key format. Do not highlight the key.
                                    
                                    """
        adjusted_prompt_messages = [
            {"role": "system", "content": f"You are a {agent_role} expert."},
        ]
        adjusted_prompt_messages = self._update_messages(adjusted_prompt_messages, prompt_to_agent_for_next_prompt)
        response = await context.reasoning_llm.query({"prompt": prompt_to_agent_for_next_prompt})
        return response["content"]
    
    def _update_messages(self, messages: List[Dict[str, str]], text: str, role: str = "user") -> List[Dict[str, str]]:
        messages.append({"role": role, "content": text})
        return messages
        
    async def _execute_prosea_step_with_validation(self, node: ExecutionNode, context: ExecutionContext,
                              validation_node: Optional[ExecutionNode] = None,
                              original_problem: Optional[str] = None, prompt: str = None,
                              prev_signals: Optional[List[ExecutionSignal]] = None,
                              agent_role: Optional[str] = None) -> List[ExecutionSignal]:
        """Execute PROSEA reasoning with validation."""
        assert context.reasoning_llm is not None
        is_matched = False
        
        # Use provided prompt or get from metadata if available, otherwise fall back to description
        if prompt is None:
            prompt = node.metadata.get("prompt", node.description)
        
        # Format the prompt with any available variables
        formatted_prompt = prompt
        
        # If we have an objective, format it into the prompt
        if context.current_workflow and context.current_workflow.objective:
            objective = context.current_workflow.objective.current
            formatted_prompt = formatted_prompt.replace("{objective}", objective)
        
        execution_messages = [
            {"role": "system", "content": f"You are a {agent_role} expert."},
            {"role": "user", "content": formatted_prompt}
        ]
        
        max_tries = 3
        for i in range(max_tries):
            response = await context.reasoning_llm.conversational_query(execution_messages)
            response_text = response["content"]
            execution_messages = self._update_messages(execution_messages, response_text, role="assistant")
            # print("Response: ", response_text, "\n\n")
            is_matched, is_contradicted, refined_criteria, is_solvable_by_continuing_prompt = await self._validate_response(response=response_text, 
                                                                                                                             node=node, validation_node=validation_node, 
                                                                                                                             context=context, original_problem=original_problem,
                                                                                                                             additional_prompt=formatted_prompt, prev_signals=prev_signals,
                                                                                                                             agent_role=agent_role)
            print("Is matched: ", is_matched)
            if is_matched:
                break
            if is_contradicted:
                validation_node = await self._adjust_criteria(validation_node=validation_node, new_criteria=refined_criteria)
            if is_solvable_by_continuing_prompt:
                prompt = await self._adjust_prompt(previous_steps=prev_signals, step_prompt=formatted_prompt, step_expectation=validation_node.description, 
                                                   previous_tried_prompt=formatted_prompt, previous_tried_output=response_text, context=context, agent_role=agent_role)
        
        # Return the result as an execution signal
        return [ExecutionSignal(
            type=ExecutionSignalType.DATA_RESULT,
            content={
                "result": response,
                "node": node.node_id
            }
        )]
        
    async def _execute_direct(self, node: ExecutionNode, context: ExecutionContext) -> List[ExecutionSignal]:
        """Execute direct LLM query."""
        assert context.reasoning_llm is not None
        
        # Get the prompt template using the context's helper method
        prompt_template = node.get_prompt()
        
        # Format the prompt with any available variables
        formatted_prompt = prompt_template
        if not formatted_prompt:
            formatted_prompt = "Help me with my objective: {objective}"
        
        # If we have an objective, format it into the prompt
        if context.current_workflow and context.current_workflow.objective:
            objective = context.current_workflow.objective.current
            formatted_prompt = formatted_prompt.replace("{objective}", objective)
        
        # Execute the query
        response = await context.reasoning_llm.query({"prompt": formatted_prompt})
        
        # Return the result
        return [ExecutionSignal(
            type=ExecutionSignalType.DATA_RESULT,
            content={
                "result": response,
                "node": node.node_id
            }
        )]

    async def _execute_cot(self, node: ExecutionNode, context: ExecutionContext) -> List[ExecutionSignal]:
        """Execute chain-of-thought reasoning."""
        assert context.reasoning_llm is not None
        
        # Use the prompt template from metadata if available, otherwise fall back to description
        prompt_template = node.metadata.get("prompt", node.description)
        
        # Format the prompt with any available variables
        formatted_prompt = prompt_template
        
        # If we have an objective, format it into the prompt
        if context.current_workflow and context.current_workflow.objective:
            objective = context.current_workflow.objective.current
            formatted_prompt = formatted_prompt.replace("{objective}", objective)
            
        # Add chain-of-thought instruction
        formatted_prompt = f"{formatted_prompt}\n\nPlease think step-by-step to solve this problem."
        
        # Execute the query
        response = await context.reasoning_llm.query({"prompt": formatted_prompt})
        
        # Return the result
        return [ExecutionSignal(
            type=ExecutionSignalType.DATA_RESULT,
            content={
                "result": response,
                "node": node.node_id
            }
        )]

    async def _execute_ooda(self, node: ExecutionNode, context: ExecutionContext) -> List[ExecutionSignal]:
        """Execute OODA loop reasoning."""
        assert context.reasoning_llm is not None
        
        # Use the prompt template from metadata if available, otherwise fall back to description
        prompt_template = node.metadata.get("prompt", node.description)
        
        # Format the prompt with any available variables
        formatted_prompt = prompt_template
        
        # If we have an objective, format it into the prompt
        if context.current_workflow and context.current_workflow.objective:
            objective = context.current_workflow.objective.current
            formatted_prompt = formatted_prompt.replace("{objective}", objective)
            
        # Add OODA loop structure
        ooda_prompt = f"""
        {formatted_prompt}
        
        Please follow the OODA loop process to address this:
        1. Observe: What are the key facts and information?
        2. Orient: How do you interpret these facts given the context?
        3. Decide: What approach will you take?
        4. Act: Execute your approach and provide the solution.
        """
        
        # Execute the query
        response = await context.reasoning_llm.query({"prompt": ooda_prompt})
        
        # Return the result
        return [ExecutionSignal(
            type=ExecutionSignalType.DATA_RESULT,
            content={
                "result": response,
                "node": node.node_id
            }
        )]

    async def _execute_dana(self, node: ExecutionNode, context: ExecutionContext) -> List[ExecutionSignal]:
        """Execute DANA reasoning."""
        assert context.reasoning_llm is not None
        
        # Use the prompt template from metadata if available, otherwise fall back to description
        prompt_template = node.metadata.get("prompt", node.description)
        
        # Format the prompt with any available variables
        formatted_prompt = prompt_template
        
        # If we have an objective, format it into the prompt
        if context.current_workflow and context.current_workflow.objective:
            objective = context.current_workflow.objective.current
            formatted_prompt = formatted_prompt.replace("{objective}", objective)
            
        # Add DANA structure
        dana_prompt = f"""
        {formatted_prompt}
        
        Please follow the DANA process to address this:
        1. Define: Clearly define the problem and objectives
        2. Analyze: Break down the problem and analyze its components
        3. Navigate: Explore possible solutions and approaches
        4. Act: Implement the best solution and provide the result
        """
        
        # Execute the query
        response = await context.reasoning_llm.query({"prompt": dana_prompt})
        
        # Return the result
        return [ExecutionSignal(
            type=ExecutionSignalType.DATA_RESULT,
            content={
                "result": response,
                "node": node.node_id
            }
        )]
