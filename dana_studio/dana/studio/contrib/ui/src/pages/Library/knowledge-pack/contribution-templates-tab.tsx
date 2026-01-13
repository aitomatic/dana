import { useState, useEffect } from 'react';
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
import { KNOWLEDGE_GENERATION_STATUS } from '@/lib/constants';

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
}

export function ContributionTemplatesTab({}: ContributionTemplatesTabProps) {
  const navigate = useNavigate();
  const { createdKnowledgePack } = useKnowledgePackStore();
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
    navigate(`/capture-template/${templateId}`);
  };

  const handleSessionClick = (sessionId: number) => {
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

    // Check if KP is completed
    if (createdKnowledgePack.status !== KNOWLEDGE_GENERATION_STATUS.COMPLETED) {
      toast.error(
        'Only completed Knowledge Packs can be used to create templates. Please generate knowledge first.',
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
            disabled={createdKnowledgePack?.status !== KNOWLEDGE_GENERATION_STATUS.COMPLETED}
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
