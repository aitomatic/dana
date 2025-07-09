// React and React Router
import { useRef, useState } from "react";
import { useParams } from "react-router-dom";

// Components
import ChatSession from "./chat-session";
// import ChatBox from './chat-box';
import { cn } from "@/lib/utils";

import ChatBox from "./chat-box";

const AgentChatView = ({ isSidebarCollapsed }: { isSidebarCollapsed: boolean }) => {
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const { chat_id } = useParams();
  const [files] = useState<any[]>([]);

  const onSendMessage = (data: any) => {
    console.log(data);
  };

  const renderWelcomeContent = () => {
    const contentClassName = `
      flex flex-col items-center justify-center h-full gap-8
      transition-all duration-300 ease-in-out
      w-full
      opacity-100
    `;

    return (
      <div className="relative flex items-center w-full h-full fade-in">
        <div className={contentClassName}>
          <div className="flex flex-col items-center">
            <span className="text-[36px] font-medium text-gray-400">
              Hi, how can I help you today?
            </span>
            <span className="text-[36px] font-medium text-gray-700">How can I help you today?</span>
          </div>
          <div className={`flex flex-col gap-2 w-[700px] transition-all duration-300`}>
            <ChatBox
              files={files}
              isShowUpload={false}
              placeholder="Ask me anything"
              handleSendMessage={onSendMessage}
            />
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="flex w-full h-full">
      <div className="w-full overflow-y-auto scrollbar-hide h-[calc(100vh-64px)] fade-in">
        {chat_id ? (
          <div className="flex items-center justify-center w-full h-full">
            <div className="relative flex items-center justify-center w-full h-full">
              <div
                id="chat-container"
                className={cn("flex flex-col items-center justify-center w-full h-full", "w-full")}
              >
                <div
                  className={cn(
                    "relative flex flex-col justify-between h-full w-full",
                    isSidebarCollapsed ? "pl-10 pr-6" : "px-4",
                    "max-w-[760px] 3xl:max-w-[1200px]",
                    "opacity-100"
                  )}
                >
                  {/* Message container with fixed height and scroll */}
                  <div
                    ref={chatContainerRef}
                    className="items-center pt-2 pb-4 overflow-y-auto scrollbar-hide fade-in"
                  >
                    <ChatSession messages={[]} isBotThinking={false} />
                  </div>

                  {/* Fixed chat box at bottom */}
                  <div className="sticky w-full bg-background bottom-6">
                    <ChatBox
                      files={files}
                      isShowUpload={false}
                      placeholder="Ask me anything"
                      handleSendMessage={onSendMessage}
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className={cn("relative flex items-center w-full h-full fade-in")}>
            {renderWelcomeContent()}
          </div>
        )}
      </div>
    </div>
  );
};

export default AgentChatView;
