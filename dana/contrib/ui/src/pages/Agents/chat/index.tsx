import { useCallback, useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import AgentChatView from "./chat-view";
import ConversationsSidebar from "./conversations-sidebar";
import { Tooltip, TooltipContent } from "@/components/ui/tooltip";
import { TooltipTrigger } from "@/components/ui/tooltip";
import { TooltipPortal } from "@radix-ui/react-tooltip";
import { ChatPlusIn, Tools } from "iconoir-react";
import { IconMenu2 } from "@tabler/icons-react";

const SIDEBAR_COLLAPSED_KEY = "agent-sidebar-collapsed";

const AgentChat = () => {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(() => {
    const savedState = localStorage.getItem(SIDEBAR_COLLAPSED_KEY);
    return savedState !== null ? JSON.parse(savedState) : true;
  });

  const toggleSidebar = useCallback(() => {
    setIsSidebarCollapsed((prev: boolean) => !prev);
  }, []);

  useEffect(() => {
    localStorage.setItem(
      SIDEBAR_COLLAPSED_KEY,
      JSON.stringify(isSidebarCollapsed),
    );
  }, [isSidebarCollapsed]);

  return (
    <div className="flex flex-1 w-full h-full overflow-hidden">
      <div className="flex w-full h-full">
        <div
          className={cn(
            "relative transition-all duration-300 ease-in-out z-31 shrink-0 overflow-x-hidden bg-background [view-transition-name:var(--sidebar-slideover)] max-md:w-0! scrollbar-hide",
            isSidebarCollapsed ? "w-0 opacity-0" : "w-[260px] opacity-100",
          )}
        >
          <div className="absolute inset-0 transition-none bg-background">
            <ConversationsSidebar
              setIsSidebarCollapsed={setIsSidebarCollapsed}
            />
          </div>
        </div>
        <div
          className={cn(
            "flex transition-all duration-300 ease-in-out",
            isSidebarCollapsed ? "w-full" : "w-[calc(100%-260px)]",
          )}
        >
          <div className="relative w-full">
            {isSidebarCollapsed && (
              <div
                className="absolute z-10 flex flex-col items-center text-gray-500 border border-gray-200 shadow-xs dark:border-gray-300 bg-background top-3 left-3 justify-evenly h-max rounded-xl w-fit"
                aria-label="Show sidebar"
              >
                <Tooltip>
                  <TooltipTrigger asChild>
                    <div
                      onClick={toggleSidebar}
                      className="flex items-center justify-center w-[40px] h-[40px] cursor-pointer"
                      role="button"
                      aria-label="Toggle sidebar"
                      data-testid="toggle-sidebar-button"
                    >
                      <IconMenu2 size={20} strokeWidth={2} />
                    </div>
                  </TooltipTrigger>
                  <TooltipPortal>
                    <TooltipContent side="right">History</TooltipContent>
                  </TooltipPortal>
                </Tooltip>

                <>
                  <div className="w-[70%] h-[1px] border-b border-gray-200 dark:border-gray-300" />
                  <Tooltip>
                    <TooltipTrigger>
                      <div
                        className="flex items-center justify-center w-[40px] h-[40px] cursor-pointer"
                        role="button"
                        aria-label="New chat"
                      >
                        <ChatPlusIn width={20} height={20} strokeWidth={2} />
                      </div>
                    </TooltipTrigger>
                    <TooltipContent side="right">New chat</TooltipContent>
                  </Tooltip>
                </>

                <>
                  <div className="w-[70%] h-[1px] border-b border-gray-200 dark:border-gray-300" />
                  <Tooltip>
                    <TooltipTrigger>
                      <div
                        className="flex items-center justify-center w-[40px] h-[40px] cursor-pointer"
                        role="button"
                        aria-label="Manage agent"
                        data-testid="manage-agent-button"
                      >
                        <Tools width={20} height={20} strokeWidth={2} />
                      </div>
                    </TooltipTrigger>
                    <TooltipContent side="right">Manage agent</TooltipContent>
                  </Tooltip>
                </>
              </div>
            )}
            <AgentChatView isSidebarCollapsed={isSidebarCollapsed} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default AgentChat;
