import React, { useState, useCallback, useRef } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Upload, FileText, X } from 'lucide-react';
import { toast } from 'sonner';
import { apiService } from '@/lib/api';

interface ImportAgentDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onImportSuccess: () => void;
}

export const ImportAgentDialog: React.FC<ImportAgentDialogProps> = ({
  open,
  onOpenChange,
  onImportSuccess,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [agentName, setAgentName] = useState('');
  const [agentDescription, setAgentDescription] = useState('');
  const [isImporting, setIsImporting] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setIsDragOver(false);

      const files = Array.from(e.dataTransfer.files);
      const file = files[0];

      if (file && file.name.endsWith('.tar.gz')) {
        setSelectedFile(file);
        // Auto-fill agent name from filename if not already set
        if (!agentName) {
          const nameFromFile = file.name
            .replace('.tar.gz', '')
            .replace(/^agent_\d+_/, '') // Remove agent_123_ prefix
            .replace(/[_-]/g, ' ')
            .replace(/\b\w/g, (l) => l.toUpperCase()); // Capitalize words
          setAgentName(nameFromFile);
        }
      } else {
        toast.error('Please select a .tar.gz file');
      }
    },
    [agentName],
  );

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file && file.name.endsWith('.tar.gz')) {
        setSelectedFile(file);
        // Auto-fill agent name from filename if not already set
        if (!agentName) {
          const nameFromFile = file.name
            .replace('.tar.gz', '')
            .replace(/^agent_\d+_/, '') // Remove agent_123_ prefix
            .replace(/[_-]/g, ' ')
            .replace(/\b\w/g, (l) => l.toUpperCase()); // Capitalize words
          setAgentName(nameFromFile);
        }
      } else {
        toast.error('Please select a .tar.gz file');
      }
    },
    [agentName],
  );

  const handleImport = async () => {
    if (!selectedFile || !agentName.trim()) {
      toast.error('Please select a file and enter an agent name');
      return;
    }

    setIsImporting(true);
    try {
      const result = await apiService.importAgentTar(
        selectedFile,
        agentName.trim(),
        agentDescription.trim() || 'Imported agent',
      );

      if (result.success) {
        toast.success('Agent imported successfully!', {
          description: `Agent "${agentName}" has been imported with ID ${result.agent_id}`,
        });

        // Reset form
        setAgentName('');
        setAgentDescription('');
        setSelectedFile(null);
        onImportSuccess();
        onOpenChange(false);
      } else {
        toast.error('Import failed', {
          description: result.message || 'Failed to import agent',
        });
      }
    } catch (error) {
      console.error('Import error:', error);
      toast.error('Import failed', {
        description: error instanceof Error ? error.message : 'Unknown error occurred',
      });
    } finally {
      setIsImporting(false);
    }
  };

  const handleClose = () => {
    if (!isImporting) {
      setSelectedFile(null);
      setAgentName('');
      setAgentDescription('');
      onOpenChange(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Import Agent from Archive</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {/* File Upload Area */}
          <div className="space-y-2">
            <Label htmlFor="file">Agent Archive (.tar.gz)</Label>
            <div
              className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors cursor-pointer ${
                isDragOver ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'
              }`}
              onDrop={handleDrop}
              onDragOver={(e) => {
                e.preventDefault();
                setIsDragOver(true);
              }}
              onDragLeave={() => setIsDragOver(false)}
              onClick={() => !isImporting && fileInputRef.current?.click()}
            >
              {selectedFile ? (
                <div className="flex items-center justify-center space-x-2">
                  <FileText className="h-8 w-8 text-blue-500" />
                  <span className="text-sm font-medium">{selectedFile.name}</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedFile(null);
                    }}
                    disabled={isImporting}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              ) : (
                <div>
                  <Upload className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                  <p className="text-sm text-gray-600 mb-3">Drag and drop a .tar.gz file here</p>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      fileInputRef.current?.click();
                    }}
                    disabled={isImporting}
                  >
                    <Upload className="h-4 w-4 mr-2" />
                    Browse Files
                  </Button>
                </div>
              )}
              <input
                ref={fileInputRef}
                id="file"
                type="file"
                accept=".tar.gz"
                onChange={handleFileSelect}
                className="hidden"
              />
            </div>
          </div>

          {/* Agent Name */}
          <div className="space-y-2">
            <Label htmlFor="agentName">Agent Name *</Label>
            <Input
              id="agentName"
              value={agentName}
              onChange={(e) => setAgentName(e.target.value)}
              placeholder="Enter agent name"
              disabled={isImporting}
            />
          </div>

          {/* Agent Description */}
          <div className="space-y-2">
            <Label htmlFor="agentDescription">Description (optional)</Label>
            <Textarea
              id="agentDescription"
              value={agentDescription}
              onChange={(e) => setAgentDescription(e.target.value)}
              placeholder="Enter agent description"
              rows={3}
              disabled={isImporting}
            />
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end space-x-2 pt-4">
            <Button variant="outline" onClick={handleClose} disabled={isImporting}>
              Cancel
            </Button>
            <Button
              onClick={handleImport}
              disabled={isImporting || !selectedFile || !agentName.trim()}
            >
              {isImporting ? 'Importing...' : 'Import Agent'}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};
