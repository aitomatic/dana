import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { X } from 'iconoir-react';
import { useState, useMemo } from 'react';
import AgentGenerationChat from '@/components/agent-generation-chat';
import { DEFAULT_DANA_AGENT_CODE } from '@/constants/dana-code';
import AgentTestChat from '@/components/agent-test-chat';
import AgentTemplateSelector from '@/components/agent-template-selector';
import { useAgentCapabilitiesStore } from '@/stores/agent-capabilities-store';
import { useAgentBuildingStore } from '@/stores/agent-building-store';
import { MarkdownViewerSmall } from '../chat/markdown-viewer';
import type { MultiFileProject } from '@/lib/api';
import DanaAvatar from '/agent-avatar/javis-avatar.svg';
import GeorgiaAvatar from '/agent-avatar/georgia-avatar.svg';
import DescriptionCodeViewer from './DescriptionCodeViewer';

function extractDescription(content: string): string {
  const match = content.match(/"""([\s\S]*?)"""/);
  return match ? match[1].trim() : '';
}

function AgentMiddlePane({ multiFileProject }: { multiFileProject?: MultiFileProject | null }) {
  // Add main tab logic
  const [mainTab] = useState<'Agent Be' | 'Agent Know' | 'Agent Do'>('Agent Be');
  // Set default subTab based on mainTab

  const defaultSubTab: Record<string, string> = {
    'Agent Be': 'Summary',
    'Agent Know': 'Knowledges',
    'Agent Do': 'Workflows',
  };
  const [subTab, setSubTab] = useState('Summary');
  const { capabilities } = useAgentCapabilitiesStore();

  // Update subTab when mainTab changes
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useMemo(() => {
    setSubTab(defaultSubTab[mainTab]);
  }, [mainTab]);

  // Categorize files
  const filesByType = useMemo(() => {
    const files = multiFileProject?.files || [];
    const map: Record<string, any> = {};
    files.forEach((f) => {
      map[f.filename] = f;
    });
    return map;
  }, [multiFileProject]);

  // Helper to get file content/description
  const getFile = (filename: string) => filesByType[filename];
  const getDescription = (filename: string) => {
    const file = getFile(filename);
    return file ? extractDescription(file.content) : '';
  };
  const getCode = (filename: string) => getFile(filename)?.content || '';

  // Sub-tab icons

  return (
    <div className="flex flex-col w-[55%] border-r border-gray-200 bg-white h-full ">
      <div className="flex gap-2 items-stretch p-2">
        <div
          className="flex flex-col justify-center rounded-t-md bg-[#F2F4F7] px-2 py-1 cursor-pointer"
          onClick={() => setSubTab('Summary')}
        >
          <div className="text-sm font-semibold uppercase">Summary</div>
        </div>
        {getCode('agent.na') ||
          (getCode('common.na') && (
            <div className="flex flex-col justify-center px-2 py-1 rounded-t-md bg-[#E1EBFE] gap-1">
              <div className="text-sm font-semibold uppercase">Be</div>
              <div className="flex gap-2 items-center">
                {getCode('main.na') && (
                  <div
                    className={cn('px-3 border-2 border-b-0  rounded-t-md cursor-pointer', {
                      'border-gray-900 bg-white': subTab === 'Agent',
                      'border-gray-300': subTab !== 'Agent',
                    })}
                    onClick={() => setSubTab('Agent')}
                  >
                    agent.na
                  </div>
                )}
                {getCode('common.na') && (
                  <div
                    className={cn('px-3 border-2 border-b-0  rounded-t-md cursor-pointer', {
                      'border-gray-900 bg-white': subTab === 'Common',
                      'border-gray-300': subTab !== 'Common',
                    })}
                    onClick={() => setSubTab('Common')}
                  >
                    common.na
                  </div>
                )}
              </div>
            </div>
          ))}
        {getCode('knowledge.na') && (
          <div className="flex flex-col justify-center px-2 py-1 gap-1 rounded-t-md bg-[#FDF4FF]">
            <div className="text-sm font-semibold uppercase">Know</div>
            <div className="flex gap-2 items-center">
              <div
                className={cn('px-3 border-2 border-b-0  rounded-t-md cursor-pointer', {
                  'border-gray-900 bg-white': subTab === 'Knowledges',
                  'border-gray-300': subTab !== 'Knowledges',
                })}
                onClick={() => setSubTab('Knowledges')}
              >
                knowledge.na
              </div>
            </div>
          </div>
        )}
        {getCode('workflows.na') && (
          <div className="flex flex-col justify-center px-2 py-1 gap-1 rounded-t-md bg-[#F0FDF9]">
            <div className="text-sm font-semibold uppercase">Do</div>
            <div className="flex gap-2 items-center">
              <div
                className={cn('px-3 border-2 border-b-0  rounded-t-md cursor-pointer', {
                  'border-gray-900 bg-white': subTab === 'Workflows',
                  'border-gray-300': subTab !== 'Workflows',
                })}
                onClick={() => setSubTab('Workflows')}
              >
                workflows.na
              </div>
              <div
                className={cn('px-3 border-2 border-b-0  rounded-t-md cursor-pointer', {
                  'border-gray-900 bg-white': subTab === 'Methods',
                  'border-gray-300': subTab !== 'Methods',
                })}
                onClick={() => setSubTab('Methods')}
              >
                methods.na
              </div>
              <div
                className={cn('px-3 border-2 border-b-0  rounded-t-md cursor-pointer', {
                  'border-gray-900 bg-white': subTab === 'Tools',
                  'border-gray-300': subTab !== 'Tools',
                })}
                onClick={() => setSubTab('Tools')}
              >
                tools.na
              </div>
            </div>
          </div>
        )}
      </div>
      {/* Main Tabs */}

      {/* Tab Content */}
      <div className="overflow-auto flex-1 p-6 h-full">
        {subTab === 'Summary' && (
          <MarkdownViewerSmall>{capabilities?.summary ?? ''}</MarkdownViewerSmall>
        )}
        {subTab === 'Agent' && (
          <DescriptionCodeViewer
            description={getDescription('main.na')}
            code={getCode('main.na')}
            filename="main.na"
            projectName={multiFileProject?.name}
          />
        )}
        {subTab === 'Common' && (
          <DescriptionCodeViewer
            description={getDescription('common.na')}
            code={getCode('common.na')}
            filename="common.na"
            projectName={multiFileProject?.name}
          />
        )}
        {subTab === 'Knowledges' && (
          // <div className="flex flex-col justify-between">
          <div className="flex flex-col flex-1 h-full">
            <DescriptionCodeViewer
              description={getDescription('knowledge.na')}
              code={getCode('knowledge.na')}
              filename="knowledge.na"
              projectName={multiFileProject?.name}
            />
          </div>
        )}
        {subTab === 'Workflows' && (
          <DescriptionCodeViewer
            description={getDescription('workflows.na')}
            code={getCode('workflows.na')}
            filename="workflows.na"
            projectName={multiFileProject?.name}
          />
        )}
        {subTab === 'Tools' && (
          <DescriptionCodeViewer
            description={getDescription('tools.na')}
            code={getCode('tools.na')}
            filename="tools.na"
            projectName={multiFileProject?.name}
          />
        )}
        {subTab === 'Methods' && (
          <DescriptionCodeViewer
            description={getDescription('methods.na')}
            code={getCode('methods.na')}
            filename="methods.na"
            projectName={multiFileProject?.name}
          />
        )}
      </div>
    </div>
  );
}

