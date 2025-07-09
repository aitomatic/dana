// SendButton.tsx - Send button component
import { ArrowUp } from "iconoir-react";
import { cn } from "@/lib/utils";

interface SendButtonProps {
  message: string | null | undefined;
  files?: any[];
  onSubmit: () => void;
  isSubmitting: boolean;
}

const SendButton = ({ message, files, onSubmit, isSubmitting }: SendButtonProps) => {
  const hasContent = message || (files && files.length > 0);
  const isDisabled = isSubmitting || !hasContent;

  return (
    <div
      onClick={!isDisabled ? onSubmit : () => {}}
      className={cn(
        "flex items-center justify-center w-9! h-9! bg-background rounded-full transition-all duration-200",
        isSubmitting && "opacity-50 cursor-not-allowed bg-gray-400",
        hasContent ? "bg-brand-600 cursor-pointer" : "bg-gray-400 cursor-not-allowed",
        isSubmitting && "opacity-50 cursor-not-allowed"
      )}
      style={{ pointerEvents: isDisabled ? "none" : "auto" }}
      data-testid="send-message-button"
    >
      <ArrowUp className="text-white" width={14} height={14} strokeWidth={3} />
    </div>
  );
};

export default SendButton;
