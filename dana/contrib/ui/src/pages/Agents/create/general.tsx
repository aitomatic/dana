import { cn } from '@/lib/utils';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Edit, X, Expand, Collapse, Book, Network, Tools, Code, List, Refresh } from 'iconoir-react';
import { AgentEditor } from '@/components/agent-editor';
import { CloudUpload } from 'iconoir-react';
import { useState } from 'react';
import AgentGenerationChat from '@/components/agent-generation-chat';
import { DEFAULT_DANA_AGENT_CODE, DANA_AGENT_PLACEHOLDER } from '@/constants/dana-code';
import AgentTestChat from '@/components/agent-test-chat';
import AgentTemplateSelector from '@/components/agent-template-selector';
import { useAgentCapabilitiesStore } from '@/stores/agent-capabilities-store';
import { MarkdownViewerSmall } from '../chat/markdown-viewer';

function AgentMiddlePane({ danaCode, setValue }: { danaCode: string; setValue: any }) {
  const [activeTab, setActiveTab] = useState('Summary');
  const { capabilities } = useAgentCapabilitiesStore();

  const tabs = [
    { label: 'Summary', icon: <List className="w-4 h-4 mr-1" /> },
    { label: 'Knowledge', icon: <Book className="w-4 h-4 mr-1" /> },
    { label: 'Workflow', icon: <Network className="w-4 h-4 mr-1" /> },
    { label: 'Tools', icon: <Tools className="w-4 h-4 mr-1" /> },
    { label: 'Code', icon: <Code className="w-4 h-4 mr-1" /> },
  ];
  return (
    <div className="flex flex-col w-[40%] border-r border-gray-200 bg-white h-full">
      {/* Header with Summary, Edit, Update Agent */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 bg-white">
        <div className='flex items-center gap-2'>

          <div className="font-semibold text-lg text-gray-900">Summary</div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" className="flex items-center gap-1">
              <Edit className="w-4 h-4" />
              Edit
            </Button>
          </div>
        </div>
        <div>
          <Button variant="outline" size="sm" className="flex items-center gap-1">
            <Refresh className="w-4 h-4" />
            Update Agent
          </Button>
        </div>
      </div>
      {/* Tabs header */}
      <div className="flex flex-row border-b border-gray-200 bg-gray-50">
        {tabs.map((tab) => (
          <button
            key={tab.label}
            className={cn(
              'px-4 py-2 text-sm font-medium focus:outline-none flex items-center',
              activeTab === tab.label
                ? 'border-b-2 border-black text-black-900'
                : 'text-gray-500 hover:text-black-900',
            )}
            onClick={() => setActiveTab(tab.label)}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>
      {/* Tab content */}
      <div className="flex-1 p-6 overflow-auto h-full">
        {activeTab === 'Summary' && <div className="text-gray-700">
          <MarkdownViewerSmall>{capabilities?.summary ?? ''}</MarkdownViewerSmall>
        </div>}
        {activeTab === 'Knowledge' && <div className="text-gray-700">
          <MarkdownViewerSmall>{capabilities?.knowledge?.join('\n -') ?? ''}</MarkdownViewerSmall>
        </div>}
        {activeTab === 'Workflow' && <div className="text-gray-700">
          <MarkdownViewerSmall>{capabilities?.workflow?.join('\n') ?? ''}</MarkdownViewerSmall>
        </div>}
        {activeTab === 'Tools' && <div className="text-gray-700">
          <MarkdownViewerSmall>{capabilities?.tools?.join('\n - ') ?? ''}</MarkdownViewerSmall>
        </div>}
        {activeTab === 'Code' && <div className="text-gray-700 h-full">
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
            onSave={() => { }}
            enableAnimation={true}
            animationSpeed={25}
            enableAutoValidation={true}
            autoValidationDelay={1000}
          /></div>}
      </div>
    </div>
  );
}

export function GeneralAgentPage({
  form,
  watch,
  isDragOver,
  fileInputRef,
  handleFileInputChange,
  triggerFileInput,
}: {
  form: any;
  watch: any;
  isDragOver: boolean;
  fileInputRef: any;
  handleFileInputChange: any;
  triggerFileInput: any;
}) {
  const [isEditingDescription, setIsEditingDescription] = useState(false);
  const [_, setIsGeneratingCode] = useState(false);
  const [showTemplateSelector, setShowTemplateSelector] = useState(false);
  const [showEditor, setShowEditor] = useState(false);
  const [isRightPanelMaximized, setIsRightPanelMaximized] = useState(false);

  const { register, setValue } = form;

  const avatar = watch('avatar');
  const danaCode = watch('general_agent_config.dana_code', DEFAULT_DANA_AGENT_CODE);
  const agentName = watch('name', 'Product Assistant');
  const agentDescription = watch('description', 'A test agent');

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

  const handleTemplateSelect = (
    templateCode: string,
    templateName: string,
    templateDescription: string,
  ) => {
    setValue('general_agent_config.dana_code', templateCode);
    setValue('name', templateName);
    setValue('description', templateDescription);
    setShowTemplateSelector(false);
  };

  return (
    <div
      className={cn(
        'flex w-full flex-col h-[calc(100vh-70px)] bg-white',
        isDragOver && 'opacity-50',
      )}
    >
      <div className="flex flex-row h-full">
        {/* Left Panel - Chat with Dana */}
        <div className={cn(
          "flex flex-col w-[30%] border-r border-gray-200",
          isRightPanelMaximized && "hidden"
        )}>
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gray-50">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">D</span>
              </div>
              <h2 className="text-lg font-semibold text-gray-900">Chat with Dana</h2>
            </div>
            <div className="flex gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowEditor(!showEditor)}
                className="text-xs"
              >
                {showEditor ? 'Summary' : 'Edit'}
              </Button>
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-hidden">
            {showEditor ? (
              <div className="h-full flex flex-col">
                {/* Agent Info Card */}
                <div className="p-4 border-b border-gray-200">
                  <div className="flex items-center gap-3 mb-4">
                    <img
                      src={`/agent-avatar${avatar}`}
                      alt="agent-placeholder"
                      className="rounded-full size-10"
                    />
                    <div className="flex-1">
                      <input
                        className="py-1 w-full text-lg font-semibold text-gray-900 border-b border-gray-300 bg-transparent focus:outline-none focus:border-blue-500 placeholder:text-gray-400"
                        {...register('name', { required: true })}
                        id="name"
                        data-testid="name"
                        placeholder="Agent Name"
                      />
                    </div>
                  </div>

                  <div className="flex flex-col gap-2">
                    {isEditingDescription ? (
                      <div className="flex flex-col gap-1">
                        <Label className="text-sm font-semibold text-gray-600">Description</Label>
                        <Textarea
                          {...register('description')}
                          id="description"
                          data-testid="description"
                          placeholder="Describe what can the tool do. E.g. search the web, analyse data, summarise content"
                          className="bg-background min-h-20 border border-gray-300 rounded-lg p-2.5 text-sm text-gray-900 focus:outline-none resize-none"
                        />
                      </div>
                    ) : (
                      <div className="flex flex-col gap-2">
                        <span className="text-sm text-gray-400">(no description)</span>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="gap-2 w-max text-gray-600 hover:text-gray-900"
                          onClick={() => setIsEditingDescription(true)}
                        >
                          <Edit className="w-4 h-4" strokeWidth={2} />
                          <span className="text-sm">Add description</span>
                        </Button>
                      </div>
                    )}
                  </div>
                </div>

                {/* Agent Configuration */}
                <div className="flex-1 flex flex-col">
                  <div className="flex items-center justify-between p-4 border-b border-gray-200">
                    <div className="flex flex-col gap-1">
                      <Label className="text-sm font-semibold text-gray-900">Agent Configuration</Label>
                      <span className="text-sm text-gray-600">Use DANA to configure your agent</span>
                    </div>
                    <div className="flex gap-2 items-center">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setShowTemplateSelector(true)}
                        className="gap-2"
                      >
                        📋 Templates
                      </Button>
                      <input
                        type="file"
                        accept=".na"
                        ref={fileInputRef}
                        onChange={handleFileInputChange}
                        className="hidden"
                      />
                      <Button
                        leftSection={<CloudUpload />}
                        variant="outline"
                        size="sm"
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
                      onSave={() => { }}
                      enableAnimation={true}
                      animationSpeed={25}
                      enableAutoValidation={true}
                      autoValidationDelay={1000}
                    />
                  </div>
                </div>
              </div>
            ) : (
              <AgentGenerationChat
                onCodeGenerated={handleCodeGenerated}
                currentCode={danaCode}
                className="h-full"
                onGenerationStart={handleGenerationStart}
              />
            )}
          </div>
        </div>

        {/* Middle Pane - Tabs */}
        <AgentMiddlePane danaCode={danaCode} setValue={setValue} />

        {/* Right Panel - Product Assistant */}
        <div className={cn(
          "flex flex-col flex-1",
          isRightPanelMaximized && "w-full"
        )}>
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gray-50">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-purple-500 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">P</span>
              </div>
              <h2 className="text-lg font-semibold text-gray-900">{agentName}</h2>
            </div>
            <div className="flex gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsRightPanelMaximized(!isRightPanelMaximized)}
                className="p-1"
              >
                {isRightPanelMaximized ? (
                  <Collapse className="w-4 h-4" />
                ) : (
                  <Expand className="w-4 h-4" />
                )}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="p-1"
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
          </div>

          {/* Chat Content */}
          <div className="flex-1 overflow-hidden">
            <AgentTestChat
              agentCode={danaCode}
              agentName={agentName}
              agentDescription={agentDescription}
              className="h-full"
            />
          </div>
        </div>
      </div>

      {/* Template Selector Modal */}
      {showTemplateSelector && (
        <div className="flex fixed inset-0 z-50 justify-center items-center">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black bg-opacity-50 transition-opacity duration-300"
            onClick={() => setShowTemplateSelector(false)}
          />

          {/* Modal */}
          <div className="relative w-[90vw] max-w-6xl h-[80vh] bg-white rounded-lg shadow-2xl overflow-hidden">
            <div className="flex flex-col h-full">
              {/* Header */}
              <div className="flex justify-between items-center p-6 border-b border-gray-200">
                <div>
                  <h2 className="text-xl font-semibold text-gray-900">Choose Agent Template</h2>
                  <p className="mt-1 text-sm text-gray-600">
                    Select a template to get started quickly, or start from scratch
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowTemplateSelector(false)}
                  className="p-2 hover:bg-gray-200"
                >
                  <X className="w-5 h-5" />
                </Button>
              </div>

              {/* Content */}
              <div className="overflow-hidden flex-1 p-6">
                <AgentTemplateSelector onTemplateSelect={handleTemplateSelect} className="h-full" />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
