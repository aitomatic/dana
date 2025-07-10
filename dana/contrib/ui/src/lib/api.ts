import axios from 'axios';
import type { AxiosInstance, AxiosResponse } from 'axios';
import type { TopicRead, TopicCreate, TopicFilters } from '@/types/topic';
import type {
  DocumentRead,
  DocumentUpdate,
  DocumentFilters,
  DocumentUploadData,
} from '@/types/document';
import type { AgentRead, AgentCreate, AgentFilters } from '@/types/agent';
import type {
  ConversationRead,
  ConversationCreate,
  ConversationWithMessages,
  ConversationFilters,
} from '@/types/conversation';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080/api';
const API_TIMEOUT = 30000; // 30 seconds

// API Response Types
export interface ApiResponse<T = any> {
  data: T;
  status: number;
  message?: string;
}

export interface HealthResponse {
  status: string;
  service: string;
}

export interface RootResponse {
  service: string;
  version: string;
  status: string;
  endpoints: Record<string, string>;
}

// POET API Types
export interface PoetConfigRequest {
  domain?: string;
  retries?: number;
  timeout?: number;
  enable_training?: boolean;
}

export interface PoetConfigResponse {
  message: string;
  config: {
    domain?: string;
    retries: number;
    timeout?: number;
    enable_training: boolean;
  };
}

export interface DomainsResponse {
  domains: string[];
}

// Error Types
export interface ApiError {
  message: string;
  status?: number;
  details?: any;
}

// Chat Types
export interface ChatRequest {
  message: string;
  conversation_id?: number;
  agent_id: number;
  context?: Record<string, any>;
}

export interface ChatResponse {
  success: boolean;
  message: string;
  conversation_id: number;
  message_id: number;
  agent_response: string;
  context?: Record<string, any>;
  error?: string;
}

