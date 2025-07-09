import { useState } from "react";
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
  IconX,
} from "@tabler/icons-react";
import type { ColumnDef } from "@tanstack/react-table";
import type { LibraryItem, FileItem, FolderItem } from "@/types/library";
import { cn } from "@/lib/utils";
import { useLibrary } from "@/hooks/use-library";
import { FileUpload } from "@/components/library/file-upload";
import { CreateFolderDialog } from "@/components/library/create-folder-dialog";
import FileIcon from "@/components/file-icon";

// Mock data for demonstration
const mockLibraryData: LibraryItem[] = [
  {
    id: "1",
    name: "Project Assets",
    type: "folder",
    itemCount: 15,
    lastModified: new Date("2024-01-15"),
    path: "/assets",
  },
  {
    id: "2",
    name: "logo.png",
    type: "file",
    size: 245760,
    extension: "png",
    lastModified: new Date("2024-01-14"),
    path: "/assets/logo.png",
    thumbnail: "/static/images/logo.svg",
  },
  {
    id: "3",
    name: "documentation.pdf",
    type: "file",
    size: 1024000,
    extension: "pdf",
    lastModified: new Date("2024-01-13"),
    path: "/docs/documentation.pdf",
  },
  {
    id: "4",
    name: "Images",
    type: "folder",
    itemCount: 8,
    lastModified: new Date("2024-01-12"),
    path: "/images",
  },
  {
    id: "5",
    name: "presentation.pptx",
    type: "file",
    size: 5120000,
    extension: "pptx",
    lastModified: new Date("2024-01-11"),
    path: "/presentations/presentation.pptx",
  },
  {
    id: "6",
    name: "data.csv",
    type: "file",
    size: 15360,
    extension: "csv",
    lastModified: new Date("2024-01-10"),
    path: "/data/data.csv",
  },
];

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
};

const formatDate = (date: Date): string => {
  return date.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

export default function LibraryPage() {
  const { filteredData, filters, updateFilters, addItem } = useLibrary(mockLibraryData);
  const [showCreateFolder, setShowCreateFolder] = useState(false);
  const [showUpload, setShowUpload] = useState(false);

  const columns: ColumnDef<LibraryItem>[] = [
    {
      accessorKey: "name",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Name" />,
      cell: ({ row }) => {
        const item = row.original;
        return (
          <div className="flex items-center space-x-3">
            <FileIcon resource={item} />
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
              {item.type === "folder" ? "Folder" : (item as FileItem).extension.toUpperCase()}
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
        return <span className="text-gray-600">{formatDate(row.original.lastModified)}</span>;
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
              <DropdownMenuItem>
                <IconEye className="mr-2 w-4 h-4" />
                View
              </DropdownMenuItem>
              {item.type === "file" && (
                <DropdownMenuItem>
                  <IconDownload className="mr-2 w-4 h-4" />
                  Download
                </DropdownMenuItem>
              )}
              <DropdownMenuItem>
                <IconEdit className="mr-2 w-4 h-4" />
                Rename
              </DropdownMenuItem>
              <DropdownMenuItem className="text-red-600">
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
    if (item.type === "folder") {
      // Navigate to folder
      console.log("Navigate to folder:", item.path);
    } else {
      // Open file preview
      console.log("Open file:", item.path);
    }
  };

  const handleSearchChange = (value: string) => {
    updateFilters({ search: value });
  };

  const handleTypeFilterChange = (type: "all" | "files" | "folders") => {
    updateFilters({ type });
  };

  const handleCreateFolder = (name: string) => {
    const newFolder: FolderItem = {
      id: Date.now().toString(),
      name,
      type: "folder",
      itemCount: 0,
      lastModified: new Date(),
      path: `/new-folder-${Date.now()}`,
    };
    addItem(newFolder);
  };

  const handleFilesUploaded = (files: File[]) => {
    files.forEach((file) => {
      const extension = file.name.split(".").pop() || "";
      const newFile: FileItem = {
        id: Date.now().toString() + Math.random(),
        name: file.name,
        type: "file",
        size: file.size,
        extension,
        lastModified: new Date(),
        path: `/uploads/${file.name}`,
      };
      addItem(newFile);
    });
  };

  return (
    <div className="flex flex-col p-6 space-y-6 h-full">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Library</h1>
          <p className="text-gray-600">Manage your files and folders</p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" onClick={() => setShowCreateFolder(true)}>
            <IconFolderPlus className="mr-2 w-4 h-4" />
            New Folder
          </Button>
          <Button onClick={() => setShowUpload(true)}>
            <IconUpload className="mr-2 w-4 h-4" />
            Upload Files
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center space-x-4">
        <div className="relative flex-1 max-w-sm">
          <IconSearch className="absolute left-3 top-1/2 w-4 h-4 text-gray-400 transform -translate-y-1/2" />
          <Input
            placeholder="Search files and folders..."
            value={filters.search}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="pl-10"
          />
        </div>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline">
              <IconFilter className="mr-2 w-4 h-4" />
              {filters.type === "all" ? "All" : filters.type === "files" ? "Files" : "Folders"}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => handleTypeFilterChange("all")}>
              All Items
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleTypeFilterChange("files")}>
              Files Only
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleTypeFilterChange("folders")}>
              Folders Only
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Data Table */}
      <div className="flex-1">
        <DataTable
          columns={columns}
          data={filteredData}
          loading={false}
          handleRowClick={handleRowClick}
          is_border={true}
        />
      </div>

      {/* Dialogs */}
      <CreateFolderDialog
        isOpen={showCreateFolder}
        onClose={() => setShowCreateFolder(false)}
        onCreateFolder={handleCreateFolder}
        currentPath="/"
      />

      {showUpload && (
        <div className="flex fixed inset-0 z-50 justify-center items-center bg-black bg-opacity-50">
          <div className="p-6 mx-4 w-full max-w-2xl bg-white rounded-lg">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Upload Files</h2>
              <Button variant="ghost" size="sm" onClick={() => setShowUpload(false)}>
                <IconX className="w-4 h-4" />
              </Button>
            </div>
            <FileUpload
              onFilesSelected={handleFilesUploaded}
              multiple={true}
              accept="*/*"
              maxSize={50 * 1024 * 1024}
            />
          </div>
        </div>
      )}
    </div>
  );
}
