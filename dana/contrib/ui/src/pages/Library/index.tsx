import { useState, useEffect, useRef } from "react";
import { DataTable } from "@/components/table/data-table";
import { DataTableColumnHeader } from "@/components/table/data-table-column-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  IconSearch,
  IconFilter,
  IconUpload,
  IconDotsVertical,
  IconDownload,
  IconTrash,
  IconEdit,
  IconEye,
  IconFolderPlus,
  IconRefresh,
} from "@tabler/icons-react";
import type { ColumnDef } from "@tanstack/react-table";
import type { LibraryItem, FileItem, FolderItem } from "@/types/library";
import type { TopicRead } from "@/types/topic";
import type { DocumentRead } from "@/types/document";
import { cn } from "@/lib/utils";
import { useTopicOperations, useDocumentOperations } from "@/hooks/use-api";
import { CreateFolderDialog } from "@/components/library/create-folder-dialog";
import FileIcon from "@/components/file-icon";

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
};

const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

// Convert API data to LibraryItem format
const convertTopicToFolderItem = (topic: TopicRead): FolderItem => ({
  id: `topic-${topic.id}`,
  name: topic.name,
  type: "folder",
  itemCount: 0, // We'll need to count documents per topic
  lastModified: new Date(topic.updated_at),
  path: `/topics/${topic.id}`,
});

const convertDocumentToFileItem = (document: DocumentRead): FileItem => ({
  id: `doc-${document.id}`,
  name: document.original_filename,
  type: "file",
  size: document.file_size,
  extension: document.original_filename.split(".").pop() || "unknown",
  lastModified: new Date(document.updated_at),
  path: `/documents/${document.id}`,
});

