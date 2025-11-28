/* eslint-disable @typescript-eslint/no-explicit-any */
import { create } from 'zustand';
import { apiService } from '@/lib/api';
import type {
  InterviewSessionRead,
  InterviewTemplateRead,
  InterviewSessionUpdate,
  InterviewSessionStatus,
} from '@/types/library';
import { toast } from 'sonner';

interface CaptureKnowledgeState {
  // Session data
  currentSession: InterviewSessionRead | null;
  isLoadingSession: boolean;
  sessionError: string | null;

  // CT data (for summary panel)
  contributionTemplate: InterviewTemplateRead | null;
  isLoadingTemplate: boolean;
  templateError: string | null;

  // Actions
  loadSession: (sessionId: number) => Promise<void>;
  loadTemplate: (templateId: number) => Promise<void>;
  updateSessionStatus: (sessionId: number, status: InterviewSessionStatus) => Promise<void>;
  updateSession: (sessionId: number, updates: InterviewSessionUpdate, options?: { silent?: boolean }) => Promise<void>;
  reset: () => void;
}

export const useCaptureKnowledgeStore = create<CaptureKnowledgeState>((set, get) => ({
  // Initial state
  currentSession: null,
  isLoadingSession: false,
  sessionError: null,
  contributionTemplate: null,
  isLoadingTemplate: false,
  templateError: null,

  // Load session data
  loadSession: async (sessionId: number) => {
    set({ isLoadingSession: true, sessionError: null });
    try {
      const response = await apiService.getInterviewSession(sessionId);
      if (response.success && response.data) {
        set({ currentSession: response.data, isLoadingSession: false });

        // Auto-load template if we have template_id
        if (response.data.interview_template_id) {
          get().loadTemplate(response.data.interview_template_id);
        }
      } else {
        const errorMsg = response.error || response.message || 'Failed to load session';
        set({ sessionError: errorMsg, isLoadingSession: false });
        toast.error(errorMsg);
      }
    } catch (error: any) {
      const errorMsg = error?.message || 'Failed to load session';
      set({ sessionError: errorMsg, isLoadingSession: false });
      toast.error(errorMsg);
    }
  },

  // Load capture template data
  loadTemplate: async (templateId: number) => {
    set({ isLoadingTemplate: true, templateError: null });
    try {
      const response = await apiService.getInterviewTemplate(templateId);
      if (response.success && response.data) {
        set({ contributionTemplate: response.data, isLoadingTemplate: false });
      } else {
        const errorMsg = response.error || response.message || 'Failed to load template';
        set({ templateError: errorMsg, isLoadingTemplate: false });
        toast.error(errorMsg);
      }
    } catch (error: any) {
      const errorMsg = error?.message || 'Failed to load template';
      set({ templateError: errorMsg, isLoadingTemplate: false });
      toast.error(errorMsg);
    }
  },

  // Update session status
  updateSessionStatus: async (sessionId: number, status: InterviewSessionStatus) => {
    try {
      const response = await apiService.updateInterviewSession(sessionId, { status });
      if (response.success && response.data) {
        set({ currentSession: response.data });
        toast.success(`Session status updated to ${status}`);
      } else {
        const errorMsg = response.error || response.message || 'Failed to update status';
        toast.error(errorMsg);
      }
    } catch (error: any) {
      const errorMsg = error?.message || 'Failed to update status';
      toast.error(errorMsg);
    }
  },

  // Update session with multiple fields
  updateSession: async (sessionId: number, updates: InterviewSessionUpdate, options?: { silent?: boolean }) => {
    const { silent = false } = options || {};
    try {
      const response = await apiService.updateInterviewSession(sessionId, updates);
      if (response.success && response.data) {
        set({ currentSession: response.data });
        if (!silent) {
          toast.success('Session updated successfully');
        }
      } else {
        const errorMsg = response.error || response.message || 'Failed to update session';
        toast.error(errorMsg);
      }
    } catch (error: any) {
      const errorMsg = error?.message || 'Failed to update session';
      toast.error(errorMsg);
    }
  },

  // Reset store
  reset: () => {
    set({
      currentSession: null,
      isLoadingSession: false,
      sessionError: null,
      contributionTemplate: null,
      isLoadingTemplate: false,
      templateError: null,
    });
  },
}));