export function GeneralAgentPage({
  form,
  watch,
  isDragOver,
  multiFileProject,
  setMultiFileProject,
}: {
  form: any;
  watch: any;
  isDragOver: boolean;
  fileInputRef: any;
  handleFileInputChange: any;
  triggerFileInput: any;
  multiFileProject: MultiFileProject | null;
  setMultiFileProject: (project: MultiFileProject | null) => void;
}) {
  // Zustand stores
  const { currentAgent, setMultiFileProject: setBuildingMultiFileProject } =
    useAgentBuildingStore();
  const [_, setIsGeneratingCode] = useState(false);
  const [showTemplateSelector, setShowTemplateSelector] = useState(false);
  // const [isRightPanelMaximized, setIsRightPanelMaximized] = useState(false);

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
    _agentIdResp?: string,
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
      setBuildingMultiFileProject(multiFileProject);
    }
  };

  const handleGenerationStart = () => {
    setIsGeneratingCode(true);
  };

  const handlePhaseChange = (phase: 'description' | 'code_generation') => {
    // The phase is now managed by the Zustand store in the chat component
    console.log('Phase changed to:', phase);
  };

  const handleReadyForCodeGeneration = (agentId: number) => {
    // The agent ID is now managed by the Zustand store in the chat component
    console.log('Ready for code generation, agent ID:', agentId);
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
            'flex flex-col w-[25%] border-r border-gray-200',
            // isRightPanelMaximized && 'hidden',
          )}
        >
          {/* Header */}
          <div className="flex justify-between items-center p-4 bg-gray-50 border-b border-gray-200">
            <div className="flex gap-2 items-center">
              <img className="w-8 h-8" src={DanaAvatar} alt="Agent avatar" />
              <div>
                <h2 className="text-lg font-semibold text-gray-900">Chat with Dana</h2>
                <div className="flex gap-2 items-center mt-1"></div>
              </div>
            </div>
          </div>

          {/* Content */}
          <div className="overflow-hidden flex-1">
            <AgentGenerationChat
              onCodeGenerated={handleCodeGenerated}
              currentCode={danaCode}
              className="h-full"
              onGenerationStart={handleGenerationStart}
              onPhaseChange={handlePhaseChange}
              onReadyForCodeGeneration={handleReadyForCodeGeneration}
            />
          </div>
        </div>

        {/* Middle Pane - Tabs */}
        <AgentMiddlePane multiFileProject={multiFileProject} />

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
              currentFolder={currentAgent?.folder_path}
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
