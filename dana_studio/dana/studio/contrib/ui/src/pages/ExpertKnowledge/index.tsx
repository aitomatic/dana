import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useCaptureKnowledgeStore } from '@/stores';
import { IconLoader2, IconCheck, IconDownload } from '@tabler/icons-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import { SESSION_STATUS } from '@/lib/constants';
import { ChatSidebar } from './chat-sidebar';
import { SummaryPanel } from './summary-panel';
import { apiService } from '@/lib/api';

export default function CaptureKnowledgePage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('summary');

  const {
    currentSession,
    isLoadingSession,
    sessionError,
    contributionTemplate,
    isLoadingTemplate,
    loadSession,
    reset,
    updateSessionStatus,
  } = useCaptureKnowledgeStore();

  useEffect(() => {
    if (sessionId) {
      loadSession(parseInt(sessionId, 10));
    }

    // Cleanup on unmount
    return () => {
      reset();
    };
  }, [sessionId, loadSession, reset]);

  const handleCompleteSession = async () => {
    if (!currentSession) return;
    
    try {
      await updateSessionStatus(currentSession.id, SESSION_STATUS.COMPLETED);
      toast.success('Session marked as completed!');
    } catch (error) {
      console.error('Failed to complete session:', error);
    }
  };

  const handleDownloadInterviewNote = async () => {
    if (!currentSession) return;
    
    try {
      const blob = await apiService.downloadInterviewNote(currentSession.id);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `interview_notes_session_${currentSession.id}.md`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      toast.success('Interview notes downloaded successfully!');
    } catch (error: any) {
      console.error('Failed to download interview notes:', error);
      toast.error('Failed to download interview notes', {
        description: error?.message || 'Please try again.',
      });
    }
  };

  // Handle session not found or error
  if (sessionError && !isLoadingSession) {
    return (
      <div className="flex justify-center items-center h-[calc(100vh-64px)] bg-gray-50 dark:bg-gray-950">
        <div className="text-center">
          <h2 className="mb-4 text-2xl font-bold text-gray-900 dark:text-gray-100">
            Session Not Found
          </h2>
          <p className="mb-6 text-gray-600 dark:text-gray-400">
            {sessionError || 'The Capture Knowledge session you are looking for does not exist.'}
          </p>
          <button
            onClick={() => navigate('/knowledge-center')}
            className="px-6 py-2 text-white bg-green-600 rounded-lg transition-colors hover:bg-green-700"
          >
            Return to Knowledge Center
          </button>
        </div>
      </div>
    );
  }

  // Loading state
  if (isLoadingSession || isLoadingTemplate || !currentSession) {
    return (
      <div className="flex justify-center items-center h-[calc(100vh-64px)] bg-gray-50 dark:bg-gray-950">
        <div className="text-center">
          <IconLoader2 className="mx-auto mb-4 w-12 h-12 text-green-600 animate-spin" />
          <p className="text-gray-600 dark:text-gray-400">Loading Capture Knowledge session...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex overflow-hidden h-full bg-gray-50 dark:bg-gray-950">
      {/* Left Panel: Chat Sidebar (50%) */}
      <div className="flex flex-col w-1/2 h-full overflow-hidden border-r border-gray-200 dark:border-gray-800">
        <ChatSidebar
          sessionId={currentSession.id}
        />
      </div>

      {/* Right Panel: Tabs (50%) */}
      <div className="w-1/2 flex flex-col">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex flex-col h-full">
          <div className="flex-shrink-0 border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900">
            <div className="flex items-center justify-between">
              <TabsList className="justify-start h-auto p-0 bg-transparent rounded-none">
                <TabsTrigger
                  value="summary"
                  className="rounded-none border-b-2 border-transparent data-[state=active]:border-green-600 data-[state=active]:bg-transparent px-6 py-4"
                >
                  Session Summary
                </TabsTrigger>
                <TabsTrigger
                  value="template"
                  className="rounded-none border-b-2 border-transparent data-[state=active]:border-green-600 data-[state=active]:bg-transparent px-6 py-4"
                >
                  Capture Template
                </TabsTrigger>
              </TabsList>
              
              {/* Action buttons - visible on all tabs */}
              <div className="px-6 flex gap-2">
                <Button
                  onClick={handleDownloadInterviewNote}
                  variant="outline"
                  className="gap-2"
                  size="sm"
                >
                  <IconDownload className="w-4 h-4" />
                  Download Notes
                </Button>
                {currentSession?.status !== SESSION_STATUS.COMPLETED && (
                  <Button
                    onClick={handleCompleteSession}
                    variant="default"
                    className="hover:bg-green-700 gap-2"
                    size="sm"
                  >
                    <IconCheck className="w-4 h-4" />
                    Mark as Completed
                  </Button>
                )}
              </div>
            </div>
          </div>
          <div className="flex-1 overflow-hidden">
            <TabsContent value="summary" className="h-full m-0">
              <SummaryPanel
                session={currentSession}
                template={contributionTemplate}
                showTemplateInfo={false}
              />
            </TabsContent>
            <TabsContent value="template" className="h-full m-0">
              <SummaryPanel
                session={currentSession}
                template={contributionTemplate}
                showSessionInfo={false}
              />
            </TabsContent>
          </div>
        </Tabs>
      </div>
    </div>
  );
}
