// Topic Types matching the API schemas
export interface TopicBase {
  name: string;
  description: string;
}

export interface TopicCreate extends TopicBase {
  // Same as TopicBase for creation
}

export interface TopicRead extends TopicBase {
  id: number;
  created_at: string; // ISO datetime string
  updated_at: string; // ISO datetime string
}

// Topic API Response Types
export interface TopicListResponse {
  topics: TopicRead[];
  total: number;
  skip: number;
  limit: number;
}

export interface TopicCreateResponse {
  topic: TopicRead;
  message: string;
}

export interface TopicUpdateResponse {
  topic: TopicRead;
  message: string;
}

export interface TopicDeleteResponse {
  message: string;
}

// Topic Filter Types
export interface TopicFilters {
  search?: string;
  skip?: number;
  limit?: number;
}

// Topic Store State
export interface TopicState {
  topics: TopicRead[];
  selectedTopic: TopicRead | null;
  isLoading: boolean;
  isCreating: boolean;
  isUpdating: boolean;
  isDeleting: boolean;
  error: string | null;
  total: number;
  skip: number;
  limit: number;
}
