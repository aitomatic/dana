import { useEffect, useMemo, useState } from 'react';
import { HybridRenderer } from './hybrid-renderer';
import { IconLoader } from '@tabler/icons-react';
import { cn } from '@/lib/utils';
// Option click handling is now done directly in HTMLRenderer
import { ArrowLeft, Hourglass } from 'iconoir-react';
import { getAgentAvatarSync } from '@/utils/avatar';
import { useParams } from 'react-router-dom';

// Helper functions to extract message content and sources
const extractMessageContent = (message: any) => {
  if (Array.isArray(message?.data?.message)) {
    return message?.data?.message?.[1];
  }
  if (message?.content) {
    return message.content;
  }
  if (message?.message) {
    return message.message;
  }
  if (message?.message?.response) {
    return message.message.response;
  }
  if (message?.data?.message?.response) {
    return message.data.message.response;
  }
  if (message?.data?.message?.content) {
    return message.data.message.content;
  }
  if (message?.data?.message?.message?.content) {
    return message.data.message.message.content;
  }
  if (message?.meta_data?.solution) {
    return message.meta_data.solution;
  }
  return message?.data?.message || '';
};

const extractMessageSources = (message: any) => {
  if (
    typeof message?.data?.citations === 'object' &&
    message?.data?.citations !== null &&
    !Array.isArray(message?.data?.citations) &&
    Object.keys(message?.data?.citations).length > 0
  ) {
    return Object.values(message.data.citations);
  }

  return [
    ...(message?.data?.citations || []),
    ...(message?.data?.meta_data?.citations || []),
    ...(message?.data?.meta_data?.result?.citations || []),
    ...(message?.data?.message?.message?.citations || []),
  ].filter(Boolean);
};

const BotMessage = ({
  message,
  className,
}: {
  message: any;
  isMessageFeedback: boolean;
  avatar?: string;
  className?: string;
}) => {
  const messages: any[] = [];
  const isSplitScreen = false;
  const thinkingMessage = 'Thinking...';
  const { agent_id } = useParams<{ agent_id: string }>();

  const [_, setIsFinished] = useState(false);
  const [isOldResponse, setIsOldResponse] = useState(false);

  const [displayText, setDisplayText] = useState('');

  // Option click handling is now done directly in HTMLRenderer
  // No local handler needed

  // Option click handling is now done directly in HTMLRenderer
  // No local handler needed

  const messageContent = extractMessageContent(message);
  const messageSources = extractMessageSources(message);

  // Typing animation effect
  useEffect(() => {
    if (message.type === 'welcome-message') {
      setDisplayText(messageContent);
      return;
    }

    if (!message.isNew) {
      setDisplayText(messageContent);
      setIsFinished(true);
      return;
    }

    // Animate typing for new messages
    let currentIndex = 0;
    setIsFinished(false);

    const intervalId = setInterval(() => {
      setDisplayText(messageContent.slice(0, currentIndex));
      currentIndex++;

      if (currentIndex > messageContent.length) {
        clearInterval(intervalId);
        setIsFinished(true);
        setDisplayText(messageContent);
      }
    }, 5);

    return () => clearInterval(intervalId);
  }, [messageContent, message]);

  // Avatar image source - use dynamic avatar based on agent ID
  const avatarSrc = agent_id ? getAgentAvatarSync(agent_id) : '/agent-avatar/agent-avatar-0.svg';

  const isLastMessage = useMemo(() => {
    if (!messages || messages.length === 0) return false;
    return messages[messages.length - 1].id === message.id;
  }, [messages, message.id]);

  const contributedMessage = message?.data?.meta_data?.added_knowledge?.answer;

  return (
    <div className="flex gap-2 items-start py-4 pl-6 w-full">
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

      <div
        className={cn(
          'flex flex-col w-full',
          isSplitScreen ? 'max-w-full 3xl:max-w-full' : 'max-w-[630px] 3xl:max-w-[1085px]',
          className,
        )}
      >
        {displayText ? (
          <div
            className={cn(
              'flex flex-col',
              message?.data?.meta_data?.type === 'dxa:prosea:user_input' &&
              isLastMessage &&
              'bg-blue-50 rounded-xl p-4 border border-blue-100',
            )}
          >
            {contributedMessage && (
              <div
                onClick={() => setIsOldResponse(!isOldResponse)}
                className="flex gap-2 items-center cursor-pointer"
              >
                <ArrowLeft
                  className={cn('w-3 h-3 text-gray-400 transition-transform duration-300', {
                    'rotate-180': isOldResponse,
                  })}
                  strokeWidth={3}
                />
                <span className="text-sm font-medium text-gray-400">
                  {isOldResponse ? 'New response' : 'Old response'}
                </span>
              </div>
            )}
            <HybridRenderer
              content={contributedMessage && !isOldResponse ? contributedMessage : displayText}
              backgroundContext="agent"
            />
            {message?.data?.meta_data?.type === 'dxa:prosea:user_input' && isLastMessage && (
              <div className="flex gap-1 items-center mt-2">
                <Hourglass className="w-5 h-5 text-brand-700" />
                <span className="font-medium text-brand-700 animate-flash">
                  Awaiting for your response
                </span>
              </div>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-[max-content_1fr] items-start gap-2">
            <IconLoader className="animate-spin text-brand-700" size={20} />
            <span className={`text-sm font-normal text-gray-900 xl:text-base animate-flash`}>
              {thinkingMessage ?? 'Thinking...'}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

export default BotMessage;
