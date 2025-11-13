/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { IconSearch, IconRefresh, IconArrowLeft, IconUpload } from '@tabler/icons-react';
import type { LibraryItem, FolderItem, FileItem } from '@/types/library';
import { useTopicOperations, useDocumentOperations } from '@/hooks/use-api';
import { CreateFolderDialog } from '@/components/library/create-folder-dialog';
import { EditTopicDialog } from '@/components/library/edit-topic-dialog';
import { EditDocumentDialog } from '@/components/library/edit-document-dialog';
import { EditTemplateDialog } from '@/components/library/edit-template-dialog';
import { EditSessionDialog } from '@/components/library/edit-session-dialog';
import { ConfirmDialog } from '@/components/library/confirm-dialog';

import { useFolderNavigation } from '@/hooks/use-folder-navigation';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';
import { convertTopicToFolderItem, convertDocumentToFileItem } from '@/components/library';
import { LibraryTable } from '@/components/library';
import { PdfViewer } from '@/components/library/pdf-viewer';
import { JsonViewer } from '@/components/library/json-viewer';
import { useExtractionFileStore } from '@/stores/extraction-file-store';
import { useKnowledgePackStore } from '@/stores';
import { ExtractionFilePopup } from './extraction-file';
import { useDanaAnalytics } from '@/hooks/useAnalytics';
import { apiService } from '@/lib/api';
import { CreateItemDropdown } from './create-item-dropdown';
import { KnowledgePackDialog } from './knowledge-pack';
import { FileSelectionBanner } from './file-selection-banner';
import { KPSelectionBanner } from './kp-selection-banner';
import { CTSelectionBanner } from './ct-selection-banner';
import { useContributionStore } from '@/stores/contribution-store';
import {
  TEMPLATE_GENERATION_STATUS,
  KNOWLEDGE_GENERATION_STATUS,
  SESSION_STATUS,
} from '@/lib/constants';

