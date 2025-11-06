/* eslint-disable @typescript-eslint/no-explicit-any */
// Document Types matching the API schemas
export interface DocumentBase {
  original_filename: string;
  topic_id?: number;
  agent_id?: number;
}

export type DocumentCreate = DocumentBase;

export interface DocumentRead extends DocumentBase {
  id: number;
  filename: string;
  file_size: number;
  mime_type: string;
  source_document_id?: number; // For JSON extraction files, links to original PDF
  created_at: string; // ISO datetime string
  updated_at: string; // ISO datetime string
  metadata: Record<string, any>; // Document metadata from database
  file_extension?: string; // File extension (e.g., 'pdf', 'docx')
  file_size_mb?: number; // File size in MB
  is_extraction_file: boolean; // Whether this is an extraction file
  days_since_created?: number; // Days since document was created
  days_since_updated?: number; // Days since document was last updated
}

export interface DocumentUpdate {
  original_filename?: string;
  topic_id?: number;
  agent_id?: number;
}

// Extraction Output Type (v2 API)
export interface ExtractionOutput {
  original_filename: string;
  source_document_id: number;
  extraction_date: string;
  total_pages: number;
  documents: Array<{
    text: string;
    page_number: number;
    [key: string]: any;
  }>;
}

// Document API Response Types
export interface DocumentListResponse {
  documents: DocumentRead[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
  metadata: {
    filters: {
      topic_id?: number;
      agent_id?: number;
    };
    pagination: {
      current_page: number;
      total_pages: number;
    };
    response_time: string;
  };
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
