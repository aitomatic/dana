from dana.core.agent.builtin_agents.dana_coding_agent import DanaCodingAgent

agent = DanaCodingAgent(
    agent_id="dana-coding-agent",
    agent_type="dana_coding_agent",
    llm_provider="anthropic_like",
    model="kimi-k2-thinking-turbo",
)

agent.set_session_id("assistant_messages_being_skip")

saved_timeline = agent._timeline.read_since(0)

agent._timeline.timeline = list(saved_timeline)

print(agent._timeline.timeline)

print(agent._timeline.to_llm_messages())