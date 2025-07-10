import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { useAgentStore } from '@/stores/agent-store';
import type { AgentSteps, DanaAgentForm, AgentCreate } from '@/types/agent';

const getRandomAvatar = () => {
  const avatarNumbers = Array.from({ length: 20 }, (_, i) => i + 1);
  const randomIndex = Math.floor(Math.random() * avatarNumbers.length);
  return `/agent-avatar-${avatarNumbers[randomIndex]}.svg`;
};

export function useDanaAgentForm() {
  const navigate = useNavigate();
  const { createAgent, isCreating, error } = useAgentStore();

  const form = useForm<DanaAgentForm>({
    defaultValues: {
      name: '',
      description: '',
      avatar: getRandomAvatar(),
      general_agent_config: {
        dana_code: 'query = \"Hi\"\n\nresponse = reason(f\"Help me to answer the question: {query}\")',
      },
      selectedKnowledge: {
        topics: [],
        documents: [],
      },
      step: 'general' as AgentSteps,
    },
  });

  const onCreateAgent = async () => {
    try {
      const values = form.getValues();

      // Validate required fields
      if (!values.name.trim()) {
        toast.error('Agent name is required');
        return;
      }

      if (!values.general_agent_config.dana_code.trim()) {
        toast.error('Agent configuration (DANA code) is required');
        return;
      }

      if (values.step === 'general') {
        form.setValue('step', 'select-knowledge');
        return;
      }

      // Transform form data to API format
      const agentData: AgentCreate = {
        name: values.name.trim(),
        description: values.description?.trim() || '',
        config: {
          avatar: values.avatar,
          dana_code: values.general_agent_config.dana_code,
          selectedKnowledge: values.selectedKnowledge,
        },
      };

      // Create the agent
      const newAgent = await createAgent(agentData);

      // Show success message
      toast.success(`Agent "${newAgent.name}" created successfully!`);

      // Navigate to agents list
      navigate('/agents');
    } catch (error) {
      // Error handling is done by the store, but we can add additional UI feedback
      const errorMessage = error instanceof Error ? error.message : 'Failed to create agent';
      toast.error(errorMessage);
      console.error('Agent creation failed:', error);
    }
  };

  return {
    form,
    onCreateAgent,
    isCreating,
    error,
  };
}
