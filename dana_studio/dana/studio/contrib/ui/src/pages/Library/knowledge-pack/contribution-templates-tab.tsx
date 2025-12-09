import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useKnowledgePackStore } from '@/stores';
import { useContributionStore } from '@/stores/contribution-store';
import { apiService } from '@/lib/api';
import { toast } from 'sonner';
import { DataTable } from '@/components/table/data-table';
import { getContributionTemplateColumns } from '@/components/library/contribution-template-columns';
import { DeleteTemplateDialog } from '@/components/library/delete-template-dialog';
import { PasteClipboard, Plus } from 'iconoir-react';
import { Button } from '@/components/ui/button';
import { KNOWLEDGE_GENERATION_STATUS, TEMPLATE_GENERATION_STATUS } from '@/lib/constants';

// Polling interval constant (10 seconds)
const POLLING_INTERVAL = 10000;

interface ContributionTemplatesTabProps {
  knowledgePackId: number;
}

// Extended LibraryItem type to include children and additional properties
interface ExtendedLibraryItem {
  id: number;
  name: string;
  type: 'file' | 'folder';
  extension: string;
  created: string;
  updated: string;
  children?: ExtendedLibraryItem[];
  template_metadata?: any;
  interview_sessions?: any[];
  status?: string;
  interviewee_name?: string;
  interviewee_role?: string;
  is_master?: boolean;
}

