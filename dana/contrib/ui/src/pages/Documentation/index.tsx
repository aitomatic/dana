import React, { useState, useMemo } from 'react';
import { Play, ChatBubble, Code, HelpCircle, Brain, Page, Search, X } from 'iconoir-react';

// Helper component for screenshot placeholders (kept for future use)
// Usage: <ScreenshotPlaceholder title="Image Title" filename="image-name.png" description="Optional description" />
const ScreenshotPlaceholder: React.FC<{ 
  title: string; 
  filename: string; 
  description?: string;
}> = ({ title, filename, description }) => (
  <div className="mt-4 p-4 bg-gray-100 rounded-lg border-2 border-dashed border-gray-300">
    <div className="text-center text-gray-500">
      <div className="w-16 h-16 mx-auto mb-2 bg-gray-200 rounded-lg flex items-center justify-center">
        <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      </div>
      <p className="text-sm font-medium">{title}</p>
      {description && <p className="text-xs text-gray-500 mt-1">{description}</p>}
      <p className="text-xs text-gray-400 mt-1">
        Replace with: <code>src="/screenshots/{filename}"</code>
      </p>
    </div>
  </div>
);

// Helper component for actual screenshots
// Usage: <Screenshot src="/screenshots/filename.png" alt="Description" caption="Optional caption" />
const Screenshot: React.FC<{ 
  src: string; 
  alt: string; 
  caption?: string;
}> = ({ src, alt, caption }) => (
  <div className="mt-4">
    <img 
      src={src} 
      alt={alt} 
      className="w-full rounded-lg border border-gray-200 shadow-sm"
    />
    {caption && (
      <p className="text-sm text-gray-700 text-center mt-2 italic">{caption}</p>
    )}
  </div>
);

