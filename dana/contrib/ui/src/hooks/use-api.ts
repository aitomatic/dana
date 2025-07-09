import { useEffect } from 'react';
import { useApiStore } from '@/stores/api-store';
import { usePoetStore } from '@/stores/poet-store';
import { useTopicStore } from '@/stores/topic-store';
import { useDocumentStore } from '@/stores/document-store';
import { useUIStore } from '@/stores/ui-store';
import { useAgentStore } from '@/stores/agent-store';

// Hook for initializing API connection
export const useApiInitialization = () => {
  const { checkApiAvailability, checkHealth, getRootInfo } = useApiStore();
  const { getDomains } = usePoetStore();
  const { addNotification } = useUIStore();

  useEffect(() => {
    const initializeApi = async () => {
      try {
        // Check if API is available
        await checkApiAvailability();

        // Check health to determine if API is truly available
        await checkHealth();
        const isHealthy = useApiStore.getState().isHealthy;

        if (isHealthy) {
          // Load initial data
          await Promise.all([
            checkHealth(),
            getRootInfo(),
            getDomains(),
          ]);

          addNotification({
            type: 'success',
            title: 'API Connected',
            message: 'Successfully connected to OpenDXA API',
            duration: 3000,
          });
        } else {
          addNotification({
            type: 'error',
            title: 'API Unavailable',
            message: 'Unable to connect to OpenDXA API. Please check if the server is running.',
            duration: 0, // Don't auto-dismiss
          });
        }
      } catch (error) {
        addNotification({
          type: 'error',
          title: 'Connection Error',
          message: 'Failed to initialize API connection',
          duration: 5000,
        });
      }
    };

    initializeApi();
  }, [checkApiAvailability, checkHealth, getRootInfo, getDomains, addNotification]);
};

// Hook for POET operations
export const usePoetOperations = () => {
  const { configurePoet, getDomains, availableDomains, selectedDomain, setSelectedDomain } = usePoetStore();
  const { addNotification } = useUIStore();

  const handleConfigurePoet = async (config: Parameters<typeof configurePoet>[0]) => {
    try {
      await configurePoet(config);
      addNotification({
        type: 'success',
        title: 'POET Configured',
        message: 'POET configuration updated successfully',
        duration: 3000,
      });
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Configuration Failed',
        message: 'Failed to configure POET',
        duration: 5000,
      });
    }
  };

  const handleRefreshDomains = async () => {
    try {
      await getDomains();
      addNotification({
        type: 'success',
        title: 'Domains Updated',
        message: 'Available domains refreshed successfully',
        duration: 2000,
      });
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Refresh Failed',
        message: 'Failed to refresh available domains',
        duration: 5000,
      });
    }
  };

  return {
    configurePoet: handleConfigurePoet,
    refreshDomains: handleRefreshDomains,
    availableDomains,
    selectedDomain,
    setSelectedDomain,
  };
};

// Hook for API health monitoring
export const useApiHealth = () => {
  const { isHealthy, isApiAvailable, healthData, checkHealth } = useApiStore();
  const { addNotification } = useUIStore();

  const checkHealthWithNotification = async () => {
    try {
      await checkHealth();
      if (isHealthy) {
        addNotification({
          type: 'success',
          title: 'API Healthy',
          message: 'OpenDXA API is running normally',
          duration: 2000,
        });
      } else {
        addNotification({
          type: 'warning',
          title: 'API Warning',
          message: 'OpenDXA API health check failed',
          duration: 5000,
        });
      }
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Health Check Failed',
        message: 'Unable to check API health status',
        duration: 5000,
      });
    }
  };

  return {
    isHealthy,
    isApiAvailable,
    healthData,
    checkHealth: checkHealthWithNotification,
  };
};

// Hook for Topic operations
export const useTopicOperations = () => {
  const {
    fetchTopics,
    fetchTopic,
    createTopic,
    updateTopic,
    deleteTopic,
    topics,
    selectedTopic,
    isLoading,
    isCreating,
    isUpdating,
    isDeleting,
    error,
    setSelectedTopic,
    clearError
  } = useTopicStore();
  const { addNotification } = useUIStore();

  const handleCreateTopic = async (topic: Parameters<typeof createTopic>[0]) => {
    try {
      await createTopic(topic);
      addNotification({
        type: 'success',
        title: 'Topic Created',
        message: 'Topic created successfully',
        duration: 3000,
      });
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Creation Failed',
        message: 'Failed to create topic',
        duration: 5000,
      });
    }
  };

  const handleUpdateTopic = async (topicId: number, topic: Parameters<typeof updateTopic>[1]) => {
    try {
      await updateTopic(topicId, topic);
      addNotification({
        type: 'success',
        title: 'Topic Updated',
        message: 'Topic updated successfully',
        duration: 3000,
      });
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Update Failed',
        message: 'Failed to update topic',
        duration: 5000,
      });
    }
  };

  const handleDeleteTopic = async (topicId: number) => {
    try {
      await deleteTopic(topicId);
      addNotification({
        type: 'success',
        title: 'Topic Deleted',
        message: 'Topic deleted successfully',
        duration: 3000,
      });
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Deletion Failed',
        message: 'Failed to delete topic',
        duration: 5000,
      });
    }
  };

  return {
    fetchTopics,
    fetchTopic,
    createTopic: handleCreateTopic,
    updateTopic: handleUpdateTopic,
    deleteTopic: handleDeleteTopic,
    topics,
    selectedTopic,
    isLoading,
    isCreating,
    isUpdating,
    isDeleting,
    error,
    setSelectedTopic,
    clearError,
  };
};