export function ContributionTemplatesTab({ knowledgePackId }: ContributionTemplatesTabProps) {
  const navigate = useNavigate();
  const { createdKnowledgePack, setCreatedKnowledgePack, setNavigationSource } = useKnowledgePackStore();
  const { createTemplate } = useContributionStore();
  const [capturingKnowledge, setCapturingKnowledge] = useState<Set<number>>(new Set());
  
  // Templates state
  const [templates, setTemplates] = useState<any[]>([]);
  const [isLoadingTemplates, setIsLoadingTemplates] = useState(false);
  
  // Delete dialog state
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [itemToDelete, setItemToDelete] = useState<{
    id: number;
    type: 'template' | 'session';
    name: string;
  } | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  
  // Track deleted items to filter them out from display
  const [deletedItemIds, setDeletedItemIds] = useState<Set<number>>(new Set());
  
  // Polling state for knowledge pack status
  const pollingIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Find master template from templates array
  const masterTemplate = templates.find((t: any) => t.is_master === true);
  const masterTemplateStatus = masterTemplate?.template_metadata?.status;

  // Function to refresh knowledge pack status from API
  const refreshKnowledgePackStatus = useCallback(async (): Promise<{ kpStatus: string | null; masterTemplateStatus: string | null }> => {
    if (!createdKnowledgePack?.id) {
      return { kpStatus: null, masterTemplateStatus: null };
    }

    let masterTemplateStatus: string | null = null;

    try {
      const response = await apiService.getKnowledgePack(createdKnowledgePack.id);
      if (response.success && response.data) {
        // Update the knowledge pack in store with fresh status
        const updatedPack = {
          ...createdKnowledgePack,
          status: response.data.status,
          generation_task_id: response.data.generation_task_id,
          kp_metadata: response.data.kp_metadata,
          folder_path: response.data.folder_path,
          interview_templates: response.data.interview_templates || [],
        };
        setCreatedKnowledgePack(updatedPack);
        console.log('✅ Knowledge pack status refreshed:', response.data.status);
        
        // Also refresh templates to get latest master template status
        try {
          const templatesResponse = await apiService.listInterviewTemplates(createdKnowledgePack.id);
          if (templatesResponse.success && templatesResponse.data) {
            const templatesWithSessions = await Promise.all(
              templatesResponse.data.map(async (template: any) => {
                try {
                  const sessionsResponse = await apiService.listInterviewSessions(
                    template.id,
                    0,
                    100,
                  );
                  return {
                    ...template,
                    interview_sessions: sessionsResponse.data || [],
                  };
                } catch (error) {
                  console.error(`Failed to fetch sessions for template ${template.id}:`, error);
                  return {
                    ...template,
                    interview_sessions: [],
                  };
                }
              }),
            );
            setTemplates(templatesWithSessions);
            const refreshedMasterTemplate = templatesWithSessions.find((t: any) => t.is_master);
            masterTemplateStatus = refreshedMasterTemplate?.template_metadata?.status || null;
            console.log('✅ Templates refreshed, master template status:', masterTemplateStatus);
          }
        } catch (error) {
          console.error('Failed to refresh templates:', error);
        }
        
        return { kpStatus: response.data.status, masterTemplateStatus };
      }
    } catch (error) {
      console.error('Failed to refresh knowledge pack status:', error);
    }
    return { kpStatus: null, masterTemplateStatus: null };
  }, [createdKnowledgePack, setCreatedKnowledgePack]);

  // Fetch templates when component mounts or knowledge pack changes
  useEffect(() => {
    const fetchTemplates = async () => {
      if (createdKnowledgePack?.id) {
        console.log('🔄 ContributionTemplatesTab - fetching templates for KP:', createdKnowledgePack.id);
        setIsLoadingTemplates(true);
        
        try {
          const response = await apiService.listInterviewTemplates(createdKnowledgePack.id!);
          if (response.success && response.data) {
            // Fetch sessions for each template
            const templatesWithSessions = await Promise.all(
              response.data.map(async (template: any) => {
                try {
                  const sessionsResponse = await apiService.listInterviewSessions(
                    template.id,
                    0,
                    100,
                  );
                  console.log(
                    `🎓 Fetched sessions for template ${template.id}:`,
                    sessionsResponse,
                  );
                  return {
                    ...template,
                    interview_sessions: sessionsResponse.data || [],
                  };
                } catch (error) {
                  console.error(`Failed to fetch sessions for template ${template.id}:`, error);
                  return {
                    ...template,
                    interview_sessions: [],
                  };
                }
              }),
            );
            
            setTemplates(templatesWithSessions);
            console.log('✅ Templates with sessions loaded:', templatesWithSessions.length);
          } else {
            console.error('Failed to load templates:', response.error);
            setTemplates([]);
          }
        } catch (error) {
          console.error('Error fetching templates:', error);
          setTemplates([]);
        } finally {
          setIsLoadingTemplates(false);
        }
      }
    };

    fetchTemplates();
  }, [createdKnowledgePack?.id]);

  // Also refresh when window regains focus (user returns from another tab/page)
  useEffect(() => {
    const handleFocus = () => {
      if (createdKnowledgePack?.id) {
        console.log('🔄 Window focused - refreshing templates');
        // Re-fetch templates when window regains focus
        const fetchTemplates = async () => {
          setIsLoadingTemplates(true);
          try {
            const response = await apiService.listInterviewTemplates(createdKnowledgePack.id!);
            if (response.success && response.data) {
              // Fetch sessions for each template
              const templatesWithSessions = await Promise.all(
                response.data.map(async (template: any) => {
                  try {
                    const sessionsResponse = await apiService.listInterviewSessions(
                      template.id,
                      0,
                      100,
                    );
                    return {
                      ...template,
                      interview_sessions: sessionsResponse.data || [],
                    };
                  } catch (error) {
                    console.error(`Failed to fetch sessions for template ${template.id}:`, error);
                    return {
                      ...template,
                      interview_sessions: [],
                    };
                  }
                }),
              );
              setTemplates(templatesWithSessions);
            }
          } catch (error) {
            console.error('Error refreshing templates:', error);
          } finally {
            setIsLoadingTemplates(false);
          }
        };
        fetchTemplates();
      }
    };
    
    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, [createdKnowledgePack?.id]);

  // Polling effect: Start/stop polling based on knowledge pack status
  useEffect(() => {
    // Cleanup function to stop polling
    const stopPolling = () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
        console.log('🛑 Stopped polling knowledge pack status');
      }
    };

    // Check if we should start polling
    const shouldPoll =
      createdKnowledgePack?.id &&
      (createdKnowledgePack.status === KNOWLEDGE_GENERATION_STATUS.GENERATING ||
        createdKnowledgePack.generation_task_id != null ||
        masterTemplateStatus === TEMPLATE_GENERATION_STATUS.GENERATING ||
        masterTemplateStatus === TEMPLATE_GENERATION_STATUS.PENDING);

    // Check if we should stop polling (status is completed or failed)
    const shouldStop =
      createdKnowledgePack?.status === KNOWLEDGE_GENERATION_STATUS.COMPLETED ||
      createdKnowledgePack?.status === KNOWLEDGE_GENERATION_STATUS.FAILED ||
      masterTemplateStatus === TEMPLATE_GENERATION_STATUS.COMPLETED ||
      masterTemplateStatus === TEMPLATE_GENERATION_STATUS.FAILED;

    if (shouldStop) {
      // Stop polling if status is completed or failed
      stopPolling();
      return;
    }

    if (shouldPoll && !pollingIntervalRef.current) {
      // Start polling
      console.log('🔄 Starting polling for knowledge pack status');
      const interval = setInterval(async () => {
        const { kpStatus, masterTemplateStatus: refreshedMasterStatus } = await refreshKnowledgePackStatus();
        
        // Stop polling if knowledge pack status or master template status changed to completed or failed
        if (
          kpStatus === KNOWLEDGE_GENERATION_STATUS.COMPLETED ||
          kpStatus === KNOWLEDGE_GENERATION_STATUS.FAILED ||
          refreshedMasterStatus === TEMPLATE_GENERATION_STATUS.COMPLETED ||
          refreshedMasterStatus === TEMPLATE_GENERATION_STATUS.FAILED
        ) {
          stopPolling();
        }
      }, POLLING_INTERVAL);
      pollingIntervalRef.current = interval;
    } else if (!shouldPoll && pollingIntervalRef.current) {
      // Stop polling if conditions no longer met
      stopPolling();
    }

    // Cleanup on unmount or when knowledge pack changes
    return () => {
      stopPolling();
    };
  }, [createdKnowledgePack?.id, createdKnowledgePack?.status, createdKnowledgePack?.generation_task_id, masterTemplateStatus, refreshKnowledgePackStatus]);

  // Templates are now managed by local state

  // Transform templates data to table format
  const transformTemplatesToTableData = (): ExtendedLibraryItem[] => {
    return templates
      .filter((template: any) => !deletedItemIds.has(template.id)) // Filter out deleted templates
      .map((template: any) => {
        const sessions = template.interview_sessions || [];
        
        // Create template item
        const templateItem: ExtendedLibraryItem = {
          id: template.id,
          name: template.name || 'Untitled Template',
          type: 'file',
          extension: 'template',
          created: template.created_at,
          updated: template.updated_at,
          template_metadata: template.template_metadata,
          interview_sessions: sessions,
          is_master: template.is_master,
          children: sessions
            .filter((session: any) => !deletedItemIds.has(session.id)) // Filter out deleted sessions
            .map((session: any) => ({
              id: session.id,
              name: session.session_name || `Session ${session.id}`,
              type: 'file' as const,
              extension: 'ek' as const,
              created: session.created_at,
              updated: session.updated_at,
              status: session.status,
              interviewee_name: session.interviewee_name,
              interviewee_role: session.interviewee_role,
            })),
        };

        return templateItem;
      });
  };

  // Get table data
  const tableData = transformTemplatesToTableData();

  const handleTemplateClick = (templateId: number) => {
    console.log('🔍 handleTemplateClick called:', { templateId, knowledgePackId });
    console.log('🔍 Setting navigation source before navigate');
    // Set navigation source before navigating
    setNavigationSource({ type: 'knowledge-pack', id: knowledgePackId });
    console.log('🔍 Navigation source set, now navigating to:', `/capture-template/${templateId}`);
    navigate(`/capture-template/${templateId}`);
  };

  const handleSessionClick = (sessionId: number) => {
    console.log('🔍 handleSessionClick called:', { sessionId, knowledgePackId });
    console.log('🔍 Setting navigation source before navigate to capture-knowledge');
    // Set navigation source before navigating
    setNavigationSource({ type: 'knowledge-pack', id: knowledgePackId });
    console.log('🔍 Navigation source set, now navigating to:', `/capture-knowledge/${sessionId}`);
    navigate(`/capture-knowledge/${sessionId}`);
  };

  const handleCaptureKnowledge = async (templateId: number, templateName: string) => {
    // Check if already capturing for this template
    if (capturingKnowledge.has(templateId)) return;
    
    setCapturingKnowledge(prev => new Set(prev).add(templateId));
    
    try {
      // Show loading toast
      toast.loading('Creating Capture Knowledge session...', { id: `capture-knowledge-${templateId}` });
      
      // Create session via API
      const response = await apiService.createInterviewSession(templateId, {
        session_name: `Capture Knowledge - ${templateName || 'Untitled'} - ${new Date().toLocaleDateString()}`,
      });
      
      // Dismiss loading toast
      toast.dismiss(`capture-knowledge-${templateId}`);
      
      if (response.success && response.data) {
        toast.success('Capture Knowledge session created!');
        
        // Set navigation source before navigating
        console.log('🔍 Setting navigation source before navigate to new capture-knowledge session');
        setNavigationSource({ type: 'knowledge-pack', id: knowledgePackId });
        
        // Navigate to the Capture Knowledge page
        navigate(`/capture-knowledge/${response.data.id}`);
      } else {
        const errorMsg = response.error || response.message || 'Failed to create session';
        toast.error(errorMsg);
      }
    } catch (error: any) {
      console.error('Failed to create capture knowledge session:', error);
      toast.dismiss(`capture-knowledge-${templateId}`);
      toast.error(error?.message || 'Failed to create session');
    } finally {
      setCapturingKnowledge(prev => {
        const newSet = new Set(prev);
        newSet.delete(templateId);
        return newSet;
      });
    }
  };

  const handleDelete = (id: number, type: 'template' | 'session', name: string) => {
    setItemToDelete({ id, type, name });
    setDeleteDialogOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (!itemToDelete) return;
    
    setIsDeleting(true);
    try {
      if (itemToDelete.type === 'template') {
        await apiService.deleteInterviewTemplate(itemToDelete.id);
        toast.success('Template deleted successfully');
      } else {
        await apiService.deleteInterviewSession(itemToDelete.id);
        toast.success('Session deleted successfully');
      }
      
      // Immediately hide the deleted item from the UI
      setDeletedItemIds(prev => new Set(prev).add(itemToDelete.id));
      
      // Refresh data by calling the global refresh function if available
      if (window.refreshKnowledgePackTree) {
        window.refreshKnowledgePackTree();
      }
      
      setDeleteDialogOpen(false);
      setItemToDelete(null);
    } catch (error: any) {
      toast.error(error?.message || 'Failed to delete');
    } finally {
      setIsDeleting(false);
    }
  };

  const handleAddCaptureTemplate = async () => {
    if (!createdKnowledgePack?.id) {
      toast.error('No Knowledge Pack selected');
      return;
    }

    // Check if KP or master template is completed
    const isCompleted = 
      masterTemplateStatus === TEMPLATE_GENERATION_STATUS.COMPLETED ||
      createdKnowledgePack.status === KNOWLEDGE_GENERATION_STATUS.COMPLETED;
    
    if (!isCompleted) {
      toast.error(
        'Only completed Knowledge Packs or master templates can be used to create templates. Please generate knowledge first.',
      );
      return;
    }

    try {
      // Extract domain and role from KP metadata (same logic as editor dialog)
      const domain = createdKnowledgePack.kp_metadata?.domain || createdKnowledgePack.specialization?.domain || 'General';
      const role = createdKnowledgePack.kp_metadata?.role || createdKnowledgePack.specialization?.role || 'Domain Expert';

      console.log('🎯 Creating capture template for KP:', createdKnowledgePack.id);

      // Create template via store
      const createdTemplate = await createTemplate(createdKnowledgePack.id, {
        domain,
        role,
      });

      toast.success('Capture Template created successfully!');

      // Navigate to the newly created template
      if (createdTemplate?.id) {
        // Set navigation source before navigating
        setNavigationSource({ type: 'knowledge-pack', id: knowledgePackId });
        navigate(`/capture-template/${createdTemplate.id}`);
      }

      // Refresh the templates list by re-fetching
      if (createdKnowledgePack?.id) {
        try {
          const response = await apiService.listInterviewTemplates(createdKnowledgePack.id!);
          if (response.success && response.data) {
            // Fetch sessions for each template
            const templatesWithSessions = await Promise.all(
              response.data.map(async (template: any) => {
                try {
                  const sessionsResponse = await apiService.listInterviewSessions(
                    template.id,
                    0,
                    100,
                  );
                  return {
                    ...template,
                    interview_sessions: sessionsResponse.data || [],
                  };
                } catch (error) {
                  console.error(`Failed to fetch sessions for template ${template.id}:`, error);
                  return {
                    ...template,
                    interview_sessions: [],
                  };
                }
              }),
            );
            setTemplates(templatesWithSessions);
          }
        } catch (error) {
          console.error('Error refreshing templates after creation:', error);
        }
      }
    } catch (error: any) {
      console.error('Failed to create capture template:', error);
      toast.error(error?.message || 'Failed to create capture template');
    }
  };

  // Function to get children for hierarchical display
  const getRowChildren = (row: ExtendedLibraryItem): ExtendedLibraryItem[] | undefined => {
    return row.children;
  };

  // Handle row click for DataTable
  const handleRowClick = (row: any) => {
    const item = row.original as ExtendedLibraryItem;
    const isTemplate = item.type === 'file' && item.extension === 'template';
    const isSession = item.type === 'file' && item.extension === 'ek';
    
    console.log('Row clicked:', { isTemplate, isSession, itemId: item.id, item });
    
    if (isTemplate) {
      // Check if master template and if it's completed
      const isMasterTemplate = item.is_master === true;
      const isCompleted = item.template_metadata?.status === TEMPLATE_GENERATION_STATUS.COMPLETED;
      const isClickable = isMasterTemplate ? isCompleted : true;
      
      console.log('Template click check:', { isMasterTemplate, isCompleted, isClickable });
      
      if (isClickable) {
        handleTemplateClick(item.id);
      }
    } else if (isSession) {
      handleSessionClick(item.id);
    }
  };

  // Get column definitions
  const columns = getContributionTemplateColumns(
    handleTemplateClick,
    handleSessionClick,
    handleCaptureKnowledge,
    capturingKnowledge,
    handleDelete
  );

  if (isLoadingTemplates) {
    return (
      <div className="flex justify-center items-center h-full">
        <div className="text-center">
          <div className="mx-auto mb-4 w-12 h-12 rounded-full border-b-2 border-blue-600 animate-spin"></div>
          <p className="text-gray-600">Loading capture templates...</p>
        </div>
      </div>
    );
  }

  if (tableData.length === 0) {
    return (
      <div className="flex justify-center items-center h-full">
        <div className="text-center">
          <PasteClipboard className="mx-auto mb-4 w-12 h-12 text-gray-300" />
          <p className="text-gray-600">No capture templates found</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col max-w-[1200px] h-full overflow-hidden">
      {/* Header */}
      <div className="py-4">
        <div className="flex justify-between items-start">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              Capture templates ({tableData.length})
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              Templates and their expert knowledge sessions
            </p>
          </div>
          <Button
            onClick={handleAddCaptureTemplate}
            disabled={
              !(
                masterTemplateStatus === TEMPLATE_GENERATION_STATUS.COMPLETED ||
                createdKnowledgePack?.status === KNOWLEDGE_GENERATION_STATUS.COMPLETED
              )
            }
            className="gap-2"
            
          >
            <Plus className="w-4 h-4" />
            Add Capture Template
          </Button>
        </div>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-hidden">
        <DataTable
          columns={columns}
          data={tableData}
          loading={isLoadingTemplates}
          handleRowClick={handleRowClick}
          getRowChildren={getRowChildren}
          is_border={false}
        />
      </div>
      
      {/* Delete Confirmation Dialog */}
      <DeleteTemplateDialog
        isOpen={deleteDialogOpen}
        onClose={() => {
          setDeleteDialogOpen(false);
          setItemToDelete(null);
        }}
        onConfirm={handleConfirmDelete}
        isDeleting={isDeleting}
        itemType={itemToDelete?.type || 'template'}
        itemName={itemToDelete?.name || ''}
      />
    </div>
  );
}
