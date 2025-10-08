import { renderHook, act } from '@testing-library/react';
import { useScreenHeight } from '../useScreenHeight';

// Mock window.innerHeight
const mockInnerHeight = (height: number) => {
  Object.defineProperty(window, 'innerHeight', {
    writable: true,
    configurable: true,
    value: height,
  });
};

// Mock window.addEventListener and window.removeEventListener
const mockAddEventListener = jest.fn();
const mockRemoveEventListener = jest.fn();

Object.defineProperty(window, 'addEventListener', {
  writable: true,
  configurable: true,
  value: mockAddEventListener,
});

Object.defineProperty(window, 'removeEventListener', {
  writable: true,
  configurable: true,
  value: mockRemoveEventListener,
});

describe('useScreenHeight', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should return correct page size for large screens', () => {
    mockInnerHeight(1024); // Large screen
    
    const { result } = renderHook(() => useScreenHeight());
    
    expect(result.current.pageSize).toBe(20);
    expect(result.current.isLargeScreen).toBe(true);
    expect(result.current.screenHeight).toBe(1024);
  });

  it('should return correct page size for small screens', () => {
    mockInnerHeight(600); // Small screen
    
    const { result } = renderHook(() => useScreenHeight());
    
    expect(result.current.pageSize).toBe(10);
    expect(result.current.isLargeScreen).toBe(false);
    expect(result.current.screenHeight).toBe(600);
  });

  it('should update page size when screen height changes', () => {
    mockInnerHeight(600); // Start with small screen
    
    const { result, rerender } = renderHook(() => useScreenHeight());
    
    expect(result.current.pageSize).toBe(10);
    expect(result.current.isLargeScreen).toBe(false);
    
    // Simulate screen resize to large
    mockInnerHeight(1024);
    
    // Trigger resize event
    const resizeHandler = mockAddEventListener.mock.calls.find(
      call => call[0] === 'resize'
    )?.[1];
    
    if (resizeHandler) {
      act(() => {
        resizeHandler();
      });
    }
    
    rerender();
    
    expect(result.current.pageSize).toBe(20);
    expect(result.current.isLargeScreen).toBe(true);
    expect(result.current.screenHeight).toBe(1024);
  });

  it('should use custom thresholds and page sizes', () => {
    mockInnerHeight(800);
    
    const { result } = renderHook(() => 
      useScreenHeight(900, 25, 15) // Custom threshold and page sizes
    );
    
    expect(result.current.pageSize).toBe(15); // Below 900px threshold
    expect(result.current.isLargeScreen).toBe(false);
  });

  it('should add and remove resize event listener', () => {
    renderHook(() => useScreenHeight());
    
    expect(mockAddEventListener).toHaveBeenCalledWith('resize', expect.any(Function));
    
    // Cleanup should remove the listener
    const { unmount } = renderHook(() => useScreenHeight());
    unmount();
    
    expect(mockRemoveEventListener).toHaveBeenCalledWith('resize', expect.any(Function));
  });
});