// Helper component to highlight search terms
const HighlightText: React.FC<{
  text: string;
  searchQuery: string;
  className?: string;
}> = ({ text, searchQuery, className = '' }) => {
  if (!searchQuery.trim()) {
    return <span className={className}>{text}</span>;
  }

  const regex = new RegExp(`(${searchQuery.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
  const parts = text.split(regex);

  return (
    <span className={className}>
      {parts.map((part, index) => {
        if (regex.test(part)) {
          return (
            <mark key={index} className="bg-yellow-200 px-1 rounded">
              {part}
            </mark>
          );
        }
        return part;
      })}
    </span>
  );
};

// Helper component to highlight content within JSX
const HighlightContent: React.FC<{
  content: React.ReactNode;
  searchQuery: string;
}> = ({ content, searchQuery }) => {
  if (!searchQuery.trim()) {
    return <>{content}</>;
  }

  const highlightTextInNode = (node: React.ReactNode): React.ReactNode => {
    if (typeof node === 'string') {
      return <HighlightText text={node} searchQuery={searchQuery} />;
    }
    
    if (React.isValidElement(node)) {
      const element = node as React.ReactElement<any>;
      if (typeof element.props.children === 'string') {
        return React.cloneElement(element, {
          ...element.props,
          children: <HighlightText text={element.props.children} searchQuery={searchQuery} />
        });
      }
      
      if (Array.isArray(element.props.children)) {
        return React.cloneElement(element, {
          ...element.props,
          children: element.props.children.map((child: React.ReactNode) => 
            React.isValidElement(child) ? highlightTextInNode(child) : child
          )
        });
      }
    }
    
    return node;
  };

  return <>{highlightTextInNode(content)}</>;
};

const DocumentationPage: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');

  const documentationSections = [
    {
      title: 'Getting Started',
      description: 'Installation, setup, and first steps with Dana Studio',
      icon: Play,
      content: (
        <div className="space-y-4">
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">Prerequisites</h3>
            <ul className="list-disc list-inside text-gray-700 space-y-1">
              <li>Python 3.7 or higher installed on your system</li>
              <li>Basic familiarity with command-line operations</li>
            </ul>
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">Installation & Setup</h3>
            <ol className="list-decimal list-inside text-gray-700 space-y-2">
              <li><strong>Navigate to your desired directory</strong>
                <pre className="bg-gray-100 p-2 rounded mt-1 text-sm"><code>cd /path/to/your/preferred/location</code></pre>
              </li>
              <li><strong>Set up a virtual environment (recommended)</strong>
                <pre className="bg-gray-100 p-2 rounded mt-1 text-sm"><code>python3 -m venv venv<br/>source venv/bin/activate  # On Windows: venv\Scripts\activate</code></pre>
              </li>
              <li><strong>Install Dana Studio</strong>
                <pre className="bg-gray-100 p-2 rounded mt-1 text-sm"><code>pip install dana</code></pre>
              </li>
              <li><strong>Configure API providers</strong>
                <pre className="bg-gray-100 p-2 rounded mt-1 text-sm"><code>dana config</code></pre>
                <p className="text-sm text-gray-500 mt-1">Select at least one AI provider (OpenAI, Anthropic, etc.) and provide the corresponding API key</p>
              </li>
              <li><strong>Launch Dana Studio</strong>
                <pre className="bg-gray-100 p-2 rounded mt-1 text-sm"><code>dana studio</code></pre>
                <p className="text-sm text-gray-500 mt-1">Open your browser and navigate to <code>http://127.0.0.1:8080/</code></p>
              </li>
            </ol>
            
            <Screenshot 
              src="/screenshots/pre-trained-agents-dashboard.png" 
              alt="Dana Studio Installation and Setup"
              caption="Dana Studio running locally with the web interface accessible at localhost:8080"
            />
          </div>
        </div>
      ),
    },
    {
      title: 'Train Your Agent',
      description: 'Create powerful, specialized AI agents',
      icon: Brain,
      content: (
        <div className="space-y-4">
          <div>
            <h3 className="font-semibold text-xl text-gray-900 mb-2">Pre-trained Agents</h3>
            <p className="text-gray-700 mb-2">Dana Studio comes with 4 ready-to-use pre-trained agents, each equipped with specialized knowledge and workflows:</p>
            <ul className="list-disc list-inside text-gray-700 space-y-1">
              <li>Browse the available pre-trained agents in the main dashboard</li>
              <li>Click "Save to my agents and use" to add an agent to your collection</li>
              <li>Each agent is designed for specific domains and can be used immediately. You can use these agents as a starting point for your own agent training.</li>
            </ul>
            
            <Screenshot 
              src="/screenshots/train-use.png" 
              alt="Pre-trained Agents Dashboard"
              caption="Select a pre-trained agent to train from or Save and use it"
            />
          </div>
       
          <div>
            <h3 className="font-semibold text-xl text-gray-900 mb-2">Train your Agent</h3>
            <div className="space-y-3">
              <div>
                <h4 className="font-medium text-gray-800">Starting from a Pre-trained Agent</h4>
                <ol className="list-decimal list-inside text-gray-700 space-y-1 ml-4">
                  <li>Select a base agent that closely matches your intended use case</li>
                  <li>Click <b>"Train from this agent"</b> to create a customizable copy. If you don't want to start from a pre-trained agent, you can start from scratch by clicking <b>"Train New Agent"</b></li>
                  <li>Example: Try training Jordan, the Financial Analysis Expert, for your specific financial analysis needs</li>
                </ol>
              </div>
              <div>
                <h4 className="font-medium text-gray-800">Working with Dana (Dana Agent Maker)</h4>
                <p className="text-gray-700 mb-2">Dana Agent Maker is your AI-powered assistant that helps gather and organize knowledge:</p>
                <ol className="list-decimal list-inside text-gray-700 space-y-1 ml-4">
                  <li>Chat with Dana and describe your intended agent's purpose. <i><b>Hint: </b>Share details about:
domain expertise needed;
specific topics to cover;
tasks the agent should excel at;
job descriptions or role requirements.</i></li>
               
                  <li>Dana will ask clarifying questions to better understand your needs or propose a knowledge structure from the domain</li>
                  <li>After confirming the organization of the Knowledge Graph, ask Dana to <b className='text-brand-700'>generate knowledge</b> so that the topics within the graph are populated with content. </li>
                </ol>
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mt-3">
              <p className="text-sm text-yellow-800">
                <strong>Important:</strong> After Dana successfully generates new knowledge, you may need to refresh your browser page to see the updated content when clicking on nodes in the Knowledge Graph.
              </p>
            </div>
              
              </div>
            </div>
            
            <Screenshot 
              src="/screenshots/dana-agent-maker.png" 
              alt="Agent Training Interface"
              caption="The agent training interface showing conversation with Dana Agent Maker and knowledge building process"
            />
             <Screenshot 
              src="/screenshots/generate-knowledge.png" 
              alt="Agent Training Interface"
              caption="Ask Dana to generate knowledge for a new knowledge topic"
            />
          </div>

          
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">Understanding the Knowledge Graph for Domain Knowledge</h3>
            <p>As you interact with Dana to build knowledge for the target agent, you can observe the Knowledge Graph in real time and see how it evolves to reflect the updates made by Dana</p>
            <ul className="list-disc list-inside text-gray-700 space-y-1">
              <li><strong>Real-time updates:</strong> Watch the graph evolve as Dana builds knowledge</li>
              <li><strong>Interactive exploration:</strong> Click any node to view detailed content</li>
              <li><strong>Knowledge connections:</strong> See how different concepts relate to each other</li>
              <li><strong>Quality assurance:</strong> Review and validate the knowledge structure before finalizing</li>
            </ul>
            
            <Screenshot 
              src="/screenshots/knowledge-graph.png" 
              alt="Knowledge Graph Visualization"
              caption="Interactive knowledge graph showing nodes and connections between concepts"
            />
             <Screenshot 
              src="/screenshots/node-details.png" 
              alt="Agent Training Interface"
              caption="The agent training interface showing conversation with Dana Agent Maker and knowledge building process"
            />
          </div>

          <div>
            <h3 className="font-semibold text-gray-900 mb-2">Dana Code of Your Agent</h3>
            <p>
            All the code powering your agent is displayed in this section, providing complete transparency and control over your agent's functionality. This feature allows you to fully customize your agent according to your specific requirements.
            </p>
            <ul className="list-disc list-inside text-gray-700 space-y-1">
              <p className='font-medium mt-2'><strong>What you can do:</strong></p>
            <li><strong>View complete codebase:</strong> See all the code that defines your agent's behavior</li>
            <li><strong>Modify agent logic:</strong> Adjust how your agent processes and responds to inputs</li>
            <li><strong>Customize workflows:</strong> Tailor the agent's decision-making processes</li>
            <li><strong>Add business logic:</strong> Incorporate specific rules or processes unique to your organization</li>
            </ul>
            
            <Screenshot 
              src="/screenshots/dana-code.png" 
              alt="Dana Code base of your agent"
              caption="Dana Code base of your agent"
            />
            
          </div>

          <div>
            <h3 className="font-semibold text-xl text-gray-900 mb-2">Train New Agents</h3>
            <p className="text-gray-700 mb-2">If none of the pre-trained agents match your needs, you can train a new agent by clicking the "Train New Agent" button in the main dashboard.</p>
            <ul className="list-disc list-inside text-gray-700 space-y-1">
              <li>Describe the agent you want to train (e.g. "I want an agent that can help me with financial analysis")</li>
              <li>Click "Start Training", the system will suggest the templates that best match your description. The templates contain pre-built code with workflows to get you started. <b>You can always modify the agent code later.</b></li>
            </ul>
            
            <Screenshot 
              src="/screenshots/train-new-agent-1.png" 
              alt="Train New Agent"
              caption="Describe the agent you want to train"
            />
            <Screenshot 
              src="/screenshots/train-new-agent-2.png" 
              alt="Train New Agent"
              caption="The system will suggest the templates that best match your description."
            />
          </div>
        </div>
      ),
    },
    {
      title: 'Library',
      description: 'Enhance your agent with relevant documents and resources',
      icon: Page,
      content: (
        <div className="space-y-4">
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">Library: Your Knowledge Repository</h3>
            <p className="text-gray-700 mb-2">The Library serves as the central hub for all document management in Dana Studio.</p>
            
            <Screenshot 
              src="/screenshots/library-interface.png" 
              alt="Library Interface"
              caption="Document management interface with upload and processing options"
            />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">Document Processing</h3>
            <div className="space-y-3">
              <div className=" pl-4">
                <h4 className="font-medium text-gray-800">Standard Extract (Default)</h4>
                <ul className="list-disc list-inside text-gray-700 space-y-1">
                  <li>Automatic processing when documents are uploaded</li>
                  <li>Suitable for general use cases</li>
                  <li>Faster processing time</li>
                </ul>
              </div>
              <div className=" pl-4">
                <h4 className="font-medium text-gray-800">Deep Extract (Recommended for Precision)</h4>
                <ul className="list-disc list-inside text-gray-700 space-y-1">
                  <li>Enhanced information extraction</li>
                  <li>Improved retrieval accuracy</li>
                  <li>Longer processing time</li>
                  <li><strong>Available only in Library</strong> - must be activated before adding documents to agents</li>
                </ul>
                <Screenshot 
              src="/screenshots/deep-extract.png" 
              alt="Library Interface"
              caption="Document management interface with upload and processing options"
            />
              </div>
            </div>
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">Adding Documents to Your Agent</h3>
            <ol className="list-decimal list-inside text-gray-700 space-y-1">
              <li>Access Resources: Navigate to your agent's Resources section</li>
              <li>Add documents: Use "Add file from library" to select relevant files</li>
              <li>Library integration: All documents must first be processed in the Library</li>
            </ol>
            <Screenshot 
              src="/screenshots/add-document-interface.png" 
              alt="Library Interface"
              caption="Add documents to your agent"
            />
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mt-3">
              <p className="text-sm text-yellow-800">
                <strong>Important:</strong> For optimal results, use the "Deep Extract" feature in the Library before adding documents to your agent. This feature provides enhanced information extraction for better retrieval accuracy.
              </p>
            </div>
            
          </div>
        </div>
      ),
    },
    {
      title: 'Use Your Agent',
      description: 'How to interact with and get the most from your trained agents',
      icon: ChatBubble,
      content: (
        <div className="space-y-4">
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">Activation Modes</h3>
            <div className="space-y-3">
              <div>
                <h4 className="font-medium text-gray-800">Option 1: Direct Use Mode</h4>
                <ul className="list-disc list-inside text-gray-700 space-y-1 ml-4">
                  <li>Select "Use mode" from your agent's dashboard</li>
                  <li>Immediate access to chat interface</li>
                </ul>
              </div>
              <div>
                <h4 className="font-medium text-gray-800">Option 2: Agent List</h4>
                <ul className="list-disc list-inside text-gray-700 space-y-1 ml-4">
                  <li>Navigate to "My Agents"</li>
                  <li>Click "Use agent" next to your desired agent</li>
                </ul>
              </div>
            </div>
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">Chat Interface</h3>
            <p className="text-gray-700 mb-2">The chat window is your primary interaction point with your agent:</p>
            <ul className="list-disc list-inside text-gray-700 space-y-1">
              <li><strong>Natural conversation:</strong> Ask questions in plain language</li>
              <li><strong>Task assignment:</strong> Give your agent specific tasks to complete</li>
              <li><strong>Document attachment:</strong> Upload files directly to the chat for context-aware responses</li>
              <li><strong>Multi-turn conversations:</strong> Build complex discussions over multiple exchanges</li>
            </ul>
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">Best Practices for Agent Interaction</h3>
            <ul className="list-disc list-inside text-gray-700 space-y-1">
              <li>Be specific in your requests</li>
              <li>Provide context when needed</li>
              <li>Use document attachments for reference-heavy tasks</li>
              <li>Take advantage of your agent's specialized knowledge domain</li>
            </ul>
          </div>
          
          <Screenshot 
            src="/screenshots/chat-interface.png" 
            alt="Agent Chat Interface"
            caption="The chat interface for interacting with your trained agent"
          />
        </div>
      ),
    },
    {
      title: 'Tips for Success',
      description: 'Best practices and optimization strategies',
      icon: HelpCircle,
      content: (
        <div className="space-y-4">
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">Agent Training Best Practices</h3>
            <ul className="list-disc list-inside text-gray-700 space-y-1">
              <li>Start with clear objectives for your agent's role</li>
              <li>Provide comprehensive domain information to Dana</li>
              <li>Review the Knowledge Graph regularly during training</li>
              <li>Test your agent frequently during the development process</li>
            </ul>
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">Document Optimization</h3>
            <ul className="list-disc list-inside text-gray-700 space-y-1">
              <li>Use Deep Extract for critical business documents</li>
              <li>Organize files logically in your Library</li>
              <li>Regularly update your document collection</li>
              <li>Remove outdated or irrelevant materials</li>
            </ul>
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">Performance Optimization</h3>
            <ul className="list-disc list-inside text-gray-700 space-y-1">
              <li>Keep your Knowledge Graph focused and relevant</li>
              <li>Avoid information overload - quality over quantity</li>
              <li>Regular agent testing and refinement</li>
              <li>Monitor chat performance and user feedback</li>
            </ul>
          </div>
        </div>
      ),
    },
    {
      title: 'Troubleshooting',
      description: 'Common issues and solutions',
      icon: Code,
      content: (
        <div className="space-y-4">
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">Common Issues</h3>
            <div className="space-y-3">
              <div>
                <h4 className="font-medium text-gray-800">Installation Problems</h4>
                <ul className="list-disc list-inside text-gray-700 space-y-1 ml-4">
                  <li>Ensure Python 3.7+ is installed</li>
                  <li>Check your internet connection during pip install</li>
                  <li>Verify virtual environment activation</li>
                </ul>
              </div>
              <div>
                <h4 className="font-medium text-gray-800">Configuration Issues</h4>
                <ul className="list-disc list-inside text-gray-700 space-y-1 ml-4">
                  <li>Double-check API key validity</li>
                  <li>Ensure at least one provider is selected</li>
                  <li>Restart Dana Studio after configuration changes</li>
                </ul>
              </div>
              <div>
                <h4 className="font-medium text-gray-800">Agent Performance</h4>
                <ul className="list-disc list-inside text-gray-700 space-y-1 ml-4">
                  <li>Check document processing status in Library</li>
                  <li>Consider using Deep Extract for better results</li>
                </ul>
              </div>
            </div>
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">Getting Help</h3>
            <ul className="list-disc list-inside text-gray-700 space-y-1">
              <li>Check the in-app help documentation</li>
              <li>Review error messages carefully</li>
              <li>Ensure all prerequisites are met</li>
              <li>Contact support for persistent issues</li>
            </ul>
          </div>
        </div>
      ),
    },
  ];

  const quickLinks = [
    { title: 'Getting Started', description: 'Installation, setup, and first steps', icon: Play, sectionId: 'getting-started' },
    { title: 'Train Your Agent', description: 'Create powerful, specialized AI agents', icon: Brain, sectionId: 'train-your-agent' },
    { title: 'Library', description: 'Central hub for document management', icon: Page, sectionId: 'library' },
    { title: 'Use Your Agent', description: 'Interact with and get the most from your agents', icon: ChatBubble, sectionId: 'use-your-agent' },
    
  ];

  const scrollToSection = (sectionId: string) => {
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  // Filter sections based on search query
  const filteredSections = useMemo(() => {
    if (!searchQuery.trim()) {
      return documentationSections;
    }

    const query = searchQuery.toLowerCase();
    return documentationSections.filter(section => {
      // Search in title, description, and content
      const titleMatch = section.title.toLowerCase().includes(query);
      const descriptionMatch = section.description.toLowerCase().includes(query);
      
      // Search in content (convert JSX to string for searching)
      const contentText = section.content?.toString().toLowerCase() || '';
      const contentMatch = contentText.includes(query);

      return titleMatch || descriptionMatch || contentMatch;
    });
  }, [searchQuery]);

  // Filter quick links based on search query
  const filteredQuickLinks = useMemo(() => {
    if (!searchQuery.trim()) {
      return quickLinks;
    }

    const query = searchQuery.toLowerCase();
    return quickLinks.filter(link => {
      const titleMatch = link.title.toLowerCase().includes(query);
      const descriptionMatch = link.description.toLowerCase().includes(query);
      return titleMatch || descriptionMatch;
    });
  }, [searchQuery]);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              Dana Studio Documentation
            </h1>
            <p className="text-SM text-gray-600 max-w-3xl mx-auto mb-6">
              Your comprehensive platform for building, training, and deploying intelligent AI agents
            </p>
            
            {/* Search Bar */}
            <div className="max-w-md mx-auto relative">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search documentation..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-10 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery('')}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    <X className="w-5 h-5" />
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Quick Links */}
        <div className="mb-12">
          <h2 className="text-xl font-bold text-gray-900 mb-6">
            Quick Links
            {searchQuery && (
              <span className="text-sm font-normal text-gray-500 ml-2">
                ({filteredQuickLinks.length} result{filteredQuickLinks.length !== 1 ? 's' : ''})
              </span>
            )}
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {filteredQuickLinks.map((link, index) => (
              <div
                key={index}
                onClick={() => scrollToSection(link.sectionId)}
                className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow cursor-pointer"
              >
                <div className="flex items-start">
                  <div className="flex-shrink-0 mr-4">
                    <link.icon className="w-6 h-6 text-blue-600" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900 mb-2">
                      <HighlightText text={link.title} searchQuery={searchQuery} />
                    </h3>
                    <p className="text-gray-700 text-sm">
                      <HighlightText text={link.description} searchQuery={searchQuery} />
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Documentation Sections */}
        <div className="space-y-12">
          {searchQuery && filteredSections.length === 0 && (
            <div className="text-center py-12">
              <Search className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">No results found</h3>
              <p className="text-gray-600">Try searching with different keywords or check your spelling.</p>
            </div>
          )}
          {filteredSections.map((section, sectionIndex) => {
            const sectionId = section.title.toLowerCase().replace(/\s+/g, '-');
            return (
            <div key={sectionIndex} id={sectionId} className="bg-white rounded-lg border border-gray-200 overflow-hidden">
              <div className="bg-gray-50 px-4 py-4 border-b border-gray-200">
                <div className="flex ">
                  <section.icon className="w-8 h-8 text-blue-600 mr-3" />
                  <div>
                    <h2 className="text-xl font-bold text-gray-900">
                      <HighlightText text={section.title} searchQuery={searchQuery} />
                    </h2>
                    <p className="text-gray-700">
                      <HighlightText text={section.description} searchQuery={searchQuery} />
                    </p>
                  </div>
                </div>
              </div>
              <div className="p-6">
                <HighlightContent content={section.content} searchQuery={searchQuery} />
              </div>
            </div>
            );
          })}
        </div>

        {/* Getting Help Section */}
        <div className="mt-12 bg-blue-50 rounded-lg border border-blue-200 p-8">
          <div className="text-center">
            <HelpCircle className="w-12 h-12 text-blue-600 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Need Help?</h2>
            <p className="text-gray-700 mb-6 max-w-3xl mx-auto">
              Can't find what you're looking for? Our support team is here to help you get the most out of Dana Studio.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button onClick={() => window.open('mailto:support@aitomatic.com', '_blank')} className="bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors">
                Contact Support
              </button>
             
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocumentationPage;
