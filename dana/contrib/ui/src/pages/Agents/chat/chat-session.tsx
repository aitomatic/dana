import { cn } from '@/lib/utils';
import { useLayoutEffect, useRef, useState } from 'react';
import BotMessage from './bot-message';
import UserMessage from './user-message';
import BotThinking from './bot-thinking';

const ChatSession = ({ messages, isBotThinking, botAvatar, isMessageFeedback, className }: any) => {
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
            {messages?.map((message: any, index: number) => {
              if (['bot', 'ai-agent'].includes(message?.role)) {
                return (
                  <BotMessage
                    key={index}
                    message={message}
                    isMessageFeedback={isMessageFeedback}
                    avatar={botAvatar}
                    className={className}
                  />
                );
              } else {
                return <UserMessage key={index} message={message} />;
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