export default function LibraryPage() {
  const navigate = useNavigate();
  const { trackFolderCreation, trackError } = useDanaAnalytics();
  // API hooks
  const {
    fetchTopics,
    createTopic,
    updateTopic,
    deleteTopic,
    topics,
    isLoading: topicsLoading,
    // isCreating: isCreatingTopic,
    isUpdating: isUpdatingTopic,
    error: topicsError,
    clearError: clearTopicsError,
  } = useTopicOperations();

  const {
    fetchDocuments,
    updateDocument,
    deleteDocument,
    documents,
    isLoading: documentsLoading,
    isUpdating: isUpdatingDocument,
    error: documentsError,
    clearError: clearDocumentsError,
  } = useDocumentOperations();

  // Folder navigation
  const { folderState, navigateToFolder, navigateToRoot, getItemsInCurrentFolder } =
    useFolderNavigation();

  // Extraction file store
  const { openExtractionPopup, openExtractionPopupWithDocument, isExtractionPopupOpen } =
    useExtractionFileStore();

  // Knowledge Pack store
  const { setKnowledgePackOpen, setSelectedFiles, setCreatedKnowledgePack } =
    useKnowledgePackStore();

  // Local state
  const [showCreateFolder, setShowCreateFolder] = useState(false);
  const [showEditTopic, setShowEditTopic] = useState(false);
  const [showEditDocument, setShowEditDocument] = useState(false);
  const [showEditTemplate, setShowEditTemplate] = useState(false);
  const [showEditSession, setShowEditSession] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [selectedItem, setSelectedItem] = useState<LibraryItem | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter] = useState<'all' | 'files' | 'folders'>('all');
  const [quickFilter, setQuickFilter] = useState<'all' | 'files' | 'kp'>('all');
  const [pdfViewerOpen, setPdfViewerOpen] = useState(false);
  const [pdfFileUrl, setPdfFileUrl] = useState<string | null>(null);
  const [pdfFileName, setPdfFileName] = useState<string | undefined>(undefined);
  const [jsonViewerOpen, setJsonViewerOpen] = useState(false);
  const [jsonFileUrl, setJsonFileUrl] = useState<string | null>(null);
  const [jsonFileName, setJsonFileName] = useState<string | undefined>(undefined);

  // Knowledge Pack file selection state
  const [showFileSelectionBanner, setShowFileSelectionBanner] = useState(false);
  const [selectedFilesForKP, setSelectedFilesForKP] = useState<LibraryItem[]>([]);

  // Capture Template KP selection state (NEW)
  const [showKPSelectionBanner, setShowKPSelectionBanner] = useState(false);
  const [selectedKPForContribution, setSelectedKPForContribution] = useState<LibraryItem | null>(
    null,
  );

  // Capture Knowledge CT selection state (NEW)
  const [showCTSelectionBanner, setShowCTSelectionBanner] = useState(false);
  const [selectedCTForEK, setSelectedCTForEK] = useState<LibraryItem | null>(null);

  // Contribution store
  const { createTemplate } = useContributionStore();

  // Local state for knowledge packs
  const [knowledgePacks, setKnowledgePacks] = useState<any[]>([]);
  const [isLoadingKP, setIsLoadingKP] = useState(false);

  // Fetch knowledge packs with sessions
  const fetchKnowledgePacks = useCallback(async () => {
    setIsLoadingKP(true);
    try {
      const response = await apiService.listKnowledgePacks(100, 0);
      console.log('📦 Fetched knowledge packs:', response.data);
      if (response.data) {
        // The API already includes interview_sessions nested in interview_templates
        // No need to make additional API calls - use the data directly
        setKnowledgePacks(response.data);
      }
    } catch (error) {
      console.error('Failed to fetch knowledge packs:', error);
    } finally {
      setIsLoadingKP(false);
    }
  }, []);

  // Fetch data on component mount
  useEffect(() => {
    fetchTopics();
    fetchDocuments();
    fetchKnowledgePacks();
  }, [fetchTopics, fetchDocuments, fetchKnowledgePacks]);

  // Convert knowledge packs to library items
  const convertKnowledgePackToItem = (kp: any): LibraryItem => {
    const metadata = kp.kp_metadata || {};
    const domain = metadata.domain || 'Unknown Domain';
    const role = metadata.role || 'Unknown Role';

    // Only show child templates if the knowledge pack is completed
    const childTemplates: any[] = [];
    if (kp.status === KNOWLEDGE_GENERATION_STATUS.COMPLETED && 
        kp.interview_templates && 
        Array.isArray(kp.interview_templates)) {
      kp.interview_templates.forEach((template: any) => {
        // Convert expert knowledge sessions as children of templates
        const templateSessions: any[] = [];
        if (template.interview_sessions && Array.isArray(template.interview_sessions)) {
          template.interview_sessions.forEach((session: any) => {
            const sessionName = session.session_name || `Session ${session.id}`;
            console.log(`✨ Creating EK item for session ${session.id}:`, sessionName);
            templateSessions.push({
              id: `ek-${session.id}`,
              name: sessionName,
              type: 'file' as const,
              size: 0,
              lastModified: new Date(session.updated_at || session.created_at || new Date()),
              created: new Date(session.created_at || new Date()),
              path: '',
              extension: 'ek',
              metadata: {
                session_id: session.id,
                status: session.status || SESSION_STATUS.DRAFT,
                interview_template_id: session.interview_template_id,
                conversation_id: session.conversation_id,
                interviewee_name: session.interviewee_name,
                interviewee_role: session.interviewee_role,
                started_at: session.started_at,
                completed_at: session.completed_at,
              },
            });
          });
        }

        // Include all templates regardless of status
        childTemplates.push({
          id: `template-${template.id}`,
          name: template.name || 'Untitled Template',
          type: 'file' as const,
          size: 0,
          lastModified: new Date(template.updated_at || template.created_at || new Date()),
          created: new Date(template.created_at || new Date()),
          path: template.folder_path || '',
          extension: 'template',
          metadata: {
            template_id: template.id,
            kp_id: template.kp_id,
            version: template.version,
            is_master: template.is_master,
            status: template.template_metadata?.status || TEMPLATE_GENERATION_STATUS.DRAFT,
            estimated_duration: template.template_metadata?.estimated_duration,
            total_topics: template.template_metadata?.total_topics,
            domain: template.template_metadata?.domain,
            role: template.template_metadata?.role,
          },
          children: templateSessions.length > 0 ? templateSessions : undefined,
        });
      });
    }

    return {
      id: `kp-${kp.id}`,
      name: `${domain} - ${role}`,
      type: 'file',
      size: 0,
      lastModified: new Date(kp.updated_at || kp.created_at || new Date()),
      created: new Date(kp.created_at || new Date()),
      path: kp.folder_path || '',
      extension: 'kp',
      metadata: {
        ...metadata,
        knowledge_pack_id: kp.id,
        status: kp.status,
      },
      children: childTemplates.length > 0 ? childTemplates : undefined,
    };
  };

  // Convert API data to LibraryItem format
  const baseLibraryItems: LibraryItem[] = [
    ...(topics?.map(convertTopicToFolderItem) || []),
    ...(documents?.map(convertDocumentToFileItem) || []),
    ...(knowledgePacks?.map(convertKnowledgePackToItem) || []),
  ];

  // Flatten capture templates as top-level items ONLY when in CT selection mode
  // This prevents duplicates when not selecting CTs
  const flattenedTemplates: LibraryItem[] = [];
  if (showCTSelectionBanner) {
    baseLibraryItems.forEach((item) => {
      if (item.type === 'file' && (item as FileItem).extension === 'kp' && 'children' in item) {
        const children = (item as any).children;
        if (Array.isArray(children)) {
          flattenedTemplates.push(...children);
        }
      }
    });
  }

  const libraryItems = showCTSelectionBanner
    ? [...baseLibraryItems, ...flattenedTemplates]
    : baseLibraryItems;


  // Calculate item counts for folders
  const itemsWithCounts = libraryItems.map((item) => {
    if (item.type === 'folder') {
      const topicId = item.topicId;
      const itemCount = documents?.filter((doc) => doc.topic_id === topicId).length || 0;
      return { ...item, itemCount };
    }
    return item;
  });

  // Get items in current folder
  // When in selection mode (KP or CT), show all items regardless of folder
  const currentFolderItems =
    showKPSelectionBanner || showCTSelectionBanner
      ? itemsWithCounts
      : getItemsInCurrentFolder(itemsWithCounts);
  console.log('📋 Current folder items:', currentFolderItems.length, 'items');

  // Filter items based on search and type
  const filteredItems = currentFolderItems.filter((item) => {
    const matchesSearch = item.name.toLowerCase().includes(searchTerm.toLowerCase());

    // Apply quick filter
    let matchesQuickFilter = true;
    if (quickFilter === 'files') {
      const fileItem = item as FileItem;
      matchesQuickFilter = item.type === 'file' && 
        !['kp', 'template', 'ek'].includes(fileItem.extension);
    } else if (quickFilter === 'kp') {
      const fileItem = item as FileItem;
      matchesQuickFilter = item.type === 'file' && fileItem.extension === 'kp';
    }

    // When file selection banner is shown, only show documents (exclude kp, template, ek)
    let matchesFileSelectionBanner = true;
    if (showFileSelectionBanner && item.type === 'file') {
      const fileItem = item as FileItem;
      matchesFileSelectionBanner = !['kp', 'template', 'ek'].includes(fileItem.extension);
    }

    // When inside a folder, only show files (folders are hidden)
    let matchesType = true;
    if (folderState.isInFolder && !showKPSelectionBanner && !showCTSelectionBanner) {
      matchesType = item.type === 'file';
    } else {
      matchesType =
        typeFilter === 'all' ||
        (typeFilter === 'folders' && item.type === 'folder') ||
        (typeFilter === 'files' && item.type === 'file');
    }

    return matchesSearch && matchesQuickFilter && matchesFileSelectionBanner && matchesType;
  });

  const handleViewItem = async (item: LibraryItem) => {
    if (item.type === 'folder') {
      // Navigate to folder
      navigateToFolder(item as FolderItem);
    } else if (item.type === 'file') {
      const fileItem = item as any;

      // Handle Knowledge Pack viewing
      if (fileItem.extension === 'kp') {
        const knowledgePackId = fileItem.metadata?.knowledge_pack_id;
        console.log('🔍 Opening knowledge pack:', { knowledgePackId, fileItem, knowledgePacks });
        if (knowledgePackId) {
          try {
            // Find the knowledge pack from the list
            const kp = knowledgePacks.find((k) => k.id === knowledgePackId);
            console.log('📦 Found knowledge pack:', kp);
            if (kp) {
              // Reconstruct the createdKnowledgePack object
              const kpMetadata = kp.kp_metadata || {};
              const packData = {
                id: kp.id,
                specialization: {
                  domain: kpMetadata.domain || 'Unknown Domain',
                  role: kpMetadata.role || 'Unknown Role',
                  task: kpMetadata.task || '',
                },
                document_ids: kpMetadata.associated_documents || [],
                status: kp.status,
                folder_path: kp.folder_path,
                kp_metadata: kpMetadata,
                generation_task_id: kp.generation_task_id, // Include task ID for status polling
                interview_templates: kp.interview_templates || [], // Include templates data
              };
              console.log('✅ Setting knowledge pack data:', packData);
              setCreatedKnowledgePack(packData);

              // Navigate to the knowledge pack detail page
              navigate(`/knowledge-pack/${knowledgePackId}`);
              console.log('📖 Navigating to knowledge pack detail page');
            } else {
              console.error('❌ Knowledge pack not found');
              toast.error('Knowledge pack not found');
            }
          } catch (error) {
            console.error('Failed to open knowledge pack:', error);
            toast.error('Failed to open knowledge pack');
          }
        } else {
          console.error('❌ No knowledge pack ID in metadata');
          toast.error('Invalid knowledge pack');
        }
        return;
      }

      // Handle Capture Template viewing
      if (fileItem.extension === 'template') {
        const templateId = fileItem.metadata?.template_id;
        console.log('📋 Opening capture template:', { templateId, fileItem });
        if (templateId) {
          navigate(`/capture-template/${templateId}`);
        } else {
          console.error('❌ No template ID in metadata');
          toast.error('Invalid capture template');
        }
        return;
      }

      // Handle Capture Knowledge session viewing
      if (fileItem.extension === 'ek') {
        const sessionId = fileItem.metadata?.session_id;
        console.log('🎓 Opening capture knowledge session:', { sessionId, fileItem });
        if (sessionId) {
          navigate(`/capture-knowledge/${sessionId}`);
        } else {
          console.error('❌ No session ID in metadata');
          toast.error('Invalid capture knowledge session');
        }
        return;
      }

      // Handle regular documents
      const documentId = parseInt(item.id.replace('doc-', ''));
      const document = documents?.find((d) => d.id === documentId);

      if (document) {
        // Open extraction dialog with the document
        openExtractionPopupWithDocument(document);
      } else {
        // Fallback to original behavior for files without document data
        if ((item as any).extension?.toLowerCase() === 'pdf') {
          setPdfFileUrl(item.path);
          setPdfFileName(item.name);
          setPdfViewerOpen(true);
        } else if ((item as any).extension?.toLowerCase() === 'json') {
          setJsonFileUrl(item.path);
          setJsonFileName(item.name);
          setJsonViewerOpen(true);
        } else {
          console.log('View document:', item);
        }
      }
    }
  };

  const handleEditItem = (item: LibraryItem) => {
    setSelectedItem(item);
    if (item.type === 'folder') {
      setShowEditTopic(true);
    } else if (item.type === 'file') {
      const fileItem = item as FileItem;
      if (fileItem.extension === 'template') {
        setShowEditTemplate(true);
      } else if (fileItem.extension === 'ek') {
        setShowEditSession(true);
      } else {
        setShowEditDocument(true);
      }
    }
  };

  const handleEditTopic = async (topicId: number, topic: { name: string; description: string }) => {
    try {
      await updateTopic(topicId, topic);
      toast.success('Topic updated successfully');
    } catch {
      toast.error('Failed to update topic');
    }
  };

  const handleEditDocument = async (
    documentId: number,
    document: { original_filename?: string; topic_id?: number },
  ) => {
    try {
      await updateDocument(documentId, document);
      toast.success('Document updated successfully');
    } catch {
      toast.error('Failed to update document');
    }
  };

  const handleEditTemplate = async (templateId: number, updates: { name: string }) => {
    try {
      await apiService.updateInterviewTemplate(templateId, updates);
      toast.success('Template updated successfully');
      await fetchKnowledgePacks();
    } catch {
      toast.error('Failed to update template');
    }
  };

  const handleEditSession = async (sessionId: number, updates: { session_name: string }) => {
    try {
      await apiService.updateInterviewSession(sessionId, updates);
      toast.success('Session updated successfully');
      await fetchKnowledgePacks();
    } catch {
      toast.error('Failed to update session');
    }
  };

  const handleDeleteItem = async (item: LibraryItem) => {
    setSelectedItem(item);
    setShowDeleteConfirm(true);
  };

  const handleConfirmDelete = async () => {
    if (!selectedItem) return;

    try {
      if (selectedItem.type === 'folder') {
        const topicId = parseInt(selectedItem.id.replace('topic-', ''));
        await deleteTopic(topicId);
        toast.success('Topic deleted successfully');
      } else {
        const fileItem = selectedItem as any;

        // Check if it's a knowledge pack
        if (fileItem.extension === 'kp') {
          const knowledgePackId = fileItem.metadata?.knowledge_pack_id;
          if (knowledgePackId) {
            console.log('🗑️ Deleting knowledge pack:', knowledgePackId);
            await apiService.deleteKnowledgePack(knowledgePackId);
            toast.success('Knowledge pack deleted successfully');

            // Refresh knowledge packs list
            await fetchKnowledgePacks();
          } else {
            throw new Error('Knowledge pack ID not found');
          }
        } else if (fileItem.extension === 'template') {
          // Capture Template deletion
          const templateId = fileItem.metadata?.template_id;
          const isMaster = fileItem.metadata?.is_master;

          if (!templateId) {
            throw new Error('Template ID not found');
          }

          // Prevent deletion of master templates
          if (isMaster) {
            toast.error('Master templates cannot be deleted');
            return;
          }

          console.log('🗑️ Deleting capture template:', templateId);
          await apiService.deleteInterviewTemplate(templateId);
          toast.success('Capture template deleted successfully');

          // Refresh knowledge packs list (to update template count)
          await fetchKnowledgePacks();
        } else if (fileItem.extension === 'ek') {
          // Capture Knowledge session deletion
          const sessionId = fileItem.metadata?.session_id;

          if (!sessionId) {
            throw new Error('Session ID not found');
          }

          console.log('🗑️ Deleting expert knowledge session:', sessionId);
          await apiService.deleteInterviewSession(sessionId);
          toast.success('Expert knowledge session deleted successfully');

          // Refresh knowledge packs list (to update session count)
          await fetchKnowledgePacks();
        } else {
          // Regular document deletion
          const documentId = parseInt(selectedItem.id.replace('doc-', ''));
          await deleteDocument(documentId);
          toast.success('Document deleted successfully');
        }
      }
    } catch (error: any) {
      // Extract error message from the error object (handles both Error and ApiError)
      const errorMessage = error?.message || 'Failed to delete item';

      // Track deletion error
      trackError('library_item_deletion_failed', errorMessage, selectedItem.id);

      // For topics with documents, the store automatically retries with force=true
      // So we should only see an error if the retry also failed
      console.log('Delete error in UI:', errorMessage);

      // If it's still about associated documents, that means the force delete also failed
      if (errorMessage.includes('associated documents')) {
        toast.error('Unable to delete topic and its associated documents. Please try again.');
      } else {
        toast.error(errorMessage);
      }
    } finally {
      setShowDeleteConfirm(false);
      setSelectedItem(null);
    }
  };

  const handleCreateFolder = async (name: string) => {
    try {
      await createTopic({ name, description: `Topic: ${name}` });

      // Track folder creation
      trackFolderCreation(name);

      setShowCreateFolder(false);
    } catch (error) {
      trackError(
        'folder_creation_failed',
        error instanceof Error ? error.message : 'Unknown error',
        name,
      );
      throw error;
    }
  };

  const handleSearchChange = (value: string) => {
    setSearchTerm(value);
  };

  const handleRefresh = useCallback(() => {
    fetchTopics();
    fetchDocuments();
    fetchKnowledgePacks();
  }, [fetchTopics, fetchDocuments, fetchKnowledgePacks]);

  // Knowledge Pack handlers
  const handleKnowledgePackClick = () => {
    setShowFileSelectionBanner(true);
    setSelectedFilesForKP([]);
  };

  const handleCancelBanner = () => {
    setShowFileSelectionBanner(false);
    setSelectedFilesForKP([]);
  };

  const handleCreateKnowledgePack = () => {
    // Store selected files in the knowledge pack store
    setSelectedFiles(selectedFilesForKP);

    // Close banner and open dialog
    setShowFileSelectionBanner(false);
    setKnowledgePackOpen(true);
  };

  const handleFileSelectionToggle = (item: LibraryItem) => {
    setSelectedFilesForKP((prev) => {
      const isSelected = prev.some((f) => f.id === item.id);
      if (isSelected) {
        return prev.filter((f) => f.id !== item.id);
      } else {
        return [...prev, item];
      }
    });
  };

  // Capture Template handlers (NEW)
  const handleContributionTemplateClick = () => {
    setShowKPSelectionBanner(true);
    setSelectedKPForContribution(null);
  };

  const handleCancelKPBanner = () => {
    setShowKPSelectionBanner(false);
    setSelectedKPForContribution(null);
  };

  const handleCreateContributionTemplate = async () => {
    if (!selectedKPForContribution) {
      toast.error('Please select a Knowledge Pack');
      return;
    }

    console.log('🎯 Creating capture template for KP:', selectedKPForContribution);

    try {
      // Extract KP ID from the selected item (we know it's a FileItem since it's a KP)
      const kpFileItem = selectedKPForContribution as FileItem;
      const kpId = kpFileItem.metadata?.knowledge_pack_id;
      const kpStatus = kpFileItem.metadata?.status;
      const kpDomain = kpFileItem.metadata?.domain || 'Unknown Domain';
      const kpRole = kpFileItem.metadata?.role || 'Unknown Role';

      if (!kpId) {
        toast.error('Invalid Knowledge Pack selected');
        return;
      }

      // Only allow creating templates from completed KPs
      if (kpStatus !== KNOWLEDGE_GENERATION_STATUS.COMPLETED) {
        toast.error(
          'Only completed Knowledge Packs can be used to create templates. Please generate knowledge first.',
        );
        return;
      }

      // Close banner
      setShowKPSelectionBanner(false);

      // Create template via store (will open dialog automatically)
      const createdTemplate = await createTemplate(kpId, {
        domain: kpDomain,
        role: kpRole,
      });

      toast.success('Capture Template created successfully!');

      // Navigate to the newly created template
      if (createdTemplate?.id) {
        navigate(`/capture-template/${createdTemplate.id}`);
      }

      // Reset selection
      setSelectedKPForContribution(null);
    } catch (error: any) {
      console.error('Failed to create capture template:', error);
      toast.error(error?.message || 'Failed to create capture template');
    }
  };

  const handleKPSelectionToggle = (item: LibraryItem) => {
    // Check if item is a KP with completed status
    const fileItem = item as FileItem;
    if (fileItem.extension === 'kp') {
      const kpStatus = fileItem.metadata?.status;

      // Only allow selecting completed KPs
      if (kpStatus !== KNOWLEDGE_GENERATION_STATUS.COMPLETED) {
        toast.warning('Only completed Knowledge Packs can be used to create templates');
        return;
      }
    }

    // Single selection - replace previous selection
    setSelectedKPForContribution(item);
  };

  // Capture Knowledge handlers (NEW)
  const handleCaptureKnowledgeClick = () => {
    setShowCTSelectionBanner(true);
    setSelectedCTForEK(null);
  };

  const handleCancelCTBanner = () => {
    setShowCTSelectionBanner(false);
    setSelectedCTForEK(null);
  };

  const handleCreateCaptureKnowledge = async () => {
    if (!selectedCTForEK) {
      toast.error('Please select a Capture Template');
      return;
    }

    console.log('🎓 Creating Capture Knowledge session for CT:', selectedCTForEK);

    try {
      // Extract CT ID from the selected item
      const ctFileItem = selectedCTForEK as FileItem;
      const templateId = ctFileItem.metadata?.template_id;
      const templateStatus = ctFileItem.metadata?.status;

      if (!templateId) {
        toast.error('Invalid Capture Template selected');
        return;
      }

      // Only allow creating sessions from completed templates
      if (templateStatus !== TEMPLATE_GENERATION_STATUS.COMPLETED) {
        toast.error(
          'Only completed Capture Templates can be used to create Capture Knowledge sessions.',
        );
        return;
      }

      // Close banner
      setShowCTSelectionBanner(false);

      // Show loading toast
      toast.loading('Creating Capture Knowledge session...', { id: 'create-ek-session' });

      // Create session via API
      const response = await apiService.createInterviewSession(templateId, {
        session_name: `Capture Knowledge Session - ${new Date().toLocaleDateString()}`,
      });

      // Dismiss loading toast
      toast.dismiss('create-ek-session');

      if (response.success && response.data) {
        toast.success('Capture Knowledge session created!');

        // Navigate immediately to the Capture Knowledge page
        // The page will handle loading and polling if needed
        navigate(`/capture-knowledge/${response.data.id}`);
      } else {
        const errorMsg = response.error || response.message || 'Failed to create session';
        toast.error(errorMsg);
      }

      // Reset selection
      setSelectedCTForEK(null);
    } catch (error: any) {
      console.error('Failed to create Capture Knowledge session:', error);
      toast.error(error?.message || 'Failed to create Capture Knowledge session');
    }
  };

  const handleCTSelectionToggle = (item: LibraryItem) => {
    // Check if item is a CT with completed status
    const fileItem = item as FileItem;
    if (fileItem.extension === 'template') {
      const ctStatus = fileItem.metadata?.status;

      // Only allow selecting completed CTs
      if (ctStatus !== TEMPLATE_GENERATION_STATUS.COMPLETED) {
        toast.warning('Only completed Capture Templates can be used to create sessions');
        return;
      }
    }

    // Single selection - replace previous selection
    setSelectedCTForEK(item);
  };

  const isLoading = topicsLoading || documentsLoading || isLoadingKP;
  const error = topicsError || documentsError;

  return (
    <div className="flex overflow-hidden flex-col h-[calc(100vh-64px)]">
      {/* File Selection Banner (Knowledge Pack) */}
      {showFileSelectionBanner && (
        <FileSelectionBanner
          selectedCount={selectedFilesForKP.length}
          onCancel={handleCancelBanner}
          onCreate={handleCreateKnowledgePack}
        />
      )}

      {/* KP Selection Banner (Capture Template) - NEW */}
      {showKPSelectionBanner && (
        <KPSelectionBanner
          selectedKP={selectedKPForContribution}
          onCancel={handleCancelKPBanner}
          onCreate={handleCreateContributionTemplate}
        />
      )}

      {/* CT Selection Banner (Capture Knowledge) - NEW */}
      {showCTSelectionBanner && (
        <CTSelectionBanner
          selectedCT={selectedCTForEK}
          onCancel={handleCancelCTBanner}
          onCreate={handleCreateCaptureKnowledge}
        />
      )}

      <div className="flex flex-col flex-1 p-6 space-y-6 min-h-0">
        {/* Header */}

        <div className="flex justify-between items-center">
          {/* Filters */}
          <div className="flex gap-3 items-center">
            <div className="relative flex-1 w-[280px]">
              <IconSearch className="absolute left-3 top-1/2 w-4 h-4 text-gray-400 transform -translate-y-1/2" />
              <Input
                placeholder="Search"
                value={searchTerm}
                onChange={(e) => handleSearchChange(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>
          {/* Action Buttons */}
          {!showFileSelectionBanner && !showKPSelectionBanner && !showCTSelectionBanner && (
            <div className="flex items-center space-x-2">
              <Button variant="outline" onClick={handleRefresh} disabled={isLoading}>
                <IconRefresh className="w-4 h-4" />
              </Button>
              <Button onClick={openExtractionPopup} variant="outline" size="lg">
                <IconUpload className="mr-2 w-4 h-4" />
                Upload File
              </Button>
              <CreateItemDropdown
                onKnowledgePackClick={handleKnowledgePackClick}
                onContributionTemplateClick={handleContributionTemplateClick}
                onCaptureKnowledgeClick={handleCaptureKnowledgeClick}
              />
            </div>
          )}
        </div>

        {/* Breadcrumb Navigation */}
        {folderState.isInFolder && (
          <div className="flex items-center space-x-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={navigateToRoot}
              className="text-gray-600 hover:text-gray-900"
            >
              <IconArrowLeft className="mr-1 w-4 h-4" />
              Back to Knowledge Center
            </Button>
          </div>
        )}

        {/* Quick Filters */}
        {!showFileSelectionBanner && !showKPSelectionBanner && !showCTSelectionBanner && (
          <div className="flex gap-2 items-center">
            <button
              onClick={() => setQuickFilter('all')}
              className={cn(
                'px-3 py-1.5 text-sm rounded-full transition-colors font-medium',
                quickFilter === 'all'
                  ? 'bg-primary text-white'
                  : 'border border-gray-200  text-gray-700 hover:bg-gray-200'
              )}
            >
              All
            </button>
            <button
              onClick={() => setQuickFilter('files')}
              className={cn(
                'px-3 py-1.5 text-sm rounded-full transition-colors font-medium',
                quickFilter === 'files'
                  ? 'bg-primary text-white'
                  : 'border border-gray-200  text-gray-700 hover:bg-gray-200'
              )}
            >
              Files
            </button>
            <button
              onClick={() => setQuickFilter('kp')}
              className={cn(
                'px-3 py-1.5 text-sm rounded-full transition-colors font-medium',
                quickFilter === 'kp'
                  ? 'bg-primary text-white'
                  : 'border border-gray-200 text-gray-700 hover:bg-gray-200'
              )}
            >
              Knowledge Packs
            </button>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="p-4 bg-red-50 rounded-lg border border-red-200">
            <p className="text-red-800">{error}</p>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                clearTopicsError();
                clearDocumentsError();
              }}
              className="mt-2"
            >
              Dismiss
            </Button>
          </div>
        )}

        {/* Data Table */}
        <div className="overflow-hidden flex-1 min-h-0">
          <LibraryTable
            data={filteredItems}
            loading={isLoading}
            mode="library"
            onRowClick={handleViewItem}
            onViewItem={handleViewItem}
            onEditItem={handleEditItem}
            onDeleteItem={handleDeleteItem}
            allLibraryItems={itemsWithCounts}
            selectionMode={
              showFileSelectionBanner
                ? 'multiple'
                : showKPSelectionBanner
                  ? 'single'
                  : showCTSelectionBanner
                    ? 'single'
                    : 'none'
            }
            selectedItems={
              showFileSelectionBanner
                ? selectedFilesForKP
                : showKPSelectionBanner && selectedKPForContribution
                  ? [selectedKPForContribution]
                  : showCTSelectionBanner && selectedCTForEK
                    ? [selectedCTForEK]
                    : []
            }
            onSelectionChange={
              showFileSelectionBanner
                ? handleFileSelectionToggle
                : showKPSelectionBanner
                  ? handleKPSelectionToggle
                  : showCTSelectionBanner
                    ? handleCTSelectionToggle
                    : undefined
            }
            filterType={
              showKPSelectionBanner
                ? 'knowledge-packs'
                : showCTSelectionBanner
                  ? 'contribution-templates'
                  : 'all'
            }
          />
        </div>

        {/* Dialogs */}
        <CreateFolderDialog
          isOpen={showCreateFolder}
          onClose={() => setShowCreateFolder(false)}
          onCreateFolder={handleCreateFolder}
          currentPath={folderState.currentPath}
        />

        {/* Edit Topic Dialog */}
        <EditTopicDialog
          topic={
            selectedItem?.type === 'folder'
              ? topics.find((t) => t.id === parseInt(selectedItem.id.replace('topic-', ''))) || null
              : null
          }
          isOpen={showEditTopic}
          onClose={() => {
            setShowEditTopic(false);
            setSelectedItem(null);
          }}
          onSave={handleEditTopic}
          isLoading={isUpdatingTopic}
        />

        {/* Edit Document Dialog */}
        <EditDocumentDialog
          document={
            selectedItem?.type === 'file'
              ? documents.find((d) => d.id === parseInt(selectedItem.id.replace('doc-', ''))) ||
                null
              : null
          }
          topics={topics}
          isOpen={showEditDocument}
          onClose={() => {
            setShowEditDocument(false);
            setSelectedItem(null);
          }}
          onSave={handleEditDocument}
          isLoading={isUpdatingDocument}
        />

        {/* Edit Template Dialog */}
        <EditTemplateDialog
          template={
            selectedItem?.type === 'file' && (selectedItem as FileItem).extension === 'template'
              ? {
                  id: (selectedItem as FileItem).metadata?.template_id,
                  name: selectedItem.name,
                }
              : null
          }
          isOpen={showEditTemplate}
          onClose={() => {
            setShowEditTemplate(false);
            setSelectedItem(null);
          }}
          onSave={handleEditTemplate}
          isLoading={false}
        />

        {/* Edit Session Dialog */}
        <EditSessionDialog
          session={
            selectedItem?.type === 'file' && (selectedItem as FileItem).extension === 'ek'
              ? {
                  id: (selectedItem as FileItem).metadata?.session_id,
                  name: selectedItem.name,
                }
              : null
          }
          isOpen={showEditSession}
          onClose={() => {
            setShowEditSession(false);
            setSelectedItem(null);
          }}
          onSave={handleEditSession}
          isLoading={false}
        />

        {/* Delete Confirmation Dialog */}
        <ConfirmDialog
          isOpen={showDeleteConfirm}
          onClose={() => {
            setShowDeleteConfirm(false);
            setSelectedItem(null);
          }}
          onConfirm={handleConfirmDelete}
          title={`Delete ${
            selectedItem?.type === 'folder'
              ? 'Topic'
              : (selectedItem as any)?.extension === 'kp'
                ? 'Knowledge Pack'
                : (selectedItem as any)?.extension === 'template'
                  ? 'Capture Template'
                  : (selectedItem as any)?.extension === 'ek'
                    ? 'Capture Knowledge Session'
                    : 'Document'
          }`}
          description={`Are you sure you want to delete "${selectedItem?.name}"? This action cannot be undone.`}
          confirmText="Delete"
          cancelText="Cancel"
          variant="destructive"
        />
        <PdfViewer
          open={pdfViewerOpen}
          onClose={() => setPdfViewerOpen(false)}
          fileUrl={pdfFileUrl || ''}
          fileName={pdfFileName}
        />

        <JsonViewer
          open={jsonViewerOpen}
          onClose={() => setJsonViewerOpen(false)}
          fileUrl={jsonFileUrl || ''}
          fileName={jsonFileName}
        />

        {/* Extraction File Popup */}
        {isExtractionPopupOpen && <ExtractionFilePopup onSaveCompleted={handleRefresh} />}

        {/* Knowledge Pack Dialog */}
        <KnowledgePackDialog />
      </div>
    </div>
  );
}
