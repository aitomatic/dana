"""
HVACAgent - HVAC control agent wired to CSXML prompt.

This agent mirrors the structure of the financial-analysis agents:
- Subclasses STARAgent
- Wires a prompt XML via prompt_path
- Provides a simple Notifiable handler and a helper to toggle verbosity
"""

import os
from datetime import datetime

from dana.core.agent.star_agent import STARAgent
from dana.common.protocols import Notifiable, DictParams
import sys
sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(__file__), "..")))
from leaners.william_learner import WilliamLearner
from environment.hvac_api import get_feedback, get_env_status
import json


class BroadcastNotificationHandler(Notifiable):
    """Notification handler that prints all broadcast messages."""

    def __init__(self, agent_name: str = "HVACAgent", verbose: bool = True):
        self.agent_name = agent_name
        self.verbose = verbose
        self.message_count = 0

    def notify(self, notifier: object, message: DictParams) -> None:
        self.message_count += 1
        if not self.verbose:
            return

        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        notifier_id = getattr(notifier, "object_id", "unknown")
        notifier_type = getattr(
            notifier, "agent_type", getattr(notifier, "__class__".__name__, "unknown")
        )

        print(f"\n{'=' * 80}")
        print(f"🔔 NOTIFICATION #{self.message_count} [{timestamp}]")
        print(f"📡 From: {notifier_type} (ID: {notifier_id})")
        print(f"🎯 To: {self.agent_name}")
        print(f"{'=' * 80}")
        for key, value in message.items():
            if key.startswith("trace_"):
                phase = key.replace("trace_", "").upper()
                print(f"\n📋 {phase} PHASE:")
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        if sub_value:
                            print(f"   {sub_key}: {sub_value}")
                else:
                    print(f"   {value}")
            else:
                print(f"\n📝 {key.upper()}:")
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        if sub_value:
                            print(f"   {sub_key}: {sub_value}")
                else:
                    print(f"   {value}")
        print(f"{'=' * 80}\n")


class HVACAgent(STARAgent):
    """
    Agent specialized in generating HVAC control plans based on environment context.

    The agent uses a CSXML prompt (`prompts/HVACAgent.xml`) to guide outputs.
    """

    def __init__(
        self,
        agent_id: str | None = None,
        llm_provider: str = "openai",
        model: str = "gpt-4.1",
        **kwargs,
    ):
        prompt_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "prompts",
            "HVACAgent.xml",
        )
        prompt_path = os.path.normpath(prompt_path)

        super().__init__(
            agent_type="hvac-agent",
            agent_id=agent_id or "hvac-agent-001",
            llm_provider=llm_provider,
            model=model,
            prompt_path=prompt_path,
            **kwargs,
        )

        self.notification_handler = BroadcastNotificationHandler("HVACAgent")
        self.with_notifiable(self.notification_handler)

    def enable_notifications(self, verbose: bool = True) -> None:
        self.notification_handler.verbose = verbose

    def get_notification_count(self) -> int:
        return getattr(self.notification_handler, "message_count", 0)


if __name__ == "__main__":
    print("=" * 80)
    print("HVACAgent Demo")
    print("=" * 80)
    print()
    print(get_env_status())
    env_status = {
  "room_name": "Conference Room A",
  "current_time": "13:26",
  "indoor_temp": 93.3,
  "outdoor_temp": 92.4,
  "meeting_plan": [
    {
      "start_time": "15:37",
      "end_time": "17:27"
    },
    {
      "start_time": "18:22",
      "end_time": "18:52"
    },
    {
      "start_time": "21:45",
      "end_time": "22:00"
    }
  ]
}

    agent = HVACAgent()
    agent.enable_notifications(verbose=False)
    learner = WilliamLearner(agent=agent)

    agent_prompt = f"""
        CURRENT ENVIRONMENT:
        {json.dumps(env_status, indent=2)}
    """
    result = agent.query(caller_message=agent_prompt)
    plan = json.loads(result["response"])
    print(plan)
    feedback = get_feedback(
        current_indoor_temp=env_status["indoor_temp"],
        outdoor_temp=env_status["outdoor_temp"],
        current_time=env_status["current_time"],
        plan=plan["plan"],  
        target_temps=plan["target_temps"],
        mode=plan["mode"],
        meeting_plan=env_status["meeting_plan"]
    )
    
    learner.save_feedback(json.dumps(feedback, indent=2))