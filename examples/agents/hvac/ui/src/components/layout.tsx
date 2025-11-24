/* eslint-disable react-hooks/exhaustive-deps */
/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useCallback, useState } from 'react';
import { useLocation, useParams, useNavigate } from 'react-router-dom';
import { SidebarProvider, SidebarInset, SidebarTrigger } from '@/components/ui/sidebar';
import { AppSidebar } from './app-sidebar';
import { ArrowLeft } from 'iconoir-react';
import { Settings } from 'iconoir-react';
import { useAgentStore } from '@/stores/agent-store';
import { apiService } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { useDanaAnalytics } from '@/hooks/useAnalytics';
import VersionNotification from '@/components/version-notification';

interface LayoutProps {
  children: React.ReactNode;
  hideLayout?: boolean; // Add this prop
}

export function Layout({ children, hideLayout = false }: LayoutProps) {
  const location = useLocation();
  const { agent_id } = useParams();
  const navigate = useNavigate();
  const agentStore = useAgentStore();
  const fetchAgent = agentStore.fetchAgent || (async () => {});
  const selectedAgent = agentStore.selectedAgent;
  const [prebuiltAgent, setPrebuiltAgent] = useState<any>(null);
  const { trackTabNavigation, trackError } = useDanaAnalytics();

  // Fetch agent data when on chat pages
  useEffect(() => {
    if (agent_id && location.pathname.includes('/chat')) {
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
      case '/documentation':
        return 'Documentation';
      case '/support':
        return 'Support';
      default:
        // Handle dynamic routes
        if (location.pathname.startsWith('/agents/') && location.pathname.includes('/chat')) {
          // Check if this is a prebuilt agent (string ID)
          if (agent_id && isNaN(Number(agent_id))) {
            return prebuiltAgent?.name || 'Chat with agent';
          }
          // Check if this is a regular agent (numeric ID)
          const selectedAgentValue = selectedAgent as { id?: number; name?: string } | null;
          return selectedAgentValue?.id === parseInt(agent_id || '0')
            ? selectedAgentValue?.name
            : 'Chat with agent';
        }
        if (location.pathname.startsWith('/agents/')) {
          return 'Agent Details';
        }
        return 'Agent workspace';
    }
  }, [
    location.pathname,
    (selectedAgent as { name?: string } | null)?.name,
    agent_id,
    prebuiltAgent?.name,
  ]);

  const isChatPage = location.pathname.includes('/chat');

  if (hideLayout) {
    return <>{children}</>;
  }

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
                  onClick={() => {
                    trackTabNavigation('back_to_agents', 'main_page');
                    navigate(-1);
                  }}
                  className="flex justify-center items-center w-8 h-8 rounded-lg transition-colors cursor-pointer hover:bg-gray-100"
                  aria-label="Back to agents"
                >
                  <ArrowLeft width={18} height={18} className="text-gray-500" />
                </button>
              )}
              <span className="font-semibold text-md">{getPageTitle()}</span>
            </div>
            {isChatPage && agent_id && (
              <div className="flex gap-2 items-center">
                <Button
                  onClick={() => {
                    trackTabNavigation('train_mode', 'main_page');
                    navigate(`/agents/${agent_id}`);
                  }}
                  variant="secondary"
                  aria-label="Train mode"
                >
                  <Settings style={{ width: '16', height: '16' }} />
                  Train mode
                </Button>
              </div>
            )}
            {isChatPage && agent_id && isNaN(Number(agent_id)) && prebuiltAgent && (
              <div>
                <Button
                  onClick={async () => {
                    try {
                      trackTabNavigation('customize_prebuilt_agent', 'main_page');
                      const newAgent = await apiService.cloneAgentFromPrebuilt(prebuiltAgent.key);
                      if (newAgent && newAgent.id) {
                        navigate(`/agents/${newAgent.id}`);
                      }
                    } catch (err) {
                      // Optionally show error toast
                      console.error(err);
                      trackError(
                        'prebuilt_agent_clone_failed',
                        (err as Error).message,
                        prebuiltAgent.key,
                      );
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
        <main>
          <VersionNotification />
          {children}
        </main>
      </SidebarInset>
    </SidebarProvider>
  );
}
