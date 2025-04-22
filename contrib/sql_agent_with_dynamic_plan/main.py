# from contrib.sql_agent_with_dynamic_plan.customized_agent_runtime import CustomizedAgentRuntime
from opendxa.execution.planning import PlanFactory
from opendxa.agent import Agent
from contrib.sql_agent_with_dynamic_plan.agent.resource.dummy_rag_resource import DummyRAGResource
from contrib.sql_agent_with_dynamic_plan.execution.customized_agent_runtime import CustomizedAgentRuntime
from opendxa.base.resource import LLMResource

question = "What percentage of monthly platform active users are transport users?"

agent = Agent()
plan_graph = PlanFactory.create_plan_by_name("sql_dynamic_plan", objective=question, config_dir="contrib/sql_agent_with_dynamic_plan/execution/planning/yaml")
"""
NOTE : 
Problem statement : I want to use a customized Executor but the only way I can add it is by using ExecutorFactory.

Explanation : 
- AgentRuntime is initialized inside the Agent class
- AgentRuntime is initialized with PlanExecutor and ReasoningExecutor
- If we want to use a customized Executor, we need a method to pass it to AgentRuntime
OR
- We create a new method to add customized AgentRuntime
"""


agent._runtime = CustomizedAgentRuntime(agent) # I'm using the 2nd approach and fake that we have a method to add customized AgentRuntime

result = agent.with_resources(
    {"rag" : DummyRAGResource(name="rag", description="Resource to get all available tables' schemas")}
)\
    .run(plan_graph)
print(result.content['choices'][0].message.content)