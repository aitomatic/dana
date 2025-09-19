/* eslint-disable @typescript-eslint/no-explicit-any */
import {
  useState,
  useCallback,
  useMemo,
  memo,
  useRef,
  forwardRef,
  useImperativeHandle,
  useEffect,
} from 'react';
import { cn } from '@/lib/utils';
import { IconLoader2 } from '@tabler/icons-react';
import { apiService } from '@/lib/api';
import type { DocumentRead } from '@/types/document';

import ChatInput from './chat-input';
import SendButton from './send-button';

// Create separate, memoized components
const MemoizedChatInput = memo(ChatInput);

interface UploadedFile {
  id: string;
  name: string;
  size: number;
  type: string;
  status: 'uploading' | 'success' | 'error';
  path?: string;
  error?: string;
}

// Define the ref interface for external control
export interface ChatBoxRef {
  setMessage: (message: string) => void;
  submitMessage: () => void;
  sendMessageDirect: (messageText: string) => void;
}

interface ChatBoxProps {
  handleSendMessage: any;
  placeholder: string;
  id?: string;
  agentId?: string;
  isShowUpload?: boolean;
  files?: any[];
}

const ChatBox = forwardRef<ChatBoxRef, ChatBoxProps>(
  ({ handleSendMessage, placeholder, id, agentId, isShowUpload = false }, ref) => {
    const [message, setMessage] = useState<string | null>('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
    const [uploadingFiles, setUploadingFiles] = useState<string[]>([]);
    const [agentDocuments, setAgentDocuments] = useState<DocumentRead[]>([]);

    const fileInputRef = useRef<HTMLInputElement>(null);

    // Fetch agent documents when agentId changes
    useEffect(() => {
      const fetchAgentDocuments = async () => {
        if (!agentId) {
          setAgentDocuments([]);
          return;
        }

        try {
          const documents = await apiService.getDocuments({ agent_id: Number(agentId) });
          setAgentDocuments(documents);
        } catch (error) {
          console.error('Failed to fetch agent documents:', error);
          setAgentDocuments([]);
        }
      };

      fetchAgentDocuments();
    }, [agentId]);

    // Convert documents to mention options for ChatInput
    const documentMentionOptions = useMemo(() => {
      return agentDocuments.map((doc) => ({
        id: doc.id.toString(),
        label: doc.original_filename,
        value: doc.original_filename,
        icon: '📄',
      }));
    }, [agentDocuments]);

    // Expose methods to parent component via ref
    useImperativeHandle(
      ref,
      () => ({
        setMessage: (newMessage: string) => {
          setMessage(newMessage);
        },
        submitMessage: () => {
          onSubmit();
        },
        sendMessageDirect: (messageText: string) => {
          // Create message data and send directly
          const messageData = {
            message: messageText,
            role: 'user',
            files: uploadedFiles
              .filter((f) => f.status === 'success')
              .map((f) => ({
                name: f.name,
                path: f.path,
                size: f.size,
                type: f.type,
              })),
          };
          handleSendMessage(messageData);
        },
      }),
      [message, uploadedFiles, isSubmitting, handleSendMessage],
    );

    const uploadFile = useCallback(
      async (file: File): Promise<UploadedFile> => {
        const uploadedFile: UploadedFile = {
          id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
          name: file.name,
          size: file.size,
          type: file.type,
          status: 'uploading',
        };

        try {
          if (agentId) {
            // Use the agent-specific upload endpoint
            const doc = await apiService.uploadAgentDocument(agentId, file);
            uploadedFile.status = 'success';
            uploadedFile.path = doc.filename;
          } else {
            // Fallback to the general upload endpoint
            const doc = await apiService.uploadDocument({ file, title: file.name });
            uploadedFile.status = 'success';
            uploadedFile.path = doc.filename;
          }
        } catch (error) {
          uploadedFile.status = 'error';
          uploadedFile.error = (error as Error).message;
        }

        return uploadedFile;
      },
      [agentId],
    );

    const handleFileInputChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (!files || files.length === 0) return;

      const fileList = Array.from(files);
      const fileNames = fileList.map((f) => f.name);

      // Set uploading state for these files
      setUploadingFiles(fileNames);

      try {
        for (const file of fileList) {
          const uploadedFile = await uploadFile(file);
          setUploadedFiles((prev) => [...prev, uploadedFile]);
          // Remove this file from uploading list as it completes
          setUploadingFiles((prev) => prev.filter((name) => name !== file.name));
        }
      } catch (error) {
        console.error('Failed to upload file:', error);
        // Clear uploading state on error
        setUploadingFiles([]);
      } finally {
        if (fileInputRef.current) fileInputRef.current.value = '';
        // Ensure all files are cleared from uploading state
        setUploadingFiles([]);
      }
    };

    const handleAddFileClick = () => {
      fileInputRef.current?.click();
    };

    const removeFile = (fileId: string) => {
      setUploadedFiles((prev) => prev.filter((f) => f.id !== fileId));
    };

    const onSubmit = useCallback(() => {
      if (isSubmitting || (!message?.trim() && uploadedFiles.length === 0)) return;
      setIsSubmitting(true);
      const messageToSend = message?.trim() || '';
      setMessage('');

      // Include uploaded files in the message data
      const messageData = {
        message: messageToSend,
        role: 'user',
        files: uploadedFiles
          .filter((f) => f.status === 'success')
          .map((f) => ({
            name: f.name,
            path: f.path,
            size: f.size,
            type: f.type,
          })),
      };

      requestAnimationFrame(() => {
        handleSendMessage(messageData);
        setMessage('');
        // Clear uploaded files after sending
        setUploadedFiles([]);
        setTimeout(() => {
          setIsSubmitting(false);
        }, 100);
      });
    }, [handleSendMessage, message, isSubmitting, uploadedFiles]);

    const viewType = useMemo(() => {
      return 'input';
    }, []);

    const MemoizedSendButton = useMemo(
      () => (
        <SendButton
          message={message}
          files={uploadedFiles}
          onSubmit={onSubmit}
          isSubmitting={isSubmitting}
          onFileUpload={isShowUpload ? handleAddFileClick : undefined}
          isUploading={uploadingFiles.length > 0}
        />
      ),
      [
        message,
        uploadedFiles,
        onSubmit,
        isSubmitting,
        isShowUpload,
        uploadingFiles,
        handleAddFileClick,
      ],
    );

    // Memoized controls area - doesn't rerender when message changes except for the SendButton
    const ControlsArea = useMemo(
      () => (
        <div className={cn('flex flex-row-reverse gap-2 justify-between items-end w-full h-10')}>
          <div className={cn('flex gap-4 justify-between items-center w-full')}>
            {MemoizedSendButton}
          </div>
        </div>
      ),
      [MemoizedSendButton],
    );

    return (
      <>
        <input
          type="file"
          ref={fileInputRef}
          style={{ display: 'none' }}
          multiple
          onChange={handleFileInputChange}
        />
        <form
          className="flex right-0 bottom-0 left-0 w-full rounded-xl border border-gray-200 dark:border-gray-100"
          onSubmit={(e) => {
            e.preventDefault();
            if (!isSubmitting) {
              onSubmit();
            }
          }}
          style={{
            boxShadow:
              '0px 20px 24px -4px rgba(16, 24, 40, 0.04), 0px 8px 8px -4px rgba(16, 24, 40, 0.03)',
          }}
        >
          {viewType === 'input' && (
            <div className="flex flex-col gap-2 p-3 w-full rounded-xl bg-background dark:bg-gray-50">
              {/* File upload progress indicator */}
              {uploadingFiles.length > 0 && (
                <div className="p-2 mb-2 bg-blue-50 rounded-lg border border-blue-200">
                  <div className="flex items-center space-x-2">
                    <IconLoader2 className="w-4 h-4 text-blue-600 animate-spin" />
                    <div className="text-sm text-blue-700">
                      Uploading {uploadingFiles.length} file{uploadingFiles.length > 1 ? 's' : ''}
                      ...
                    </div>
                  </div>
                </div>
              )}

              {/* Uploaded files display */}
              {uploadedFiles.length > 0 && (
                <div className="flex flex-wrap gap-2 mb-2">
                  {uploadedFiles.map((file) => (
                    <div
                      key={file.id}
                      className="flex items-center px-2 py-1 space-x-2 text-sm bg-gray-100 rounded-lg"
                    >
                      <span className="text-gray-700">{file.name}</span>
                      {file.status === 'success' && (
                        <button
                          type="button"
                          onClick={() => removeFile(file.id)}
                          className="text-gray-500 hover:text-red-500"
                        >
                          ×
                        </button>
                      )}
                      {file.status === 'error' && (
                        <span className="text-xs text-red-500">Error</span>
                      )}
                    </div>
                  ))}
                </div>
              )}

              <div className="flex flex-col">
                <MemoizedChatInput
                  id={id}
                  message={message}
                  setMessage={setMessage}
                  placeholder={placeholder}
                  isBotThinking={false}
                  mentionOptions={documentMentionOptions}
                />
              </div>
              {ControlsArea}
            </div>
          )}
        </form>
      </>
    );
  },
);

export default ChatBox;
