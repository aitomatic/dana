import { useState } from 'react';
import { toast } from 'sonner';
import { MarkdownViewerSmall } from '../chat/markdown-viewer';
import { AgentEditor } from '@/components/agent-editor';
import { cn } from '@/lib/utils';
import { Code, File } from 'lucide-react';
import { apiService } from '@/lib/api';

export default function DescriptionCodeViewer({
  description,
  code,
  filename,
  projectName,
}: {
  description: string;
  code: string;
  filename?: string;
  projectName?: string;
}) {
  const [viewMode, setViewMode] = useState<'description' | 'code'>('description');

  const handleFileClick = async () => {
    if (!filename) return;
    
    try {
      // Construct file path based on auto-storage pattern
      // This matches the backend auto-storage folder structure
      const sanitizedName = (projectName || 'Generated_Agent')
        .toLowerCase()
        .replace(/[^a-zA-Z0-9_\-]/g, '_');
      
      // Use the same pattern as file-paths component
      const filePath = `generated/generated_${sanitizedName}*/${filename}`;
      
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

  return (
    <div className='flex flex-col gap-2 h-full'>

      <div className="flex justify-between text-gray-500">
        <div 
          className={cn('flex items-center', {
            'cursor-pointer hover:text-blue-600 hover:underline': filename
          })}
          onClick={handleFileClick}
          title={filename ? 'Click to open file location' : undefined}
        >
          {filename}
        </div>
        <div className='flex p-1 text-sm items-center'>
          <div className={
            cn('flex items-center px-2 py-1 bg-gray-50 border border-gray-200 rounded-l-sm cursor-pointer', {
              'font-semibold bg-white text-gray-800': viewMode === 'description',
            })}
            onClick={() => setViewMode('description')}
          > <File className='w-4 h-4 mr-1' /> Description</div>
          <div className={
            cn('flex items-center px-2 py-1 bg-gray-50 border border-gray-200 rounded-r-sm cursor-pointer', {
              'font-semibold bg-white text-gray-800': viewMode === 'code',
            })}
            onClick={() => setViewMode('code')}
          > <Code className='w-4 h-4 mr-1' /> Code</div>
        </div>

      </div>
      <div className='flex-1 h-full'>
        {viewMode === 'description' ? (
          <MarkdownViewerSmall>{description}</MarkdownViewerSmall>
        ) : (
          <AgentEditor value={code} onChange={() => { }} readOnly={true} />
        )}
      </div>
    </div>
  );
} 