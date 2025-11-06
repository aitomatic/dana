import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import React from 'react';
import { useSidebar, SidebarContext } from '../use-sidebar';

describe('useSidebar', () => {
  const mockContextValue = {
    state: 'expanded' as const,
    open: true,
    setOpen: vi.fn(),
    openMobile: false,
    setOpenMobile: vi.fn(),
    isMobile: false,
    toggleSidebar: vi.fn(),
  };

  const createWrapper = (contextValue: any) => {
    return ({ children }: { children: React.ReactNode }) =>
      React.createElement(SidebarContext.Provider, { value: contextValue }, children);
  };

  it('should return context values when used within provider', () => {
    const { result } = renderHook(() => useSidebar(), {
      wrapper: createWrapper(mockContextValue),
    });

    expect(result.current.state).toBe('expanded');
    expect(result.current.open).toBe(true);
    expect(result.current.openMobile).toBe(false);
    expect(result.current.isMobile).toBe(false);
    expect(typeof result.current.setOpen).toBe('function');
    expect(typeof result.current.setOpenMobile).toBe('function');
    expect(typeof result.current.toggleSidebar).toBe('function');
  });

  it('should throw error when used outside of provider', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    expect(() => {
      renderHook(() => useSidebar());
    }).toThrow('useSidebar must be used within a SidebarProvider.');

    consoleSpy.mockRestore();
  });

  it('should handle collapsed state', () => {
    const collapsedContextValue = {
      ...mockContextValue,
      state: 'collapsed' as const,
      open: false,
    };

    const { result } = renderHook(() => useSidebar(), {
      wrapper: createWrapper(collapsedContextValue),
    });

    expect(result.current.state).toBe('collapsed');
    expect(result.current.open).toBe(false);
  });

  it('should handle mobile state', () => {
    const mobileContextValue = {
      ...mockContextValue,
      openMobile: true,
      isMobile: true,
    };

    const { result } = renderHook(() => useSidebar(), {
      wrapper: createWrapper(mobileContextValue),
    });

    expect(result.current.openMobile).toBe(true);
    expect(result.current.isMobile).toBe(true);
  });

  it('should provide setter functions', () => {
    const { result } = renderHook(() => useSidebar(), {
      wrapper: createWrapper(mockContextValue),
    });

    act(() => {
      result.current.setOpen(false);
    });

    expect(mockContextValue.setOpen).toHaveBeenCalledWith(false);

    act(() => {
      result.current.setOpenMobile(true);
    });

    expect(mockContextValue.setOpenMobile).toHaveBeenCalledWith(true);

    act(() => {
      result.current.toggleSidebar();
    });

    expect(mockContextValue.toggleSidebar).toHaveBeenCalled();
  });

  it('should handle null context gracefully', () => {
    const nullWrapper = ({ children }: { children: React.ReactNode }) =>
      React.createElement(SidebarContext.Provider, { value: null }, children);

    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    expect(() => {
      renderHook(() => useSidebar(), { wrapper: nullWrapper });
    }).toThrow('useSidebar must be used within a SidebarProvider.');

    consoleSpy.mockRestore();
  });
});