export default function LibraryPage() {
  // API hooks
  const {
    fetchTopics,
    createTopic,
    deleteTopic,
    topics,
    isLoading: topicsLoading,
    isCreating: isCreatingTopic,
    error: topicsError,
    clearError: clearTopicsError,
  } = useTopicOperations();

  const {
    fetchDocuments,
    uploadDocument,
    deleteDocument,
    downloadDocument,
    documents,
    isLoading: documentsLoading,
    isUploading,
    error: documentsError,
    clearError: clearDocumentsError,
  } = useDocumentOperations();

  // Local state
  const [showCreateFolder, setShowCreateFolder] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [typeFilter, setTypeFilter] = useState<"all" | "files" | "folders">("all");
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Fetch data on component mount
  useEffect(() => {
    fetchTopics();
    fetchDocuments();
  }, [fetchTopics, fetchDocuments]);

  console.log(topics);
  console.log(documents);

  // Convert API data to LibraryItem format
  const libraryItems: LibraryItem[] = [
    ...(topics?.map(convertTopicToFolderItem) || []),
    ...(documents?.map(convertDocumentToFileItem) || []),
  ];

  // Filter items based on search and type
  const filteredItems = libraryItems.filter((item) => {
    const matchesSearch = item.name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType =
      typeFilter === "all" ||
      (typeFilter === "folders" && item.type === "folder") ||
      (typeFilter === "files" && item.type === "file");

    return matchesSearch && matchesType;
  });

  const columns: ColumnDef<LibraryItem>[] = [
    {
      accessorKey: "name",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Name" />,
      cell: ({ row }) => {
        const item: any = row.original;
        return (
          <div className="flex space-x-3">
            <FileIcon ext={item?.extension} />
            <div className="flex flex-col">
              <span className="font-medium text-gray-900">{item.name}</span>
              <span className="text-sm text-gray-500">{item.path}</span>
            </div>
          </div>
        );
      },
    },
    {
      accessorKey: "type",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Type" />,
      cell: ({ row }) => {
        const item = row.original;
        return (
          <div className="flex items-center">
            <span
              className={cn(
                "px-2 py-1 text-xs font-medium rounded-full",
                item.type === "folder" ? "bg-blue-100 text-blue-800" : "bg-gray-100 text-gray-800"
              )}
            >
              {item.type === "folder" ? "Topic" : (item as FileItem).extension.toUpperCase()}
            </span>
          </div>
        );
      },
    },
    {
      accessorKey: "size",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Size" />,
      cell: ({ row }) => {
        const item = row.original;
        if (item.type === "folder") {
          return <span className="text-gray-500">{(item as FolderItem).itemCount} items</span>;
        }
        return <span className="text-gray-900">{formatFileSize((item as FileItem).size)}</span>;
      },
    },
    {
      accessorKey: "lastModified",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Last Modified" />,
      cell: ({ row }) => {
        return (
          <span className="text-gray-600">
            {formatDate(row.original.lastModified.toISOString())}
          </span>
        );
      },
    },
    {
      id: "actions",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Actions" />,
      cell: ({ row }) => {
        const item = row.original;
        return (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="p-0 w-8 h-8">
                <IconDotsVertical className="w-4 h-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => handleViewItem(item)}>
                <IconEye className="mr-2 w-4 h-4" />
                View
              </DropdownMenuItem>
              {item.type === "file" && (
                <DropdownMenuItem onClick={() => handleDownloadDocument(item)}>
                  <IconDownload className="mr-2 w-4 h-4" />
                  Download
                </DropdownMenuItem>
              )}
              <DropdownMenuItem onClick={() => handleEditItem(item)}>
                <IconEdit className="mr-2 w-4 h-4" />
                Edit
              </DropdownMenuItem>
              <DropdownMenuItem className="text-red-600" onClick={() => handleDeleteItem(item)}>
                <IconTrash className="mr-2 w-4 h-4" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        );
      },
    },
  ];

  const handleRowClick = (row: { original: LibraryItem }) => {
    const item = row.original;
    handleViewItem(item);
  };

  const handleViewItem = (item: LibraryItem) => {
    if (item.type === "folder") {
      // Navigate to topic view
      console.log("View topic:", item);
    } else {
      // Open document preview
      console.log("View document:", item);
    }
  };

  const handleEditItem = (item: LibraryItem) => {
    if (item.type === "folder") {
      // Edit topic
      const topicId = parseInt(item.id.replace("topic-", ""));
      const topic = topics.find((t) => t.id === topicId);
      if (topic) {
        // You can implement topic editing here
        console.log("Edit topic:", topic);
      }
    } else {
      // Edit document
      const documentId = parseInt(item.id.replace("doc-", ""));
      const document = documents.find((d) => d.id === documentId);
      if (document) {
        // You can implement document editing here
        console.log("Edit document:", document);
      }
    }
  };

  const handleDeleteItem = async (item: LibraryItem) => {
    if (item.type === "folder") {
      // Delete topic
      const topicId = parseInt(item.id.replace("topic-", ""));
      if (window.confirm("Are you sure you want to delete this topic?")) {
        await deleteTopic(topicId);
      }
    } else {
      // Delete document
      const documentId = parseInt(item.id.replace("doc-", ""));
      if (window.confirm("Are you sure you want to delete this document?")) {
        await deleteDocument(documentId);
      }
    }
  };

  const handleDownloadDocument = async (item: LibraryItem) => {
    if (item.type === "file") {
      const documentId = parseInt(item.id.replace("doc-", ""));
      await downloadDocument(documentId);
    }
  };

  const handleCreateFolder = async (name: string) => {
    await createTopic({ name, description: `Topic: ${name}` });
    setShowCreateFolder(false);
  };

  const handleFilesUploaded = async (files: File[]) => {
    for (const file of files) {
      await uploadDocument({
        file,
        title: file.name,
        description: `Uploaded: ${file.name}`,
      });
    }
  };

  const handleSearchChange = (value: string) => {
    setSearchTerm(value);
  };

  const handleTypeFilterChange = (type: "all" | "files" | "folders") => {
    setTypeFilter(type);
  };

  const handleRefresh = () => {
    fetchTopics();
    fetchDocuments();
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files && files.length > 0) {
      const fileArray = Array.from(files);
      await handleFilesUploaded(fileArray);
      // Reset the input
      event.target.value = "";
    }
  };

  const isLoading = topicsLoading || documentsLoading;
  const error = topicsError || documentsError;

  return (
    <div className="flex flex-col p-6 space-y-6 h-full">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Library</h1>
          <p className="text-gray-600">Manage your topics and documents</p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" onClick={handleRefresh} disabled={isLoading}>
            <IconRefresh className="mr-2 w-4 h-4" />
            Refresh
          </Button>
          <Button
            variant="outline"
            onClick={() => setShowCreateFolder(true)}
            disabled={isCreatingTopic}
          >
            <IconFolderPlus className="mr-2 w-4 h-4" />
            New Topic
          </Button>
          <Button onClick={handleUploadClick} disabled={isUploading}>
            <IconUpload className="mr-2 w-4 h-4" />
            Add Documents
          </Button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800">{error}</p>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              clearTopicsError();
              clearDocumentsError();
            }}
            className="mt-2"
          >
            Dismiss
          </Button>
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center space-x-4">
        <div className="relative flex-1 max-w-sm">
          <IconSearch className="absolute left-3 top-1/2 w-4 h-4 text-gray-400 transform -translate-y-1/2" />
          <Input
            placeholder="Search topics and documents..."
            value={searchTerm}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="pl-10"
          />
        </div>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline">
              <IconFilter className="mr-2 w-4 h-4" />
              {typeFilter === "all" ? "All" : typeFilter === "files" ? "Documents" : "Topics"}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => handleTypeFilterChange("all")}>
              All Items
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleTypeFilterChange("files")}>
              Documents Only
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleTypeFilterChange("folders")}>
              Topics Only
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Data Table */}
      <div className="flex-1">
        <DataTable
          columns={columns}
          data={filteredItems}
          loading={isLoading}
          handleRowClick={handleRowClick}
          is_border={true}
        />
      </div>

      {/* Hidden file input for upload */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        onChange={handleFileChange}
        style={{ display: "none" }}
        accept="*/*"
      />

      {/* Dialogs */}
      <CreateFolderDialog
        isOpen={showCreateFolder}
        onClose={() => setShowCreateFolder(false)}
        onCreateFolder={handleCreateFolder}
        currentPath="/"
      />
    </div>
  );
}
