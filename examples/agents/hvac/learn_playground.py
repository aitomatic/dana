import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.normpath(os.path.dirname(__file__)))

from agent.hvac_agent import HVACAgent
from leaners.william_learner2 import WilliamLearner2

SESSION_ID = "hvac-agent-session-001"

# Get the current directory
current_dir = Path(__file__).parent

print("=" * 80)
print("HVAC Agent Episodic Learning Playground")
print("=" * 80)
print()

# Initialize the HVAC agent
print("🤖 Initializing HVACAgent...")
agent = HVACAgent(
    agent_id="hvac-agent-001",
    model="gpt-4.1",
)
agent.enable_notifications(verbose=False)
agent.set_session_id(SESSION_ID)

# Create learner
agent_learner = WilliamLearner2(agent=agent)
agent._learner = agent_learner

print()
print("📚 Loading Acquisitive Learning")
print("=" * 80)
acquisitive_learnings = agent_learner._load_acquisitive()
print(f"Loaded {len(acquisitive_learnings)} acquisitive learning entries")
if acquisitive_learnings:
    print("\nRecent acquisitive learnings:")
    for i, learning in enumerate(acquisitive_learnings[-3:], 1):
        print(f"{i}. {learning[:100]}...")
print()

print("=" * 80)
print("🔄 Running Episodic Learning")
print("=" * 80)
print()

# Run episodic learning - this analyzes the entire session timeline
trace_learning = agent_learner._reflect_episodic({})
learning_content = trace_learning.get("trace_learning", {}).get("simple_summary", "")
print("Episodic Learning Output:")
print(learning_content)
print()

print("=" * 80)
print("💾 Storing Episodic Learning")
print("=" * 80)
# Store episodic learning
agent_learner._store_episodic_learning(learning_content)
print("✅ Episodic learning stored")
print()

print("=" * 80)
print("📖 Loading Stored Episodic Learning")
print("=" * 80)
stored_learning = agent_learner._load_episodic()
if stored_learning:
    print(stored_learning)
else:
    print("No episodic learning found")
print()

print("=" * 80)
print("📊 Loading Feedback")
print("=" * 80)
feedback = agent_learner._load_feedback()
if feedback:
    print(f"Feedback loaded ({len(feedback)} characters)")
    print(feedback[:200] + "..." if len(feedback) > 200 else feedback)
else:
    print("No feedback found")
print()

print("=" * 80)
print("📝 Getting Timeline Entries")
print("=" * 80)
timeline_entries = agent_learner._get_timeline_entries(checkpoint=-10)
print(f"Found {len(timeline_entries)} timeline entries")
if timeline_entries:
    print("\nRecent timeline entries:")
    for i, entry in enumerate(timeline_entries[-5:], 1):
        entry_preview = entry.content[:80] + "..." if len(entry.content) > 80 else entry.content
        print(f"{i}. [{entry.entry_type.value}] {entry_preview}")
print()

print("=" * 80)
print("✅ Episodic Learning Playground Complete")
print("=" * 80)
