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
import { toast } from 'sonner';

interface EditTemplateDialogProps {
  template: {
    id: number;
    name: string;
  } | null;
  isOpen: boolean;
  onClose: () => void;
  onSave: (templateId: number, updates: { name: string }) => Promise<void>;
  isLoading?: boolean;
}

export function EditTemplateDialog({
  template,
  isOpen,
  onClose,
  onSave,
  isLoading = false,
}: EditTemplateDialogProps) {
  const [name, setName] = useState('');
  const [errors, setErrors] = useState<{ name?: string }>({});

  // Reset form when template changes
  useEffect(() => {
    if (template) {
      setName(template.name);
      setErrors({});
    }
  }, [template]);

  const validateForm = () => {
    const newErrors: { name?: string } = {};

    if (!name.trim()) {
      newErrors.name = 'Template name is required';
    } else if (name.trim().length < 1) {
      newErrors.name = 'Template name must be at least 1 character';
    } else if (name.trim().length > 255) {
      newErrors.name = 'Template name must be less than 255 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = async () => {
    if (!template || !validateForm()) {
      return;
    }

    try {
      await onSave(template.id, { name: name.trim() });
      toast.success('Capture Template has been updated successfully.');
      onClose();
    } catch {
      toast.error('Failed to update template. Please try again.');
    }
  };

  const handleCancel = () => {
    // Reset form to original values
    if (template) {
      setName(template.name);
    }
    setErrors({});
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Edit Capture Template</DialogTitle>
          <DialogDescription>
            Update the template name. Click save when you're done.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 pb-8">
          <div className="grid gap-2">
            <Label htmlFor="template-name">Template Name</Label>
            <Input
              id="template-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter template name"
              className={errors.name ? 'border-red-500' : ''}
            />
            {errors.name && <p className="text-sm text-red-500">{errors.name}</p>}
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

