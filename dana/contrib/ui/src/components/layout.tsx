import * as React from 'react';
import { useLocation, useParams, useNavigate } from 'react-router-dom';
import { SidebarProvider, SidebarInset, SidebarTrigger } from '@/components/ui/sidebar';
import { AppSidebar } from './app-sidebar';
import { ArrowLeft } from 'iconoir-react';
import { useAgentStore } from '@/stores/agent-store';

interface LayoutProps {
  children: React.ReactNode;
  hideLayout?: boolean; // Add this prop
}

export function Layout({ children, hideLayout = false }: LayoutProps) {
  const location = useLocation();
  const { agent_id } = useParams();
  const navigate = useNavigate();
  const { fetchAgent, selectedAgent } = useAgentStore();

  // Fetch agent data when on chat pages
  React.useEffect(() => {
    if (agent_id && location.pathname.includes('/chat')) {
      fetchAgent(parseInt(agent_id)).catch(console.error);
    }
  }, [agent_id, location.pathname, fetchAgent]);

  // Get page title based on current route - moved before early return
  const getPageTitle = React.useCallback(() => {
    switch (location.pathname) {
      case '/':
        return 'Home';
      case '/agents':
        return 'Dana Expert Agents';
      case '/library':
        return 'Library';
      default:
        // Handle dynamic routes
        if (location.pathname.startsWith('/agents/') && location.pathname.includes('/chat')) {
          return selectedAgent?.name || 'Agent Chat';
        }
        if (location.pathname.startsWith('/agents/')) {
          return 'Agent Details';
        }
        return 'Agent workspace';
    }
  }, [location.pathname, selectedAgent?.name]);

  // Check if we're on a chat page
  const isChatPage = location.pathname.includes('/chat');

  // If hideLayout is true, render children without layout
  if (hideLayout) {
    return <>{children}</>;
  }

  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset>
        <header className="flex gap-2 items-center px-4 h-16 border-b shrink-0">
          <SidebarTrigger className="-ml-1 text-gray-500 size-6" />
          <div className="flex gap-2 items-center">
            {isChatPage && (
              <button
                onClick={() => navigate('/agents')}
                className="flex items-center justify-center w-8 h-8 rounded-lg hover:bg-gray-100 transition-colors"
                aria-label="Back to agents"
              >
                <ArrowLeft width={20} height={20} className="text-gray-500" />
              </button>
            )}
            <span className="text-md font-semibold">{getPageTitle()}</span>
          </div>
        </header>
        <main className="overflow-auto flex-1">{children}</main>
      </SidebarInset>
    </SidebarProvider>
  );
}
