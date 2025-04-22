"""
This is a test script for the SQL Agent with Dynamic Plan.
"""
from pathlib import Path
from opendxa.execution.planning import PlanFactory
from opendxa.agent import Agent
from opendxa.contrib.sql_agent_with_dynamic_plan.agent.resource.sample_schema_resource import SampleSchemaResource
from opendxa.contrib.sql_agent_with_dynamic_plan.execution.planning.dynamic_plan_executor import DynamicPlanExecutor

question = "What percentage of monthly platform active users are transport users?"

agent = Agent() \
    .with_planning(planner=DynamicPlanExecutor()) \
    .with_resources({
        "sample_schema": SampleSchemaResource(name="sample_schema", description="Resource to get all available table schemas")
    })

config_dir = Path(__file__).parent / "execution/planning/yaml"

plan_graph = PlanFactory.create_plan_by_name(
    "sql_dynamic_plan",
    objective=question,
    config_dir=config_dir
)

result = agent.run(plan_graph)
print(result.content['choices'][0].message.content)