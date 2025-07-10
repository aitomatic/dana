import { ArrowLeft, Xmark } from 'iconoir-react';
import { useDanaAgentForm } from '@/hooks/use-dana-agent-form';
import { useDragDrop } from '@/hooks/use-drag-drop';
import { cn } from '@/lib/utils';
import { DragOverComponent } from '@/components/drag-over-component';
import { useNavigate } from 'react-router-dom';
import { GeneralAgentPage } from './general';
import SelectKnowledgePage from './select-knowledge';
import { IconButton } from '@/components/ui/button';

export function CreateAgentPage() {
  const { form } = useDanaAgentForm();
  const { watch, setValue } = form;
  const navigate = useNavigate();

  const handleFileUpload = (file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target?.result as string;
      setValue('general_agent_config.dana_code', text);
    };
    reader.readAsText(file);
  };

  const { isDragOver, dragOverProps, fileInputRef, handleFileInputChange, triggerFileInput } =
    useDragDrop({
      onFileUpload: handleFileUpload,
      acceptedFileTypes: ['.na'],
    });

  const step = watch('step');
  const name = watch('name');
  const avatar = watch('avatar');

  return (
    <div className="flex flex-col w-full h-full" {...dragOverProps}>
      {isDragOver && <DragOverComponent title="Drag file here" description="(only .na file)" />}
      <header
        className={cn(
          'h-[70px] flex items-center justify-between px-8 py-4 bg-white border-b border-gray-200 shadow-sm',
          isDragOver && 'opacity-50',
        )}
      >
        <div className="flex items-center gap-4">
          {step === 'select-knowledge' && (
            <IconButton
              variant="ghost"
              size="sm"
              onClick={() => {
                setValue('step', 'general');
              }}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              aria-label="Go back"
            >
              <ArrowLeft className="size-5" strokeWidth={2} />
            </IconButton>
          )}

          {step === 'select-knowledge' && avatar && (
            <div className="flex-shrink-0">
              <img
                src={`/agent-avatar${avatar}`}
                alt="Agent avatar"
                className="rounded-full size-10 border-2 border-gray-100"
              />
            </div>
          )}

          <div className="flex flex-col">
            <h1 className="text-xl font-bold text-gray-900 leading-tight">
              {step === 'general' ? 'Create Domain-Expert Agent' : name || 'Agent'}
            </h1>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {step === 'general' && (
            <IconButton
              variant="ghost"
              size="sm"
              onClick={() => {
                navigate('/agents');
              }}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              aria-label="Close and return to agents"
            >
              <Xmark className="size-5 text-gray-500" strokeWidth={2} />
            </IconButton>
          )}
        </div>
      </header>

      {step === 'general' && (
        <GeneralAgentPage
          form={form}
          watch={watch}
          isDragOver={isDragOver}
          fileInputRef={fileInputRef}
          handleFileInputChange={handleFileInputChange}
          triggerFileInput={triggerFileInput}
        />
      )}
      {step === 'select-knowledge' && <SelectKnowledgePage />}
    </div>
  );
}
