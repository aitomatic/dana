"""Optimal workflow executor implementation."""

import json
import logging
from typing import List, Dict, Any, Optional
from opendxa.common.graph import (
    Node,
)
from opendxa.base.execution.execution_graph import ExecutionGraph
from opendxa.base.execution.execution_context import ExecutionContext
from opendxa.base.execution.execution_types import (
    ExecutionSignal,
    ExecutionSignalType,
    Objective,
)
from opendxa.execution.planning import PlanExecutor
from opendxa.execution.reasoning import ReasoningExecutor
from opendxa.execution.workflow.workflow_executor import WorkflowExecutor
from opendxa.execution.workflow.workflow_strategy import WorkflowStrategy
from opendxa.execution.planning import PlanStrategy
from opendxa.execution.reasoning import ReasoningStrategy

logger = logging.getLogger(__name__)

# Define OODA steps for reasoning
OODA_STEPS = ["OBSERVE", "ORIENT", "DECIDE", "ACT"]

class OptimalWorkflowExecutor(WorkflowExecutor):
    """Executes workflows with optimized three-layer execution.
    
    This executor extends WorkflowExecutor to implement an optimized execution pattern that:
    1. Determines the entire plan graph structure in a single LLM call
    2. Executes plan graphs based on their determined structure
    3. Optimizes reasoning layer execution based on complexity
    """

    def __init__(self,
                 workflow_strategy: WorkflowStrategy = WorkflowStrategy.DEFAULT,
                 planning_strategy: PlanStrategy = PlanStrategy.DEFAULT,
                 reasoning_strategy: ReasoningStrategy = ReasoningStrategy.DEFAULT):
        super().__init__(workflow_strategy, planning_strategy, reasoning_strategy)
        self.results = ExecutionResults()
        self.plan_executor = PlanExecutor()
        self.reasoning_executor = ReasoningExecutor()
        self.workflow = None
        self.context = None
    
    async def execute_workflow(
        self,
        workflow: ExecutionGraph,
        context: ExecutionContext
    ) -> List[ExecutionSignal]:
        """Execute a workflow graph with optimized three-layer pattern.
        
        Args:
            workflow: The workflow graph to execute
            context: Execution context
            
        Returns:
            List of execution signals
        """
        # Set up execution context
        self.workflow = workflow
        self.context = context
        
        # Initialize results manager with workflow
        start_node = workflow.get_start_node()
        assert start_node is not None, "Workflow must have a start node"
        self.results.set_current_plan(start_node.node_id)
        
        # Execute the graph
        return await self.execute(
            workflow,
            context
        )
    
    async def _execute_node_core(
        self,
        node: Node,
        context: ExecutionContext
    ) -> List[ExecutionSignal]:
        """Execute the plan layer for a workflow node with optimizations.
        
        This method implements an optimized execution pattern that:
        1. Determines the entire plan graph structure in a single LLM call
        2. Executes the plan graph based on its structure
        3. Creates a workflow-level summary of all results
        4. Returns the results as execution signals
        
        Args:
            node: Node to execute lower layer for
            context: Execution context
            
        Returns:
            List of execution signals
        """
        if not self.workflow:
            raise RuntimeError("No graph set in workflow executor")
            
        # Get the objective from the graph
        objective = self.workflow.objective if self.workflow else None
        if not objective:
            objective = Objective(f"Execute workflow node {node.node_id}")
        
        # Determine the plan graph structure
        plan_graph = await self._create_plan_graph(node, objective, context)
        if not plan_graph:
            logger.warning(f"No plan created for workflow node {node.node_id}")
            return []
        
        # Execute the plan graph
        plan_results = await self._execute_plan_graph(plan_graph, objective, context, [node])
        
        # Create workflow-level summary of all results
        await self._create_workflow_summary(node, plan_results, objective, context)
        
        # Convert results to execution signals
        signals = []
        for plan_id, result in plan_results.items():
            if isinstance(result, dict) and 'consolidated' in result:
                # Option A: One consolidated result
                signal = ExecutionSignal(
                    type=ExecutionSignalType.DATA_RESULT,
                    content={
                        "node": plan_id,
                        "result": result['consolidated']
                    }
                )
                signals.append(signal)
            else:
                # Option B: Multiple results
                signal = ExecutionSignal(
                    type=ExecutionSignalType.DATA_RESULT,
                    content={
                        "node": plan_id,
                        "result": result
                    }
                )
                signals.append(signal)
        
        return signals
    
    async def _create_plan_graph(
        self,
        workflow_node: Node,
        objective: Objective,
        context: ExecutionContext,
        parent_nodes: Optional[List[Node]] = None
    ) -> Dict[str, Any]:
        """Create a plan graph for a workflow node.
        
        Args:
            workflow_node: The workflow node to create plans for
            objective: The overall task objective
            context: Current execution context
            parent_nodes: Optional ordered list of nodes from workflow root to current node,
                          where parent_nodes[0] is the workflow node
        
        Returns:
            Dictionary mapping plan IDs to their graph structures
        """
        if parent_nodes is None:
            parent_nodes = [workflow_node]
        
        # Get previous results for the workflow node
        previous_results = {}
        for parent_node in parent_nodes:
            result_key = ResultKey(
                node_id=parent_node.node_id,
                step="REASONING"
            )
            previous_results[parent_node.node_id] = self.results.get_relevant_context(result_key)
        
        # Create a prompt for the LLM to create the plan graph
        hierarchy_text = self._create_hierarchy_text(parent_nodes)
        previous_results_text = self._format_previous_results(previous_results, workflow_node.node_id)
        
        # Example JSON structure (non-f-string part)
        example_json = '''
        {
            "understanding": "Your confirmation of understanding the tasks",
            "plan_graph": {
                "ANALYZE_DATA": {
                    "node": {
                        "node_id": "ANALYZE_DATA",
                        "description": "Analyze the data to identify patterns and insights"
                    },
                    "objective": "Extract meaningful insights from the data",
                    "requires_sub_plan": false,
                    "reasoning_nodes": [
                        {
                            "id": "REASONING",
                            "description": "Combined OODA (Observe, Orient, Decide, Act) reasoning step",
                            "ooda_steps": ["OBSERVE", "ORIENT", "DECIDE", "ACT"]
                        }
                    ]
                },
                "GENERATE_REPORT": {
                    "node": {
                        "node_id": "GENERATE_REPORT",
                        "description": "Generate a comprehensive report of findings"
                    },
                    "objective": "Create a clear and actionable report",
                    "requires_sub_plan": true,
                    "reasoning_nodes": [
                        {
                            "id": "REASONING",
                            "description": "Combined OODA (Observe, Orient, Decide, Act) reasoning step",
                            "ooda_steps": ["OBSERVE", "ORIENT", "DECIDE", "ACT"]
                        }
                    ]
                }
            }
        }
        '''
        
        # Main prompt with f-strings
        prompt = f"""
        Create a plan graph for the workflow node: {workflow_node.node_id}
        
        Node Hierarchy:
        {hierarchy_text}
        
        Current Node Description: {workflow_node.description}
        Overall Objective: {objective.current}
        
        Previous Results:
        {previous_results_text}
        
        Instructions:
        1. First, explicitly confirm your understanding of:
           a) The workflow node task
           b) The overall objective
           c) The previous results and their implications
        
        2. Create a plan graph that:
           a) Breaks down the workflow node into specific plan nodes with descriptive IDs
           b) Each plan node should have a clear objective
           c) Plan nodes can be sequential or parallel
           d) Some plan nodes may require sub-plans
        
        3. For each plan node:
           a) Define a clear objective
           b) Specify if it requires sub-plans
           c) Include a single reasoning step that combines OODA (Observe, Orient, Decide, Act)
              - OBSERVE: Gather and collect information about the current situation
              - ORIENT: Analyze and synthesize the observed information
              - DECIDE: Make decisions based on the analysis
              - ACT: Execute the decided actions
        
        4. Ensure the plan graph:
           a) Builds upon previous results
           b) Advances the overall objective
           c) Maintains consistency with workflow-level outcomes
        
        Your response should be a JSON object with the following structure:
        {example_json}
        
        Each plan node should have exactly one reasoning node with id "REASONING".
        The reasoning node should combine all OODA steps into a single step while maintaining
        the descriptive nature of the plan node IDs.
        """
        
        # Call the LLM to create the plan graph
        result = await self._call_llm(
            prompt,
            context,
            "You are creating a plan graph for a workflow node."
        )
        
        try:
            # Parse the JSON response
            response_data = json.loads(result)
            plan_graph = response_data.get('plan_graph', {})
            
            # Validate the plan graph structure
            for plan_id, plan_data in plan_graph.items():
                if not isinstance(plan_data, dict):
                    raise ValueError(f"Invalid plan data for {plan_id}")
                
                if 'node' not in plan_data:
                    raise ValueError(f"Missing node data for {plan_id}")
                
                if 'reasoning_nodes' not in plan_data:
                    raise ValueError(f"Missing reasoning nodes for {plan_id}")
                
                # Ensure there is exactly one reasoning node with id "REASONING"
                reasoning_nodes = plan_data['reasoning_nodes']
                if len(reasoning_nodes) != 1:
                    raise ValueError(f"Expected exactly one reasoning node for {plan_id}")
                if reasoning_nodes[0]['id'] != "REASONING":
                    raise ValueError(f"Reasoning node must have id 'REASONING' for {plan_id}")
                
                # Ensure the reasoning node has OODA steps
                if 'ooda_steps' not in reasoning_nodes[0]:
                    raise ValueError(f"Reasoning node must have ooda_steps for {plan_id}")
                if reasoning_nodes[0]['ooda_steps'] != OODA_STEPS:
                    raise ValueError(f"Reasoning node must have correct OODA steps for {plan_id}")
            
            return plan_graph
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse plan graph as JSON: {e}")
            logger.error(f"Raw response: {result}")
            return {}
        except ValueError as e:
            logger.error(f"Invalid plan graph structure: {e}")
            return {}
    
    async def _execute_plan_graph(
        self,
        plan_graph: Dict[str, Any],
        objective: Objective,
        context: ExecutionContext,
        parent_nodes: List[Node]
    ) -> Dict[str, Any]:
        """Execute the plan graph based on its structure, supporting hierarchical plans.
        
        Args:
            plan_graph: The plan graph structure
            objective: The overall task objective
            context: Current execution context
            parent_nodes: Ordered list of nodes from workflow root to current plan,
                          where parent_nodes[0] is the workflow node
        
        Returns:
            Dictionary of plan results
        """
        plan_results = {}
        
        logger.info(f"\nExecuting plan graph with parent nodes: {[n.node_id for n in parent_nodes]}")
        
        for plan_id, plan_data in plan_graph.items():
            plan_node = plan_data['node']
            requires_sub_plan = plan_data.get('requires_sub_plan', False)
            
            # Set current plan for results tracking
            self.results.set_current_plan(plan_id)
            logger.info(f"\nProcessing plan node: {plan_id}")
            logger.info(f"Parent nodes: {[n.node_id for n in parent_nodes]}")
            
            if requires_sub_plan:
                # Create sub-plan graph for this node
                sub_plan_graph = await self._create_plan_graph(
                    parent_nodes[0],  # workflow node
                    objective,
                    context,
                    parent_nodes[1:] + [plan_node]  # existing plans + current plan
                )
                
                if sub_plan_graph:
                    # Execute the sub-plan graph
                    sub_results = await self._execute_plan_graph(
                        sub_plan_graph,
                        objective,
                        context,
                        parent_nodes + [plan_node]  # full hierarchy including current plan
                    )
                    plan_results[plan_id] = sub_results
                else:
                    plan_results[plan_id] = {
                        'error': 'Failed to create sub-plan graph'
                    }
            else:
                # Execute reasoning for this plan node
                reasoning_node = plan_data['reasoning_nodes'][0]  # Get the single reasoning node
                
                # Create result key for the reasoning step
                workflow_node_id = parent_nodes[0].node_id
                composite_id = f"{workflow_node_id}.{plan_id}"
                
                # Get previous results for the reasoning step
                result_key = ResultKey(
                    node_id=composite_id,
                    step="REASONING"
                )
                previous_results = self.results.get_relevant_context(result_key)
                
                # Create a prompt for the reasoning step
                workflow_task = parent_nodes[0].description
                plan_task = plan_node.description
                reasoning_task = reasoning_node.get('description', '')
                
                # Create hierarchy text and previous results text
                hierarchy_text = self._create_hierarchy_text(parent_nodes + [plan_node])
                previous_results_text = self._format_previous_results(previous_results, composite_id)
                
                # Build the prompt using string concatenation
                reasoning_prompt = (
                    "Execute the reasoning step for the current plan node.\n\n"
                    f"Node Hierarchy:\n{hierarchy_text}\n\n"
                    f"Current Plan Node: {plan_id}\n"
                    f"Plan Description: {plan_node.description}\n"
                    f"Plan Objective: {reasoning_node.get('description', '')}\n\n"
                    f"Overall Objective: {objective.current}\n\n"
                    f"Previous Results:\n{previous_results_text}\n\n"
                    "Instructions:\n"
                    "1. First, explicitly confirm your understanding of the tasks,\n"
                    f"   a) The workflow node task: {workflow_task}\n"
                    f"   b) The current plan node task: {plan_task}\n"
                    f"   c) Your specific reasoning step task: {reasoning_task}\n\n"
                    "2. Review all previous results carefully, following the usage instructions for each context\n"
                    "3. Build upon earlier observations and analysis\n"
                    "4. Maintain consistency with workflow-level outcomes\n"
                    "5. Coordinate with results from parallel plan nodes\n"
                    "6. Ensure your response advances the overall objective\n\n"
                    "7. Execute the OODA (Observe, Orient, Decide, Act) cycle:\n"
                    "   a) OBSERVE: Gather and collect information about the current situation\n"
                    "      - What information is available?\n"
                    "      - What are the key facts and data points?\n"
                    "      - What is the current state of the system?\n"
                    "      - What patterns or anomalies can be identified?\n\n"
                    "   b) ORIENT: Analyze and synthesize the observed information\n"
                    "      - What does the collected information mean in this context?\n"
                    "      - How does it relate to the objective?\n"
                    "      - What patterns or relationships emerge?\n"
                    "      - What are the implications of these observations?\n\n"
                    "   c) DECIDE: Make decisions based on the analysis\n"
                    "      - What are the possible courses of action?\n"
                    "      - What are the pros and cons of each option?\n"
                    "      - What is the best path forward?\n"
                    "      - What specific actions should be taken?\n\n"
                    "   d) ACT: Execute the decided actions\n"
                    "      - What specific steps need to be taken?\n"
                    "      - How should the decision be implemented?\n"
                    "      - What is the expected outcome?\n"
                    "      - How will success be measured?\n\n"
                    "Your response should be a JSON object with the following structure:\n"
                    "{\n"
                    "    \"understanding\": \"Your confirmation of understanding\",\n"
                    "    \"result\": {\n"
                    "        \"OBSERVE\": \"Your observations\",\n"
                    "        \"ORIENT\": \"Your analysis\",\n"
                    "        \"DECIDE\": \"Your decisions\",\n"
                    "        \"ACT\": \"Your actions\"\n"
                    "    }\n"
                    "}"
                )
                
                # Execute the reasoning step
                result = await self._call_llm(
                    reasoning_prompt,
                    context,
                    "You are executing a reasoning step for a plan node."
                )
                
                try:
                    # Parse the JSON response
                    response_data = json.loads(result)
                    reasoning_result = response_data.get('result', {})
                    
                    # Store the reasoning result
                    result_key = ResultKey(
                        node_id=composite_id,
                        step="REASONING"
                    )
                    self.results.store(result_key, reasoning_result)
                    logger.info(f"Stored reasoning result for key: {result_key}")
                    
                    # Get the reasoning result for this plan node
                    plan_results[plan_id] = {
                        'reasoning': self.results.get_latest(composite_id, "REASONING")
                    }
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse reasoning result as JSON: {e}")
                    logger.error(f"Raw response: {result}")
                    plan_results[plan_id] = {
                        'error': 'Failed to parse reasoning result'
                    }
        
        return plan_results
    
    def _create_reasoning_prompt(
        self,
        parent_nodes: List[Node],
        reasoning_node: Dict[str, Any],
        objective: Objective,
        context: ExecutionContext,
        previous_results: Dict[str, Any]
    ) -> str:
        """Create a prompt for reasoning execution.
        
        Args:
            parent_nodes: Ordered list of nodes from workflow root to current plan,
                          where parent_nodes[0] is the workflow node
            reasoning_node: The reasoning node data
            objective: The overall task objective
            context: Current execution context
            previous_results: Results from previous steps with usage instructions
        
        Returns:
            The reasoning prompt
        """
        # Build hierarchy description
        hierarchy_desc = []
        for i, node in enumerate(parent_nodes):
            if i == 0:
                hierarchy_desc.append(f"Workflow Node: {node.node_id} - {node.description}")
            else:
                hierarchy_desc.append(f"Level {i} Plan: {node.node_id} - {node.description}")
        
        hierarchy_text = "\n".join(hierarchy_desc)
        
        # Get the current plan node (last in hierarchy)
        current_plan = parent_nodes[-1]
        
        # Get OODA step description
        ooda_descriptions = {
            "OBSERVE": """
                OBSERVE: Gather and collect information about the current situation
                - What information is available?
                - What are the key facts and data points?
                - What is the current state of the system?
                - What patterns or anomalies can be identified?
                Your response should focus on objective observations and data gathering.
            """,
            "ORIENT": """
                ORIENT: Analyze and synthesize the observed information
                - What does the collected information mean in this context?
                - How does it relate to the objective?
                - What patterns or relationships emerge?
                - What are the implications of these observations?
                Your response should focus on analysis and understanding of the observations.
            """,
            "DECIDE": """
                DECIDE: Make decisions based on the analysis
                - What are the possible courses of action?
                - What are the pros and cons of each option?
                - What is the best path forward?
                - What specific actions should be taken?
                Your response should focus on clear decision-making and justification.
            """,
            "ACT": """
                ACT: Execute the decided actions
                - What specific steps need to be taken?
                - How should the decision be implemented?
                - What is the expected outcome?
                - How will success be measured?
                Your response should focus on concrete actions and implementation details.
            """
        }
        
        step_description = ooda_descriptions.get(reasoning_node['id'], "")
        
        # Build previous results section with explicit usage instructions
        previous_results_text = []
        
        # Add immediate context (previous steps in current plan)
        immediate_context = previous_results.get('immediate_context', {})
        if immediate_context.get('results'):
            composite_id = f"{parent_nodes[0].node_id}.{current_plan.node_id}"
            previous_results_text.append(f"Previous steps in current plan ({composite_id}):")
            previous_results_text.append(immediate_context['usage'])
            for key, result in immediate_context['results'].items():
                step = key.split('.')[-1]  # Get the OODA step from the key
                previous_results_text.append(f"- {step}: {result}")
        
        # Add recent context (other plan nodes)
        recent_context = previous_results.get('recent_context', {})
        if recent_context.get('results'):
            previous_results_text.append(f"\nResults from recent plan nodes ({parent_nodes[0].node_id}):")
            previous_results_text.append(recent_context['usage'])
            for key, result in recent_context['results'].items():
                plan_id = key.split('.')[0]  # Get the plan ID from the key
                step = key.split('.')[-1]    # Get the OODA step from the key
                previous_results_text.append(f"- {plan_id} ({step}): {result}")
        
        # Add historical context (important historical steps)
        historical_context = previous_results.get('historical_context', {})
        if historical_context.get('results'):
            previous_results_text.append(f"\nImportant historical results ({parent_nodes[0].node_id}):")
            previous_results_text.append(historical_context['usage'])
            for key, result in historical_context['results'].items():
                node_id = key.split('.')[0]  # Get the node ID from the key
                step = key.split('.')[-1]    # Get the OODA step from the key
                previous_results_text.append(f"- {node_id} ({step}): {result}")
        
        previous_results_section = (
            "\n".join(previous_results_text) if previous_results_text 
            else "No previous results available"
        )
        
        return f"""
        Execute the following reasoning step as part of the OODA (Observe, Orient, Decide, Act) loop.
        Each step has a specific purpose in the decision-making process.
        
        Node Hierarchy:
        {hierarchy_text}
        
        Current Reasoning Step ID: {parent_nodes[0].node_id}.{current_plan.node_id}.{reasoning_node['id']}
        
        Current Plan Node: {current_plan.node_id}
        Plan Description: {current_plan.description}
        
        {step_description}
        
        Specific Task Description: {reasoning_node.get('description', '')}
        Overall Objective: {objective.current}
        
        Previous Results:
        {previous_results_section}
        
        Instructions:
        1. First, explicitly confirm your understanding of the tasks,
           a) The workflow node task: {parent_nodes[0].description}
           b) The current plan node task: {current_plan.description}
           c) Your specific reasoning step task: {reasoning_node.get('description', '')}
        
        2. Review all previous results carefully, following the usage instructions for each context
        3. Build upon earlier observations and analysis
        4. Maintain consistency with workflow-level outcomes
        5. Coordinate with results from parallel plan nodes
        6. Ensure your response advances the overall objective
        7. Follow the specific requirements of your OODA step
        
        Your response should start with a clear confirmation of your understanding of the tasks,
        then proceed with the actual reasoning step execution.
        
        Return a complete, well-structured reasoning result that fulfills the specific requirements
        of this OODA step while advancing toward the overall objective.
        """
    
    async def _call_llm(
        self,
        prompt: str,
        context: ExecutionContext,
        system_prompt: str = "You are executing a plan or reasoning task."
    ) -> str:
        """Call the LLM with a prompt.
        
        Args:
            prompt: The prompt to send
            context: Current execution context
            system_prompt: The system prompt to use
        
        Returns:
            The LLM response
        """
        if context and context.reasoning_llm:
            response = await context.reasoning_llm.query({
                "prompt": prompt,
                "system_prompt": system_prompt,
                "parameters": {
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
            })
            
            if response and "content" in response:
                return response["content"]
        
        return "Error: No LLM response available"
    
    async def _create_workflow_summary(
        self,
        workflow_node: Node,
        plan_results: Dict[str, Any],
        objective: Objective,
        context: ExecutionContext
    ) -> None:
        """Create and store a workflow-level summary of all plan results.
        
        Args:
            workflow_node: The current workflow node
            plan_results: Results from all plan nodes
            objective: The overall task objective
            context: Current execution context
        """
        # Create a summary prompt that includes all plan results
        summary_prompt = f"""
        Create a comprehensive summary of the results from the {workflow_node.node_id} workflow step.
        This summary will be used by subsequent workflow steps to understand what has been accomplished
        and avoid repeating work.
        
        Workflow Node: {workflow_node.node_id}
        Description: {workflow_node.description}
        Objective: {objective.current}
        
        Plan Results:
        """
        
        # Add each plan's results to the prompt
        for plan_id, results in plan_results.items():
            if isinstance(results, dict) and 'reasoning' in results:
                summary_prompt += f"\nPlan: {plan_id}\n"
                for step, result in results['reasoning'].items():
                    summary_prompt += f"{step}:\n{result}\n"
        
        summary_prompt += """
        Instructions:
        1. Review all plan results carefully
        2. Create a clear, concise summary that:
           - Captures the key findings and decisions
           - Highlights important patterns or insights
           - Notes any limitations or assumptions
           - Identifies what work has been completed
        3. Format the summary in a way that will be useful for subsequent workflow steps
        4. Focus on information that will help avoid repeating work
        """
        
        # Get the summary from the LLM
        if context and context.reasoning_llm:
            response = await context.reasoning_llm.query({
                "prompt": summary_prompt,
                "system_prompt": "You are creating a workflow-level summary of completed work.",
                "parameters": {
                    "temperature": 0.3,
                    "max_tokens": 1000
                }
            })
            
            if response and "content" in response:
                # Store the summary with a special key format
                summary_key = ResultKey(
                    node_id=f"{workflow_node.node_id}.SUMMARY",
                    step="ALL"
                )
                self.results.store(summary_key, response["content"])
                logger.info(f"Stored workflow summary for {workflow_node.node_id}")
            else:
                logger.warning(f"Failed to create workflow summary for {workflow_node.node_id}")
        else:
            logger.warning("No LLM available to create workflow summary")
    
    def _create_hierarchy_text(self, nodes: List[Node]) -> str:
        """Create a text description of the node hierarchy.
        
        Args:
            nodes: List of nodes from workflow root to current node
            
        Returns:
            Formatted hierarchy text
        """
        hierarchy_desc = []
        for i, node in enumerate(nodes):
            if i == 0:
                hierarchy_desc.append(f"Workflow Node: {node.node_id} - {node.description}")
            else:
                hierarchy_desc.append(f"Level {i} Plan: {node.node_id} - {node.description}")
        return "\n".join(hierarchy_desc)
    
    def _get_ooda_description(self, step: str) -> str:
        """Get the description for an OODA step.
        
        Args:
            step: The OODA step name
            
        Returns:
            The step description
        """
        ooda_descriptions = {
            "OBSERVE": """
                OBSERVE: Gather and collect information about the current situation
                - What information is available?
                - What are the key facts and data points?
                - What is the current state of the system?
                - What patterns or anomalies can be identified?
                Your response should focus on objective observations and data gathering.
            """,
            "ORIENT": """
                ORIENT: Analyze and synthesize the observed information
                - What does the collected information mean in this context?
                - How does it relate to the objective?
                - What patterns or relationships emerge?
                - What are the implications of these observations?
                Your response should focus on analysis and understanding of the observations.
            """,
            "DECIDE": """
                DECIDE: Make decisions based on the analysis
                - What are the possible courses of action?
                - What are the pros and cons of each option?
                - What is the best path forward?
                - What specific actions should be taken?
                Your response should focus on clear decision-making and justification.
            """,
            "ACT": """
                ACT: Execute the decided actions
                - What specific steps need to be taken?
                - How should the decision be implemented?
                - What is the expected outcome?
                - How will success be measured?
                Your response should focus on concrete actions and implementation details.
            """
        }
        return ooda_descriptions.get(step, "")
    
    def _format_previous_results(
        self,
        previous_results: Dict[str, Any],
        composite_id: str
    ) -> str:
        """Format previous results for inclusion in a prompt.
        
        Args:
            previous_results: Dictionary of previous results with context
            composite_id: The composite node ID
            
        Returns:
            Formatted previous results text
        """
        result_texts = []
        
        # Add immediate context
        immediate_context = previous_results.get('immediate_context', {})
        if immediate_context.get('results'):
            result_texts.append("Previous steps in current plan:")
            result_texts.append(immediate_context['usage'])
            for key, result in immediate_context['results'].items():
                step = key.split('.')[-1]
                result_texts.append(f"- {step}: {result}")
        
        # Add recent context
        recent_context = previous_results.get('recent_context', {})
        if recent_context.get('results'):
            result_texts.append("\nResults from recent plan nodes:")
            result_texts.append(recent_context['usage'])
            for key, result in recent_context['results'].items():
                plan_id = key.split('.')[0]
                step = key.split('.')[-1]
                result_texts.append(f"- {plan_id} ({step}): {result}")
        
        # Add historical context
        historical_context = previous_results.get('historical_context', {})
        if historical_context.get('results'):
            result_texts.append("\nImportant historical results:")
            result_texts.append(historical_context['usage'])
            for key, result in historical_context['results'].items():
                node_id = key.split('.')[0]
                step = key.split('.')[-1]
                result_texts.append(f"- {node_id} ({step}): {result}")
        
        return "\n".join(result_texts) if result_texts else "No previous results available" 