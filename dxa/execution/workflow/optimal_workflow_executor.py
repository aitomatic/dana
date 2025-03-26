"""Optimal workflow executor implementation.

This module provides an optimized workflow executor that implements
a three-layer execution pattern with planning ahead and node optimization.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from ...common.graph import (
    Node,
    NodeType,
)
from ..results import (
    ExecutionResults,
    ResultKey,
    OODA_STEPS
)
from ..execution_graph import ExecutionGraph
from ..execution_context import ExecutionContext
from ..execution_types import (
    ExecutionSignal,
    ExecutionSignalType,
    Objective,
)
from ..planning import PlanExecutor
from ..reasoning import ReasoningExecutor
from .workflow_executor import WorkflowExecutor
from .workflow_strategy import WorkflowStrategy
from ..planning import PlanStrategy
from ..reasoning import ReasoningStrategy

logger = logging.getLogger(__name__)

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
        context: ExecutionContext,
        prev_signals: Optional[List[ExecutionSignal]] = None,
        upper_signals: Optional[List[ExecutionSignal]] = None,
        lower_signals: Optional[List[ExecutionSignal]] = None
    ) -> List[ExecutionSignal]:
        """Execute a workflow graph with optimized three-layer pattern.
        
        Args:
            workflow: The workflow graph to execute
            context: Execution context
            prev_signals: Previous execution signals
            upper_signals: Signals from upper layer
            lower_signals: Signals from lower layer
            
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
        return await self.execute_graph(
            workflow,
            context,
            prev_signals,
            upper_signals,
            lower_signals
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
        3. Returns the results as execution signals
        
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
    ) -> Optional[Dict[str, Any]]:
        """Determine the plan graph structure, supporting hierarchical plans.
        
        Args:
            workflow_node: The current workflow node
            objective: The overall task objective
            context: Current execution context
            parent_nodes: Optional list of parent nodes in the hierarchy
        
        Returns:
            A complete plan graph structure
        """
        if parent_nodes is None:
            parent_nodes = []
        
        # Get all workflow steps and current position
        workflow_steps = []
        if self.workflow:
            # Get start node
            start_node = self.workflow.get_start_node()
            if start_node:
                current_node_id = start_node.node_id
                while current_node_id:
                    workflow_steps.append(current_node_id)
                    next_nodes = self.workflow.get_next_nodes(current_node_id)
                    current_node_id = next_nodes[0].node_id if next_nodes else None
        
        # Create workflow steps description with current step highlighted
        workflow_desc = []
        for i, step in enumerate(workflow_steps):
            if step == workflow_node.node_id:
                workflow_desc.append(f"  {i + 1}. {step} (CURRENT)")
            else:
                workflow_desc.append(f"  {i + 1}. {step}")
        workflow_text = "\n".join(workflow_desc)
        
        # Get previous results for this workflow node and its plans
        previous_results = {}
        
        # Get workflow-level results
        logger.info(f"Getting workflow-level results for node {workflow_node.node_id}")
        for step in OODA_STEPS:
            result = self.results.get_latest(workflow_node.node_id, step)
            if result:
                logger.info(f"Found workflow result for {workflow_node.node_id}.{step}")
                previous_results[f"{workflow_node.node_id}.{step}"] = result
        
        # Get results from previous plans
        logger.info(f"Getting plan-level results for {len(parent_nodes)} parent nodes")
        for parent in parent_nodes:
            for step in OODA_STEPS:
                # Create composite node_id by concatenating workflow and plan IDs
                composite_node_id = f"{workflow_node.node_id}.{parent.node_id}"
                result = self.results.get_latest(composite_node_id, step)
                if result:
                    logger.info(f"Found plan result for {composite_node_id}.{step}")
                    previous_results[f"{composite_node_id}.{step}"] = result
        
        logger.info(f"Total previous results found: {len(previous_results)}")
        
        # Create prompt to determine planning structure
        # Build hierarchy description, starting with workflow node
        hierarchy_desc = []
        hierarchy_desc.append(f"Workflow Node: {workflow_node.node_id} - {workflow_node.description}")
        for i, parent in enumerate(parent_nodes):
            hierarchy_desc.append(f"Level {i + 1} Plan: {parent.node_id} - {parent.description}")
        
        hierarchy_text = "\n".join(hierarchy_desc)
        
        # Format previous results for the prompt
        previous_results_section = ""
        if previous_results:
            previous_results_section = "\nPREVIOUS RESULTS:\n"
            # Group results by node
            results_by_node = {}
            for key, result in previous_results.items():
                # Split the key into node_id and step
                parts = key.split('.')
                node_id = '.'.join(parts[:-1])  # Everything except the last part
                step = parts[-1]  # The last part is the step
                if node_id not in results_by_node:
                    results_by_node[node_id] = {}
                results_by_node[node_id][step] = result
            
            # Format results grouped by node
            for node_id, node_results in results_by_node.items():
                previous_results_section += f"\nNode: {node_id}\n"
                for step in OODA_STEPS:
                    if step in node_results:
                        result_text = str(node_results[step])
                        # Truncate long results to keep the prompt manageable
                        if len(result_text) > 500:
                            result_text = result_text[:497] + "..."
                        previous_results_section += f"  {step}:\n{result_text}\n"
            previous_results_section += "\nYou can reuse these results where appropriate."
            
            logger.info(f"Previous results section length: {len(previous_results_section)}")
            logger.info(f"Previous results section:\n{previous_results_section}")
        else:
            logger.info("No previous results found to include in prompt")
        
        plan_structure_prompt = f"""
        Based on the following node hierarchy and objective "{objective.current}",
        determine the most appropriate plan structure. Each plan node can either:
        1. Map directly to reasoning nodes (for simple tasks)
        2. Require further breakdown into sub-plans (for complex tasks that need decomposition)
        3. Reuse previous results (if available and still valid)
        
        IMPORTANT: This is the {workflow_node.node_id} step of the workflow.
        Complete Workflow Steps:
        {workflow_text}
        
        {previous_results_section}
        
        Your plan should focus ONLY on this step's responsibilities.
        Do not try to handle responsibilities of other workflow steps.
        
        CRITICAL PRINCIPLES:
        1. Start Simple:
           - Begin with a single plan node
           - Only break down into multiple nodes if absolutely necessary
           - Each additional node adds complexity and potential for duplication
        
        2. Respect Workflow Boundaries:
           - Focus only on the current workflow step
           - Don't try to handle responsibilities of future workflow steps
           - Let each workflow step handle its own concerns
        
        3. Minimal OODA Steps:
           - Only include OODA steps that are truly necessary
           - Different tasks need different combinations of steps
           - Avoid including steps just because they're available
        
        4. Reuse Previous Results:
           - If previous results exist and are still valid, reuse them
           - Only create new reasoning nodes for missing or invalid results
           - Mark nodes as PREVIOUS_RESULTS when reusing existing results
           - You can mark individual nodes or the entire plan as PREVIOUS_RESULTS
        
        Examples of GOOD Simple Plans:
        1. Single Node with Minimal Steps:
           {{
               "id": "ANALYZE_REVIEWS",
               "description": "Analyze customer reviews to identify key themes",
               "requires_sub_plan": false,
               "reasoning_nodes": [
                   {{
                       "id": "OBSERVE",
                       "description": "Review the prepared data"
                   }},
                   {{
                       "id": "ORIENT",
                       "description": "Identify key themes and patterns"
                   }}
               ]
           }}
        
        2. Single Node with Selective Steps:
           {{
               "id": "MAKE_DECISION",
               "description": "Make a decision based on previous analysis",
               "requires_sub_plan": false,
               "reasoning_nodes": [
                   {{
                       "id": "ORIENT",
                       "description": "Review previous analysis"
                   }},
                   {{
                       "id": "DECIDE",
                       "description": "Make the decision"
                   }}
               ]
           }}
        
        3. Reusing Previous Results:
           {{
               "id": "PREVIOUS_RESULTS",
               "description": "Using previously completed results",
               "requires_sub_plan": false,
               "reasoning_nodes": []
           }}
        
        4. Mixed Plan with Reused Results:
           {{
               "id": "ANALYZE_AND_DECIDE",
               "description": "Analyze data and make decision",
               "requires_sub_plan": true,
               "sub_plans": [
                   {{
                       "id": "PREVIOUS_RESULTS",
                       "description": "Using previous analysis results",
                       "requires_sub_plan": false,
                       "reasoning_nodes": []
                   }},
                   {{
                       "id": "MAKE_DECISION",
                       "description": "Make decision based on analysis",
                       "requires_sub_plan": false,
                       "reasoning_nodes": [
                           {{
                               "id": "DECIDE",
                               "description": "Make the final decision"
                           }}
                       ]
                   }}
               ]
           }}
        
        Example of BAD Complex Plan (Avoid This):
        {{
            "id": "COMPLEX_ANALYSIS",
            "description": "Overly complex plan trying to do too much",
            "requires_sub_plan": true,
            "sub_plans": [
                {{
                    "id": "GATHER_DATA",
                    "description": "Gather all possible data",
                    "requires_sub_plan": false,
                    "reasoning_nodes": [
                        {{"id": "OBSERVE", "description": "Gather data"}},
                        {{"id": "ORIENT", "description": "Organize data"}},
                        {{"id": "DECIDE", "description": "Decide what to keep"}},
                        {{"id": "ACT", "description": "Store the data"}}
                    ]
                }},
                {{
                    "id": "ANALYZE_DATA",
                    "description": "Analyze the gathered data",
                    "requires_sub_plan": false,
                    "reasoning_nodes": [
                        {{"id": "OBSERVE", "description": "Review data"}},
                        {{"id": "ORIENT", "description": "Find patterns"}},
                        {{"id": "DECIDE", "description": "Determine insights"}},
                        {{"id": "ACT", "description": "Document findings"}}
                    ]
                }}
            ]
        }}
        
        Node Hierarchy:
        {hierarchy_text}
        
        You MUST respond with a valid JSON object in the following exact format:
        {{
            "justification": "Your explanation for choosing this structure",
            "plan_nodes": [
                {{
                    "id": "ANALYZE_TASK",
                    "description": "Clear description of what this plan node does",
                    "requires_sub_plan": false,
                    "reasoning_nodes": [
                        {{
                            "id": "OBSERVE|ORIENT|DECIDE|ACT",
                            "description": "What this reasoning step will do"
                        }}
                    ]
                }}
            ]
        }}
        
        Rules for the JSON:
        1. Plan node IDs must be:
           - In UPPERCASE
           - Single word or multiple words joined by underscores
           - Descriptive of the node's task
           - Examples: ANALYZE, CREATE_REPORT, PROCESS_DATA, GENERATE_SUMMARY
           - Use PREVIOUS_RESULTS when reusing existing results
        2. The requires_sub_plan property must be a boolean:
           - If true: The node will be broken down into sub-plans later
           - If false: The node must have reasoning_nodes
        3. For nodes with requires_sub_plan=false:
           - Must include reasoning_nodes array
           - Each reasoning_node.id must be one of: OBSERVE, ORIENT, DECIDE, ACT
           - Include ONLY the reasoning steps that are necessary and sufficient
           - Do not include steps just because they're available
        4. For nodes with requires_sub_plan=true:
           - Must NOT include reasoning_nodes
           - Will be broken down into sub-plans during execution
        5. All fields are required
        6. No additional fields are allowed
        7. The JSON must be properly formatted with no trailing commas
        
        Consider the node hierarchy when deciding whether to:
        1. Break down a task into sub-plans (prefer not to)
        2. Choose which reasoning steps are necessary (be selective!)
        3. Structure the overall plan (keep it simple!)
        4. Ensure each node builds upon previous results without duplication
        5. Reuse previous results when available and valid
        """
        
        # Use LLM to determine the structure
        if context and context.reasoning_llm:
            response = await context.reasoning_llm.query({
                "prompt": plan_structure_prompt,
                "system_prompt": (
                    "You are determining the optimal plan structure for a workflow node. "
                    "You must respond with a valid JSON object in the exact format specified."
                ),
                "parameters": {
                    "temperature": 0.3,
                    "max_tokens": 1000
                }
            })
            
            if response and "content" in response:
                try:
                    # Clean the response to ensure it's valid JSON
                    content = response["content"].strip()
                    
                    # Find the first { and last } to extract just the JSON object
                    start = content.find('{')
                    end = content.rfind('}') + 1
                    if start >= 0 and end > start:
                        content = content[start:end]
                    
                    # Parse the JSON structure
                    structure = json.loads(content)
                    
                    # Validate the structure
                    if not isinstance(structure, dict):
                        raise ValueError("Response must be a JSON object")
                    
                    if "justification" not in structure or "plan_nodes" not in structure:
                        raise ValueError("Response must contain 'justification' and 'plan_nodes'")
                    
                    if not isinstance(structure["plan_nodes"], list):
                        raise ValueError("'plan_nodes' must be a list")
                    
                    # Convert the structure into our plan graph format
                    plan_graph = {}
                    for plan_node in structure["plan_nodes"]:
                        if not all(k in plan_node for k in ["id", "description", "requires_sub_plan"]):
                            raise ValueError(
                                "Each plan node must have 'id', 'description', and 'requires_sub_plan'"
                            )
                        
                        plan_id = plan_node["id"]
                        if not plan_id.isupper():
                            raise ValueError(f"Plan node ID must be in UPPERCASE: {plan_id}")
                        
                        if not all(word.isalnum() for word in plan_id.split('_')):
                            raise ValueError(
                                "Plan node ID must contain only alphanumeric characters and underscores: "
                                f"{plan_id}"
                            )
                        
                        if len(plan_id.split('_')) > 5:  # Limit to 5 words for readability
                            raise ValueError(f"Plan node ID should not exceed 5 words: {plan_id}")
                        
                        requires_sub_plan = plan_node["requires_sub_plan"]
                        if not isinstance(requires_sub_plan, bool):
                            raise ValueError("requires_sub_plan must be a boolean")
                        
                        if requires_sub_plan:
                            if "reasoning_nodes" in plan_node:
                                raise ValueError(
                                    "Nodes with requires_sub_plan=true must not have reasoning_nodes"
                                )
                        else:
                            if "reasoning_nodes" not in plan_node:
                                raise ValueError(
                                    "Nodes with requires_sub_plan=false must have reasoning_nodes"
                                )
                            
                            reasoning_nodes = plan_node["reasoning_nodes"]
                            if not isinstance(reasoning_nodes, list):
                                raise ValueError("'reasoning_nodes' must be a list")
                            
                            # Validate reasoning nodes
                            valid_steps = {"OBSERVE", "ORIENT", "DECIDE", "ACT"}
                            for rnode in reasoning_nodes:
                                required_fields = ["id", "description"]
                                if not all(k in rnode for k in required_fields):
                                    raise ValueError(
                                        "Each reasoning node must have 'id' and 'description'"
                                    )
                                
                                if rnode["id"] not in valid_steps:
                                    raise ValueError(f"Invalid reasoning step: {rnode['id']}")
                        
                        plan_graph[plan_id] = {
                            'node': Node(
                                node_id=plan_id,
                                node_type=NodeType.TASK,
                                description=plan_node["description"],
                                metadata={
                                    'requires_sub_plan': requires_sub_plan,
                                    'justification': structure["justification"]
                                }
                            ),
                            'requires_sub_plan': requires_sub_plan
                        }
                        
                        if not requires_sub_plan:
                            plan_graph[plan_id]['reasoning_nodes'] = reasoning_nodes
                    
                    return plan_graph
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON in response: {e}")
                    logger.error(f"Response content: {response['content']}")
                    return None
                except ValueError as e:
                    logger.error(f"Invalid structure in response: {e}")
                    logger.error(f"Response content: {response['content']}")
                    return None
                except Exception as e:
                    logger.error(f"Unexpected error parsing plan structure: {e}")
                    logger.error(f"Response content: {response['content']}")
                    return None
        
        return None
    
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
        
        for plan_id, plan_data in plan_graph.items():
            plan_node = plan_data['node']
            requires_sub_plan = plan_data.get('requires_sub_plan', False)
            
            # Set current plan for results tracking
            self.results.set_current_plan(plan_id)
            
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
                # Execute reasoning nodes for this plan node
                reasoning_nodes = plan_data['reasoning_nodes']
                
                for reasoning_node in reasoning_nodes:
                    # Create result key for this step, prepending workflow node ID
                    workflow_node_id = parent_nodes[0].node_id
                    result_key = ResultKey(
                        node_id=f"{workflow_node_id}.{plan_id}",
                        step=reasoning_node['id']
                    )
                    
                    # Get previous results
                    previous_results = self.results.get_relevant_context(result_key)
                    
                    # Create prompt for this reasoning step
                    prompt = self._create_reasoning_prompt(
                        parent_nodes + [plan_node],  # full hierarchy including current plan
                        reasoning_node,
                        objective,
                        context,
                        previous_results
                    )
                    
                    # Execute the reasoning node
                    result = await self._call_llm(prompt, context)
                    
                    # Store result
                    self.results.store(result_key, result)
                
                # Get all results for this plan node
                plan_results[plan_id] = {
                    'reasoning': {
                        step: self.results.get_latest(f"{workflow_node_id}.{plan_id}", step)
                        for step in OODA_STEPS
                    }
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
        1. First, explicitly confirm your understanding of:
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