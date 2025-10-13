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
  const avatarSrc = avatar || (agent_id ? getAgentAvatarSync(agent_id) : getAgentAvatarSync(0));

  return (
    <div className="grid grid-cols-[max-content_1fr] items-start w-full gap-2 px-6 py-4">
      <div className="flex overflow-hidden justify-center items-center w-8 h-8 rounded-full">
        <img
          className="object-cover w-full h-full"
          src={avatarSrc}
          alt="Agent avatar"
          onError={(e) => {
            // Fallback to colored circle if image fails to load
            const target = e.target as HTMLImageElement;
            target.style.display = 'none';
            const parent = target.parentElement;
            if (parent) {
              parent.className = `flex justify-center items-center w-8 h-8 text-sm font-bold text-white bg-gradient-to-br from-pink-400 to-purple-400 rounded-full`;
              parent.innerHTML = `<span className="text-white">A</span>`;
            }
          }}
        />
      </div>
      <div className="flex gap-2">
        <div className="flex justify-center items-start">
          <IconLoader className="mt-0.5 animate-spin text-brand-700" size={20} />
        </div>
        <div className="flex flex-col">
          <span className="text-sm font-normal text-gray-900 break-words xl:text-base animate-flash">
            {message ?? thinkingMessage ?? 'Thinking...'}
          </span>
          {currentStep && <span className="mt-1 text-xs italic text-gray-600">{currentStep}</span>}
        </div>
      </div>
    </div>
  );
};

export default BotThinking;
