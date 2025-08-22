import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { SystemRestart } from 'iconoir-react';

interface PromptSectionProps {
  showPromptInput: boolean;
  setShowPromptInput: (show: boolean) => void;
  prompt: string;
  setPrompt: (prompt: string) => void;
  isDeepExtracting: boolean;
  isDeepExtracted: boolean;
  onDeepExtractWithPrompt: () => void;
  onDeepExtractWithoutPrompt: () => void;
}

export const PromptSection = ({
  showPromptInput,
  setShowPromptInput,
  prompt,
  setPrompt,
  isDeepExtracting,
  isDeepExtracted,
  onDeepExtractWithPrompt,
  onDeepExtractWithoutPrompt,
}: PromptSectionProps) => {
  if (showPromptInput) {
    return (
      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-2">
          <h3 className="text-sm font-semibold text-gray-700">Additional Context</h3>
          <Textarea
            id="prompt"
            placeholder="Enter additional context or instructions for extraction..."
            value={prompt}
            onChange={e => setPrompt(e.target.value)}
            className="min-h-[120px] rounded-lg resize-none border-gray-300"
            disabled={isDeepExtracting}
          />
        </div>
        <div className="flex gap-2">
          <Button
            leftSection={isDeepExtracting && <SystemRestart className="animate-spin size-4" />}
            onClick={prompt && prompt.trim() !== '' ? onDeepExtractWithPrompt : onDeepExtractWithoutPrompt}
            variant="secondary"
            size="sm"
            className="w-max text-gray-700"
            disabled={isDeepExtracting}
          >
            {isDeepExtracting
              ? 'Deep extraction in progress...'
              : prompt && prompt.trim() !== ''
                ? 'Deep Extract with Context'
                : 'Deep Extract'}
          </Button>
        </div>
      </div>
    );
  }

  // Show prompt text only when there's a non-empty prompt and either deep extracting or deep extracted
  if (prompt && prompt.trim() !== '' && (isDeepExtracted || isDeepExtracting)) {
    return (
      <div className="flex flex-col gap-2">
        <div className="flex justify-between items-center">
          <h3 className="text-sm font-semibold text-gray-700">Additional Context</h3>
          {isDeepExtracted && (
            <Button
              variant="ghost"
              size="sm"
              className="text-gray-500 hover:text-gray-700"
              onClick={() => setShowPromptInput(true)}
            >
              Edit Prompt
            </Button>
          )}
        </div>
        <span className="px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg">{prompt}</span>
      </div>
    );
  }

  // Hide the entire section when:
  // 1. No prompt exists (empty or undefined) OR
  // 2. Deep extraction is in progress without a prompt OR
  // 3. Deep extraction is completed without a prompt
  return null;
};
