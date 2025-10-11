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
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import type { TopicRead, TopicCreate } from '@/types/topic';

interface EditTopicDialogProps {
  topic: TopicRead | null;
  isOpen: boolean;
  onClose: () => void;
  onSave: (topicId: number, topic: TopicCreate) => Promise<void>;
  isLoading?: boolean;
}

export function EditTopicDialog({
  topic,
  isOpen,
  onClose,
  onSave,
  isLoading = false,
}: EditTopicDialogProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [errors, setErrors] = useState<{ name?: string; description?: string }>({});

  // Reset form when topic changes
  useEffect(() => {
    if (topic) {
      setName(topic.name);
      setDescription(topic.description || '');
      setErrors({});
    }
  }, [topic]);

  const validateForm = () => {
    const newErrors: { name?: string; description?: string } = {};

    if (!name.trim()) {
      newErrors.name = 'Topic name is required';
    } else if (name.trim().length < 2) {
      newErrors.name = 'Topic name must be at least 2 characters';
    } else if (name.trim().length > 100) {
      newErrors.name = 'Topic name must be less than 100 characters';
    }

    if (description.trim().length > 500) {
      newErrors.description = 'Description must be less than 500 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = async () => {
    if (!topic || !validateForm()) {
      return;
    }

    try {
      await onSave(topic.id, {
        name: name.trim(),
        description: description.trim() || '',
      });

      toast.success('Topic has been updated successfully.');

      onClose();
    } catch {
      toast.error('Failed to update topic. Please try again.');
    }
  };

  const handleCancel = () => {
    // Reset form to original values
    if (topic) {
      setName(topic.name);
      setDescription(topic.description || '');
    }
    setErrors({});
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Edit Topic</DialogTitle>
          <DialogDescription>
            Update the topic name and description. Click save when you're done.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="name">Name</Label>
            <Input
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter topic name"
              className={errors.name ? 'border-red-500' : ''}
            />
            {errors.name && <p className="text-sm text-red-500">{errors.name}</p>}
          </div>
          <div className="grid gap-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Enter topic description (optional)"
              rows={3}
              className={errors.description ? 'border-red-500' : ''}
            />
            {errors.description && <p className="text-sm text-red-500">{errors.description}</p>}
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
