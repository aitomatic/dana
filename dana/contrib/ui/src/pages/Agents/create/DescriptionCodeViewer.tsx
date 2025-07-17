import { useEffect, useState } from 'react';
import { toast } from 'sonner';
import { MarkdownViewerSmall } from '../chat/markdown-viewer';
import { AgentEditor } from '@/components/agent-editor';
import { cn } from '@/lib/utils';
// import { Code, File } from 'lucide-react';
import { apiService } from '@/lib/api';

export default function DescriptionCodeViewer({
  description,
  code,
  filename,
  projectName,
  agentFolder,
}: {
  description: string;
  code: string;
  filename?: string;
  projectName?: string;
  agentFolder?: string;
}) {
  const [viewMode, setViewMode] = useState<'description' | 'code'>('code');

  const handleFileClick = async () => {
    if (!filename) return;

    try {
      let filePath: string;

      if (agentFolder) {
        // Use the actual agent folder from the API response
        // Extract the relative path from the absolute path
        let relativePath = agentFolder;
        if (agentFolder.includes('/generated/')) {
          // Extract everything from 'generated/' onwards
          relativePath = agentFolder.substring(agentFolder.indexOf('generated/'));
        } else if (agentFolder.includes('/agents/')) {
          // Extract everything from 'agents/' onwards
          relativePath = agentFolder.substring(agentFolder.indexOf('agents/'));
        }
        filePath = `${relativePath}/${filename}`;
      } else {
        // Fallback to the old pattern-matching approach
        const sanitizedName = (projectName || 'Generated_Agent')
          .toLowerCase()
          .replace(/[^a-zA-Z0-9_\-]/g, '_');
        filePath = `generated/generated_${sanitizedName}*/${filename}`;
      }

      const result = await apiService.openFileLocation(filePath);
      if (result.success) {
        toast.success('Opened file location!');
      } else {
        toast.error('Failed to open file location');
      }
    } catch (error) {
      console.error('Error opening file:', error);
      toast.error('Failed to open file location');
    }
  };

  useEffect(() => {
    if (!description || description === '') {
      setViewMode('code');
    }
  }, [code, description]);

  return (
    <div className="flex flex-col gap-2 h-full">
      <div className="flex justify-between text-gray-500">
        <div
          className={cn('flex items-center', {
            'cursor-pointer hover:text-blue-600 hover:underline': filename,
          })}
          onClick={handleFileClick}
          title={filename ? 'Click to open file location' : undefined}
        >
          {filename}
        </div>
        {/* <div className="flex items-center p-1 text-sm">
          <div
            className={cn(
              'flex items-center px-2 py-1 bg-gray-50 border border-gray-200 rounded-l-sm cursor-pointer',
              {
                'font-semibold bg-white text-gray-800': viewMode === 'description',
              },
            )}
            onClick={() => setViewMode('description')}
          >
            {' '}
            <File className="mr-1 w-4 h-4" /> Description
          </div>
          <div
            className={cn(
              'flex items-center px-2 py-1 bg-gray-50 border border-gray-200 rounded-r-sm cursor-pointer',
              {
                'font-semibold bg-white text-gray-800': viewMode === 'code',
              },
            )}
            onClick={() => setViewMode('code')}
          >
            {' '}
            <Code className="mr-1 w-4 h-4" /> Code
          </div>
        </div> */}
      </div>
      <div className="flex-1 h-full">
        {viewMode === 'description' ? (
          <MarkdownViewerSmall>{description}</MarkdownViewerSmall>
        ) : (
          <AgentEditor value={code} onChange={() => { }} readOnly={true} />
        )}
      </div>
    </div>
  );
}
