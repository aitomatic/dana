import { cn } from '@/lib/utils';
import { useLayoutEffect, useRef, useState } from 'react';
import BotMessage from './bot-message';
import UserMessage from './user-message';
import BotThinking from './bot-thinking';
import type { MessageRead } from '@/types/conversation';

interface ChatSessionProps {
  messages: MessageRead[];
  isBotThinking: boolean;
  botAvatar?: string;
  isMessageFeedback?: boolean;
  className?: string;
}

const ChatSession: React.FC<ChatSessionProps> = ({
  messages,
  isBotThinking,
  botAvatar,
  isMessageFeedback = false,
  className
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const listRef = useRef<HTMLDivElement>(null);
  const [isScrollEnable, setIsScrollEnable] = useState(false);

  useLayoutEffect(() => {
    if (containerRef?.current && listRef.current) {
      const { scrollHeight } = containerRef.current;
      const message_chilren = listRef.current.children;
      let totalHeight = 0;
      setTimeout(() => {
        for (let i = 0; i < message_chilren.length; i++) {
          totalHeight += Math.max(message_chilren.item(i)?.clientHeight ?? 0, 100);
        }

        if (scrollHeight - 20 < totalHeight) {
          setIsScrollEnable(true);
        } else {
          setIsScrollEnable(false);
        }

        setTimeout(() => {
          const bottomOfChat = document.getElementById('bottom-of-chat');
          if (bottomOfChat) {
            bottomOfChat.scrollIntoView({ behavior: 'smooth' });
          }
        }, 10);
      }, 50);

      return;
    }
    setIsScrollEnable(false);
    // return false;
  }, [containerRef, listRef, messages, isBotThinking]);

  return (
    <div className="flex overflow-scroll flex-col flex-1 w-full scrollbar-hide">
      <div className="flex overflow-scroll flex-col flex-1 scrollbar-hide">
        <div
          className={cn('flex overflow-y-scroll flex-col flex-1 max-h-full scrollbar-hide')}
          ref={containerRef}
        >
          <div
            className={cn(
              'flex overflow-y-scroll flex-col flex-1 pb-8 h-full scrollbar-hide chat-wrapper',
              isScrollEnable ? '' : 'justify-end',
            )}
            ref={listRef}
          >
            <div className="text-xs text-gray-500 p-2">
              Messages: {messages?.length || 0}
            </div>

            {messages?.map((message: MessageRead, index: number) => {
              console.log('Processing message:', message);

              // Convert API message format to component format
              const messageForComponent = {
                id: message.id,
                role: message.sender === 'agent' ? 'bot' : 'user',
                content: message.content,
                message: message.content,
                data: {
                  message: message.content,
                },
                timestamp: message.created_at,
                isNew: false,
              };

              console.log('Converted message:', messageForComponent);

              if (message.sender === 'agent') {
                return (
                  <BotMessage
                    key={index}
                    message={messageForComponent}
                    isMessageFeedback={isMessageFeedback}
                    avatar={botAvatar}
                    className={className}
                  />
                );
              } else {
                return <UserMessage key={index} message={messageForComponent} />;
              }
            })}
            {isBotThinking && <BotThinking avatar={botAvatar} />}
            <div id="bottom-of-chat" />
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatSession;
