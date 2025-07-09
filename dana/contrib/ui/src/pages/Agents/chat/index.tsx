import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import AgentChatView from "./chat-view";

const SIDEBAR_COLLAPSED_KEY = "agent-sidebar-collapsed";

const AgentConversations = () => {
  const [isSidebarCollapsed] = useState(() => {
    const savedState = localStorage.getItem(SIDEBAR_COLLAPSED_KEY);
    return savedState !== null ? JSON.parse(savedState) : true;
  });

  useEffect(() => {
    localStorage.setItem(SIDEBAR_COLLAPSED_KEY, JSON.stringify(isSidebarCollapsed));
  }, [isSidebarCollapsed]);

  return (
    <div className="flex flex-1 w-full h-full overflow-hidden">
      <div className="flex w-full h-full">
        <div
          className={cn(
            "relative transition-all duration-300 ease-in-out z-31 shrink-0 overflow-x-hidden bg-background [view-transition-name:var(--sidebar-slideover)] max-md:w-0! scrollbar-hide",
            isSidebarCollapsed ? "w-0 opacity-0" : "w-[260px] opacity-100"
          )}
        >
          <div className="absolute inset-0 transition-none bg-background">
            {/* <ConversationsSidebar setIsSidebarCollapsed={setIsSidebarCollapsed} /> */}
          </div>
        </div>
        <div
          className={cn(
            "flex transition-all duration-300 ease-in-out",
            isSidebarCollapsed ? "w-full" : "w-[calc(100%-260px)]"
          )}
        >
          <div className="relative w-full">
            {isSidebarCollapsed && (
              <div
                className="absolute z-10 flex flex-col items-center text-gray-500 border border-gray-200 shadow-xs dark:border-gray-300 bg-background top-3 left-3 justify-evenly h-max rounded-xl w-fit"
                aria-label="Show sidebar"
              ></div>
            )}
            <AgentChatView isSidebarCollapsed={isSidebarCollapsed} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default AgentConversations;
