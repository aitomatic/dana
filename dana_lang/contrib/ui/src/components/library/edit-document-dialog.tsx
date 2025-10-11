import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { IconChevronDown } from '@tabler/icons-react';

import { toast } from 'sonner';
import type { DocumentRead, DocumentUpdate } from '@/types/document';
import type { TopicRead } from '@/types/topic';

interface EditDocumentDialogProps {
  document: DocumentRead | null;
  topics: TopicRead[];
  isOpen: boolean;
  onClose: () => void;
  onSave: (documentId: number, document: DocumentUpdate) => Promise<void>;
  isLoading?: boolean;
}

export function EditDocumentDialog({
  document,
  topics,
  isOpen,
  onClose,
  onSave,
  isLoading = false,
}: EditDocumentDialogProps) {
  const [filename, setFilename] = useState('');
  const [topicId, setTopicId] = useState<string>('');
  const [errors, setErrors] = useState<{ filename?: string }>({});

  // Reset form when document changes
  useEffect(() => {
    if (document) {
      setFilename(document.original_filename);
      setTopicId(document.topic_id?.toString() || '');
      setErrors({});
    }
  }, [document]);

  const validateForm = () => {
    const newErrors: { filename?: string } = {};

    if (!filename.trim()) {
      newErrors.filename = 'Document name is required';
    } else if (filename.trim().length < 1) {
      newErrors.filename = 'Document name must be at least 1 character';
    } else if (filename.trim().length > 255) {
      newErrors.filename = 'Document name must be less than 255 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = async () => {
    if (!document || !validateForm()) {
      return;
    }

    try {
      const updateData: DocumentUpdate = {
        original_filename: filename.trim(),
      };

      // Only include topic_id if it's different from current or if it's being set
      if (topicId !== document.topic_id?.toString()) {
        updateData.topic_id = topicId ? parseInt(topicId) : undefined;
      }

      await onSave(document.id, updateData);

      toast.success('Document has been updated successfully.');

      onClose();
    } catch {
      toast.error('Failed to update document. Please try again.');
    }
  };

  const handleCancel = () => {
    // Reset form to original values
    if (document) {
      setFilename(document.original_filename);
      setTopicId(document.topic_id?.toString() || '');
    }
    setErrors({});
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Edit Document</DialogTitle>
          <DialogDescription>
            Update the document name and topic assignment. Click save when you're done.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="filename">Document Name</Label>
            <Input
              id="filename"
              value={filename}
              onChange={(e) => setFilename(e.target.value)}
              placeholder="Enter document name"
              className={errors.filename ? 'border-red-500' : ''}
            />
            {errors.filename && <p className="text-sm text-red-500">{errors.filename}</p>}
          </div>
          <div className="grid gap-2">
            <Label htmlFor="topic">Topic (Optional)</Label>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" className="justify-between">
                  {topicId
                    ? topics.find((t) => t.id.toString() === topicId)?.name || 'Select a topic'
                    : 'No Topic'}
                  <IconChevronDown className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuItem onClick={() => setTopicId('')}>No Topic</DropdownMenuItem>
                {topics.map((topic) => (
                  <DropdownMenuItem key={topic.id} onClick={() => setTopicId(topic.id.toString())}>
                    {topic.name}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={handleCancel} disabled={isLoading}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={isLoading}>
            {isLoading ? 'Saving...' : 'Save Changes'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
