"""
This is a simple example of how to use the code agent.
"""

from pathlib import Path

from dana.common.utils.logging import DANA_LOGGER
from dana.contrib.code_agent.code_resource import CodeResource
from dana.contrib.sql_agent_with_dynamic_plan.execution.planning.dynamic_plan_executor import (
    DynamicPlanExecutor,
)
from dana.frameworks.agent import Agent

DANA_LOGGER.setLevel(DANA_LOGGER.DEBUG)

# load_dotenv()  # no longer needed; done by the framework

question = "I need a function to manually bubble sort the following list of numbers:\
    [3, 2, 1, 4, 5, 6, 7, 0, -8, -12]."

agent = Agent().with_planning(planner=DynamicPlanExecutor()).with_resources({"code_resource": CodeResource()})

config_dir = Path(__file__).parent

# TODO: Replace PlanFactory with Dana equivalent
# plan_graph = PlanFactory.create_plan_by_name("code_planning", objective=question, config_dir=config_dir)

# result = agent.run(plan_graph)
# print(result)
print("Code agent example temporarily disabled pending PlanFactory replacement")
