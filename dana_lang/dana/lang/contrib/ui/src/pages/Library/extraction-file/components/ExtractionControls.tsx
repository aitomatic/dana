import { Button } from '@/components/ui/button';
import { EditPencil } from 'iconoir-react';

interface ExtractionControlsProps {
  isDeepExtracting: boolean;
  isEditing: boolean;
  onEdit: () => void;
  onSave: () => void;
}

export const ExtractionControls = ({
  isDeepExtracting,
  isEditing,
  onEdit,
  onSave,
}: ExtractionControlsProps) => {
  return (
    <div className="flex gap-2 items-center">
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
};
