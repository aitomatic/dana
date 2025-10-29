import { useEffect, useState } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { useKnowledgePackStore } from '@/stores';
import DomainKnowledgeTree from './domain-tree';
import { KnowledgePackChatSidebar } from './chat-sidebar';
import { toast } from 'sonner';
import { Eye, EyeClosed, GridPlus, Xmark } from 'iconoir-react';
import { BookOpen, List, Files, FileText } from 'lucide-react';
import { ContributionTemplatesTab } from './contribution-templates-tab';
import { CaptureSummaryTab } from './capture-summary-tab';
import { DocumentsTab } from './documents-tab';
import { AssignAgentsDialog } from '@/components/library/assign-agents-dialog';
import { AssignSuccessDialog } from '@/components/library/assign-success-dialog';
import type { AssignmentResult } from '@/types/domainKnowledge';
import { apiService } from '@/lib/api';

// Extend Window interface for global refresh function
declare global {
  interface Window {
    refreshKnowledgePackTree?: () => void;
  }
}

const TABS = ['Knowledge Pack', 'Capture Templates', 'Capture Summary', 'Documents'];
const TAB_ICONS = {
  'Knowledge Pack': <BookOpen className="w-4 h-4" />,
  'Capture Templates': <List className="w-4 h-4" />,
  'Capture Summary': <FileText className="w-4 h-4" />,
  'Documents': <Files className="w-4 h-4" />,
};

