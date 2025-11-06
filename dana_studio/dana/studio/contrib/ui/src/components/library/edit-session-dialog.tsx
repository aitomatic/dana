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

interface EditSessionDialogProps {
  session: {
    id: number;
    name: string;
  } | null;
  isOpen: boolean;
  onClose: () => void;
  onSave: (sessionId: number, updates: { session_name: string }) => Promise<void>;
  isLoading?: boolean;
}

export function EditSessionDialog({
  session,
  isOpen,
  onClose,
  onSave,
  isLoading = false,
}: EditSessionDialogProps) {
  const [name, setName] = useState('');
  const [errors, setErrors] = useState<{ name?: string }>({});

  // Reset form when session changes
  useEffect(() => {
    if (session) {
      setName(session.name);
      setErrors({});
    }
  }, [session]);

  const validateForm = () => {
    const newErrors: { name?: string } = {};

    if (!name.trim()) {
      newErrors.name = 'Session name is required';
    } else if (name.trim().length < 1) {
      newErrors.name = 'Session name must be at least 1 character';
    } else if (name.trim().length > 255) {
      newErrors.name = 'Session name must be less than 255 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = async () => {
    if (!session || !validateForm()) {
      return;
    }

    try {
      await onSave(session.id, { session_name: name.trim() });
      toast.success('Capture Knowledge session has been updated successfully.');
      onClose();
    } catch {
      toast.error('Failed to update session. Please try again.');
    }
  };

  const handleCancel = () => {
    // Reset form to original values
    if (session) {
      setName(session.name);
    }
    setErrors({});
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Edit Capture Knowledge Session</DialogTitle>
          <DialogDescription>
            Update the session name. Click save when you're done.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="session-name">Session Name</Label>
            <Input
              id="session-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter session name"
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

