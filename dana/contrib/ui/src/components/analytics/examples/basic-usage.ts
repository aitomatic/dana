/**
 * Basic Analytics Usage Examples
 * 
 * This file contains common patterns for implementing analytics tracking
 * in Dana Agent Studio components.
 */

import { useDanaAnalytics } from '@/hooks/useAnalytics';

// ============================================================================
// 1. BASIC EVENT TRACKING
// ============================================================================

export const BasicEventTracking = () => {
  const { trackAgentCreation, trackError } = useDanaAnalytics();

  const handleCreateAgent = async (agentData: any) => {
    try {
      // Your agent creation logic here
      await createAgent(agentData);
      
      // Track successful creation
      trackAgentCreation(agentData.name, agentData.domain);
      
    } catch (error) {
      // Track error with context
      trackError(
        'agent_creation_failed',
        error instanceof Error ? error.message : 'Unknown error',
        `agent_${agentData.name}`
      );
    }
  };

  return (
    <button onClick={() => handleCreateAgent({ name: 'MyAgent', domain: 'finance' })}>
      Create Agent
    </button>
  );
};

// ============================================================================
// 2. FILE OPERATIONS TRACKING
// ============================================================================

export const FileOperationsTracking = () => {
  const { trackFileUpload, trackFileDownload, trackError } = useDanaAnalytics();

  const handleFileUpload = async (file: File) => {
    try {
      // Upload logic here
      await uploadFile(file);
      
      // Track successful upload
      const fileExtension = file.name.split('.').pop() || 'unknown';
      trackFileUpload(fileExtension, file.size);
      
    } catch (error) {
      trackError('file_upload_failed', error.message, file.name);
    }
  };

  const handleFileDownload = async (fileName: string) => {
    try {
      await downloadFile(fileName);
      
      // Track download
      const fileExtension = fileName.split('.').pop() || 'unknown';
      trackFileDownload(fileExtension, fileName);
      
    } catch (error) {
      trackError('file_download_failed', error.message, fileName);
    }
  };

  return (
    <div>
      <input type="file" onChange={(e) => handleFileUpload(e.target.files[0])} />
      <button onClick={() => handleFileDownload('document.pdf')}>Download</button>
    </div>
  );
};

// ============================================================================
// 3. TAB NAVIGATION TRACKING
// ============================================================================

export const TabNavigationTracking = () => {
  const { trackTabNavigation } = useDanaAnalytics();
  const [activeTab, setActiveTab] = useState('overview');

  const handleTabChange = (tabName: string) => {
    setActiveTab(tabName);
    
    // Track tab navigation
    trackTabNavigation(tabName, 'agent_detail');
  };

  return (
    <div>
      <button 
        className={activeTab === 'overview' ? 'active' : ''}
        onClick={() => handleTabChange('overview')}
      >
        Overview
      </button>
      <button 
        className={activeTab === 'resources' ? 'active' : ''}
        onClick={() => handleTabChange('resources')}
      >
        Resources
      </button>
    </div>
  );
};

// ============================================================================
// 4. CHAT INTERACTION TRACKING
// ============================================================================

export const ChatTracking = () => {
  const { trackChatMessage } = useDanaAnalytics();
  const [messages, setMessages] = useState([]);

  const handleSendMessage = async (message: string, agentId: string) => {
    try {
      // Send message logic
      await sendMessage(message, agentId);
      
      // Track user message
      trackChatMessage(agentId, 'user');
      
      // Add to local state
      setMessages(prev => [...prev, { role: 'user', content: message }]);
      
    } catch (error) {
      // Track chat error
      trackError('chat_message_failed', error.message, agentId);
    }
  };

  const handleReceiveMessage = (agentId: string) => {
    // Track agent response
    trackChatMessage(agentId, 'agent');
  };

  return (
    <div>
      <input 
        placeholder="Type your message..."
        onKeyPress={(e) => {
          if (e.key === 'Enter') {
            handleSendMessage(e.target.value, 'agent-123');
          }
        }}
      />
    </div>
  );
};

// ============================================================================
// 5. ERROR BOUNDARY TRACKING
// ============================================================================

export const ErrorBoundaryTracking = ({ children }: { children: React.ReactNode }) => {
  const { trackError } = useDanaAnalytics();

  return (
    <ErrorBoundary
      onError={(error, errorInfo) => {
        // Track React error boundary errors
        trackError(
          'react_error_boundary',
          error.message,
          errorInfo.componentStack
        );
      }}
    >
      {children}
    </ErrorBoundary>
  );
};

// ============================================================================
// 6. FORM INTERACTION TRACKING
// ============================================================================

export const FormTracking = () => {
  const { trackError } = useDanaAnalytics();
  const [formData, setFormData] = useState({});

  const handleFormSubmit = async (data: any) => {
    try {
      // Form submission logic
      await submitForm(data);
      
      // Success is tracked by the specific action (e.g., trackAgentCreation)
      
    } catch (error) {
      // Track form submission error
      trackError('form_submission_failed', error.message, 'agent_creation_form');
    }
  };

  const handleFormValidationError = (field: string, error: string) => {
    // Track validation errors
    trackError('form_validation_error', error, field);
  };

  return (
    <form onSubmit={(e) => {
      e.preventDefault();
      handleFormSubmit(formData);
    }}>
      {/* Form fields */}
    </form>
  );
};

// ============================================================================
// 7. TIMING TRACKING
// ============================================================================

export const TimingTracking = () => {
  const { trackTiming } = useDanaAnalytics();

  const performLongOperation = async () => {
    const startTime = Date.now();
    
    try {
      // Long operation (e.g., file extraction, agent generation)
      await longOperation();
      
      // Track timing
      const duration = Date.now() - startTime;
      trackTiming('long_operation_duration', duration, 'performance', 'file_extraction');
      
    } catch (error) {
      // Track failed operation timing
      const duration = Date.now() - startTime;
      trackTiming('long_operation_failed_duration', duration, 'performance', 'file_extraction');
    }
  };

  return (
    <button onClick={performLongOperation}>
      Start Long Operation
    </button>
  );
};

// ============================================================================
// HELPER FUNCTIONS (Mock implementations)
// ============================================================================

async function createAgent(data: any) {
  // Mock implementation
  return Promise.resolve();
}

async function uploadFile(file: File) {
  // Mock implementation
  return Promise.resolve();
}

async function downloadFile(fileName: string) {
  // Mock implementation
  return Promise.resolve();
}

async function sendMessage(message: string, agentId: string) {
  // Mock implementation
  return Promise.resolve();
}

async function submitForm(data: any) {
  // Mock implementation
  return Promise.resolve();
}

async function longOperation() {
  // Mock implementation
  return new Promise(resolve => setTimeout(resolve, 2000));
}

// ============================================================================
// USAGE NOTES
// ============================================================================

/*
Key Principles:

1. Always track both success and error cases
2. Include context in error tracking (component, action, user state)
3. Use consistent naming conventions
4. Track timing for operations that might be slow
5. Don't block the UI with analytics calls
6. Use the appropriate tracking function for the action type

Common Patterns:

- Agent operations: trackAgentCreation, trackAgentEdit, trackAgentDeletion
- File operations: trackFileUpload, trackFileDownload, trackFileExtraction
- Navigation: trackTabNavigation
- Chat: trackChatMessage
- Errors: trackError (with context)
- Timing: trackTiming (for performance-critical operations)

Remember:
- Analytics should never crash your app
- Track meaningful user actions, not every click
- Include enough context to debug issues
- Use consistent event naming across the app
*/
