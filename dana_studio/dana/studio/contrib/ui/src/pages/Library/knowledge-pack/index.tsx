/* eslint-disable @typescript-eslint/no-explicit-any */
import { useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { IconPaperclip, IconLoader2 } from '@tabler/icons-react';
import { useKnowledgePackStore } from '@/stores';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
const ALLOWED_FILE_TYPES = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'text/plain',
];

export function KnowledgePackDialog() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  // Store state
  const {
    isKnowledgePackOpen,
    setKnowledgePackOpen,
    textareaContent,
    setTextareaContent,
    uploadedFile,
    specialization,
    selectedDocumentIds,
    isParsingDocument,
    isCreatingPack,
    processingStep,
    parseDocument,
    buildKnowledgePack,
    reset,
  } = useKnowledgePackStore();

  // No local state needed - all managed by store

  // Handle textarea change
  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setTextareaContent(e.target.value);
  };

  // Handle browse file button click
  const handleBrowseClick = () => {
    fileInputRef.current?.click();
  };

  // Handle file selection
  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!ALLOWED_FILE_TYPES.includes(file.type)) {
      toast.error('Unsupported file type', {
        description: 'Please upload a PDF, DOCX, or TXT file.',
      });
      return;
    }

    // Validate file size
    if (file.size > MAX_FILE_SIZE) {
      toast.error('File too large', {
        description: `File size must be less than ${MAX_FILE_SIZE / 1024 / 1024}MB.`,
      });
      return;
    }

    // Show processing toast
    toast.info('Processing document...', {
      description: 'This may take 1-3 minutes.',
    });

    try {
      // Parse document immediately
      await parseDocument(file);

      // Success toast
      toast.success('Document processed!', {
        description: `Extracted specialization from ${file.name}`,
      });
    } catch (error: any) {
      toast.error('Failed to process document', {
        description: error?.message || 'Please try again.',
      });
    }

    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Handle build knowledge pack
  const handleBuild = async () => {
    if (!canBuild) return;

    try {
      // Show initial toast
      toast.info('Building Knowledge Pack...', {
        description: 'This may take a while',
      });

      // Build knowledge pack (two-step process)
      const knowledgePackId = await buildKnowledgePack(textareaContent, selectedDocumentIds);

      // Navigate to the newly created pack's detail page
      if (knowledgePackId) {
        navigate(`/knowledge-pack/${knowledgePackId}`, {
          state: { originalDescription: textareaContent }
        });
      }

      // // Success toast
      // toast.success('Knowledge Pack created successfully!', {
      //   description: 'Opening editor...',
      // });
    } catch (error: any) {
      toast.error('Failed to build Knowledge Pack', {
        description: error?.message || 'Please try again.',
      });
    }
  };

  // Handle cancel
  const handleCancel = () => {
    setKnowledgePackOpen(false);
    reset();
  };

  // Calculate if build button should be enabled
  // Button enabled if:
  // 1. Not currently processing (parsing or creating)
  // 2. AND has any text content OR has uploaded a file
  // Note: No character limits, no document requirements
  const hasAnyContent = textareaContent.trim().length > 0 || uploadedFile !== null;
  const canBuild = !isParsingDocument && !isCreatingPack && hasAnyContent;

  // Count tasks in textarea
  const taskCount = textareaContent
    .split('\n')
    .filter((line) => line.trim().startsWith('-')).length;

  return (
    <Dialog open={isKnowledgePackOpen} onOpenChange={setKnowledgePackOpen}>
      <DialogContent
        className="w-[80vw] max-w-2xl min-w-2xl  h-[60vh] max-h-[60vh] p-0 flex flex-col"
        onInteractOutside={(e) => e.preventDefault()}
      >
        <DialogHeader className="px-6 pt-6 pb-4 border-b">
          <DialogTitle className="flex gap-2 items-center text-lg font-semibold">
            What's this knowledge pack about?
          </DialogTitle>
        </DialogHeader>

        <div className="flex overflow-y-auto flex-col flex-1 gap-4 px-6 py-4">
          {/* Header Label */}
          <div className="text-sm font-medium text-gray-600 dark:text-gray-400">
            Provide a description to initiate your knowledge pack
          </div>

          {/* Textarea Container */}
          <div className="flex relative flex-col flex-1 min-h-0">
            <Textarea
              value={textareaContent}
              onChange={handleTextareaChange}
              placeholder="Provide a job description, CV, or any document describing the knowledge pack you want to create."
              className="pb-16 h-full text-sm leading-relaxed bg-gray-50 resize-none dark:bg-surface dark:text-white dark:border-primary"
              disabled={isParsingDocument || isCreatingPack}
            />

            {/* Browse File Button (Inside Textarea) */}
            <div className="absolute bottom-3 left-3">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleBrowseClick}
                disabled={isParsingDocument || isCreatingPack}
                className="gap-2 text-xs"
              >
                <IconPaperclip className="w-3.5 h-3.5" />
                Browse File
              </Button>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.docx,.txt"
                onChange={handleFileSelect}
                className="hidden"
              />
            </div>
          </div>

          {/* File Status Display */}
          <div className="flex flex-col gap-2">
            {/* Processing State */}
            {isParsingDocument && (
              <div className="flex gap-2 items-center p-3 bg-blue-50 rounded-lg border border-blue-200 dark:bg-blue-950/20 dark:border-blue-900">
                <IconLoader2 className="w-4 h-4 text-blue-600 animate-spin" />
                <span className="text-sm text-blue-700 dark:text-blue-400">
                  🔄 Processing document... (1-3 minutes)
                </span>
              </div>
            )}

            {/* Specialization Preview */}
            {specialization && !isParsingDocument && (
              <div className="flex flex-col gap-2 p-4 bg-purple-50 rounded-lg border border-purple-200 dark:bg-purple-950/20 dark:border-purple-900">
                <div className="text-sm font-semibold text-purple-900 dark:text-purple-300">
                  Extracted Specialization:
                </div>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <span className="font-medium text-gray-700 dark:text-gray-300">Domain:</span>
                    <span className="ml-2 text-gray-600 dark:text-gray-400">
                      {specialization.domain}
                    </span>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700 dark:text-gray-300">Role:</span>
                    <span className="ml-2 text-gray-600 dark:text-gray-400">
                      {specialization.role}
                    </span>
                  </div>
                  <div className="col-span-2">
                    <span className="font-medium text-gray-700 dark:text-gray-300">Tasks:</span>
                    <span className="ml-2 text-gray-600 dark:text-gray-400">
                      {taskCount} tasks identified
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Document count info (optional) */}
            {selectedDocumentIds.length > 0 && (
              <div className="text-sm text-gray-600 dark:text-gray-400">
                📄 {selectedDocumentIds.length} document
                {selectedDocumentIds.length > 1 ? 's' : ''} selected
              </div>
            )}
          </div>
        </div>

        {/* Footer with buttons */}
        <DialogFooter className="flex gap-4 justify-between items-center px-6 py-4 bg-gray-50 border-t dark:bg-gray-900/50">
          {/* Processing Step Indicator */}
          {processingStep ? (
            <div className="flex flex-1 gap-2 items-center text-sm text-gray-600 dark:text-gray-400">
              <IconLoader2 className="w-4 h-4 animate-spin" />
              <span>{processingStep}</span>
            </div>
          ) : (
            <div className="flex-1"></div>
          )}

          <div className="flex gap-3">
            <Button
              variant="outline"
              size="lg"
              onClick={handleCancel}
              disabled={isParsingDocument || isCreatingPack}
              className={cn(
                'transition-all duration-300',
                (isParsingDocument || isCreatingPack) && 'opacity-50 cursor-not-allowed',
              )}
            >
              Cancel
            </Button>

            <Button
              size="lg"
              onClick={handleBuild}
              disabled={!canBuild}
              className={cn(
                'gap-2 transition-all duration-300',
                !canBuild && 'opacity-50 cursor-not-allowed',
                canBuild && 'opacity-100',
              )}
            >
              {isCreatingPack && <IconLoader2 className="w-4 h-4 animate-spin" />}
              {isCreatingPack ? 'Building...' : 'Build Knowledge Pack'}
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
