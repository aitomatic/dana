// SendButton.tsx - Send button component
import { ArrowUp, Attachment } from 'iconoir-react';
import { IconLoader2 } from '@tabler/icons-react';
import { cn } from '@/lib/utils';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';

interface SendButtonProps {
  message: string | null | undefined;
  files?: any[];
  onSubmit: () => void;
  isSubmitting: boolean;
  onFileUpload?: () => void;
  isUploading?: boolean;
}

const SendButton = ({
  message,
  files,
  onSubmit,
  isSubmitting,
  onFileUpload,
  isUploading = false,
}: SendButtonProps) => {
  const hasContent = message || (files && files.length > 0);
  const isDisabled = isSubmitting || !hasContent;

  return (
    <div className="flex gap-2 items-center w-full justify-between">
      {/* File Upload Button */}
      {onFileUpload && (
        <Tooltip>
          <TooltipTrigger asChild>
            <div
              onClick={!isSubmitting && !isUploading ? onFileUpload : () => {}}
              className={cn(
                'flex items-center justify-center w-9 h-9 border bg-white border-gray-300 rounded-full transition-all duration-200 cursor-pointer',
                isSubmitting || isUploading
                  ? 'opacity-50 cursor-not-allowed bg-gray-100'
                  : ' hover:bg-gray-100',
              )}
              style={{ pointerEvents: isSubmitting || isUploading ? 'none' : 'auto' }}
            >
              {isUploading ? (
                <IconLoader2 className="w-4 h-4 text-gray-600 animate-spin" />
              ) : (
                <Attachment className="w-4 h-4 text-gray-500" />
              )}
            </div>
          </TooltipTrigger>
          <TooltipContent>
            <p>Add files</p>
          </TooltipContent>
        </Tooltip>
      )}

      {/* Send Button */}
      <div
        onClick={!isDisabled ? onSubmit : () => {}}
        className={cn(
          'flex items-center justify-center w-9! h-9! bg-background rounded-full transition-all duration-200',
          isSubmitting && 'opacity-50 cursor-not-allowed bg-gray-400',
          hasContent ? 'bg-brand-600 cursor-pointer' : 'bg-gray-400 cursor-not-allowed',
          isSubmitting && 'opacity-50 cursor-not-allowed',
        )}
        style={{ pointerEvents: isDisabled ? 'none' : 'auto' }}
        data-testid="send-message-button"
      >
        <ArrowUp className="text-white" width={14} height={14} strokeWidth={3} />
      </div>
    </div>
  );
};

export default SendButton;
