/* eslint-disable @typescript-eslint/no-explicit-any */
import { create } from 'zustand';
import { apiService } from '@/lib/api';
import type {
  InterviewTemplateRead,
  InterviewTemplateResponse,
  TemplateChatMessage,
  TemplateFinetuneChannelResponse,
} from '@/types/library';

export type EditorMode = 'interview' | 'preview';

export interface ContributionState {
  // Template data
  currentTemplate: InterviewTemplateRead | null;
  isCreatingTemplate: boolean;

  // Knowledge structure (from KP) - kept for potential future use
  domainKnowledge: any | null;
  isLoadingStructure: boolean;

  // Loading state for conversation
  isLoadingConversation: boolean;

  // Editor state
  editorMode: EditorMode;
  isSendingMessage: boolean;

  // Animation state
  isAnimatingTemplate: boolean;
  templateDiff: any | null;
  previousContent: string | null;

  // Auto-save state
  hasUnsavedChanges: boolean;
  lastSavedTime: Date | null;
  isSaving: boolean;
  saveError: string | null;

  // Error handling
  error: string | null;
}

export interface ContributionActions {
  // Template Management
  createTemplate: (kpId: number, kpData?: { domain: string; role: string }) => Promise<InterviewTemplateRead | null>;
  openTemplate: (templateId: number) => Promise<void>;
  closeTemplate: () => void;
  deleteTemplate: (templateId: number) => Promise<void>;
  duplicateCurrentTemplate: () => Promise<void>;

  // Interview Chat
  sendMessage: (message: string) => Promise<{
    response: string;
    templateModified: boolean;
    templateDiff?: any;
  } | null>;
  loadConversation: (templateId: number) => Promise<TemplateChatMessage[]>;
  refreshTemplate: () => Promise<void>;

  // Editor Controls
  setEditorMode: (mode: EditorMode) => void;

  // Animation Controls
  setAnimatingTemplate: (isAnimating: boolean) => void;
  setTemplateDiff: (diff: any | null) => void;

  // Save Operations
  saveTemplate: () => Promise<void>;
  markUnsavedChanges: (hasChanges: boolean) => void;
  markTemplateAsCompleted: () => Promise<void>;

  // Structure Loading (kept for potential future use)
  loadTemplateStructure: (kpId: number) => Promise<void>;

  // Utility
  reset: () => void;
  clearError: () => void;
}

export type ContributionStore = ContributionState & ContributionActions;

// Initial state
const initialState: ContributionState = {
  currentTemplate: null,
  isCreatingTemplate: false,
  domainKnowledge: null,
  isLoadingStructure: false,
  isLoadingConversation: false,
  editorMode: 'interview',
  isSendingMessage: false,
  isAnimatingTemplate: false,
  templateDiff: null,
  previousContent: null,
  hasUnsavedChanges: false,
  lastSavedTime: null,
  isSaving: false,
  saveError: null,
  error: null,
};

