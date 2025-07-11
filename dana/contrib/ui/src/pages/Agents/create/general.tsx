import { cn } from '@/lib/utils';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Edit } from 'iconoir-react';
import { AgentEditor } from '@/components/agent-editor';
import { CloudUpload } from 'iconoir-react';
import { useState } from 'react';
import AgentGenerationChat from '@/components/agent-generation-chat';
import { DEFAULT_DANA_AGENT_CODE, DANA_AGENT_PLACEHOLDER } from '@/constants/dana-code';

export function GeneralAgentPage({
  form,
  watch,
  isDragOver,
  fileInputRef,
  handleFileInputChange,
  triggerFileInput,
  onCreateAgent,
  isCreating,
}: {
  form: any;
  watch: any;
  isDragOver: boolean;
  fileInputRef: any;
  handleFileInputChange: any;
  triggerFileInput: any;
  onCreateAgent: () => Promise<void>;
  isCreating: boolean;
}) {
  const [isEditingDescription, setIsEditingDescription] = useState(false);
  const [isGeneratingCode, setIsGeneratingCode] = useState(false);

  const { register, setValue, formState } = form;
  const isDisabled = !formState.isValid || isCreating;

  const avatar = watch('avatar');
  const danaCode = watch('general_agent_config.dana_code', DEFAULT_DANA_AGENT_CODE);

  const handleCodeGenerated = (code: string, name?: string, description?: string) => {
    // Update the Dana code in the form
    setValue('general_agent_config.dana_code', code);

    // Update agent name if provided
    if (name) {
      setValue('name', name);
    }

    // Update description if provided
    if (description) {
      setValue('description', description);
    }
  };

  const handleGenerationStart = () => {
    setIsGeneratingCode(true);
  };

  return (
    <div
      className={cn(
        'flex w-full flex-col h-[calc(100vh-70px)] gap-4 bg-gray-50',
        isDragOver && 'opacity-50',
      )}
    >
      <div className="flex flex-row gap-4 px-6 pt-4 h-full">
        {/* Left side - Agent Info and Chat */}
        <div className="flex flex-col w-[400px] gap-4">
          {/* Agent Info Card */}
          <div className="flex flex-col gap-4 p-4 rounded-xl border border-gray-200 dark:border-gray-300 bg-background">
            <img
              src={`/agent-avatar${avatar}`}
              alt="agent-placeholder"
              className="rounded-full size-10"
            />
            <div className="flex flex-col gap-1">
              <input
                className="py-1 w-full text-xl font-semibold text-gray-900 border-b border-gray-900 bg-background border-l-none border-r-none border-t-none focus:outline-none placeholder:text-gray-300"
                {...register('name', { required: true })}
                id="name"
                data-testid="name"
                placeholder="Agent Name"
              />
            </div>
            <div className="flex flex-col gap-1 h-full">
              {isEditingDescription ? (
                <div className="flex flex-col gap-1">
                  <Label className="text-sm font-semibold text-gray-600">Description</Label>
                  <Textarea
                    {...register('description')}
                    id="description"
                    data-testid="description"
                    placeholder="Describe what can the tool do. E.g. search the web, analyse data, summarise content"
                    className="bg-background min-h-22 border border-gray-300 rounded-lg p-2.5 text-sm text-gray-900 focus:outline-none resize-none"
                  />
                </div>
              ) : (
                <div className="flex flex-col gap-2">
                  <span className="text-sm text-gray-300">(no description)</span>
                  <Button
                    variant="tertiary"
                    className="gap-2 w-max"
                    onClick={() => setIsEditingDescription(true)}
                  >
                    <Edit className="text-gray-600" width={18} height={18} strokeWidth={2} />
                    <span className="text-sm text-gray-600">Add description</span>
                  </Button>
                </div>
              )}
            </div>
          </div>

          {/* Agent Generation Chat */}
          <div className="flex-1 min-h-0">
            <AgentGenerationChat
              onCodeGenerated={handleCodeGenerated}
              currentCode={danaCode}
              className="h-full"
              onGenerationStart={handleGenerationStart}
            />
          </div>
        </div>

        {/* Right side - Agent Configuration */}
        <div className="flex flex-col flex-1 gap-2 h-full">
          <div className="flex flex-col gap-2 h-full">
            <div className="flex flex-row gap-1 justify-between">
              <div className="flex flex-col gap-1">
                <Label className="text-sm font-semibold text-gray-900">Agent Configuration</Label>
                <span className="text-sm text-gray-600">Use DANA to configure your agent</span>
              </div>
              <input
                type="file"
                accept=".na"
                ref={fileInputRef}
                onChange={handleFileInputChange}
                className="hidden"
              />
              <div className="flex gap-2 items-center">
                <Button
                  leftSection={<CloudUpload />}
                  variant="outline"
                  className="w-max bg-background"
                  onClick={(e) => {
                    e.preventDefault();
                    triggerFileInput();
                  }}
                >
                  Upload .na file
                </Button>
              </div>
            </div>

            <div className="flex-1 min-h-0">
              <AgentEditor
                value={danaCode ?? DEFAULT_DANA_AGENT_CODE}
                onChange={(value) => {
                  console.log('AgentEditor onChange called:', {
                    value,
                    currentDanaCode: danaCode,
                    isDifferent: value !== danaCode,
                  });
                  setValue('general_agent_config.dana_code', value);
                }}
                placeholder={DANA_AGENT_PLACEHOLDER}
                onSave={() => {}}
                enableAnimation={true}
                animationSpeed={25}
                enableAutoValidation={true}
                autoValidationDelay={1000}
              />
            </div>
          </div>
        </div>
      </div>

      <div className="flex gap-4 justify-end px-6 py-4 bg-white border-t">
        <Button size="lg" disabled={isDisabled} className="gap-2 w-max" onClick={onCreateAgent}>
          {isCreating ? 'Creating Agent...' : 'Create Agent'}
        </Button>
      </div>
    </div>
  );
}