// Hook for Document operations
export const useDocumentOperations = () => {
  const {
    fetchDocuments,
    fetchDocument,
    uploadDocument,
    updateDocument,
    deleteDocument,
    downloadDocument,
    documents,
    selectedDocument,
    isLoading,
    isUploading,
    isUpdating,
    isDeleting,
    isDownloading,
    error,
    uploadProgress,
    setSelectedDocument,
    setUploadProgress,
    clearError
  } = useDocumentStore();
  const { addNotification } = useUIStore();

  const handleUploadDocument = async (uploadData: Parameters<typeof uploadDocument>[0]) => {
    try {
      await uploadDocument(uploadData);
      addNotification({
        type: 'success',
        title: 'Document Uploaded',
        message: 'Document uploaded successfully',
        duration: 3000,
      });
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Upload Failed',
        message: 'Failed to upload document',
        duration: 5000,
      });
    }
  };

  const handleUpdateDocument = async (documentId: number, document: Parameters<typeof updateDocument>[1]) => {
    try {
      await updateDocument(documentId, document);
      addNotification({
        type: 'success',
        title: 'Document Updated',
        message: 'Document updated successfully',
        duration: 3000,
      });
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Update Failed',
        message: 'Failed to update document',
        duration: 5000,
      });
    }
  };

  const handleDeleteDocument = async (documentId: number) => {
    try {
      await deleteDocument(documentId);
      addNotification({
        type: 'success',
        title: 'Document Deleted',
        message: 'Document deleted successfully',
        duration: 3000,
      });
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Deletion Failed',
        message: 'Failed to delete document',
        duration: 5000,
      });
    }
  };

  const handleDownloadDocument = async (documentId: number) => {
    try {
      await downloadDocument(documentId);
      addNotification({
        type: 'success',
        title: 'Document Downloaded',
        message: 'Document downloaded successfully',
        duration: 2000,
      });
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Download Failed',
        message: 'Failed to download document',
        duration: 5000,
      });
    }
  };

  return {
    fetchDocuments,
    fetchDocument,
    uploadDocument: handleUploadDocument,
    updateDocument: handleUpdateDocument,
    deleteDocument: handleDeleteDocument,
    downloadDocument: handleDownloadDocument,
    documents,
    selectedDocument,
    isLoading,
    isUploading,
    isUpdating,
    isDeleting,
    isDownloading,
    error,
    uploadProgress,
    setSelectedDocument,
    setUploadProgress,
    clearError,
  };
};

// Hook for Agent operations
export const useAgentOperations = () => {
  const {
    fetchAgents,
    fetchAgent,
    createAgent,
    updateAgent,
    deleteAgent,
    agents,
    selectedAgent,
    isLoading,
    isCreating,
    isUpdating,
    isDeleting,
    error,
    setSelectedAgent,
    clearError
  } = useAgentStore();
  const { addNotification } = useUIStore();

  const handleCreateAgent = async (agent: Parameters<typeof createAgent>[0]) => {
    try {
      await createAgent(agent);
      addNotification({
        type: 'success',
        title: 'Agent Created',
        message: 'Agent created successfully',
        duration: 3000,
      });
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Creation Failed',
        message: 'Failed to create agent',
        duration: 5000,
      });
    }
  };

  const handleUpdateAgent = async (agentId: number, agent: Parameters<typeof updateAgent>[1]) => {
    try {
      await updateAgent(agentId, agent);
      addNotification({
        type: 'success',
        title: 'Agent Updated',
        message: 'Agent updated successfully',
        duration: 3000,
      });
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Update Failed',
        message: 'Failed to update agent',
        duration: 5000,
      });
    }
  };

  const handleDeleteAgent = async (agentId: number) => {
    try {
      await deleteAgent(agentId);
      addNotification({
        type: 'success',
        title: 'Agent Deleted',
        message: 'Agent deleted successfully',
        duration: 3000,
      });
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Deletion Failed',
        message: 'Failed to delete agent',
        duration: 5000,
      });
    }
  };

  return {
    fetchAgents,
    fetchAgent,
    createAgent: handleCreateAgent,
    updateAgent: handleUpdateAgent,
    deleteAgent: handleDeleteAgent,
    agents,
    selectedAgent,
    isLoading,
    isCreating,
    isUpdating,
    isDeleting,
    error,
    setSelectedAgent,
    clearError,
  };
}; 