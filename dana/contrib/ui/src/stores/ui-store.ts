import { create } from "zustand";

export interface UIState {
  // Dialog States
  isCreateAgentDialogOpen: boolean;
  isSettingsDialogOpen: boolean;
  isHelpDialogOpen: boolean;

  // Navigation
  currentPage: string;
  sidebarCollapsed: boolean;

  // Theme & Appearance
  theme: "light" | "dark" | "system";
  sidebarWidth: number;

  // Notifications
  notifications: Array<{
    id: string;
    type: "success" | "error" | "warning" | "info";
    title: string;
    message: string;
    duration?: number;
  }>;

  // Actions
  // Dialog Actions
  openCreateAgentDialog: () => void;
  closeCreateAgentDialog: () => void;
  openSettingsDialog: () => void;
  closeSettingsDialog: () => void;
  openHelpDialog: () => void;
  closeHelpDialog: () => void;

  // Navigation Actions
  setCurrentPage: (page: string) => void;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;

  // Theme Actions
  setTheme: (theme: "light" | "dark" | "system") => void;
  setSidebarWidth: (width: number) => void;

  // Notification Actions
  addNotification: (
    notification: Omit<UIState["notifications"][0], "id">,
  ) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;

  // Reset
  reset: () => void;
}

export const useUIStore = create<UIState>((set, get) => ({
  // Initial State
  isCreateAgentDialogOpen: false,
  isSettingsDialogOpen: false,
  isHelpDialogOpen: false,
  currentPage: "dashboard",
  sidebarCollapsed: false,
  theme: "system",
  sidebarWidth: 280,
  notifications: [],

  // Dialog Actions
  openCreateAgentDialog: () => set({ isCreateAgentDialogOpen: true }),
  closeCreateAgentDialog: () => set({ isCreateAgentDialogOpen: false }),
  openSettingsDialog: () => set({ isSettingsDialogOpen: true }),
  closeSettingsDialog: () => set({ isSettingsDialogOpen: false }),
  openHelpDialog: () => set({ isHelpDialogOpen: true }),
  closeHelpDialog: () => set({ isHelpDialogOpen: false }),

  // Navigation Actions
  setCurrentPage: (page: string) => set({ currentPage: page }),
  toggleSidebar: () =>
    set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
  setSidebarCollapsed: (collapsed: boolean) =>
    set({ sidebarCollapsed: collapsed }),

  // Theme Actions
  setTheme: (theme: "light" | "dark" | "system") => set({ theme }),
  setSidebarWidth: (width: number) => set({ sidebarWidth: width }),

  // Notification Actions
  addNotification: (notification) => {
    const id = Math.random().toString(36).substr(2, 9);
    const newNotification = { ...notification, id };

    set((state) => ({
      notifications: [...state.notifications, newNotification],
    }));

    // Auto-remove notification after duration (default: 5000ms)
    const duration = notification.duration || 5000;
    if (duration > 0) {
      setTimeout(() => {
        get().removeNotification(id);
      }, duration);
    }
  },

  removeNotification: (id: string) => {
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    }));
  },

  clearNotifications: () => set({ notifications: [] }),

  // Reset
  reset: () => {
    set({
      isCreateAgentDialogOpen: false,
      isSettingsDialogOpen: false,
      isHelpDialogOpen: false,
      currentPage: "dashboard",
      sidebarCollapsed: false,
      theme: "system",
      sidebarWidth: 280,
      notifications: [],
    });
  },
}));
