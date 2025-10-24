import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useDragDrop } from '../use-drag-drop';

describe('useDragDrop', () => {
  const mockOnFileUpload = vi.fn();
  const mockFile = new File(['test content'], 'test.txt', { type: 'text/plain' });
  const mockImageFile = new File(['image content'], 'test.jpg', { type: 'image/jpeg' });

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should initialize with default values', () => {
    const { result } = renderHook(() => useDragDrop({ onFileUpload: mockOnFileUpload }));

    expect(result.current.isDragOver).toBe(false);
    expect(result.current.fileInputRef.current).toBeNull();
    expect(typeof result.current.handleDragOver).toBe('function');
    expect(typeof result.current.handleDragLeave).toBe('function');
    expect(typeof result.current.handleDrop).toBe('function');
    expect(typeof result.current.handleFileInputChange).toBe('function');
    expect(typeof result.current.triggerFileInput).toBe('function');
    expect(result.current.dragOverProps).toEqual({
      onDragOver: result.current.handleDragOver,
      onDragLeave: result.current.handleDragLeave,
      onDrop: result.current.handleDrop,
    });
  });

  it('should handle drag over event', () => {
    const { result } = renderHook(() => useDragDrop({ onFileUpload: mockOnFileUpload }));
    const mockEvent = {
      preventDefault: vi.fn(),
      stopPropagation: vi.fn(),
    } as unknown as React.DragEvent;

    act(() => {
      result.current.handleDragOver(mockEvent);
    });

    expect(mockEvent.preventDefault).toHaveBeenCalled();
    expect(mockEvent.stopPropagation).toHaveBeenCalled();
    expect(result.current.isDragOver).toBe(true);
  });

  it('should handle drag leave event', () => {
    const { result } = renderHook(() => useDragDrop({ onFileUpload: mockOnFileUpload }));
    const mockEvent = {
      preventDefault: vi.fn(),
      stopPropagation: vi.fn(),
    } as unknown as React.DragEvent;

    // First set drag over to true
    act(() => {
      result.current.handleDragOver(mockEvent);
    });
    expect(result.current.isDragOver).toBe(true);

    // Then handle drag leave
    act(() => {
      result.current.handleDragLeave(mockEvent);
    });

    expect(mockEvent.preventDefault).toHaveBeenCalled();
    expect(mockEvent.stopPropagation).toHaveBeenCalled();
    expect(result.current.isDragOver).toBe(false);
  });

  it('should handle drop event with valid file', () => {
    const { result } = renderHook(() => useDragDrop({ onFileUpload: mockOnFileUpload }));
    const mockEvent = {
      preventDefault: vi.fn(),
      stopPropagation: vi.fn(),
      dataTransfer: {
        files: [mockFile],
      },
    } as unknown as React.DragEvent;

    act(() => {
      result.current.handleDrop(mockEvent);
    });

    expect(mockEvent.preventDefault).toHaveBeenCalled();
    expect(mockEvent.stopPropagation).toHaveBeenCalled();
    expect(mockOnFileUpload).toHaveBeenCalledWith(mockFile);
    expect(result.current.isDragOver).toBe(false);
  });

  it('should not call onFileUpload when no files are dropped', () => {
    const { result } = renderHook(() => useDragDrop({ onFileUpload: mockOnFileUpload }));
    const mockEvent = {
      preventDefault: vi.fn(),
      stopPropagation: vi.fn(),
      dataTransfer: {
        files: [],
      },
    } as unknown as React.DragEvent;

    act(() => {
      result.current.handleDrop(mockEvent);
    });

    expect(mockOnFileUpload).not.toHaveBeenCalled();
  });

  it('should handle file input change with valid file', () => {
    const { result } = renderHook(() => useDragDrop({ onFileUpload: mockOnFileUpload }));
    const mockEvent = {
      target: {
        files: [mockFile],
      },
    } as unknown as React.ChangeEvent<HTMLInputElement>;

    act(() => {
      result.current.handleFileInputChange(mockEvent);
    });

    expect(mockOnFileUpload).toHaveBeenCalledWith(mockFile);
  });

  it('should not call onFileUpload when no file is selected', () => {
    const { result } = renderHook(() => useDragDrop({ onFileUpload: mockOnFileUpload }));
    const mockEvent = {
      target: {
        files: [],
      },
    } as unknown as React.ChangeEvent<HTMLInputElement>;

    act(() => {
      result.current.handleFileInputChange(mockEvent);
    });

    expect(mockOnFileUpload).not.toHaveBeenCalled();
  });

  it('should validate file types when acceptedFileTypes are provided', () => {
    const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
    const { result } = renderHook(() =>
      useDragDrop({ onFileUpload: mockOnFileUpload, acceptedFileTypes: ['.txt'] }),
    );

    // Test with valid file type
    const mockEvent = {
      preventDefault: vi.fn(),
      stopPropagation: vi.fn(),
      dataTransfer: {
        files: [mockFile], // .txt file
      },
    } as unknown as React.DragEvent;

    act(() => {
      result.current.handleDrop(mockEvent);
    });

    expect(mockOnFileUpload).toHaveBeenCalledWith(mockFile);

    // Test with invalid file type
    const mockEventInvalid = {
      preventDefault: vi.fn(),
      stopPropagation: vi.fn(),
      dataTransfer: {
        files: [mockImageFile], // .jpg file
      },
    } as unknown as React.DragEvent;

    act(() => {
      result.current.handleDrop(mockEventInvalid);
    });

    expect(consoleSpy).toHaveBeenCalledWith('Invalid file type');
    expect(mockOnFileUpload).toHaveBeenCalledTimes(1); // Should not be called again

    consoleSpy.mockRestore();
  });

  it('should accept all files when no acceptedFileTypes are provided', () => {
    const { result } = renderHook(() => useDragDrop({ onFileUpload: mockOnFileUpload }));
    const mockEvent = {
      preventDefault: vi.fn(),
      stopPropagation: vi.fn(),
      dataTransfer: {
        files: [mockImageFile], // .jpg file
      },
    } as unknown as React.DragEvent;

    act(() => {
      result.current.handleDrop(mockEvent);
    });

    expect(mockOnFileUpload).toHaveBeenCalledWith(mockImageFile);
  });

  it('should trigger file input click', () => {
    const { result } = renderHook(() => useDragDrop({ onFileUpload: mockOnFileUpload }));
    const mockClick = vi.fn();

    // Mock the file input ref
    result.current.fileInputRef.current = {
      click: mockClick,
    } as unknown as HTMLInputElement;

    act(() => {
      result.current.triggerFileInput();
    });

    expect(mockClick).toHaveBeenCalled();
  });

  it('should not throw error when file input ref is null', () => {
    const { result } = renderHook(() => useDragDrop({ onFileUpload: mockOnFileUpload }));

    // Ensure ref is null
    result.current.fileInputRef.current = null;

    expect(() => {
      act(() => {
        result.current.triggerFileInput();
      });
    }).not.toThrow();
  });
});
