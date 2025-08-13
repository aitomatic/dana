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
  return (
    <div className="flex flex-col w-full h-full">
      {(isUploading || isDeepExtracting) && (
        <div className="flex flex-col gap-2">
          <Skeleton className="w-[300px] h-4 rounded-full" />
          <Skeleton className="w-[250px] h-4 rounded-full" />
          <Skeleton className="w-[200px] h-4 rounded-full" />
        </div>
      )}
      {!isDeepExtracting &&
        (isUploading === false && isEditing ? (
          <div className="flex flex-col w-full h-full">
            <MarkdownEditor value={value} onChange={setValue} />
          </div>
        ) : (
          <FadeText text={value} />
        ))}
    </div>
  );
};
