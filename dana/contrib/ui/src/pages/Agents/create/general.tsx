import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import {
  X,
  Book,
  Network,
  Tools,
  List,
  User,
  Page,
  Box3dCenter,
} from 'iconoir-react';
import { useState, useMemo } from 'react';
import type { ReactElement } from 'react';
import AgentGenerationChat from '@/components/agent-generation-chat';
import { DEFAULT_DANA_AGENT_CODE } from '@/constants/dana-code';
import AgentTestChat from '@/components/agent-test-chat';
import AgentTemplateSelector from '@/components/agent-template-selector';
import { useAgentCapabilitiesStore } from '@/stores/agent-capabilities-store';
import { MarkdownViewerSmall } from '../chat/markdown-viewer';
import type { MultiFileProject } from '@/lib/api';
import DanaAvatar from '/agent-avatar/javis-avatar.svg';
import GeorgiaAvatar from '/agent-avatar/georgia-avatar.svg';
import DescriptionCodeViewer from './DescriptionCodeViewer';
import MultiFileViewer from '@/components/multi-file-viewer';

function extractDescription(content: string): string {
  const match = content.match(/"""([\s\S]*?)"""/);
  return match ? match[1].trim() : '';
}

function AgentMiddlePane({
  multiFileProject,
}: {
  multiFileProject?: MultiFileProject | null;
}) {
  // Add main tab logic
  const [mainTab] = useState<'Agent Be' | 'Agent Know' | 'Agent Do'>('Agent Be');
  // Set default subTab based on mainTab
  const mainTabToSubTabs: Record<string, string[]> = {
    'Agent Be': ['Summary', 'Agent'],
    'Agent Know': ['Knowledge'],
    'Agent Do': ['Tools', 'Workflow', 'Others'],
  };
  const defaultSubTab: Record<string, string> = {
    'Agent Be': 'Summary',
    'Agent Know': 'Knowledge',
    'Agent Do': 'Tools',
  };
  const [subTab, setSubTab] = useState('Summary');
  const { capabilities } = useAgentCapabilitiesStore();

  // Update subTab when mainTab changes
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useMemo(() => { setSubTab(defaultSubTab[mainTab]); }, [mainTab]);

  // Categorize files
  const filesByType = useMemo(() => {
    const files = multiFileProject?.files || [];
    const map: Record<string, any> = {};
    files.forEach(f => { map[f.filename] = f; });
    return map;
  }, [multiFileProject]);

  // Others: files not in main tabs
  const others = (multiFileProject?.files || []).filter(
    f =>
      !['agents.na', 'knowledges.na', 'workflows.na', 'tools.na'].includes(f.filename)
  );


  // Helper to get file content/description
  const getFile = (filename: string) => filesByType[filename];
  const getDescription = (filename: string) => {
    const file = getFile(filename);
    return file ? extractDescription(file.content) : '';
  };
  const getCode = (filename: string) => getFile(filename)?.content || '';

  // Main tab icons
  const mainTabs = [
    { label: 'Agent Be', icon: <User className="mr-1 w-4 h-4" /> },
    { label: 'Agent Know', icon: <Book className="mr-1 w-4 h-4" /> },
    { label: 'Agent Do', icon: <Tools className="mr-1 w-4 h-4" /> },
  ];

  const subtabToTabs: Record<string, string> = {
    'Summary': 'Agent Be',
    'Agent': 'Agent Be',
    'Knowledge': 'Agent Know',
    'Tools': 'Agent Do',
    'Workflow': 'Agent Do',
    'Others': 'Agent Do',
  };

  // Sub-tab icons
  const subTabIcons: Record<string, ReactElement> = {
    'Summary': <List className="mr-1 w-4 h-4" />,
    'Agent': <Box3dCenter className="mr-1 w-4 h-4" />,
    'Knowledge': <Book className="mr-1 w-4 h-4" />,
    'Tools': <Tools className="mr-1 w-4 h-4" />,
    'Workflow': <Network className="mr-1 w-4 h-4" />,
    'Others': <Page className="mr-1 w-4 h-4" />,
  };

  return (
    <div className="flex flex-col w-[40%] border-r border-gray-200 bg-white h-full ">
      {/* Main Tabs */}
      <div className="flex flex-row bg-gray-100 px-4 pt-2 gap-2">
        {mainTabs.map(tab => (
          <div className={cn('flex flex-col gap-1 px-3', {
            'border-b-2 border-blue-500': subtabToTabs[subTab] === tab.label,
          })}>

            <button
              key={tab.label}
              className={cn(
                'flex items-center font-semibold text-base text-sm p-1 rounded-md',

              )}
            >
              <span className={cn('px-2 py-1 rounded-md', {
                'bg-[#E1EBFE]': tab.label === 'Agent Be',
                'bg-[#FBE8FF]': tab.label === 'Agent Know',
                'bg-[#CCFBEF]': tab.label === 'Agent Do',
              })}>
                {tab.label}
              </span>
            </button>
            <div className='flex gap-1'>
              {mainTabToSubTabs[tab.label].map(subTabItem => (
                <button
                  key={subTabItem}
                  className={cn(
                    'flex items-center font-medium text-sm p-1 -mb-[2px] px-2 rounded-t-md',
                    {
                      'border-white border border-[#1570EF] border-b-white bg-white': subTab === subTabItem,
                    }
                  )}
                  onClick={() => {
                    setSubTab(subTabItem);
                  }}
                >
                  {subTabIcons[subTabItem]}
                  {subTabItem}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
      {/* Tab Content */}
      <div className="overflow-auto flex-1 p-6 h-full">
        {subTab === 'Summary' && (
          <MarkdownViewerSmall>{capabilities?.summary ?? ''}</MarkdownViewerSmall>
        )}
        {subTab === 'Agent' && (
          <DescriptionCodeViewer
            description={getDescription('agents.na')}
            code={getCode('agents.na')}
            filename="agents.na"
            projectName={multiFileProject?.name}
          />
        )}
        {subTab === 'Knowledge' && (
          <DescriptionCodeViewer
            description={getDescription('knowledges.na')}
            code={getCode('knowledges.na')}
            filename="knowledges.na"
            projectName={multiFileProject?.name}
          />
        )}
        {subTab === 'Workflow' && (
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
        {subTab === 'Others' && (
          <MultiFileViewer
            project={{
              name: 'Other Files',
              description: 'Additional agent files',
              structure_type: 'simple',
              main_file: others[0]?.filename || '',
              files: others,
            }}
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
          multiFileProject={multiFileProject}
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
