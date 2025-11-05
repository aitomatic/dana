/* eslint-disable @typescript-eslint/no-explicit-any */
import { create } from 'zustand';
import { apiService } from '@/lib/api';
import type { KnowledgePackData, Topic } from '@/types/library';
import type { DomainKnowledgeResponse } from '@/types/domainKnowledge';
import type { KnowledgeStatusResponse } from '@/lib/api';

// Processing status enum
export type ProcessingStatus = 'idle' | 'processing' | 'success' | 'error';

export interface KnowledgePackState {
  // Dialog state
  isKnowledgePackOpen: boolean;
  isEditorOpen: boolean;

  // File selection (optional - from banner)
  selectedFiles: any[];
  selectedDocumentIds: number[];

  // Processing state
  processingStatus: ProcessingStatus;
  processingStep: string | null;

  // Extracted specialization data
  specialization: {
    domain: string;
    role: string;
    task: string;
  } | null;
  extractedText: string | null;

  // Textarea content (task-2: user-editable)
  textareaContent: string;

  // Uploaded file info
  uploadedFile: {
    name: string;
    size: number;
    type: string;
  } | null;

  // Created knowledge pack
  createdKnowledgePack: KnowledgePackData | null;

  // Topic tree for visualization (legacy/future use)
  topicTree: Topic[] | null;

  // Loading states for individual operations
  isParsingDocument: boolean;
  isParsingText: boolean;
  isCreatingPack: boolean;

  // Error state
  error: string | null;

  // Domain knowledge tree state
  domainKnowledge: DomainKnowledgeResponse | null;
  isLoadingTree: boolean;
  treeError: string | null;

  // Knowledge status state (NEW)
  knowledgeStatus: KnowledgeStatusResponse | null;
  isLoadingStatus: boolean;
  statusError: string | null;
  lastFetchedKpId: number | null; // Track which KP's status was last fetched

  // Knowledge generation state
  isGeneratingKnowledge: boolean; // Track if knowledge generation is in progress
}

export interface KnowledgePackActions {
  // Dialog controls
  setKnowledgePackOpen: (isOpen: boolean) => void;
  setEditorOpen: (isOpen: boolean) => void;

  // File selection
  setSelectedFiles: (files: any[]) => void;
  clearSelectedFiles: () => void;

  // Textarea content
  setTextareaContent: (content: string) => void;

  // Set created knowledge pack (for viewing existing packs)
  setCreatedKnowledgePack: (pack: KnowledgePackData) => void;

  // Parse document (immediate on upload)
  parseDocument: (file: File) => Promise<void>;

  // Parse text (on build button for text-only)
  parseText: (text: string) => Promise<void>;

  // Build knowledge pack (two-step process)
  buildKnowledgePack: (textContent: string, documentIds: number[]) => Promise<number | null>;

  // Tree data management (new - proper KP-specific methods)
  fetchKnowledgePackTree: (knowledgePackId: number) => Promise<void>;
  clearTreeData: () => void;

  // Knowledge status management (NEW)
  fetchKnowledgeStatus: (knowledgePackId: number, force?: boolean) => Promise<void>;
  clearKnowledgeStatus: () => void;
  updateNodeStatus: (nodePath: string, status: string) => void;

  // Knowledge generation management
  setIsGeneratingKnowledge: (isGenerating: boolean) => void;

  // Helper methods
  _extractStatusFromTree: (node: any, pathParts?: string[]) => any[];

  // Reset store
  reset: () => void;

  // Clear error
  clearError: () => void;
}

export type KnowledgePackStore = KnowledgePackState & KnowledgePackActions;

// Initial state
const initialState: KnowledgePackState = {
  isKnowledgePackOpen: false,
  isEditorOpen: false,
  selectedFiles: [],
  selectedDocumentIds: [],
  processingStatus: 'idle',
  processingStep: null,
  specialization: null,
  extractedText: null,
  textareaContent: '',
  uploadedFile: null,
  createdKnowledgePack: null,
  topicTree: null,
  isParsingDocument: false,
  isParsingText: false,
  isCreatingPack: false,
  error: null,
  domainKnowledge: null,
  isLoadingTree: false,
  treeError: null,
  knowledgeStatus: null,
  isLoadingStatus: false,
  statusError: null,
  lastFetchedKpId: null,
  isGeneratingKnowledge: false,
};

