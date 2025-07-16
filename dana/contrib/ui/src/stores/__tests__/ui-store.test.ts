import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useUIStore } from '../ui-store';

describe('UI Store', () => {
  beforeEach(() => {
    // Reset the store before each test
    useUIStore.getState().reset();
  });

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const state = useUIStore.getState();

      expect(state.isCreateAgentDialogOpen).toBe(false);
      expect(state.isSettingsDialogOpen).toBe(false);
      expect(state.isHelpDialogOpen).toBe(false);
      expect(state.currentPage).toBe('dashboard');
      expect(state.sidebarCollapsed).toBe(false);
      expect(state.theme).toBe('system');
      expect(state.sidebarWidth).toBe(280);
      expect(state.notifications).toEqual([]);
    });
  });

  describe('Dialog Actions', () => {
    it('should open and close create agent dialog', () => {
      const { result } = renderHook(() => useUIStore());

      expect(result.current.isCreateAgentDialogOpen).toBe(false);

      act(() => {
        result.current.openCreateAgentDialog();
      });

      expect(result.current.isCreateAgentDialogOpen).toBe(true);

      act(() => {
        result.current.closeCreateAgentDialog();
      });

      expect(result.current.isCreateAgentDialogOpen).toBe(false);
    });

    it('should open and close settings dialog', () => {
      const { result } = renderHook(() => useUIStore());

      expect(result.current.isSettingsDialogOpen).toBe(false);

      act(() => {
        result.current.openSettingsDialog();
      });

      expect(result.current.isSettingsDialogOpen).toBe(true);

      act(() => {
        result.current.closeSettingsDialog();
      });

      expect(result.current.isSettingsDialogOpen).toBe(false);
    });

    it('should open and close help dialog', () => {
      const { result } = renderHook(() => useUIStore());

      expect(result.current.isHelpDialogOpen).toBe(false);

      act(() => {
        result.current.openHelpDialog();
      });

      expect(result.current.isHelpDialogOpen).toBe(true);

      act(() => {
        result.current.closeHelpDialog();
      });

      expect(result.current.isHelpDialogOpen).toBe(false);
    });
  });

  describe('Navigation Actions', () => {
    it('should set current page', () => {
      const { result } = renderHook(() => useUIStore());

      expect(result.current.currentPage).toBe('dashboard');

      act(() => {
        result.current.setCurrentPage('agents');
      });

      expect(result.current.currentPage).toBe('agents');
    });

    it('should toggle sidebar', () => {
      const { result } = renderHook(() => useUIStore());

      expect(result.current.sidebarCollapsed).toBe(false);

      act(() => {
        result.current.toggleSidebar();
      });

      expect(result.current.sidebarCollapsed).toBe(true);

      act(() => {
        result.current.toggleSidebar();
      });

      expect(result.current.sidebarCollapsed).toBe(false);
    });

    it('should set sidebar collapsed state', () => {
      const { result } = renderHook(() => useUIStore());

      expect(result.current.sidebarCollapsed).toBe(false);

      act(() => {
        result.current.setSidebarCollapsed(true);
      });

      expect(result.current.sidebarCollapsed).toBe(true);

      act(() => {
        result.current.setSidebarCollapsed(false);
      });

      expect(result.current.sidebarCollapsed).toBe(false);
    });
  });

  describe('Theme Actions', () => {
    it('should set theme', () => {
      const { result } = renderHook(() => useUIStore());

      expect(result.current.theme).toBe('system');

      act(() => {
        result.current.setTheme('light');
      });

      expect(result.current.theme).toBe('light');

      act(() => {
        result.current.setTheme('dark');
      });

      expect(result.current.theme).toBe('dark');
    });

    it('should set sidebar width', () => {
      const { result } = renderHook(() => useUIStore());

      expect(result.current.sidebarWidth).toBe(280);

      act(() => {
        result.current.setSidebarWidth(320);
      });

      expect(result.current.sidebarWidth).toBe(320);
    });
  });

  describe('Notification Actions', () => {
    it('should add notification', () => {
      const { result } = renderHook(() => useUIStore());

      expect(result.current.notifications).toEqual([]);

      act(() => {
        result.current.addNotification({
          type: 'success',
          title: 'Success',
          message: 'Operation completed successfully',
        });
      });

      expect(result.current.notifications).toHaveLength(1);
      expect(result.current.notifications[0]).toMatchObject({
        type: 'success',
        title: 'Success',
        message: 'Operation completed successfully',
      });
      expect(result.current.notifications[0].id).toBeDefined();
    });

    it('should add notification with custom duration', () => {
      const { result } = renderHook(() => useUIStore());

      act(() => {
        result.current.addNotification({
          type: 'info',
          title: 'Info',
          message: 'Information message',
          duration: 10000,
        });
      });

      expect(result.current.notifications[0].duration).toBe(10000);
    });

    it('should add notification with zero duration (no auto-remove)', () => {
      const { result } = renderHook(() => useUIStore());

      act(() => {
        result.current.addNotification({
          type: 'warning',
          title: 'Warning',
          message: 'Warning message',
          duration: 0,
        });
      });

      expect(result.current.notifications[0].duration).toBe(0);
    });

    it('should remove notification by id', () => {
      const { result } = renderHook(() => useUIStore());

      act(() => {
        result.current.addNotification({
          type: 'success',
          title: 'Success',
          message: 'Operation completed successfully',
        });
      });

      expect(result.current.notifications).toHaveLength(1);
      const notificationId = result.current.notifications[0].id;

      act(() => {
        result.current.removeNotification(notificationId);
      });

      expect(result.current.notifications).toEqual([]);
    });

    it('should clear all notifications', () => {
      const { result } = renderHook(() => useUIStore());

      act(() => {
        result.current.addNotification({
          type: 'success',
          title: 'Success 1',
          message: 'First notification',
        });
        result.current.addNotification({
          type: 'error',
          title: 'Error',
          message: 'Second notification',
        });
      });

      expect(result.current.notifications).toHaveLength(2);

      act(() => {
        result.current.clearNotifications();
      });

      expect(result.current.notifications).toEqual([]);
    });

    it('should handle multiple notifications', () => {
      const { result } = renderHook(() => useUIStore());

      act(() => {
        result.current.addNotification({
          type: 'success',
          title: 'Success',
          message: 'Success message',
        });
        result.current.addNotification({
          type: 'error',
          title: 'Error',
          message: 'Error message',
        });
        result.current.addNotification({
          type: 'warning',
          title: 'Warning',
          message: 'Warning message',
        });
        result.current.addNotification({
          type: 'info',
          title: 'Info',
          message: 'Info message',
        });
      });

      expect(result.current.notifications).toHaveLength(4);
      expect(result.current.notifications.map((n) => n.type)).toEqual([
        'success',
        'error',
        'warning',
        'info',
      ]);
    });

    it('should generate unique ids for notifications', () => {
      const { result } = renderHook(() => useUIStore());

      act(() => {
        result.current.addNotification({
          type: 'success',
          title: 'Success 1',
          message: 'First notification',
        });
        result.current.addNotification({
          type: 'success',
          title: 'Success 2',
          message: 'Second notification',
        });
      });

      expect(result.current.notifications).toHaveLength(2);
      expect(result.current.notifications[0].id).not.toBe(result.current.notifications[1].id);
    });
  });

  describe('Auto-remove Notifications', () => {
    it('should auto-remove notification after duration', async () => {
      vi.useFakeTimers();
      useUIStore.getState().addNotification({
        type: 'success',
        title: 'Success',
        message: 'Will be removed',
        duration: 1000,
      });
      expect(useUIStore.getState().notifications).toHaveLength(1);
      vi.advanceTimersByTime(1000);
      expect(useUIStore.getState().notifications).toEqual([]);
      vi.useRealTimers();
    });
    it('should not auto-remove notification with zero duration', async () => {
      vi.useFakeTimers();
      useUIStore.getState().addNotification({
        type: 'error',
        title: 'Error',
        message: 'Will not be removed',
        duration: 0,
      });
      expect(useUIStore.getState().notifications).toHaveLength(1);
      vi.advanceTimersByTime(10000);
      expect(useUIStore.getState().notifications).toHaveLength(1);
      vi.useRealTimers();
    });
    it('should use default duration when not specified', async () => {
      vi.useFakeTimers();
      useUIStore.getState().addNotification({
        type: 'info',
        title: 'Info',
        message: 'Default duration',
      });
      expect(useUIStore.getState().notifications).toHaveLength(1);
      vi.advanceTimersByTime(5000);
      expect(useUIStore.getState().notifications).toEqual([]);
      vi.useRealTimers();
    });
  });

  describe('Reset', () => {
    it('should reset store to initial state', () => {
      const { result } = renderHook(() => useUIStore());

      // Modify state
      act(() => {
        result.current.openCreateAgentDialog();
        result.current.openSettingsDialog();
        result.current.openHelpDialog();
        result.current.setCurrentPage('agents');
        result.current.setSidebarCollapsed(true);
        result.current.setTheme('dark');
        result.current.setSidebarWidth(320);
        result.current.addNotification({
          type: 'success',
          title: 'Test',
          message: 'Test notification',
        });
      });

      // Verify state was modified
      expect(result.current.isCreateAgentDialogOpen).toBe(true);
      expect(result.current.isSettingsDialogOpen).toBe(true);
      expect(result.current.isHelpDialogOpen).toBe(true);
      expect(result.current.currentPage).toBe('agents');
      expect(result.current.sidebarCollapsed).toBe(true);
      expect(result.current.theme).toBe('dark');
      expect(result.current.sidebarWidth).toBe(320);
      expect(result.current.notifications).toHaveLength(1);

      // Reset
      act(() => {
        result.current.reset();
      });

      // Verify reset to initial state
      expect(result.current.isCreateAgentDialogOpen).toBe(false);
      expect(result.current.isSettingsDialogOpen).toBe(false);
      expect(result.current.isHelpDialogOpen).toBe(false);
      expect(result.current.currentPage).toBe('dashboard');
      expect(result.current.sidebarCollapsed).toBe(false);
      expect(result.current.theme).toBe('system');
      expect(result.current.sidebarWidth).toBe(280);
      expect(result.current.notifications).toEqual([]);
    });
  });

  describe('Integration Tests', () => {
    it('should handle complex UI state changes', () => {
      // Simulate user workflow
      useUIStore.getState().openCreateAgentDialog();
      expect(useUIStore.getState().isCreateAgentDialogOpen).toBe(true);
      useUIStore.getState().setTheme('dark');
      expect(useUIStore.getState().theme).toBe('dark');
      useUIStore.getState().toggleSidebar();
      expect(useUIStore.getState().sidebarCollapsed).toBe(true);
      useUIStore.getState().setCurrentPage('agents');
      expect(useUIStore.getState().currentPage).toBe('agents');
      useUIStore.getState().addNotification({
        type: 'success',
        title: 'Agent Created',
        message: 'New agent has been created successfully',
      });
      expect(useUIStore.getState().notifications).toHaveLength(1);
      useUIStore.getState().closeCreateAgentDialog();
      expect(useUIStore.getState().isCreateAgentDialogOpen).toBe(false);
      // Verify final state
      expect(useUIStore.getState().theme).toBe('dark');
      expect(useUIStore.getState().sidebarCollapsed).toBe(true);
      expect(useUIStore.getState().currentPage).toBe('agents');
      expect(useUIStore.getState().notifications).toHaveLength(1);
      expect(useUIStore.getState().isCreateAgentDialogOpen).toBe(false);
    });

    it('should handle multiple dialogs simultaneously', () => {
      const { result } = renderHook(() => useUIStore());

      act(() => {
        result.current.openCreateAgentDialog();
        result.current.openSettingsDialog();
        result.current.openHelpDialog();
      });

      expect(result.current.isCreateAgentDialogOpen).toBe(true);
      expect(result.current.isSettingsDialogOpen).toBe(true);
      expect(result.current.isHelpDialogOpen).toBe(true);

      act(() => {
        result.current.closeCreateAgentDialog();
        result.current.closeSettingsDialog();
      });

      expect(result.current.isCreateAgentDialogOpen).toBe(false);
      expect(result.current.isSettingsDialogOpen).toBe(false);
      expect(result.current.isHelpDialogOpen).toBe(true);
    });
  });
});
