import { ArrowLeft, Xmark } from 'iconoir-react';
import { useDanaAgentForm } from '@/hooks/use-dana-agent-form';
import { useDragDrop } from '@/hooks/use-drag-drop';
import { cn } from '@/lib/utils';
import { useNavigate } from 'react-router-dom';
import { GeneralAgentPage } from './general';
import SelectKnowledgePage from './select-knowledge';
import { IconButton } from '@/components/ui/button';
import { Button } from '@/components/ui/button';
import { useState } from 'react';
import type { MultiFileProject } from '@/lib/api';

export function CreateAgentPage() {
  const { form, onCreateAgent, isCreating, error } = useDanaAgentForm();
  const { watch, setValue } = form;
  const navigate = useNavigate();

  // Multi-file project state at the top level
  const [multiFileProject, setMultiFileProject] = useState<MultiFileProject | null>(null);

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
      {/* {isDragOver && <DragOverComponent title="Drag file here" description="(only .na file)" />} */}
      <header
        className={cn(
          'h-[70px] flex items-center justify-between px-8 py-4 bg-white border-b border-gray-200 shadow-sm',
          isDragOver && 'opacity-50',
        )}
      >
        <div className="flex gap-4 items-center">
          {step === 'select-knowledge' && (
            <IconButton
              variant="ghost"
              size="sm"
              onClick={() => {
                setValue('step', 'general');
              }}
              className="p-2 rounded-lg transition-colors hover:bg-gray-100"
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
                className="rounded-full border-2 border-gray-100 size-10"
              />
            </div>
          )}

          <div className="flex flex-col">
            <h1 className="text-xl font-bold leading-tight text-gray-900">
              {step === 'general' ? 'Agent Builder' : name || 'Agent'}
            </h1>
          </div>
        </div>
        <div className="flex gap-3 items-center">
          {step === 'general' && (
            <>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  navigate('/agents');
                }}
                className="text-gray-600 hover:text-gray-900"
              >
                Discard
              </Button>
              <Button
                variant="default"
                size="sm"
                onClick={() => onCreateAgent(multiFileProject)}
                disabled={isCreating}
                className="text-white bg-blue-600 hover:bg-blue-700"
              >
                {isCreating ? 'Deploying...' : 'Deploy Agent'}
              </Button>
            </>
          )}
          {step === 'select-knowledge' && (
            <IconButton
              variant="ghost"
              size="sm"
              onClick={() => {
                navigate('/agents');
              }}
              className="p-2 rounded-lg transition-colors hover:bg-gray-100"
              aria-label="Close and return to agents"
            >
              <Xmark className="text-gray-500 size-5" strokeWidth={2} />
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
          multiFileProject={multiFileProject}
          setMultiFileProject={setMultiFileProject}
        />
      )}
      {step === 'select-knowledge' && (
        <SelectKnowledgePage
          onCreateAgent={() => onCreateAgent(multiFileProject)}
          isCreating={isCreating}
          error={error}
          form={form}
        />
      )}
    </div>
  );
}
