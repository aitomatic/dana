"""Factory for creating planning patterns."""

from typing import Optional, cast, Dict, Any, List, Union
from pathlib import Path

from opendxa.base.execution.execution_types import Objective, ExecutionNode, NodeType
from opendxa.execution.planning.plan import Plan
from opendxa.base.execution.execution_factory import ExecutionFactory

class PlanFactory(ExecutionFactory[Plan]):
    """Creates planning pattern instances."""
    
    # Override class variables
    graph_class = Plan
    
    @classmethod
    def create_plan(
        cls, 
        objective: Objective, 
        name: Optional[str] = None
    ) -> Plan:
        """Create a plan instance."""
        return cast(Plan, cls.create_basic_graph(objective, name))
    
    @classmethod
    def create_plan_by_name(
        cls,
        name: str,
        objective: Union[str, Objective],
        role: Optional[str] = None,
        custom_prompts: Optional[Dict[str, str]] = None,
        config_dir: Optional[Union[str, Path]] = None
    ) -> Plan:
        """Create a plan from a named configuration."""
        return cast(Plan, cls.create_from_config(
            config_name=name,
            objective=objective,
            role=role,
            custom_prompts=custom_prompts,
            config_dir=config_dir
        ))
        
    @classmethod
    def create_default_plan(cls, objective: Union[str, Objective]) -> Plan:
        """Create a standard plan with default structure."""
        if not isinstance(objective, Objective):
            objective = Objective(objective)
            
        plan = cls.graph_class(objective=objective)
        
        # Add default nodes
        start_node = ExecutionNode(
            node_id="START",
            node_type=NodeType.START,
            objective="Start node"
        )
        plan.add_node(start_node)
        
        task_node = ExecutionNode(
            node_id="TASK",
            node_type=NodeType.TASK,
            objective="Execute task"
        )
        plan.add_node(task_node)
        
        end_node = ExecutionNode(
            node_id="END",
            node_type=NodeType.END,
            objective="End node"
        )
        plan.add_node(end_node)
        
        # Connect START → task → END
        plan.add_edge_between("START", task_node.node_id)
        plan.add_edge_between(task_node.node_id, "END")
        
        return cast(Plan, plan)
        
    @classmethod
    def create_basic_plan(
        cls,
        objective: Union[str, Objective],
        commands: List[str]
    ) -> Plan:
        """Create a plan with sequential tasks.
        
        Args:
            objective: Plan objective
            commands: List of task descriptions
            
        Returns:
            Plan: A plan with sequential tasks
        """
        # Create task nodes from commands
        nodes = [
            ExecutionNode(
                node_id=f"TASK_{i}",
                node_type=NodeType.TASK,
                objective=f"{command} in {objective.current if isinstance(objective, Objective) else objective}"
            )
            for i, command in enumerate(commands)
        ]
        
        # Use base class method to create sequential graph
        return cast(Plan, cls.create_sequential_graph(
            nodes=nodes,
            objective=objective
        ))
        
    @classmethod
    def _add_edges_to_graph(
        cls,
        plan: Plan,
        data: Dict[str, Any],
        node_ids: List[str]
    ) -> None:
        """Add edges to plan from YAML data.
        
        Args:
            plan: The plan to add edges to
            data: YAML data containing edge definitions
            node_ids: List of valid node IDs in the plan
        """
        if "edges" not in data:
            return
            
        for edge_data in data["edges"]:
            source = edge_data.get("source")
            target = edge_data.get("target")
            
            if not source or not target:
                continue
                
            if source not in node_ids or target not in node_ids:
                continue
                
            plan.add_edge_between(source, target)
            
    @classmethod
    def from_yaml(cls, data: Dict[str, Any], objective: Optional[Objective] = None) -> Plan:
        """Create a plan from YAML data."""
        if not objective and "objective" in data:
            objective = Objective(data["objective"])
        plan = cls.create_basic_graph(objective)

        # Store metadata
        predefined_keys = {"objective", "nodes", "edges"}
        for key, value in data.items():
            if key not in predefined_keys:
                plan.metadata[key] = value
        
        # Store prompts in metadata if present (kept for backward compatibility/clarity, though covered by above)
        # if "prompts" in data:  # This block is now redundant due to the loop above but kept for clarity if desired
        #    plan.metadata["prompts"] = data["prompts"]
            
        # Add nodes
        node_ids = []
        if "nodes" in data:
            for node_data in data["nodes"]:
                node_objective = node_data.get("objective", "")
                node_description = node_data.get("description", node_objective)
                node = ExecutionNode(
                    node_id=node_data["id"],
                    node_type=NodeType[node_data["type"].upper()],
                    objective=node_objective,
                    description=node_description
                )
                plan.add_node(node)
                node_ids.append(node.node_id)
                
        # Add edges
        cls._add_edges_to_graph(plan, data, node_ids)
        
        return cast(Plan, plan)