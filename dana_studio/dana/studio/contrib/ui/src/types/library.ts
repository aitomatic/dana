/* eslint-disable @typescript-eslint/no-explicit-any */
export interface FileItem {
  id: string;
  name: string;
  type: 'file';
  size: number;
  extension: string;
  lastModified: Date;
  created: Date;
  path: string;
  thumbnail?: string;
  topicId?: number; // Add topic association
  metadata?: Record<string, any>; // Add metadata field for extraction status
  children?: FileItem[]; // Support for expandable rows (e.g., templates within knowledge packs)
}

export interface FolderItem {
  id: string;
  name: string;
  type: 'folder';
  itemCount: number;
  lastModified: Date;
  created: Date;
  path: string;
  topicId?: number; // Add topic ID for API operations
}

export type LibraryItem = FileItem | FolderItem;

export interface LibraryFilters {
  search: string;
  type: 'all' | 'files' | 'folders';
  extension?: string;
}

// New types for folder navigation
export interface BreadcrumbItem {
  id: string;
  name: string;
  path: string;
  type: 'root' | 'folder';
}

export interface FolderViewState {
  currentPath: string;
  breadcrumbs: BreadcrumbItem[];
  currentFolderId?: string;
  isInFolder: boolean;
}

export interface BulkOperation {
  type: 'delete' | 'download' | 'move';
  items: LibraryItem[];
}

// Knowledge Pack Types
export interface ParseSpecializationResponse {
  success: boolean;
  message: string;
  error: string | null;
  specialization: {
    domain: string;
    role: string;
    task: string;
  } | null;
  extracted_text: string | null;
}

export interface KnowledgePackCreateResponse {
  success: boolean;
  message: string;
  error: string | null;
  data: {
    id: number;
    folder_path: string;
    status: 'draft' | 'published';
    kp_metadata: Record<string, any>;
    created_at: string;
    updated_at: string;
    interview_templates: any[];
  } | null;
}

export interface KnowledgePackData {
  id?: number;
  specialization: {
    domain: string;
    role: string;
    task: string;
  };
  document_ids: number[];
  status?: 'draft' | 'generating' | 'completed' | 'failed';
  folder_path?: string;
  kp_metadata?: Record<string, any>;
  generation_task_id?: number | null;
  // NEW: Preserve original user description for auto-first message
  originalDescription?: string;
  // NEW: Include interview templates data
  interview_templates?: any[];
}

export interface Topic {
  topic_id: string;
  label: string;
  description: string;
  confidence_score: number;
  level: number;
  parent_topic: string | null;
  subtopics: string[];
  key_concepts: string[];
  related_existing_topics: string[];
  children: string[];
  chunk_ids: string[];
  metadata: Record<string, any>;
}

export interface KnowledgePackChatMessage {
  sender: 'user' | 'agent' | 'assistant';
  content: string;
  require_user: boolean;
  treat_as_tool: boolean;
  metadata: Record<string, any>;
}

export interface KnowledgePackChatResponse {
  success: boolean;
  is_tree_modified: boolean;
  agent_response: string;
  internal_conversation: KnowledgePackChatMessage[];
  error: string | null;
}

// ========================================
// Interview Template Types (Capture Template)
// ========================================

export type TemplateGenerationStatus = 'pending' | 'generating' | 'completed' | 'failed';

export interface InterviewTemplateMetadata {
  domain?: string;
  role?: string;
  status?: TemplateGenerationStatus;
  total_topics?: number;
  completed_topics?: number;
  estimated_duration?: number;
  last_topic?: string;
  progress?: number;
  [key: string]: any;
}

export interface InterviewTemplateBase {
  name?: string | null;
  description?: string | null;
  template_metadata?: InterviewTemplateMetadata;
}

export interface InterviewTemplateCreate extends InterviewTemplateBase {
  kp_id: number;
  folder_path: string;
  is_active?: boolean;
  is_master?: boolean;
  source_template_id?: number | null;
}

// Update type - all fields from base are optional
export type InterviewTemplateUpdate = Partial<InterviewTemplateBase>;

export interface InterviewTemplateRead extends InterviewTemplateBase {
  id: number;
  kp_id: number;
  folder_path: string;
  is_active: boolean;
  is_master: boolean;
  version?: number;
  created_at: string;
  updated_at: string;
  readme_content?: string | null;
}

export interface InterviewTemplateResponse {
  success: boolean;
  message: string;
  data: InterviewTemplateRead | null;
  error: string | null;
}

export interface InterviewTemplateListResponse {
  success: boolean;
  message: string;
  data: InterviewTemplateRead[];
  total: number;
  error: string | null;
}

// Interview Chat Types
export interface TemplateChatMessage {
  sender: 'user' | 'agent' | 'assistant';
  content: string;
  require_user?: boolean;
  treat_as_tool?: boolean;
  metadata?: Record<string, any>;
}

export interface TemplateFinetuneChannelResponse {
  success: boolean;
  template_modified: boolean;
  agent_response: string;
  internal_conversation: TemplateChatMessage[];
  template_diff?: any;
  error: string | null;
}

// Conversation Types for Templates
export interface TemplateConversation {
  id: number;
  title: string;
  type: string;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface TemplateConversationsResponse {
  success: boolean;
  template_id: number;
  conversations: TemplateConversation[];
  error?: string | null;
}

// ========================================
// Interview Session Types (Capture Knowledge)
// ========================================

export type InterviewSessionStatus = 'draft' | 'in_progress' | 'completed';

export interface InterviewSessionBase {
  session_name?: string | null;
  status?: InterviewSessionStatus;
  interviewee_name?: string | null;
  interviewee_role?: string | null;
  session_metadata?: Record<string, any>;
}

export interface InterviewSessionCreate extends InterviewSessionBase {
  interview_template_id: number;
}

export interface InterviewSessionUpdate {
  session_name?: string | null;
  status?: InterviewSessionStatus | null;
  interviewee_name?: string | null;
  interviewee_role?: string | null;
  session_metadata?: Record<string, any> | null;
  started_at?: string | null;
  completed_at?: string | null;
}

export interface InterviewSessionRead extends InterviewSessionBase {
  id: number;
  interview_template_id: number;
  conversation_id?: number | null;
  started_at?: string | null;
  completed_at?: string | null;
  created_at: string;
  updated_at: string;
  content?: string | null;  // Interview notes markdown content
}

export interface InterviewSessionResponse {
  success: boolean;
  message: string;
  data: InterviewSessionRead | null;
  error?: string | null;
}

export interface InterviewSessionListResponse {
  success: boolean;
  message: string;
  data: InterviewSessionRead[];
  total: number;
  error?: string | null;
}

// Session Chat Types
export interface SessionChatRequest {
  message: string;
  user_id?: string;
  session_id: number;
}

export interface SessionChatMessage {
  sender: 'user' | 'agent' | 'assistant';
  content: string;
  require_user?: boolean;
  treat_as_tool?: boolean;
  metadata?: Record<string, any>;
}

export interface SessionChatResponse {
  success: boolean;
  message: string;
  agent_response: string;
  conversation_id?: number;
  message_id?: number;
  internal_conversation?: SessionChatMessage[];
  error?: string | null;
}
