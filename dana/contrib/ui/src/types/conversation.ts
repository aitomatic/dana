// Conversation Types matching the API schemas
export interface ConversationBase {
  title: string;
  agent_id: number;
}

export interface ConversationCreate extends ConversationBase {
  // Same as ConversationBase for creation
}

export interface ConversationRead extends ConversationBase {
  id: number;
  created_at: string;
  updated_at: string;
}

export interface MessageBase {
  sender: string;
  content: string;
}

export interface MessageCreate extends MessageBase {
  // Same as MessageBase for creation
}

export interface MessageRead extends MessageBase {
  id: number;
  conversation_id: number;
  created_at: string;
  updated_at: string;
}

export interface ConversationWithMessages extends ConversationRead {
  messages: MessageRead[];
}

// Conversation Filter Types
export interface ConversationFilters {
  agent_id?: number;
  skip?: number;
  limit?: number;
}

// Conversation Store State
export interface ConversationState {
  conversations: ConversationRead[];
  selectedConversation: ConversationWithMessages | null;
  isLoading: boolean;
  isCreating: boolean;
  isUpdating: boolean;
  isDeleting: boolean;
  error: string | null;
  total: number;
  skip: number;
  limit: number;

  // Actions
  fetchConversations: (filters?: ConversationFilters) => Promise<void>;
  fetchConversation: (conversationId: number) => Promise<ConversationWithMessages>;
  createConversation: (conversation: ConversationCreate) => Promise<ConversationRead>;
  updateConversation: (conversationId: number, conversation: ConversationCreate) => Promise<ConversationRead>;
  deleteConversation: (conversationId: number) => Promise<void>;
  setSelectedConversation: (conversation: ConversationWithMessages | null) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
  reset: () => void;
} 