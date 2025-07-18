import type { LibraryItem, FileItem, FolderItem } from '@/types/library';
import type { TopicRead } from '@/types/topic';
import type { DocumentRead } from '@/types/document';

// Helper functions to convert API data to LibraryItem format
export const convertTopicToFolderItem = (topic: TopicRead): FolderItem => ({
  id: `topic-${topic.id}`,
  name: topic.name,
  type: 'folder',
  itemCount: 0, // Will be calculated later
  lastModified: new Date(topic.updated_at),
  path: `/topics/${topic.id}`,
  topicId: topic.id,
});

export const convertDocumentToFileItem = (document: DocumentRead): FileItem => ({
  id: `doc-${document.id}`,
  name: document.original_filename,
  type: 'file',
  size: document.file_size,
  extension: document.original_filename.split('.').pop()?.toLowerCase() || 'unknown',
  lastModified: new Date(document.updated_at),
  path: `/documents/${document.id}`,
  topicId: document.topic_id || undefined,
});

export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

export const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

// Process library items with counts
export const processLibraryItems = (
  topics: TopicRead[] | undefined,
  documents: DocumentRead[] | undefined,
): LibraryItem[] => {
  const libraryItems: LibraryItem[] = [
    ...(topics?.map(convertTopicToFolderItem) || []),
    ...(documents?.map(convertDocumentToFileItem) || []),
  ];

  // Calculate item counts for folders
  return libraryItems.map((item) => {
    if (item.type === 'folder') {
      const topicId = item.topicId;
      const itemCount = documents?.filter((doc) => doc.topic_id === topicId).length || 0;
      return { ...item, itemCount };
    }
    return item;
  });
};