export const useContributionStore = create<ContributionStore>((set, get) => ({
  ...initialState,

  // ========================================
  // Template Management
  // ========================================

  createTemplate: async (kpId: number, kpData?: { domain: string; role: string }) => {
    console.log('🎯 Contribution: Creating interview template for KP:', kpId);
    set({ isCreatingTemplate: true, error: null });

    try {
      const templateName = kpData
        ? `${kpData.domain} - ${kpData.role} Interview`
        : `Knowledge Pack ${kpId} Interview`;

      const response: InterviewTemplateResponse = await apiService.createInterviewTemplate(kpId, {
        name: templateName,
        description: 'Expert interview template for knowledge contribution',
        template_metadata: {
          domain: kpData?.domain || '',
          role: kpData?.role || '',
          status: 'pending',
        },
      });

      if (response.success && response.data) {
        console.log('✅ Contribution: Template created:', response.data.id);

        set({
          currentTemplate: response.data,
          isCreatingTemplate: false,
        });

        // Return the created template data
        return response.data;
      } else {
        throw new Error(response.error || 'Failed to create template');
      }
    } catch (error: any) {
      const errorMessage = error?.message || 'Failed to create template';
      console.error('❌ Contribution: Template creation failed:', error);

      set({
        isCreatingTemplate: false,
        error: errorMessage,
      });

      throw error;
      return null; // Won't reach here but TypeScript needs it
    }
  },

  openTemplate: async (templateId: number) => {
    console.log('📂 Contribution: Opening template:', templateId);
    set({ isCreatingTemplate: true, error: null });

    try {
      const response: InterviewTemplateResponse = await apiService.getInterviewTemplate(templateId);

      if (response.success && response.data) {
        console.log('✅ Contribution: Template loaded:', response.data);

        set({
          currentTemplate: response.data,
          isCreatingTemplate: false,
        });

        // Load conversation history (KP structure not needed anymore)
        await get().loadConversation(templateId);
      } else {
        throw new Error(response.error || 'Failed to load template');
      }
    } catch (error: any) {
      const errorMessage = error?.message || 'Failed to load template';
      console.error('❌ Contribution: Template load failed:', error);

      set({
        isCreatingTemplate: false,
        error: errorMessage,
      });

      throw error;
    }
  },

  closeTemplate: () => {
    const { hasUnsavedChanges } = get();

    if (hasUnsavedChanges) {
      // Caller should show confirmation dialog
      console.warn('⚠️ Contribution: Unsaved changes detected');
      return;
    }

    console.log('🔒 Contribution: Closing template');
    get().reset();
  },

  deleteTemplate: async (templateId: number) => {
    console.log('🗑️ Contribution: Deleting template:', templateId);

    try {
      const response = await apiService.deleteInterviewTemplate(templateId);

      if (response.success) {
        console.log('✅ Contribution: Template deleted');
        get().reset();
      } else {
        throw new Error(response.error || 'Failed to delete template');
      }
    } catch (error: any) {
      const errorMessage = error?.message || 'Failed to delete template';
      console.error('❌ Contribution: Template deletion failed:', error);
      set({ error: errorMessage });
      throw error;
    }
  },

  duplicateCurrentTemplate: async () => {
    const { currentTemplate } = get();

    if (!currentTemplate) {
      console.error('❌ Contribution: No template to duplicate');
      throw new Error('No template selected');
    }

    console.log('📋 Contribution: Duplicating template:', currentTemplate.id);
    set({ isCreatingTemplate: true, error: null });

    try {
      const templateName = currentTemplate.name
        ? `${currentTemplate.name} (Copy)`
        : 'Interview Template (Copy)';

      const response: InterviewTemplateResponse = await apiService.duplicateInterviewTemplate(
        currentTemplate.id,
        currentTemplate.kp_id,
        {
          name: templateName,
          description: currentTemplate.description || 'Duplicated interview template',
          template_metadata: {
            ...currentTemplate.template_metadata,
            domain: currentTemplate.template_metadata?.domain || '',
            role: currentTemplate.template_metadata?.role || '',
            status: 'draft',
          },
        },
      );

      if (response.success && response.data) {
        console.log('✅ Contribution: Template duplicated:', response.data.id);

        // Switch to the new duplicated template
        set({
          currentTemplate: response.data,
          isCreatingTemplate: false,
        });
      } else {
        throw new Error(response.error || 'Failed to duplicate template');
      }
    } catch (error: any) {
      const errorMessage = error?.message || 'Failed to duplicate template';
      console.error('❌ Contribution: Template duplication failed:', error);

      set({
        isCreatingTemplate: false,
        error: errorMessage,
      });

      throw error;
    }
  },

  // ========================================
  // Interview Chat
  // ========================================

  sendMessage: async (message: string) => {
    const { currentTemplate } = get();

    if (!currentTemplate) {
      console.error('❌ Contribution: No template selected');
      return null;
    }

    console.log('💬 Contribution: Sending message...', message.substring(0, 50));
    
    // Store previous content for diff tracking
    const previousContent = currentTemplate.readme_content || '';
    
    set({ isSendingMessage: true, error: null, previousContent });

    try {
      const response: TemplateFinetuneChannelResponse = await apiService.chatWithTemplate(
        currentTemplate.id,
        message,
      );

      if (response.success) {
        console.log('✅ Contribution: Message sent, response received');

        // If template was modified, handle refresh based on whether we have a diff
        if (response.template_modified) {
          if (response.template_diff) {
            // Have diff - don't refresh yet, let animation play
            console.log('📊 Contribution: Template diff received, skipping refresh for animation');
            set({ templateDiff: response.template_diff });
          } else {
            // No diff - refresh immediately to get new content
            console.log('🔄 Contribution: Template modified (no diff), refreshing...');
            await get().refreshTemplate();
          }
        }

        set({
          isSendingMessage: false,
          hasUnsavedChanges: true, // Mark as changed
          lastSavedTime: new Date(), // Conversation auto-saved by backend
        });

        return {
          response: response.agent_response,
          templateModified: response.template_modified,
          templateDiff: response.template_diff,
        };
      } else {
        throw new Error(response.error || 'Failed to send message');
      }
    } catch (error: any) {
      const errorMessage = error?.message || 'Failed to send message';
      console.error('❌ Contribution: Send message failed:', error);

      set({
        isSendingMessage: false,
        error: errorMessage,
      });

      throw error;
    }
  },

  loadConversation: async (templateId: number) => {
    console.log('📜 Contribution: Loading conversation for template:', templateId);
    set({ isLoadingConversation: true, error: null });

    try {
      const conversation = await apiService.getTemplateConversation(templateId);

      // Backend returns ConversationWithMessages directly (not wrapped in {success, data})
      if (conversation && conversation.messages) {
        console.log(
          '✅ Contribution: Conversation loaded with',
          conversation.messages.length,
          'messages',
        );

        // Convert messages to our format
        const messages: TemplateChatMessage[] = conversation.messages.map((msg: any) => ({
          sender: msg.sender,
          content: msg.content,
          metadata: msg.metadata || {},
        }));

        set({ isLoadingConversation: false });
        return messages;
      } else {
        // No conversation yet - that's okay
        console.log('ℹ️ Contribution: No conversation history');
        set({ isLoadingConversation: false });
        return [];
      }
    } catch (error: any) {
      console.warn('⚠️ Contribution: Failed to load conversation (non-critical):', error);
      set({ isLoadingConversation: false });
      return [];
    }
  },

  refreshTemplate: async () => {
    const { currentTemplate } = get();

    if (!currentTemplate) {
      console.error('❌ Contribution: No template to refresh');
      return;
    }

    console.log('🔄 Contribution: Refreshing template:', currentTemplate.id);

    try {
      const response: InterviewTemplateResponse = await apiService.getInterviewTemplate(
        currentTemplate.id,
      );

      if (response.success && response.data) {
        console.log('✅ Contribution: Template refreshed with updated content');
        set({
          currentTemplate: response.data,
        });
      } else {
        throw new Error(response.error || 'Failed to refresh template');
      }
    } catch (error: any) {
      console.error('❌ Contribution: Template refresh failed:', error);
      // Don't throw - this is a background operation
    }
  },

  // ========================================
  // Editor Controls
  // ========================================

  setEditorMode: (mode: EditorMode) => {
    console.log('🎨 Contribution: Setting editor mode:', mode);
    set({ editorMode: mode });
  },

  // ========================================
  // Animation Controls
  // ========================================

  setAnimatingTemplate: (isAnimating: boolean) => {
    set({ isAnimatingTemplate: isAnimating });
  },

  setTemplateDiff: (diff: any | null) => {
    set({ templateDiff: diff });
  },

  // ========================================
  // Save Operations
  // ========================================

  saveTemplate: async () => {
    const { currentTemplate } = get();

    if (!currentTemplate) {
      console.error('❌ Contribution: No template to save');
      return;
    }

    console.log('💾 Contribution: Saving template...');
    set({ isSaving: true, saveError: null });

    try {
      const response = await apiService.updateInterviewTemplate(currentTemplate.id, {
        template_metadata: {
          ...currentTemplate.template_metadata,
          last_saved: new Date().toISOString(),
        },
      });

      if (response.success) {
        console.log('✅ Contribution: Template saved');

        set({
          isSaving: false,
          hasUnsavedChanges: false,
          lastSavedTime: new Date(),
          saveError: null,
        });
      } else {
        throw new Error(response.error || 'Failed to save template');
      }
    } catch (error: any) {
      const errorMessage = error?.message || 'Failed to save template';
      console.error('❌ Contribution: Save failed:', error);

      set({
        isSaving: false,
        saveError: errorMessage,
      });

      throw error;
    }
  },

  markUnsavedChanges: (hasChanges: boolean) => {
    set({ hasUnsavedChanges: hasChanges });
  },

  markTemplateAsCompleted: async () => {
    const { currentTemplate } = get();

    if (!currentTemplate) {
      console.error('❌ Contribution: No template to mark as completed');
      return;
    }

    // Don't allow marking master templates as completed (they're read-only)
    if (currentTemplate.is_master) {
      console.warn('⚠️ Contribution: Cannot mark master template as completed');
      return;
    }

    // Don't allow if already completed
    if (currentTemplate.template_metadata?.status === 'completed') {
      console.warn('⚠️ Contribution: Template is already completed');
      return;
    }

    console.log('✅ Contribution: Marking template as completed...');
    set({ isSaving: true, saveError: null });

    try {
      const response = await apiService.updateInterviewTemplate(currentTemplate.id, {
        template_metadata: {
          ...currentTemplate.template_metadata,
          status: 'completed',
        },
      });

      if (response.success && response.data) {
        console.log('✅ Contribution: Template marked as completed');

        set({
          currentTemplate: {
            ...currentTemplate,
            ...response.data,
            readme_content: currentTemplate.readme_content, // Preserve readme_content
          },
          isSaving: false,
          hasUnsavedChanges: false,
          lastSavedTime: new Date(),
          saveError: null,
        });
      } else {
        throw new Error(response.error || 'Failed to mark template as completed');
      }
    } catch (error: any) {
      const errorMessage = error?.message || 'Failed to mark template as completed';
      console.error('❌ Contribution: Mark as completed failed:', error);

      set({
        isSaving: false,
        saveError: errorMessage,
      });

      throw error;
    }
  },

  // ========================================
  // Structure Loading
  // ========================================

  loadTemplateStructure: async (kpId: number) => {
    console.log('🌳 Contribution: Loading KP structure for:', kpId);
    set({ isLoadingStructure: true, error: null });

    try {
      const response = await apiService.getKnowledgePack(kpId);

      if (response.success && response.data) {
        console.log('✅ Contribution: Structure loaded');

        set({
          domainKnowledge: response.data,
          isLoadingStructure: false,
        });
      } else {
        throw new Error(response.error || 'Failed to load structure');
      }
    } catch (error: any) {
      const errorMessage = error?.message || 'Failed to load structure';
      console.error('❌ Contribution: Structure load failed:', error);

      set({
        isLoadingStructure: false,
        error: errorMessage,
      });

      throw error;
    }
  },

  // ========================================
  // Utility
  // ========================================

  reset: () => {
    console.log('🔄 Contribution: Resetting store');
    set(initialState);
  },

  clearError: () => {
    set({ error: null, saveError: null });
  },
}));
