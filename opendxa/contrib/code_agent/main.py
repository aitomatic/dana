"""
This is a simple example of how to use the code agent.
"""
from pathlib import Path
from opendxa.agent import Agent
from opendxa.contrib.code_agent.code_resource import CodeResource
from opendxa.contrib.sql_agent_with_dynamic_plan.execution.planning.dynamic_plan_executor import (
    DynamicPlanExecutor,
)
from opendxa import PlanFactory, DXA_LOGGER

DXA_LOGGER.setLevel(DXA_LOGGER.DEBUG)

# load_dotenv()  # no longer needed; done by the framework

question = "I need a function to manually bubble sort the following list of numbers:\
    [3, 2, 1, 4, 5, 6, 7, 0, -8, -12]."

agent = (
    Agent()
    .with_planning(planner=DynamicPlanExecutor())
    .with_resources({"code_resource": CodeResource()})
)

config_dir = Path(__file__).parent

plan_graph = PlanFactory.create_plan_by_name(
    "code_planning", objective=question, config_dir=config_dir
)

result = agent.run(plan_graph)
print(result)
