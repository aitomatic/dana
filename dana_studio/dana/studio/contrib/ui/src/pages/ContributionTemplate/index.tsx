import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useContributionStore } from '@/stores/contribution-store';
import { IconLoader2 } from '@tabler/icons-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipTrigger, TooltipProvider } from '@/components/ui/tooltip';
import { apiService } from '@/lib/api';
import { toast } from 'sonner';
import { ChatSidebar } from './chat-sidebar';
import { TemplatePanel } from './template-panel';
import { SystemPromptPanel } from './system-prompt-panel';

export default function ContributionTemplatePage() {
  const { templateId } = useParams<{ templateId: string }>();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('template');
  const [isCreatingSession, setIsCreatingSession] = useState(false);

  const {
    currentTemplate,
    isCreatingTemplate,
    error,
    openTemplate,
    reset,
  } = useContributionStore();

  useEffect(() => {
    if (templateId) {
      openTemplate(parseInt(templateId, 10)).catch((error) => {
        console.error('Failed to load template:', error);
      });
    }

    // Cleanup on unmount
    return () => {
      reset();
    };
  }, [templateId, openTemplate, reset]);

  // Handle template not found or error
  if (error && !isCreatingTemplate) {
    return (
      <div className="flex justify-center items-center h-[calc(100vh-64px)] bg-gray-50 dark:bg-gray-950">
        <div className="text-center">
          <h2 className="mb-4 text-2xl font-bold text-gray-900 dark:text-gray-100">
            Template Not Found
          </h2>
          <p className="mb-6 text-gray-600 dark:text-gray-400">
            {error || 'The capture template you are looking for does not exist.'}
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
  if (isCreatingTemplate || !currentTemplate) {
    return (
      <div className="flex justify-center items-center h-[calc(100vh-64px)] bg-gray-50 dark:bg-gray-950">
        <div className="text-center">
          <IconLoader2 className="mx-auto mb-4 w-12 h-12 text-green-600 animate-spin" />
          <p className="text-gray-600 dark:text-gray-400">Loading capture template...</p>
        </div>
      </div>
    );
  }

  const handleStartExpertInterview = async () => {
    if (!currentTemplate) return;
    
    // Check if template is completed
    const templateStatus = currentTemplate.template_metadata?.status;
    if (templateStatus !== 'completed') {
      toast.error('Capture template must be completed first');
      return;
    }
    
    setIsCreatingSession(true);
    
    try {
      // Show loading toast
      toast.loading('Initiating Capture Knowledge session...', { id: 'create-ek-session' });
      
      // Create session via API
      const response = await apiService.createInterviewSession(currentTemplate.id, {
        session_name: `Capture Knowledge - ${currentTemplate.name || 'Untitled'} - ${new Date().toLocaleDateString()}`,
      });
      
      // Dismiss loading toast
      toast.dismiss('create-ek-session');
      
      if (response.success && response.data) {
        toast.success('Capture Knowledge session created!');
        
        // Navigate to the Capture Knowledge page
        navigate(`/capture-knowledge/${response.data.id}`);
      } else {
        const errorMsg = response.error || response.message || 'Failed to create session';
        toast.error(errorMsg);
      }
    } catch (error: any) {
      console.error('Failed to create capture knowledge session:', error);
      toast.dismiss('create-ek-session');
      toast.error(error?.message || 'Failed to create session');
    } finally {
      setIsCreatingSession(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-64px)] bg-gray-50 dark:bg-gray-950">
      {/* Main Content Area */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Panel: Chat Sidebar (50%) */}
        <div className="w-1/2 border-r border-gray-200 dark:border-gray-800">
          <ChatSidebar templateId={currentTemplate.id} />
        </div>

        {/* Right Panel: Tabs (50%) */}
        <div className="w-1/2 flex flex-col">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="flex flex-col h-full">
            <div className="flex-shrink-0 flex flex-row justify-between items-center border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900">
              <TabsList className="w-full justify-start h-auto p-0 bg-transparent rounded-none">
                <TabsTrigger
                  value="template"
                  className="rounded-none border-b-2 border-transparent data-[state=active]:border-green-600 data-[state=active]:bg-transparent px-6 py-4"
                >
                  Template Detail
                </TabsTrigger>
                <TabsTrigger
                  value="metadata"
                  className="rounded-none border-b-2 border-transparent data-[state=active]:border-green-600 data-[state=active]:bg-transparent px-6 py-4"
                >
                  Template Info
                </TabsTrigger>
                <TabsTrigger
                  value="system-prompt"
                  className="rounded-none border-b-2 border-transparent data-[state=active]:border-green-600 data-[state=active]:bg-transparent px-6 py-4"
                >
                  System Prompt
                </TabsTrigger>
              </TabsList>
              <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <div className='mr-4'>
                <Button
                  onClick={handleStartExpertInterview}
                  disabled={
                    isCreatingSession ||
                    currentTemplate.template_metadata?.status !== 'completed'
                  }
                  className="gap-2"
                  variant="default"
                >
                  {isCreatingSession ? (
                    <>
                      <IconLoader2 className="w-4 h-4 animate-spin" />
                      Creating session...
                    </>
                  ) : (
                    <>
                      <svg
                        className="w-4 h-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                        />
                      </svg>
                      Capture Knowledge
                    </>
                  )}
                </Button>
              </div>
            </TooltipTrigger>
            {currentTemplate.template_metadata?.status !== 'completed' && (
              <TooltipContent>
                <p>Capture template must be completed first</p>
              </TooltipContent>
            )}
          </Tooltip>
        </TooltipProvider>
            </div>
            <div className="flex-1 overflow-hidden">
              <TabsContent value="template" className="h-full m-0">
                <TemplatePanel
                  template={currentTemplate}
                  showMetadata={false}
                />
              </TabsContent>
              <TabsContent value="metadata" className="h-full m-0">
                <TemplatePanel
                  template={currentTemplate}
                  showContent={false}
                />
              </TabsContent>
              <TabsContent value="system-prompt" className="h-full m-0">
                <SystemPromptPanel template={currentTemplate} />
              </TabsContent>
            </div>
          </Tabs>
        </div>
      </div>
    </div>
  );
}

