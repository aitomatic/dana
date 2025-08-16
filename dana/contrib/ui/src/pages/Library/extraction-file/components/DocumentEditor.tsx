import { Skeleton } from '@/components/ui/skeleton';
import MarkdownEditor from '@/components/markdown-editor';
import { MarkdownViewerSmall } from '@/pages/Agents/chat/markdown-viewer';

interface FadeTextProps {
  text: string | undefined;
}

const FadeText = ({ text }: FadeTextProps) => {
  return (
    <div
      className={`flex overflow-y-auto w-full min-w-full h-full transition-opacity duration-500 scrollbar-hide`}
      key={text ? text.slice(0, 16) : 'empty'}
    >
      <MarkdownViewerSmall>{text as string}</MarkdownViewerSmall>
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
  console.log('[DocumentEditor] value:', value);
  console.log('[DocumentEditor] value length:', value?.length);
  console.log('[DocumentEditor] value preview:', value?.substring(0, 200));
  console.log('[DocumentEditor] isEditing:', isEditing);
  console.log('[DocumentEditor] isUploading:', isUploading);
  console.log('[DocumentEditor] isDeepExtracting:', isDeepExtracting);

  return (
    <div className="flex flex-col w-full h-full">
      {(isUploading || isDeepExtracting) && (
        <div className="flex flex-col gap-2">
          <Skeleton className="w-[300px] h-4 rounded-full" />
          <Skeleton className="w-[250px] h-4 rounded-full" />
          <Skeleton className="w-[200px] h-4 rounded-full" />
          <div className="flex items-center gap-2 mt-2">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600"></div>
            <span className="text-sm text-gray-600">
              {isUploading ? 'Uploading file...' : 'Extracting content...'}
            </span>
          </div>
        </div>
      )}
      {!isDeepExtracting &&
        !isUploading &&
        (isEditing ? (
          <div className="flex flex-col w-full h-full">
            <MarkdownEditor value={value} onChange={setValue} />
          </div>
        ) : (
          <FadeText text={value} />
        ))}
    </div>
  );
};