// API Service Class
class ApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: API_TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        console.error('❌ API Request Error:', error);
        return Promise.reject(error);
      },
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        console.log(`✅ API Response: ${response.status} ${response.config.url}`);
        return response;
      },
      (error) => {
        console.error('❌ API Response Error:', error);
        const apiError: ApiError = {
          message: error.response?.data?.detail || error.message || 'Unknown error occurred',
          status: error.response?.status,
          details: error.response?.data,
        };
        return Promise.reject(apiError);
      },
    );
  }

  // Health Check
  async checkHealth(): Promise<HealthResponse> {
    const response = await this.client.get<HealthResponse>('/health');
    return response.data;
  }

  // Root Info
  async getRootInfo(): Promise<RootResponse> {
    const response = await this.client.get<RootResponse>('/');
    return response.data;
  }

  // POET Service Methods
  async configurePoet(config: PoetConfigRequest): Promise<PoetConfigResponse> {
    const response = await this.client.post<PoetConfigResponse>('/poet/configure', config);
    return response.data;
  }

  async getPoetDomains(): Promise<DomainsResponse> {
    const response = await this.client.get<DomainsResponse>('/poet/domains');
    return response.data;
  }

  // Topic API Methods
  async getTopics(filters?: TopicFilters): Promise<TopicRead[]> {
    const params = new URLSearchParams();
    if (filters?.skip) params.append('skip', filters.skip.toString());
    if (filters?.limit) params.append('limit', filters.limit.toString());

    const response = await this.client.get<TopicRead[]>(`/topics/?${params.toString()}`);
    return response.data;
  }

  async getTopic(topicId: number): Promise<TopicRead> {
    const response = await this.client.get<TopicRead>(`/topics/${topicId}`);
    return response.data;
  }

  async createTopic(topic: TopicCreate): Promise<TopicRead> {
    const response = await this.client.post<TopicRead>('/topics/', topic);
    return response.data;
  }

  async updateTopic(topicId: number, topic: TopicCreate): Promise<TopicRead> {
    const response = await this.client.put<TopicRead>(`/topics/${topicId}`, topic);
    return response.data;
  }

  async deleteTopic(topicId: number): Promise<{ message: string }> {
    const response = await this.client.delete<{ message: string }>(`/topics/${topicId}`);
    return response.data;
  }

  // Document API Methods
  async getDocuments(filters?: DocumentFilters): Promise<DocumentRead[]> {
    const params = new URLSearchParams();
    if (filters?.skip) params.append('skip', filters.skip.toString());
    if (filters?.limit) params.append('limit', filters.limit.toString());
    if (filters?.topic_id) params.append('topic_id', filters.topic_id.toString());

    const response = await this.client.get<DocumentRead[]>(`/documents/?${params.toString()}`);
    return response.data;
  }

  async getDocument(documentId: number): Promise<DocumentRead> {
    const response = await this.client.get<DocumentRead>(`/documents/${documentId}`);
    return response.data;
  }

  async uploadDocument(uploadData: DocumentUploadData): Promise<DocumentRead> {
    const formData = new FormData();
    formData.append('file', uploadData.file);
    formData.append('title', uploadData.title);
    if (uploadData.description) formData.append('description', uploadData.description);
    if (uploadData.topic_id) formData.append('topic_id', uploadData.topic_id.toString());

    const response = await this.client.post<DocumentRead>('/documents/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  async updateDocument(documentId: number, document: DocumentUpdate): Promise<DocumentRead> {
    const response = await this.client.put<DocumentRead>(`/documents/${documentId}`, document);
    return response.data;
  }

  async deleteDocument(documentId: number): Promise<{ message: string }> {
    const response = await this.client.delete<{ message: string }>(`/documents/${documentId}`);
    return response.data;
  }

  async downloadDocument(documentId: number): Promise<Blob> {
    const response = await this.client.get(`/documents/${documentId}/download`, {
      responseType: 'blob',
    });
    return response.data;
  }

  // Agent API Methods
  async getAgents(filters?: AgentFilters): Promise<AgentRead[]> {
    const params = new URLSearchParams();
    if (filters?.skip) params.append('skip', filters.skip.toString());
    if (filters?.limit) params.append('limit', filters.limit.toString());

    const response = await this.client.get<AgentRead[]>(`/agents/?${params.toString()}`);
    return response.data;
  }

  async getAgent(agentId: number): Promise<AgentRead> {
    const response = await this.client.get<AgentRead>(`/agents/${agentId}`);
    return response.data;
  }

  async createAgent(agent: AgentCreate): Promise<AgentRead> {
    const response = await this.client.post<AgentRead>('/agents/', agent);
    return response.data;
  }

  async updateAgent(agentId: number, agent: AgentCreate): Promise<AgentRead> {
    const response = await this.client.put<AgentRead>(`/agents/${agentId}`, agent);
    return response.data;
  }

  async deleteAgent(agentId: number): Promise<{ message: string }> {
    const response = await this.client.delete<{ message: string }>(`/agents/${agentId}`);
    return response.data;
  }

  // Chat API Methods
  async chatWithAgent(request: ChatRequest): Promise<ChatResponse> {
    const response = await this.client.post<ChatResponse>('/chat/', request);
    return response.data;
  }

  // Conversation API Methods
  async getConversations(agentId?: number): Promise<ConversationRead[]> {
    const params = new URLSearchParams();
    if (agentId) params.append('agent_id', agentId.toString());

    console.log('Fetching conversations for agent:', agentId);
    const response = await this.client.get<ConversationRead[]>(`/conversations/?${params.toString()}`);
    console.log('Conversations response:', response.data);
    return response.data;
  }

  async getConversation(conversationId: number): Promise<ConversationWithMessages> {
    console.log('Fetching conversation:', conversationId);
    const response = await this.client.get<ConversationWithMessages>(`/conversations/${conversationId}`);
    console.log('Conversation response:', response.data);
    return response.data;
  }

  async createConversation(conversation: ConversationCreate): Promise<ConversationRead> {
    const response = await this.client.post<ConversationRead>('/conversations/', conversation);
    return response.data;
  }

  async updateConversation(conversationId: number, conversation: ConversationCreate): Promise<ConversationRead> {
    const response = await this.client.put<ConversationRead>(`/conversations/${conversationId}`, conversation);
    return response.data;
  }

  async deleteConversation(conversationId: number): Promise<{ message: string }> {
    const response = await this.client.delete<{ message: string }>(`/conversations/${conversationId}`);
    return response.data;
  }

  // Utility method to check if API is available
  async isApiAvailable(): Promise<boolean> {
    try {
      await this.checkHealth();
      return true;
    } catch (error) {
      console.warn('API not available:', error);
      return false;
    }
  }
}

// Export singleton instance
export const apiService = new ApiService();
