import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { useAgentStore } from '@/stores/agent-store';
import type { AgentSteps, DanaAgentForm } from '@/types/agent';
import { DEFAULT_DANA_AGENT_CODE } from '@/constants/dana-code';

const getRandomAvatar = () => {
  const avatarNumbers = Array.from({ length: 20 }, (_, i) => i + 1);
  const randomIndex = Math.floor(Math.random() * avatarNumbers.length);
  return `/agent-avatar-${avatarNumbers[randomIndex]}.svg`;
};

export function useDanaAgentForm() {
  const navigate = useNavigate();
  const { deployAgent, isCreating, error } = useAgentStore();

  const form = useForm<DanaAgentForm>({
    defaultValues: {
      name: '',
      description: '',
      avatar: getRandomAvatar(),
      general_agent_config: {
        dana_code: DEFAULT_DANA_AGENT_CODE,
      },
      selectedKnowledge: {
        topics: [],
        documents: [],
      },
      step: 'general' as AgentSteps,
    },
  });

  const onCreateAgent = async (multiFileProject?: any) => {
    try {
      const values = form.getValues();

      // Validate required fields
      if (!values.name.trim()) {
        toast.error('Agent name is required');
        return;
      }

      if (!values.general_agent_config.dana_code.trim() && !multiFileProject) {
        toast.error('Agent configuration (DANA code) is required');
        return;
      }

      if (values.step === 'general') {
        form.setValue('step', 'select-knowledge');
        return;
      }

      // Prepare deployment request
      const deployRequest = {
        name: values.name.trim(),
        description: values.description?.trim() || '',
        config: {
          avatar: values.avatar,
          selectedKnowledge: values.selectedKnowledge,
        },
        // Include either single file code or multi-file project
        ...(multiFileProject 
          ? { multi_file_project: multiFileProject }
          : { dana_code: values.general_agent_config.dana_code }
        )
      };

      // Deploy the agent with .na file storage
      const newAgent = await deployAgent(deployRequest);

      // Show success message with file storage info
      const deploymentType = multiFileProject ? 'multi-file' : 'single-file';
      toast.success(`Agent "${newAgent.name}" deployed successfully as ${deploymentType} project!`);

      // Navigate to agents list
      navigate('/agents');
    } catch (error) {
      // Error handling is done by the store, but we can add additional UI feedback
      const errorMessage = error instanceof Error ? error.message : 'Failed to deploy agent';
      toast.error(errorMessage);
      console.error('Agent deployment failed:', error);
    }
  };

  return {
    form,
    onCreateAgent,
    isCreating,
    error,
  };
}
