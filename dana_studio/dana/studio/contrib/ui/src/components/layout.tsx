/* eslint-disable react-hooks/exhaustive-deps */
/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useCallback, useState, useRef } from 'react';
import { useLocation, useParams, useNavigate } from 'react-router-dom';
import { SidebarProvider, SidebarInset, SidebarTrigger } from '@/components/ui/sidebar';
import { AppSidebar } from './app-sidebar';
import { ArrowLeft, ArrowUpRight, Play, Pause } from 'iconoir-react';
import { Settings } from 'iconoir-react';
import { useAgentStore } from '@/stores/agent-store';
import { useContributionStore } from '@/stores/contribution-store';
import { useCaptureKnowledgeStore } from '@/stores/capture-knowledge-store';
import { apiService } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { useDanaAnalytics } from '@/hooks/useAnalytics';
import VersionNotification from '@/components/version-notification';
import { useSessionTimer } from '@/hooks/useSessionTimer';
import { SESSION_STATUS } from '@/lib/constants';
import { toast } from 'sonner';

interface LayoutProps {
  children: React.ReactNode;
  hideLayout?: boolean; // Add this prop
}

export function Layout({ children, hideLayout = false }: LayoutProps) {
  const location = useLocation();
  const { agent_id } = useParams();
  const navigate = useNavigate();
  const { fetchAgent, selectedAgent } = useAgentStore();
  const { currentTemplate } = useContributionStore();
  const { 
    contributionTemplate, 
    currentSession, 
    updateSession, 
    updateSessionStatus 
  } = useCaptureKnowledgeStore();
  const [prebuiltAgent, setPrebuiltAgent] = useState<any>(null);
  const [knowledgePack, setKnowledgePack] = useState<any>(null);
  const [isSaving, setIsSaving] = useState(false);
  const { trackTabNavigation, trackError } = useDanaAnalytics();

  const isCaptureKnowledgePage = location.pathname.includes('/capture-knowledge');
  
  // Track last saved duration to prevent duplicate saves
  const lastSavedDurationRef = useRef<number>(0);
  const lastSessionIdRef = useRef<number | null>(null);
  
  // Initialize timer for capture-knowledge page
  // Use a memoized value to ensure timer hook gets updated when session loads
  const initialDuration = currentSession?.session_metadata?.duration_seconds || 0;
  const initialIsPaused = currentSession?.session_metadata?.timer_paused ?? undefined;
  const timer = useSessionTimer({
    initialDurationSeconds: initialDuration,
    autoStart: isCaptureKnowledgePage,
    initialIsPaused: initialIsPaused,
  });

  // Reset last saved duration and paused state when session ID changes
  useEffect(() => {
    if (currentSession?.id !== lastSessionIdRef.current) {
      lastSessionIdRef.current = currentSession?.id || null;
      const savedDuration = currentSession?.session_metadata?.duration_seconds || 0;
      const savedPaused = currentSession?.session_metadata?.timer_paused;
      lastSavedDurationRef.current = savedDuration;
      lastSavedPausedRef.current = savedPaused;
      if (isCaptureKnowledgePage && savedDuration > 0) {
        console.log('[Timer] Session loaded with saved duration:', savedDuration, 'seconds, paused:', savedPaused);
      }
    }
  }, [currentSession?.id, currentSession?.session_metadata?.duration_seconds, currentSession?.session_metadata?.timer_paused, isCaptureKnowledgePage]);

  // Track last saved paused state to prevent duplicate saves
  const lastSavedPausedRef = useRef<boolean | undefined>(undefined);

  // Save timer duration and paused state when paused
  useEffect(() => {
    if (
      isCaptureKnowledgePage &&
      timer.isPaused &&
      currentSession?.id &&
      timer.elapsedSeconds > 0 &&
      (timer.elapsedSeconds !== lastSavedDurationRef.current || timer.isPaused !== lastSavedPausedRef.current)
    ) {
      const saveTimerState = async () => {
        try {
          const durationToSave = timer.elapsedSeconds;
          console.log('[Timer] Saving timer duration on pause:', durationToSave, 'seconds, paused:', timer.isPaused);
          const updatedMetadata = {
            ...(currentSession.session_metadata || {}),
            duration_seconds: durationToSave,
            timer_paused: timer.isPaused,
          };
          await updateSession(currentSession.id, {
            session_metadata: updatedMetadata,
          }, { silent: true });
          // Update last saved values after successful save
          lastSavedDurationRef.current = durationToSave;
          lastSavedPausedRef.current = timer.isPaused;
          console.log('[Timer] Successfully saved duration:', durationToSave, 'seconds, paused:', timer.isPaused);
        } catch (error) {
          console.error('[Timer] Failed to save timer state:', error);
        }
      };
      saveTimerState();
    }
  }, [timer.isPaused, timer.elapsedSeconds, isCaptureKnowledgePage, currentSession?.id, updateSession]);

  // Save timer state when resumed (to clear paused state)
  useEffect(() => {
    if (
      isCaptureKnowledgePage &&
      !timer.isPaused &&
      currentSession?.id &&
      lastSavedPausedRef.current === true
    ) {
      const saveTimerState = async () => {
        try {
          const durationToSave = timer.elapsedSeconds;
          console.log('[Timer] Saving timer state on resume:', durationToSave, 'seconds, paused:', timer.isPaused);
          const updatedMetadata = {
            ...(currentSession.session_metadata || {}),
            duration_seconds: durationToSave,
            timer_paused: timer.isPaused,
          };
          await updateSession(currentSession.id, {
            session_metadata: updatedMetadata,
          }, { silent: true });
          // Update last saved paused state
          lastSavedPausedRef.current = timer.isPaused;
          console.log('[Timer] Successfully saved state on resume, paused:', timer.isPaused);
        } catch (error) {
          console.error('[Timer] Failed to save timer state on resume:', error);
        }
      };
      saveTimerState();
    }
  }, [timer.isPaused, timer.elapsedSeconds, isCaptureKnowledgePage, currentSession?.id, updateSession]);

  // Handle Save & Exit
  const handleSaveAndExit = async () => {
    if (!currentSession || isSaving) return;

    setIsSaving(true);
    try {
      // Save current timer duration
      const updatedMetadata = {
        ...(currentSession.session_metadata || {}),
        duration_seconds: timer.getDurationSeconds(),
      };
      
      // Update session with timer duration
      await updateSession(currentSession.id, {
        session_metadata: updatedMetadata,
      });

      // Mark as completed if not already completed
      if (currentSession.status !== SESSION_STATUS.COMPLETED) {
        await updateSessionStatus(currentSession.id, SESSION_STATUS.COMPLETED);
      }

      // Navigate to knowledge center
      navigate('/knowledge-center');
    } catch (error: any) {
      console.error('Failed to save and exit:', error);
      toast.error('Failed to save session', {
        description: error?.message || 'Please try again.',
      });
    } finally {
      setIsSaving(false);
    }
  };

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

  // Fetch knowledge pack when template is loaded for capture-template page
  useEffect(() => {
    const fetchKnowledgePack = async () => {
      if (currentTemplate?.kp_id && location.pathname.includes('/capture-template')) {
        try {
          const response = await apiService.getKnowledgePack(currentTemplate.kp_id);
          if (response.success && response.data) {
            setKnowledgePack(response.data);
          }
        } catch (error) {
          console.error('Error fetching knowledge pack:', error);
        }
      } else {
        setKnowledgePack(null);
      }
    };

    fetchKnowledgePack();
  }, [currentTemplate?.kp_id, location.pathname]);

  // Get page title based on current route - moved before early return
  const getPageTitle = useCallback(() => {
    switch (location.pathname) {
      case '/':
        return 'Home';
      case '/agents':
        return 'Dana Expert Agents';
      case '/knowledge-center':
        return 'Knowledge Center';
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
          return selectedAgent?.id === parseInt(agent_id || '0')
            ? selectedAgent?.name
            : 'Chat with agent';
        }
        if (location.pathname.startsWith('/agents/')) {
          return 'Agent Details';
        }
        if (location.pathname.startsWith('/capture-template/')) {
          // Return JSX for capture-template page to show knowledge pack link
          return (
            <div className="flex items-center gap-2">
              <span className="font-semibold">{currentTemplate?.name || 'Capture Template'}</span>
              {knowledgePack?.id && (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      onClick={() => {
                        window.open(`/knowledge-pack/${knowledgePack.id}`, '_blank');
                      }}
                      className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800 hover:bg-gray-200 transition-colors cursor-pointer"
                    >
                      <span>To Knowledge Pack</span>
                      <ArrowUpRight className="w-3 h-3" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>Open Knowledge Pack</p>
                  </TooltipContent>
                </Tooltip>
              )}
            </div>
          );
        }
        if (location.pathname.startsWith('/capture-knowledge/')) {
          // Return JSX for capture-knowledge page to apply different styling
          return (
            <div className="flex items-center gap-3">
              <span className="font-semibold">Capture knowledge</span>
              {contributionTemplate?.name && (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      onClick={() => {
                        if (contributionTemplate?.id) {
                          window.open(`/capture-template/${contributionTemplate.id}`, '_blank');
                        }
                      }}
                      className="inline-block px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800 max-w-60 overflow-hidden text-ellipsis whitespace-nowrap hover:bg-gray-200 transition-colors cursor-pointer"
                    >
                      {contributionTemplate.name}
                    </button>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>{contributionTemplate.name}</p>
                  </TooltipContent>
                </Tooltip>
              )}
              {/* Timer display */}
              {isCaptureKnowledgePage && (
                <div className="flex items-center gap-2 ml-2">
                  <span className="text-sm font-mono text-gray-600 dark:text-gray-400">
                    {timer.formattedTime}
                  </span>
                  <Button
                    onClick={timer.toggle}
                    variant="ghost"
                    size="sm"
                    className="h-7 px-3"
                    aria-label={timer.isPaused ? 'Continue session' : 'Pause session'}
                  >
                    {timer.isPaused ? 'Continue' : 'Pause'}
                  </Button>
                </div>
              )}
            </div>
          );
        }
        return 'Agent workspace';
    }
  }, [location.pathname, selectedAgent?.name, agent_id, prebuiltAgent?.name, currentTemplate?.name, contributionTemplate?.name, knowledgePack, isCaptureKnowledgePage, timer.formattedTime, timer.isPaused]);

  const isChatPage = location.pathname.includes('/chat');
  const isContributionTemplatePage = location.pathname.includes('/capture-template');

  if (hideLayout) {
    return <>{children}</>;
  }

  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset className={isCaptureKnowledgePage ? 'h-screen overflow-hidden' : ''}>
        <header className="flex gap-2 items-center px-4 h-16 border-b shrink-0">
          <SidebarTrigger className="-ml-1 text-gray-500 size-6" />
          <div className="flex gap-2 justify-between items-center w-full">
            <div className="flex gap-2 items-center">
              {(isChatPage || isContributionTemplatePage || isCaptureKnowledgePage) && (
                <button
                  onClick={() => {
                    if (isContributionTemplatePage || isCaptureKnowledgePage) {
                      trackTabNavigation(isContributionTemplatePage ? 'back_to_knowledge_center' : 'back_to_knowledge_center_from_capture', 'main_page');
                      navigate('/knowledge-center');
                    } else {
                      trackTabNavigation('back_to_agents', 'main_page');
                      navigate(-1);
                    }
                  }}
                  className="flex justify-center items-center w-8 h-8 rounded-lg transition-colors cursor-pointer hover:bg-gray-100"
                  aria-label={
                    isContributionTemplatePage 
                      ? "Back to Knowledge Center" 
                      : isCaptureKnowledgePage 
                        ? "Back to Knowledge Center" 
                        : "Back to agents"
                  }
                >
                  <ArrowLeft width={18} height={18} className="text-gray-500" />
                </button>
              )}
              <div className="font-semibold text-md">{getPageTitle()}</div>
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
            {isCaptureKnowledgePage && currentSession && currentSession.status !== SESSION_STATUS.COMPLETED && (
              <div className="flex gap-2 items-center">
                <Button
                  onClick={handleSaveAndExit}
                  variant="default"
                  className="hover:bg-green-700"
                  disabled={isSaving}
                  aria-label="Save & Exit"
                >
                  {isSaving ? 'Saving...' : 'Save & Exit'}
                </Button>
              </div>
            )}
          </div>
        </header>
        <main className={isCaptureKnowledgePage ? 'flex-1 min-h-0 overflow-hidden' : ''}>
          <VersionNotification />
          {children}
        </main>
      </SidebarInset>
    </SidebarProvider>
  );
}
