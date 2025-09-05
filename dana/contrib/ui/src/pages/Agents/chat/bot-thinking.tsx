import { IconLoader } from '@tabler/icons-react';
import { useParams } from 'react-router-dom';
import { getAgentAvatarSync } from '@/utils/avatar';

const BotThinking = ({
  message,
  avatar,
  currentStep,
}: {
  message?: string;
  avatar?: string;
  currentStep?: string;
}) => {
  const thinkingMessage = 'Thinking...';
  const { agent_id } = useParams<{ agent_id: string }>();

  // Use dynamic avatar based on agent ID, fallback to provided avatar or default
  const avatarSrc =
    avatar || (agent_id ? getAgentAvatarSync(agent_id) : '/agent-avatar/agent-avatar-0.svg');

  return (
    <div className="grid grid-cols-[max-content_1fr] items-start w-full gap-2 px-6 py-4">
      <div className="w-8 h-8 rounded-full overflow-hidden flex items-center justify-center">
        <img
          className="w-full h-full object-cover"
          src={avatarSrc}
          alt="Agent avatar"
          onError={(e) => {
            // Fallback to colored circle if image fails to load
            const target = e.target as HTMLImageElement;
            target.style.display = 'none';
            const parent = target.parentElement;
            if (parent) {
              parent.className = `w-8 h-8 rounded-full bg-gradient-to-br from-pink-400 to-purple-400 flex items-center justify-center text-white text-sm font-bold`;
              parent.innerHTML = `<span className="text-white">A</span>`;
            }
          }}
        />
      </div>
      <div className="flex gap-2">
        <div className="flex items-start justify-center">
          <IconLoader className="mt-0.5 animate-spin text-brand-700" size={20} />
        </div>
        <div className="flex flex-col">
          <span className="text-sm font-normal text-gray-900 break-words xl:text-base animate-flash">
            {message ?? thinkingMessage ?? 'Thinking...'}
          </span>
          {currentStep && <span className="text-xs text-gray-600 mt-1 italic">{currentStep}</span>}
        </div>
      </div>
    </div>
  );
};

export default BotThinking;