export const useKnowledgePackStore = create<KnowledgePackStore>((set, get) => ({
  ...initialState,

  // Dialog controls
  setKnowledgePackOpen: (isOpen: boolean) => {
    set({ isKnowledgePackOpen: isOpen });
    if (!isOpen) {
      // Reset on close
      get().reset();
    }
  },

  setEditorOpen: (isOpen: boolean) => {
    set({ isEditorOpen: isOpen });
  },

  // File selection
  setSelectedFiles: (files: any[]) => {
    const documentIds = files
      .map((f) => {
        // Extract numeric ID from "doc-X" format
        if (typeof f.id === 'string' && f.id.startsWith('doc-')) {
          return parseInt(f.id.replace('doc-', ''), 10);
        }
        return typeof f.id === 'number' ? f.id : null;
      })
      .filter((id): id is number => id !== null && !isNaN(id));
    set({ selectedFiles: files, selectedDocumentIds: documentIds });
  },

  clearSelectedFiles: () => {
    set({ selectedFiles: [], selectedDocumentIds: [] });
  },

  // Textarea content
  setTextareaContent: (content: string) => {
    set({ textareaContent: content });
  },

  // Set created knowledge pack (for viewing existing packs)
  setCreatedKnowledgePack: (pack: KnowledgePackData) => {
    set({ createdKnowledgePack: pack });
  },

  // Parse document - Called immediately when file is uploaded
  parseDocument: async (file: File) => {
    console.log('📄 Knowledge Pack: Parsing document...', file.name);
    set({
      isParsingDocument: true,
      processingStatus: 'processing',
      processingStep: 'Processing document...',
      error: null,
      uploadedFile: {
        name: file.name,
        size: file.size,
        type: file.type,
      },
    });

    try {
      // Call API to parse document
      const response = await apiService.parseDocumentSpecialization(file);

      if (response.success && response.specialization) {
        // Store specialization data
        set({
          specialization: response.specialization,
          extractedText: response.extracted_text,
          textareaContent: response.specialization.task, // Auto-fill textarea
          processingStatus: 'success',
          processingStep: null,
          isParsingDocument: false,
        });

        console.log('✅ Knowledge Pack: Document parsed successfully', {
          domain: response.specialization.domain,
          role: response.specialization.role,
          tasksLength: response.specialization.task.length,
        });
      } else {
        throw new Error(response.error || 'Failed to parse document');
      }
    } catch (error: any) {
      const errorMessage = error?.message || 'Failed to parse document';
      console.error('❌ Knowledge Pack: Parse document failed:', error);

      set({
        processingStatus: 'error',
        processingStep: null,
        isParsingDocument: false,
        error: errorMessage,
        uploadedFile: null,
      });

      throw error; // Re-throw for toast handling
    }
  },

  // Parse text - Called when building with text-only
  parseText: async (text: string) => {
    console.log('📝 Knowledge Pack: Parsing text...', text.substring(0, 100));
    set({
      isParsingText: true,
      processingStatus: 'processing',
      processingStep: 'Processing tasks...',
      error: null,
    });

    try {
      const response = await apiService.parseTextSpecialization(text);

      if (response.success && response.specialization) {
        set({
          specialization: response.specialization,
          extractedText: response.extracted_text,
          isParsingText: false,
        });

        console.log('✅ Knowledge Pack: Text parsed successfully', {
          domain: response.specialization.domain,
          role: response.specialization.role,
        });

        return response.specialization;
      } else {
        throw new Error(response.error || 'Failed to parse text');
      }
    } catch (error: any) {
      const errorMessage = error?.message || 'Failed to parse text';
      console.error('❌ Knowledge Pack: Parse text failed:', error);

      set({
        processingStatus: 'error',
        processingStep: null,
        isParsingText: false,
        error: errorMessage,
      });

      throw error;
    }
  },

  // Build knowledge pack - Two-step process
  buildKnowledgePack: async (textContent: string, documentIds: number[]) => {
    console.log('🏗️ Knowledge Pack: Building knowledge pack...');

    try {
      set({
        isCreatingPack: true,
        processingStatus: 'processing',
        processingStep: 'Step 1/2: Processing tasks...',
        error: null,
      });

      // Step 1: Parse text to get final structured specialization (task-3)
      const step1Response = await apiService.parseTextSpecialization(textContent);

      if (!step1Response.success || !step1Response.specialization) {
        throw new Error(step1Response.error || 'Failed to process tasks');
      }

      console.log('✅ Step 1/2: Tasks processed', step1Response.specialization);

      // Step 2: Create knowledge pack with task-3
      set({ processingStep: 'Step 2/2: Creating knowledge pack...' });

      const step2Response = await apiService.createKnowledgePack({
        specialization: step1Response.specialization,
        document_ids: documentIds,
      });

      if (!step2Response.success || !step2Response.data) {
        throw new Error(step2Response.error || 'Failed to create knowledge pack');
      }

      console.log('✅ Step 2/2: Knowledge pack created', step2Response.data);

      // Success! Store the created pack data
      set({
        createdKnowledgePack: {
          id: step2Response.data.id,
          specialization: step1Response.specialization,
          document_ids: documentIds,
          status: step2Response.data.status,
          folder_path: step2Response.data.folder_path,
          kp_metadata: step2Response.data.kp_metadata,
          // NEW: Preserve original description for auto-first message
          originalDescription: textContent,
        },
        processingStatus: 'success',
        processingStep: null,
        isCreatingPack: false,
        isKnowledgePackOpen: false, // Close creation dialog
        isEditorOpen: true, // Open editor dialog
      });

      console.log('🎉 Knowledge Pack: Build complete!');
      
      return step2Response.data.id; // Return the created knowledge pack ID
    } catch (error: any) {
      const errorMessage = error?.message || 'Failed to build knowledge pack';
      console.error('❌ Knowledge Pack: Build failed:', error);

      set({
        processingStatus: 'error',
        processingStep: null,
        isCreatingPack: false,
        error: errorMessage,
      });

      throw error;
    }
  },

  // Helper to extract status from tree nodes recursively
  _extractStatusFromTree: (node: any, pathParts: string[] = []): any[] => {
    const topics: any[] = [];
    const currentPath = [...pathParts, node.topic];
    
    // Only add status for leaf nodes (nodes without children)
    const isLeaf = !node.children || node.children.length === 0;
    if (isLeaf && node.status) {
      // Build path without root (matching the format used elsewhere)
      const nodePath = currentPath.slice(1).join(' - ');
      topics.push({
        id: nodePath.replace(/\s+/g, '_').toLowerCase(),
        path: nodePath,
        status: node.status as 'draft' | 'pending' | 'generating' | 'in_progress' | 'question_generated' | 'completed' | 'success' | 'failed',
        last_generated: null,
        error: null,
        file: '',
        last_topic_update: new Date().toISOString(),
      });
    }
    
    // Recursively process children
    if (node.children && node.children.length > 0) {
      for (const child of node.children) {
        topics.push(...get()._extractStatusFromTree(child, currentPath));
      }
    }
    
    return topics;
  },

  // Fetch knowledge pack tree data (new - proper KP-specific method)
  fetchKnowledgePackTree: async (knowledgePackId: number) => {
    console.log('📡 [STORE] fetchKnowledgePackTree called for ID:', knowledgePackId);
    set({ isLoadingTree: true, treeError: null });

    try {
      console.log('🌐 [STORE] Fetching from API...');
      const response = await apiService.getKnowledgePack(knowledgePackId);

      if (response.success && response.data) {
        // Handle both new format (response.data.tree) and legacy format (response.data directly)
        const treeData = response.data.tree || response.data;
        console.log('📦 [STORE] Received tree data with root:', treeData.root?.topic);
        
        // Extract status from tree nodes
        const topics = treeData.root ? get()._extractStatusFromTree(treeData.root) : [];
        console.log('📊 [STORE] Extracted', topics.length, 'topic statuses from tree');
        
        console.log('💾 [STORE] Updating store with new tree data - this will trigger domainTree useEffect');
        set({
          domainKnowledge: treeData,
          knowledgeStatus: { topics }, // Set status immediately from tree
          isLoadingTree: false,
          treeError: null,
          lastFetchedKpId: knowledgePackId,
        });
        console.log('✅ [STORE] Store updated with new tree data');
      } else {
        throw new Error(response.error || 'Failed to load knowledge pack tree');
      }
    } catch (error: any) {
      const errorMessage = error?.message || 'Failed to load knowledge pack tree';
      console.error('❌ [STORE] Failed to fetch tree:', error);
      set({
        isLoadingTree: false,
        treeError: errorMessage,
      });
      throw error;
    }
  },

  // Clear tree data
  clearTreeData: () => {
    console.log('🗑️ Knowledge Pack: Clearing tree data');
    set({
      domainKnowledge: null,
      isLoadingTree: false,
      treeError: null,
    });
  },

  // Fetch knowledge status (NEW)
  fetchKnowledgeStatus: async (knowledgePackId: number, force: boolean = false) => {
    const state = get();

    // Prevent duplicate calls: skip if already loading or already fetched for this KP
    if (!force && state.isLoadingStatus) {
      console.log('⏭️ Knowledge Pack: Skipping status fetch (already loading)');
      return;
    }

    if (!force && state.lastFetchedKpId === knowledgePackId && state.knowledgeStatus) {
      console.log('⏭️ Knowledge Pack: Skipping status fetch (already have data for this KP)');
      return;
    }

    console.log('📊 Knowledge Pack: Fetching knowledge status for ID:', knowledgePackId);
    set({ isLoadingStatus: true, statusError: null });

    try {
      const response = await apiService.getKnowledgePackStatus(knowledgePackId);
      console.log('✅ Knowledge Pack: Knowledge status loaded successfully');
      set({
        knowledgeStatus: response,
        isLoadingStatus: false,
        statusError: null,
        lastFetchedKpId: knowledgePackId,
      });
    } catch (error: any) {
      const errorMessage = error?.message || 'Failed to load knowledge status';
      console.error('❌ Knowledge Pack: Failed to fetch knowledge status:', error);
      set({
        knowledgeStatus: { topics: [] }, // Set empty status on error
        isLoadingStatus: false,
        statusError: errorMessage,
        lastFetchedKpId: knowledgePackId, // Mark as attempted even on error
      });
    }
  },

  // Clear knowledge status (NEW)
  clearKnowledgeStatus: () => {
    console.log('🗑️ Knowledge Pack: Clearing knowledge status');
    set({
      knowledgeStatus: null,
      isLoadingStatus: false,
      statusError: null,
      lastFetchedKpId: null,
    });
  },

  // Update individual node status (for WebSocket updates)
  updateNodeStatus: (nodePath: string, status: string) => {
    const currentStatus = get().knowledgeStatus;
    
    console.log('🔄 Knowledge Pack: Updating node status:', { nodePath, status, hasCurrentStatus: !!currentStatus });

    // If no knowledge status loaded yet, create initial structure with this topic
    if (!currentStatus) {
      console.log('⚠️ Knowledge Pack: No knowledge status loaded, creating initial structure');
      set({
        knowledgeStatus: {
          topics: [{
            id: nodePath.replace(/\s+/g, '_').toLowerCase(),
            path: nodePath,
            status: status as 'draft' | 'pending' | 'generating' | 'in_progress' | 'question_generated' | 'completed' | 'success' | 'failed',
            last_generated: null,
            error: null,
            file: '',
            last_topic_update: new Date().toISOString(),
          }],
        },
      });
      console.log('✅ Knowledge Pack: Initial node status created');
      return;
    }

    // Find the topic index
    const topicIndex = currentStatus.topics.findIndex((topic: any) => topic.path === nodePath);

    let updatedTopics;
    if (topicIndex >= 0) {
      // Update existing topic
      updatedTopics = currentStatus.topics.map((topic: any, index: number) =>
        index === topicIndex ? { ...topic, status } : topic
      );
      console.log('✅ Knowledge Pack: Node status updated successfully');
    } else {
      // Topic not found, add it to the list
      console.log('⚠️ Knowledge Pack: Topic not found, adding new topic for path:', nodePath);
      updatedTopics = [
        ...currentStatus.topics,
        {
          id: nodePath.replace(/\s+/g, '_').toLowerCase(),
          path: nodePath,
          status: status as 'draft' | 'pending' | 'generating' | 'in_progress' | 'question_generated' | 'completed' | 'success' | 'failed',
          last_generated: null,
          error: null,
          file: '',
          last_topic_update: new Date().toISOString(),
        },
      ];
      console.log('✅ Knowledge Pack: New topic added');
    }

    set({
      knowledgeStatus: {
        ...currentStatus,
        topics: updatedTopics,
      },
    });
  },

  // Set knowledge generation status
  setIsGeneratingKnowledge: (isGenerating: boolean) => {
    console.log('🔄 Knowledge Pack: Setting isGeneratingKnowledge to', isGenerating);
    set({ isGeneratingKnowledge: isGenerating });
  },

  // Reset store
  reset: () => {
    console.log('🔄 Knowledge Pack: Resetting store');
    set(initialState);
  },

  // Clear error
  clearError: () => {
    set({ error: null });
  },
}));
