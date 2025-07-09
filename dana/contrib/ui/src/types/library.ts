export interface FileItem {
  id: string;
  name: string;
  type: "file";
  size: number;
  extension: string;
  lastModified: Date;
  path: string;
  thumbnail?: string;
}

export interface FolderItem {
  id: string;
  name: string;
  type: "folder";
  itemCount: number;
  lastModified: Date;
  path: string;
}

export type LibraryItem = FileItem | FolderItem;

export interface LibraryFilters {
  search: string;
  type: "all" | "files" | "folders";
  extension?: string;
}
