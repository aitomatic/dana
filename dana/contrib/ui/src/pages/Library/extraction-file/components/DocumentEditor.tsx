import { Skeleton } from '@/components/ui/skeleton';
import MarkdownEditor from '@/components/markdown-editor';
import { MarkdownViewerSmall } from '@/pages/Agents/chat/markdown-viewer';
import { SystemRestart } from 'iconoir-react';
// Analytics hook available but not used in this component

interface FadeTextProps {
  text: string | undefined;
}

const FadeText = ({ text }: FadeTextProps) => {
  return (
    <div
      className={`flex overflow-auto w-full min-w-full h-full transition-opacity duration-500 scrollbar-hide`}
      key={text ? text.slice(0, 16) : 'empty'}
    >
      <MarkdownViewerSmall>{text || 'No content available'}</MarkdownViewerSmall>
    </div>
  );
};

interface DocumentEditorProps {
  isEditing: boolean;
  value: string;
  setValue: (value: string) => void;
  onSave: () => void;
  onEdit: () => void;
  isUploading: boolean;
  isDeepExtracting: boolean;
}

export const DocumentEditor = ({
  isEditing,
  value,
  setValue,
  isUploading,
  isDeepExtracting,
}: DocumentEditorProps) => {
  // Analytics hook available but not used in this component

  console.log('[DocumentEditor] value:', value);
  console.log('[DocumentEditor] value length:', value?.length);
  console.log('[DocumentEditor] value preview:', value?.substring(0, 200));
  console.log('[DocumentEditor] isEditing:', isEditing);
  console.log('[DocumentEditor] isUploading:', isUploading);
  console.log('[DocumentEditor] isDeepExtracting:', isDeepExtracting);

  return (
    <div className="flex flex-col w-full h-full">
      {isUploading && (
        <div className="flex flex-col gap-2">
          <Skeleton className="w-[300px] h-4 rounded-full" />
          <Skeleton className="w-[250px] h-4 rounded-full" />
          <Skeleton className="w-[200px] h-4 rounded-full" />
          <div className="flex gap-2 items-center mt-2">
            <SystemRestart className="animate-spin size-4" />
            <span className="text-sm text-gray-600">Uploading file...</span>
          </div>
        </div>
      )}
      {!isUploading && (
        <>
          {isDeepExtracting && value && (
            <div className="flex gap-2 items-center p-2 mb-2 bg-blue-50 rounded-md border border-blue-200">
              <SystemRestart className="text-blue-600 animate-spin size-4" />
              <span className="text-sm text-blue-600">Deep extraction in progress...</span>
            </div>
          )}
          {isEditing ? (
            <div className="flex flex-col h-full">
              <MarkdownEditor value={value} onChange={setValue} />
            </div>
          ) : (
            <FadeText text={value} />
          )}
        </>
      )}
    </div>
  );
};