export default function KnowledgePackDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const {
    createdKnowledgePack,
    setCreatedKnowledgePack,
    fetchKnowledgePackTree,
    isLoadingTree,
  } = useKnowledgePackStore();
  
  const [showLegend, setShowLegend] = useState(true);
  const [activeTab, setActiveTab] = useState('Knowledge Pack');
  const [isLoadingPack, setIsLoadingPack] = useState(true);
  
  // Assignment dialog states
  const [showAssignDialog, setShowAssignDialog] = useState(false);
  const [showSuccessDialog, setShowSuccessDialog] = useState(false);
  const [assignmentResults, setAssignmentResults] = useState<AssignmentResult[]>([]);

  // Get originalDescription from navigation state (for newly created packs)
  const originalDescription = location.state?.originalDescription;

  // Fetch knowledge pack data on mount
  useEffect(() => {
    const fetchKnowledgePack = async () => {
      if (!id) {
        toast.error('Knowledge pack ID not found');
        navigate('/knowledge-center');
        return;
      }

      try {
        setIsLoadingPack(true);
        
        // Fetch knowledge pack details
        const response = await apiService.getKnowledgePack(parseInt(id));
        
        if (response.success && response.data) {
          // Convert API response to the format expected by the store
          const packData = {
            id: parseInt(id),
            specialization: {
              domain: response.data.kp_metadata?.domain || 'Unknown Domain',
              role: response.data.kp_metadata?.role || 'Unknown Role',
              task: response.data.kp_metadata?.task || '',
            },
            document_ids: response.data.kp_metadata?.associated_documents || [],
            status: response.data.status,
            folder_path: response.data.folder_path,
            kp_metadata: response.data.kp_metadata,
            generation_task_id: response.data.generation_task_id,
            interview_templates: response.data.interview_templates || [],
            // Preserve originalDescription from navigation state (for newly created packs)
            originalDescription: originalDescription || undefined,
          };
          
          setCreatedKnowledgePack(packData);
          
          // Fetch the knowledge pack tree
          await fetchKnowledgePackTree(parseInt(id));
        } else {
          throw new Error(response.error || 'Failed to load knowledge pack');
        }
      } catch (error: any) {
        console.error('Failed to fetch knowledge pack:', error);
        toast.error('Failed to load knowledge pack');
        navigate('/knowledge-center');
      } finally {
        setIsLoadingPack(false);
      }
    };

    fetchKnowledgePack();
  }, [id, navigate, setCreatedKnowledgePack, fetchKnowledgePackTree]);

  // Expose refresh function globally for chat sidebar to call
  useEffect(() => {
    if (createdKnowledgePack?.id !== undefined) {
      // Make refresh function available globally
      window.refreshKnowledgePackTree = () => {
        console.log('🔄 Refreshing knowledge pack tree from chat sidebar');
        fetchKnowledgePackTree(createdKnowledgePack.id!);
      };
    }

    // Cleanup
    return () => {
      if (window.refreshKnowledgePackTree) {
        delete window.refreshKnowledgePackTree;
      }
    };
  }, [createdKnowledgePack?.id, fetchKnowledgePackTree]);

  const handleClose = () => {
    navigate(-1); // Go back to previous page
  };

  if (isLoadingPack) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="text-center">
          <div className="mx-auto mb-4 w-12 h-12 rounded-full border-b-2 border-blue-600 animate-spin"></div>
          <p className="text-gray-600">Loading knowledge pack...</p>
        </div>
      </div>
    );
  }

  if (!createdKnowledgePack) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="text-center">
          <p className="text-gray-600">Knowledge pack not found</p>
          <Button onClick={handleClose} className="mt-4">
            Go Back
          </Button>
        </div>
      </div>
    );
  }

  // Use kp_metadata as primary source, fallback to specialization for backward compatibility
  const domain = createdKnowledgePack.kp_metadata?.domain || createdKnowledgePack.specialization?.domain || 'General';
  
  const title = `${domain}`;

  return (
    <div className="flex flex-col h-screen bg-white dark:bg-surface">
      {/* Header */}
      <div className="flex justify-between items-center px-6 py-4 bg-white border-b h-[64px] dark:bg-surface">
        <div className="font-semibold text-gray-700 dark:text-gray-300">
          Knowledge Pack: {title}
        </div>
        <div className="flex gap-2 items-center">
          <Button
            variant="ghost"
            size="sm"
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100"
            onClick={handleClose}
          >
            <Xmark className="w-5 h-5" />
          </Button>
        </div>
      </div>

      {/* Tab System */}
      <div className="flex flex-col overflow-hidden relative flex-1">
        {/* Tab Bar */}
        <div className="flex justify-between items-center bg-gray-50 border-b border-gray-200">
          <div className="flex">
            {TABS.map((tab) => (
              <button
                key={tab}
                className={`cursor-pointer px-4 py-4 h-14 font-medium text-sm flex items-center gap-2 transition-colors relative ${
                  activeTab === tab
                    ? 'text-primary bg-white before:absolute before:bottom-[-1px] before:left-0 before:right-0 before:h-1 before:bg-white before:content-[""]'
                    : 'text-gray-500'
                }`}
                onClick={() => setActiveTab(tab)}
              >
                {TAB_ICONS[tab as keyof typeof TAB_ICONS]}
                {tab}
              </button>
            ))}
          </div>
          
          {/* Assign to Agent Button */}
          <div className="pr-4">
            <Button
              variant="outline"
              onClick={() => setShowAssignDialog(true)}
              className="gap-2"
            >
              <GridPlus className="w-4 h-4" />
              Assign to Agent
            </Button>
          </div>
        </div>

        {/* Tab Content */}
        <div className="flex overflow-hidden flex-1 justify-center">
          {activeTab === 'Knowledge Pack' && (
            <>
              {/* Left: Chat Sidebar for Building Knowledge Pack */}
              <KnowledgePackChatSidebar knowledgePackId={createdKnowledgePack?.id?.toString()} />

              {/* Right: Domain Knowledge Tree */}
              <div className="overflow-hidden relative flex-1">
                {isLoadingTree ? (
                  <div className="flex justify-center items-center h-full">
                    <div className="text-center">
                      <div className="mx-auto mb-4 w-12 h-12 rounded-full border-b-2 border-blue-600 animate-spin"></div>
                      <p className="text-gray-600">Loading knowledge pack details...</p>
                    </div>
                  </div>
                ) : (
                  <DomainKnowledgeTree
                    knowledgePackId={createdKnowledgePack.id}
                    knowledgePackMetadata={(() => {
                      const metadata = {
                        domain: createdKnowledgePack.kp_metadata?.domain || createdKnowledgePack.specialization?.domain || 'General',
                        role: createdKnowledgePack.kp_metadata?.role || createdKnowledgePack.specialization?.role || 'Domain Expert',
                      };
                      
                      return metadata;
                    })()}
                  />
                )}

                {/* Show Legend Button - Only show when legend is hidden */}
                {!isLoadingTree && !showLegend && (
                  <div className="absolute right-2 bottom-4 z-10">
                    <button
                      onClick={() => setShowLegend(true)}
                      className="flex gap-2 items-center px-3 py-2 text-sm text-gray-600 bg-white rounded-lg border border-gray-200 shadow-lg transition-colors hover:bg-gray-50"
                      title="Show Legend"
                    >
                      <Eye className="w-4 h-4" />
                      <span>Show Legend</span>
                    </button>
                  </div>
                )}

                {/* Status Legend - Only show when toggled on and not loading */}
                {!isLoadingTree && showLegend && (
                  <div className="absolute right-2 bottom-4 z-10 transform">
                    <div className="flex gap-4 items-center px-4 py-2 text-sm text-gray-600 bg-white rounded-lg border border-gray-200 shadow-lg">
                      <div className="flex gap-2 items-center">
                        <div
                          className="w-4 h-4 bg-gray-100 rounded border border-gray-500"
                          style={{ opacity: 0.6 }}
                        ></div>
                        <span>Content generation required</span>
                      </div>
                      <div className="flex gap-2 items-center">
                        <div
                          className="w-4 h-4 rounded border border-warning-400 bg-warning-100"
                          style={{ opacity: 0.8 }}
                        ></div>
                        <span>Pending</span>
                      </div>
                      <div className="flex gap-2 items-center">
                        <div
                          className="w-4 h-4 bg-cyan-100 rounded border border-cyan-400"
                          style={{ boxShadow: '0 0 0 1px rgb(79, 204, 255)' }}
                        ></div>
                        <span>In Progress</span>
                      </div>
                      <div className="flex gap-2 items-center">
                        <div
                          className="w-4 h-4 rounded border border-purple-400"
                          style={{ background: 'rgb(243, 232, 255)', opacity: 0.9 }}
                        ></div>
                        <span>Question Generated</span>
                      </div>
                      <div className="flex gap-2 items-center">
                        <div className="w-4 h-4 rounded border border-success-500 bg-success-50"></div>
                        <span>Content Generated</span>
                      </div>
                      <div className="flex gap-2 items-center">
                        <div className="w-4 h-4 rounded border border-error-500 bg-error-100"></div>
                        <span>Failed</span>
                      </div>

                      {/* Separator */}
                      <div className="w-px h-4 bg-gray-300"></div>
                      {/* Hide Legend Button */}
                      <button
                        onClick={() => setShowLegend(false)}
                        className="flex gap-1 items-center px-2 py-1 text-xs text-gray-500 rounded transition-colors hover:text-gray-700 hover:bg-gray-100"
                        title="Hide Legend"
                      >
                        <EyeClosed className="w-3 h-3" />
                        <span>Hide</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </>
          )}
          
          {activeTab === 'Capture Templates' && createdKnowledgePack.id !== undefined && (
            <ContributionTemplatesTab knowledgePackId={createdKnowledgePack.id} />
          )}
          
          {activeTab === 'Capture Summary' && createdKnowledgePack.id !== undefined && (
            <CaptureSummaryTab knowledgePackId={createdKnowledgePack.id} />
          )}
          
          {activeTab === 'Documents' && (
            <DocumentsTab documentIds={createdKnowledgePack.document_ids || []} />
          )}
        </div>
      </div>

      {/* Assignment Dialogs */}
      {createdKnowledgePack?.id && (
        <>
          <AssignAgentsDialog
            isOpen={showAssignDialog}
            onClose={() => setShowAssignDialog(false)}
            knowledgePackId={createdKnowledgePack.id}
            knowledgePackName={title}
            onSuccess={(results) => {
              setAssignmentResults(results);
              setShowSuccessDialog(true);
            }}
          />
          
          <AssignSuccessDialog
            isOpen={showSuccessDialog}
            onClose={() => setShowSuccessDialog(false)}
            knowledgePackName={title}
            results={assignmentResults}
          />
        </>
      )}
    </div>
  );
}
