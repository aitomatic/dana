export interface FileItem {
  id: string;
  name: string;
  type: "file";
  size: number;
  extension: string;
  lastModified: Date;
  path: string;
  thumbnail?: string;
  topicId?: number; // Add topic association
}

export interface FolderItem {
  id: string;
  name: string;
  type: "folder";
  itemCount: number;
  lastModified: Date;
  path: string;
  topicId?: number; // Add topic ID for API operations
}

export type LibraryItem = FileItem | FolderItem;

export interface LibraryFilters {
  search: string;
  type: "all" | "files" | "folders";
  extension?: string;
}

// New types for folder navigation
export interface BreadcrumbItem {
  id: string;
  name: string;
  path: string;
  type: "root" | "folder";
}

export interface FolderViewState {
  currentPath: string;
  breadcrumbs: BreadcrumbItem[];
  currentFolderId?: string;
  isInFolder: boolean;
}

export interface BulkOperation {
  type: "delete" | "download" | "move";
  items: LibraryItem[];
}
