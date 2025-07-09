import { useForm } from "react-hook-form";
import type { AgentSteps, DanaAgentForm } from "@/types/agent";

const getRandomAvatar = () => {
  const avatarNumbers = Array.from({ length: 20 }, (_, i) => i + 1);
  const randomIndex = Math.floor(Math.random() * avatarNumbers.length);
  return `/agent-avatar-${avatarNumbers[randomIndex]}.svg`;
};

export function useDanaAgentForm() {
  const form = useForm<DanaAgentForm>({
    defaultValues: {
      name: "",
      description: "",
      avatar: getRandomAvatar(),
      general_agent_config: {
        dana_code: "",
      },
      step: "general" as AgentSteps,
    },
  });

  const onCreateAgent = () => {
    const values = form.getValues();
    console.log("Creating agent:", values);
    // TODO: Implement actual agent creation logic
  };

  return {
    form,
    onCreateAgent,
  };
}
