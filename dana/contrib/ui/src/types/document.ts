// Document Types matching the API schemas
export interface DocumentBase {
  original_filename: string;
  topic_id?: number;
  agent_id?: number;
}

export interface DocumentCreate extends DocumentBase {
  // Same as DocumentBase for creation
}

export interface DocumentRead extends DocumentBase {
  id: number;
  filename: string;
  file_size: number;
  mime_type: string;
  created_at: string; // ISO datetime string
  updated_at: string; // ISO datetime string
}

export interface DocumentUpdate {
  original_filename?: string;
  topic_id?: number;
  agent_id?: number;
}

// Document API Response Types
export interface DocumentListResponse {
  documents: DocumentRead[];
  total: number;
  skip: number;
  limit: number;
}

export interface DocumentCreateResponse {
  document: DocumentRead;
  message: string;
}

export interface DocumentUpdateResponse {
  document: DocumentRead;
  message: string;
}

export interface DocumentDeleteResponse {
  message: string;
}

// Document Upload Types
export interface DocumentUploadData {
  file: File;
  title: string;
  description?: string;
  topic_id?: number;
}

// Document Filter Types
export interface DocumentFilters {
  search?: string;
  topic_id?: number;
  agent_id?: number;
  skip?: number;
  limit?: number;
  mime_type?: string;
}

// Document Store State
export interface DocumentState {
  documents: DocumentRead[];
  selectedDocument: DocumentRead | null;
  isLoading: boolean;
  isCreating: boolean;
  isUpdating: boolean;
  isDeleting: boolean;
  isUploading: boolean;
  isDownloading: boolean;
  error: string | null;
  total: number;
  skip: number;
  limit: number;
  uploadProgress: number;
}
