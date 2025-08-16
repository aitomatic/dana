import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { IconCopy, IconDownload } from '@tabler/icons-react';
import { toast } from 'sonner';

interface JsonViewerProps {
  open: boolean;
  onClose: () => void;
  fileUrl: string;
  fileName?: string;
}

export function JsonViewer({ open, onClose, fileUrl, fileName }: JsonViewerProps) {
  const [jsonData, setJsonData] = useState<any>(null);
  const [rawContent, setRawContent] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'formatted' | 'raw'>('formatted');

  useEffect(() => {
    if (open && fileUrl) {
      loadJsonFile();
    }
  }, [open, fileUrl]);

  const loadJsonFile = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(fileUrl);
      if (!response.ok) {
        throw new Error(`Failed to load file: ${response.statusText}`);
      }

      const content = await response.text();
      setRawContent(content);

      try {
        const parsed = JSON.parse(content);
        setJsonData(parsed);
      } catch (parseError) {
        console.warn('Failed to parse JSON, will show raw content:', parseError);
        setJsonData(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load JSON file');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyToClipboard = async () => {
    try {
      const content =
        viewMode === 'formatted' && jsonData ? JSON.stringify(jsonData, null, 2) : rawContent;
      await navigator.clipboard.writeText(content);
      toast.success('JSON content copied to clipboard');
    } catch (err) {
      toast.error('Failed to copy content');
    }
  };

  const handleDownload = () => {
    try {
      const content =
        viewMode === 'formatted' && jsonData ? JSON.stringify(jsonData, null, 2) : rawContent;
      const blob = new Blob([content], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = fileName || 'download.json';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success('JSON file downloaded');
    } catch (err) {
      toast.error('Failed to download file');
    }
  };

  const renderJsonContent = () => {
    if (loading) {
      return (
        <div className="flex justify-center items-center h-64">
          <div className="text-muted-foreground">Loading JSON file...</div>
        </div>
      );
    }

    if (error) {
      return (
        <div className="flex justify-center items-center h-64">
          <div className="text-center text-destructive">
            <p className="font-medium">Error loading JSON file</p>
            <p className="mt-1 text-sm">{error}</p>
          </div>
        </div>
      );
    }

    if (viewMode === 'raw') {
      return (
        <pre className="overflow-auto p-4 h-full font-mono text-sm whitespace-pre rounded-md bg-muted">
          {rawContent || 'No content'}
        </pre>
      );
    }

    // Formatted view
    if (jsonData) {
      return (
        <pre className="overflow-auto p-4 h-full font-mono text-sm whitespace-pre rounded-md bg-muted">
          {JSON.stringify(jsonData, null, 2)}
        </pre>
      );
    }

    // Fallback: if JSON parsing failed, show raw content with a note
    return (
      <div className="flex flex-col space-y-2 h-full">
        <p className="text-sm text-muted-foreground shrink-0">
          Could not parse as JSON. Showing raw content:
        </p>
        <pre className="overflow-auto flex-1 p-4 font-mono text-sm whitespace-pre rounded-md bg-muted">
          {rawContent || 'No content'}
        </pre>
      </div>
    );
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent
        className="flex flex-col gap-0 p-0 w-screen h-screen rounded-none min-w-screen max-w-screen"
        showCloseButton={false}
      >
        <div className="flex overflow-hidden flex-col h-full">
          {/* Header */}
          <DialogHeader className="flex flex-row justify-between items-center p-6 border-b shrink-0">
            <DialogTitle className="text-lg font-semibold">{fileName || 'JSON Viewer'}</DialogTitle>
          </DialogHeader>

          {/* Controls */}
          <div className="flex justify-between items-center p-4 border-b shrink-0 bg-background">
            <div className="flex items-center space-x-2">
              <Button
                variant={viewMode === 'formatted' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setViewMode('formatted')}
              >
                Formatted
              </Button>
              <Button
                variant={viewMode === 'raw' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setViewMode('raw')}
              >
                Raw
              </Button>
            </div>

            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleCopyToClipboard}
                disabled={loading}
              >
                <IconCopy className="mr-2 w-4 h-4" />
                Copy
              </Button>
              <Button variant="outline" size="sm" onClick={handleDownload} disabled={loading}>
                <IconDownload className="mr-2 w-4 h-4" />
                Download
              </Button>
            </div>
          </div>

          {/* JSON Content - takes remaining space */}
          <div className="overflow-hidden flex-1 p-4">
            <div className="overflow-auto h-full">{renderJsonContent()}</div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
