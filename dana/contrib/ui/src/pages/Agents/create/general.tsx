import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import {
  Edit,
  X,
  // Expand,
  // Collapse,
  Book,
  Network,
  Tools,
  Code,
  List,
  Refresh,
} from 'iconoir-react';
import { AgentEditor } from '@/components/agent-editor';
import { useState } from 'react';
import AgentGenerationChat from '@/components/agent-generation-chat';
import { DEFAULT_DANA_AGENT_CODE, DANA_AGENT_PLACEHOLDER } from '@/constants/dana-code';
import AgentTestChat from '@/components/agent-test-chat';
import AgentTemplateSelector from '@/components/agent-template-selector';
import { useAgentCapabilitiesStore } from '@/stores/agent-capabilities-store';
import { MarkdownViewerSmall } from '../chat/markdown-viewer';
import MultiFileCodeEditor from '@/components/multi-file-code-editor';
import type { MultiFileProject } from '@/lib/api';
import DanaAvatar from '/agent-avatar/javis-avatar.svg';
import GeorgiaAvatar from '/agent-avatar/georgia-avatar.svg';

function AgentMiddlePane({
  danaCode,
  setValue,
  multiFileProject,
  setMultiFileProject,
}: {
  danaCode: string;
  setValue: any;
  multiFileProject?: MultiFileProject | null;
  setMultiFileProject?: (project: MultiFileProject | null) => void;
}) {
  const [activeTab, setActiveTab] = useState('Summary');
  const { capabilities } = useAgentCapabilitiesStore();

  const tabs = [
    { label: 'Summary', icon: <List className="mr-1 w-4 h-4" /> },
    { label: 'Knowledge', icon: <Book className="mr-1 w-4 h-4" /> },
    { label: 'Workflow', icon: <Network className="mr-1 w-4 h-4" /> },
    { label: 'Tools', icon: <Tools className="mr-1 w-4 h-4" /> },
    { label: 'Code', icon: <Code className="mr-1 w-4 h-4" /> },
  ];
  return (
    <div className="flex flex-col w-[40%] border-r border-gray-200 bg-white h-full">
      {/* Header with Summary, Edit, Update Agent */}
      <div className="flex justify-between items-center px-4 py-3 bg-white border-b border-gray-100">
        <div className="flex gap-2 items-center">
          <div className="text-lg font-semibold text-gray-900">Summary</div>
          <div className="flex gap-2 items-center">
            <Button variant="outline" size="sm" className="flex gap-1 items-center">
              <Edit className="w-4 h-4" />
              Edit
            </Button>
          </div>
        </div>
        <div>
          <Button variant="outline" size="sm" className="flex gap-1 items-center">
            <Refresh className="w-4 h-4" />
            Update Agent
          </Button>
        </div>
      </div>
      {/* Tabs header */}
      <div className="flex flex-row bg-gray-50 border-b border-gray-200">
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
      <div className="overflow-auto flex-1 p-6 h-full">
        {activeTab === 'Summary' && (
          <div className="text-gray-700">
            <MarkdownViewerSmall>{capabilities?.summary ?? ''}</MarkdownViewerSmall>
          </div>
        )}
        {activeTab === 'Knowledge' && (
          <div className="text-gray-700">
            <MarkdownViewerSmall>{capabilities?.knowledge?.join('\n -') ?? ''}</MarkdownViewerSmall>
          </div>
        )}
        {activeTab === 'Workflow' && (
          <div className="text-gray-700">
            <MarkdownViewerSmall>{capabilities?.workflow?.join('\n') ?? ''}</MarkdownViewerSmall>
          </div>
        )}
        {activeTab === 'Tools' && (
          <div className="text-gray-700">
            <MarkdownViewerSmall>{capabilities?.tools?.join('\n - ') ?? ''}</MarkdownViewerSmall>
          </div>
        )}
        {activeTab === 'Code' && (
          <div className="h-full text-gray-700">
            {multiFileProject ? (
              <MultiFileCodeEditor
                project={multiFileProject}
                onFileChange={(file, newContent) => {
                  // Update the file content in the multi-file project
                  if (multiFileProject && setMultiFileProject) {
                    const updatedProject = {
                      ...multiFileProject,
                      files: multiFileProject.files.map((f) =>
                        f.filename === file.filename ? { ...f, content: newContent } : f,
                      ),
                    };
                    setMultiFileProject(updatedProject);

                    // If it's the main file, also update the main code editor
                    if (file.filename === multiFileProject.main_file) {
                      setValue('general_agent_config.dana_code', newContent);
                    }
                  }
                }}
                onDownload={(project) => {
                  // Call the API to download as ZIP
                  fetch('/api/agents/write-files', {
                    method: 'POST',
                    headers: {
                      'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(project),
                  })
                    .then((response) => response.blob())
                    .then((blob) => {
                      const url = window.URL.createObjectURL(blob);
                      const a = document.createElement('a');
                      a.href = url;
                      a.download = `${project.name.replace(' ', '_')}.zip`;
                      document.body.appendChild(a);
                      a.click();
                      window.URL.revokeObjectURL(url);
                      document.body.removeChild(a);
                    })
                    .catch((error) => {
                      console.error('Download failed:', error);
                    });
                }}
                className="h-full"
              />
            ) : (
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
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export function GeneralAgentPage({
  form,
  watch,
  isDragOver,
}: {
  form: any;
  watch: any;
  isDragOver: boolean;
  fileInputRef: any;
  handleFileInputChange: any;
  triggerFileInput: any;
}) {
  const [_, setIsGeneratingCode] = useState(false);
  const [showTemplateSelector, setShowTemplateSelector] = useState(false);
  // const [isRightPanelMaximized, setIsRightPanelMaximized] = useState(false);
  const [multiFileProject, setMultiFileProject] = useState<MultiFileProject | null>(null);

  const { setValue } = form;

  const danaCode = watch('general_agent_config.dana_code', DEFAULT_DANA_AGENT_CODE);
  const agentName = watch('name', 'Product Assistant');
  const agentDescription = watch('description', 'A test agent');

  console.log({ multiFileProject });

  const handleCodeGenerated = (
    code: string,
    name?: string,
    description?: string,
    multiFileProject?: MultiFileProject,
  ) => {
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

    // Store multi-file project if provided
    if (multiFileProject) {
      setMultiFileProject(multiFileProject);
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
        <div
          className={cn(
            'flex flex-col w-[30%] border-r border-gray-200',
            // isRightPanelMaximized && 'hidden',
          )}
        >
          {/* Header */}
          <div className="flex justify-between items-center p-4 bg-gray-50 border-b border-gray-200">
            <div className="flex gap-2 items-center">
              <img className="w-8 h-8" src={DanaAvatar} alt="Agent avatar" />
              <h2 className="text-lg font-semibold text-gray-900">Chat with Dana</h2>
            </div>
          </div>

          {/* Content */}
          <div className="overflow-hidden flex-1">
            <AgentGenerationChat
              onCodeGenerated={handleCodeGenerated}
              currentCode={danaCode}
              className="h-full"
              onGenerationStart={handleGenerationStart}
            />
          </div>
        </div>

        {/* Middle Pane - Tabs */}
        <AgentMiddlePane
          danaCode={danaCode}
          setValue={setValue}
          multiFileProject={multiFileProject}
          setMultiFileProject={setMultiFileProject}
        />

        {/* Right Panel - Product Assistant */}
        <div
          className={cn(
            'flex flex-col flex-1',
            // isRightPanelMaximized && 'w-full'
          )}
        >
          {/* Header */}
          <div className="flex justify-between items-center p-4 bg-gray-50 border-b border-gray-200">
            <div className="flex gap-2 items-center">
              <img className="w-8 h-8" src={GeorgiaAvatar} alt="Georgia avatar" />
              <h2 className="text-lg font-semibold text-gray-900">Georgia</h2>
            </div>
            {/* <div className="flex gap-2">
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
              <Button variant="ghost" size="sm" className="p-1">
                <X className="w-4 h-4" />
              </Button>
            </div> */}
          </div>

          {/* Chat Content */}
          <div className="overflow-hidden flex-1">
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
