import { Button } from '@/components/ui/button';
import { SystemRestart, EditPencil } from 'iconoir-react';

interface ExtractionControlsProps {
  isDeepExtracted: boolean;
  isDeepExtracting: boolean;
  showPromptInput: boolean;
  onShowPromptInput: () => void;
  onDeepExtractWithPrompt: () => void;
  onDeepExtractWithoutPrompt: () => void;
  isEditing: boolean;
  onEdit: () => void;
  onSave: () => void;
}

export const ExtractionControls = ({
  isDeepExtracted,
  isDeepExtracting,
  showPromptInput,
  onDeepExtractWithPrompt,
  onDeepExtractWithoutPrompt,
  isEditing,
  onEdit,
  onSave,
}: ExtractionControlsProps) => {
  if (!isDeepExtracted && !showPromptInput) {
    return (
      <div className="flex gap-2 items-center">
        <Button
          variant="outline"
          size="sm"
          className="text-gray-700"
          onClick={onDeepExtractWithoutPrompt}
          disabled={isDeepExtracting}
          leftSection={isDeepExtracting && <SystemRestart className="animate-spin size-4" />}
        >
          {isDeepExtracting ? 'Extracting...' : 'Deep Extract: Off'}
        </Button>
        {!isDeepExtracting &&
          (isEditing ? (
            <Button variant="secondary" size="sm" className="text-gray-700" onClick={onSave}>
              Save
            </Button>
          ) : (
            <Button
              variant="outline"
              size="sm"
              className="text-gray-700"
              leftSection={<EditPencil />}
              onClick={onEdit}
            >
              Edit
            </Button>
          ))}
      </div>
    );
  }

  if (showPromptInput && !isDeepExtracted) {
    return (
      <div className="flex gap-2 items-center">
        <Button
          leftSection={isDeepExtracting && <SystemRestart className="animate-spin size-4" />}
          disabled={isDeepExtracting}
          onClick={onDeepExtractWithPrompt}
          variant="outline"
          size="sm"
          className="text-gray-700"
        >
          {isDeepExtracting ? 'Extraction in progress...' : 'Start Extract'}
        </Button>
        {!isDeepExtracting &&
          (isEditing ? (
            <Button variant="secondary" size="sm" className="text-gray-700" onClick={onSave}>
              Save
            </Button>
          ) : (
            <Button
              variant="secondary"
              size="sm"
              className="text-gray-700"
              leftSection={<EditPencil />}
              onClick={onEdit}
            >
              Edit
            </Button>
          ))}
      </div>
    );
  }

  if (isDeepExtracted) {
    return (
      <div className="flex gap-2 items-center">
        {!isDeepExtracting &&
          (isEditing ? (
            <Button variant="secondary" size="sm" className="text-gray-700" onClick={onSave}>
              Save
            </Button>
          ) : (
            <Button
              variant="secondary"
              size="sm"
              className="text-gray-700"
              leftSection={<EditPencil />}
              onClick={onEdit}
            >
              Edit
            </Button>
          ))}
      </div>
    );
  }

  return null;
};
