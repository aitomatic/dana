import { IconLoader } from '@tabler/icons-react';

const BotThinking = ({ message, avatar, currentStep }: { message?: string; avatar?: string; currentStep?: string }) => {
  const currentAgent = {
    avatar: '1',
  };
  const thinkingMessage = 'Thinking...';

  return (
    <div className="grid grid-cols-[max-content_1fr] items-start w-full gap-2 px-6 py-4">
      <img
        className="w-8 h-8"
        src={
          avatar ||
          (currentAgent?.avatar !== '1'
            ? `/assets${currentAgent?.avatar ?? '/agent-avatar.svg'}`
            : '/assets/aito-circle-logo.svg')
        }
        alt="/assets/aito-circle-logo.svg"
      />
      <div className="flex gap-2">
        <div className="flex items-start justify-center">
          <IconLoader className="mt-0.5 animate-spin text-brand-700" size={20} />
        </div>
        <div className="flex flex-col">
          <span className="text-sm font-normal text-gray-900 break-words xl:text-base animate-flash">
            {message ?? thinkingMessage ?? 'Thinking...'}
          </span>
          {currentStep && (
            <span className="text-xs text-gray-600 mt-1 italic">
              {currentStep}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

export default BotThinking;
