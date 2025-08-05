import { useEffect, useCallback, useState } from 'react';
import { useLocation, useParams, useNavigate } from 'react-router-dom';
import { SidebarProvider, SidebarInset, SidebarTrigger } from '@/components/ui/sidebar';
import { AppSidebar } from './app-sidebar';
import { ArrowLeft } from 'iconoir-react';
import { Settings } from 'iconoir-react';
import { useAgentStore } from '@/stores/agent-store';
import { apiService } from '@/lib/api';
import { Button } from '@/components/ui/button';
// import { Button } from './ui/button';
// import { apiService } from '@/lib/api';

interface LayoutProps {
  children: React.ReactNode;
  hideLayout?: boolean; // Add this prop
}

export function Layout({ children, hideLayout = false }: LayoutProps) {
  const location = useLocation();
  const { agent_id } = useParams();
  const navigate = useNavigate();
  const { fetchAgent, selectedAgent } = useAgentStore();
  const [prebuiltAgent, setPrebuiltAgent] = useState<any>(null);

  // Fetch agent data when on chat pages
  useEffect(() => {
    if (agent_id && location.pathname.includes('/chat')) {
      // Only fetch agent details for numeric IDs (regular agents)
      // Prebuilt agents with string IDs will be handled differently
      if (!isNaN(Number(agent_id))) {
        fetchAgent(parseInt(agent_id)).catch(console.error);
      } else {
        // For prebuilt agents, fetch their information from the prebuilt agents API
        console.log('Prebuilt agent in chat:', agent_id);
        const fetchPrebuiltAgent = async () => {
          try {
            const prebuiltAgents = await apiService.getPrebuiltAgents();
            const agent = prebuiltAgents.find((a: any) => a.id === agent_id || a.key === agent_id);
            if (agent) {
              setPrebuiltAgent(agent);
            }
          } catch (error) {
            console.error('Error fetching prebuilt agent:', error);
          }
        };
        fetchPrebuiltAgent();
      }
    }
  }, [agent_id, location.pathname, fetchAgent]);

  // Get page title based on current route - moved before early return
  const getPageTitle = useCallback(() => {
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
          // Check if this is a prebuilt agent (string ID)
          if (agent_id && isNaN(Number(agent_id))) {
            return prebuiltAgent?.name || 'Chat with agent';
          }
          // Check if this is a regular agent (numeric ID)
          return selectedAgent?.id === parseInt(agent_id || '0')
            ? selectedAgent?.name
            : 'Chat with agent';
        }
        if (location.pathname.startsWith('/agents/')) {
          return 'Agent Details';
        }
        return 'Agent workspace';
    }
  }, [location.pathname, selectedAgent?.name, agent_id, prebuiltAgent?.name]);

  // Check if we're on a chat page
  const isChatPage = location.pathname.includes('/chat');

  // If hideLayout is true, render children without layout
  if (hideLayout) {
    return <>{children}</>;
  }

  console.log(selectedAgent, '-----------------selectedAgent');

  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset>
        <header className="flex gap-2 items-center px-4 h-16 border-b shrink-0">
          <SidebarTrigger className="-ml-1 text-gray-500 size-6" />
          <div className="flex gap-2 justify-between items-center w-full">
            <div className="flex gap-2 items-center">
              {isChatPage && (
                <button
                  onClick={() => navigate('/agents')}
                  className="flex justify-center items-center w-8 h-8 rounded-lg transition-colors hover:bg-gray-100 cursor-pointer"
                  aria-label="Back to agents"
                >
                  <ArrowLeft width={18} height={18} className="text-gray-500" />
                </button>
              )}
              <span className="font-semibold text-md">{getPageTitle()}</span>
            </div>
            {isChatPage && agent_id && isNaN(Number(agent_id)) && prebuiltAgent && (
              <div>
                <Button
                  onClick={async () => {
                    try {
                      const newAgent = await apiService.cloneAgentFromPrebuilt(prebuiltAgent.key);
                      if (newAgent && newAgent.id) {
                        navigate(`/agents/${newAgent.id}`);
                      }
                    } catch (err) {
                      // Optionally show error toast
                      console.error(err);
                    }
                  }}
                  className="font-semibold"
                  variant="outline"
                >
                  <Settings style={{ width: '16', height: '16' }} />
                  Customize
                </Button>
              </div>
            )}
          </div>
        </header>
        <main className="overflow-auto flex-1">{children}</main>
      </SidebarInset>
    </SidebarProvider>
  );
}
