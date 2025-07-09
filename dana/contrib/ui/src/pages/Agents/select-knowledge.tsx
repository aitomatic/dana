import { useState, useMemo } from "react";
import { FileUpload } from "@/components/library/file-upload";
import { DataTable } from "@/components/table/data-table";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { IconTrash } from "@tabler/icons-react";
import type { LibraryItem, FileItem } from "@/types/library";
import { useLibrary } from "@/hooks/use-library";

// Mock data for demonstration (replace with real data/fetch later)
const mockLibraryData: LibraryItem[] = [
  {
    id: "1",
    name: "Root Cause Diagnostics",
    type: "folder",
    itemCount: 10,
    lastModified: new Date(),
    path: "/root-cause",
  },
  {
    id: "2",
    name: "Material Properties",
    type: "folder",
    itemCount: 5,
    lastModified: new Date(),
    path: "/material-properties",
  },
  {
    id: "3",
    name: "Fabrication Processes",
    type: "file",
    size: 12 * 1024 * 1024,
    extension: "pdf",
    lastModified: new Date(),
    path: "/fab-proc-1.pdf",
  },
  {
    id: "4",
    name: "Fabrication Processes",
    type: "file",
    size: 29 * 1024 * 1024,
    extension: "pdf",
    lastModified: new Date(),
    path: "/fab-proc-2.pdf",
  },
  {
    id: "5",
    name: "Equipment Protocol",
    type: "file",
    size: 240 * 1024,
    extension: "docx",
    lastModified: new Date(),
    path: "/equip-protocol-1.docx",
  },
  {
    id: "6",
    name: "Equipment Protocol",
    type: "file",
    size: 240 * 1024,
    extension: "docx",
    lastModified: new Date(),
    path: "/equip-protocol-2.docx",
  },
  // Add more as needed
];

function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}

export default function SelectKnowledgePage() {
  const { filteredData, filters, updateFilters } = useLibrary(mockLibraryData);
  const [selectedIds, setSelectedIds] = useState<string[]>(["1", "3", "4"]); // Preselect for demo
  const [sidebarSearch, setSidebarSearch] = useState("");

  // Selected items for sidebar
  const selectedItems = useMemo(
    () =>
      mockLibraryData.filter(
        (item) =>
          selectedIds.includes(item.id) &&
          item.name.toLowerCase().includes(sidebarSearch.toLowerCase()),
      ),
    [selectedIds, sidebarSearch],
  );

  // Table columns
  const columns = [
    {
      id: "select",
      header: () => (
        <Checkbox
          checked={
            filteredData.length > 0
              ? filteredData.every((item) => selectedIds.includes(item.id))
                ? true
                : filteredData.some((item) => selectedIds.includes(item.id))
                  ? "indeterminate"
                  : false
              : false
          }
          onCheckedChange={(checked) => {
            if (checked) {
              setSelectedIds((prev) =>
                Array.from(
                  new Set([...prev, ...filteredData.map((item) => item.id)]),
                ),
              );
            } else {
              setSelectedIds((prev) =>
                prev.filter(
                  (id) => !filteredData.map((item) => item.id).includes(id),
                ),
              );
            }
          }}
        />
      ),
      cell: ({ row }: any) => (
        <Checkbox
          checked={selectedIds.includes(row.original.id)}
          onCheckedChange={(checked) => {
            setSelectedIds((prev) =>
              checked
                ? [...prev, row.original.id]
                : prev.filter((id) => id !== row.original.id),
            );
          }}
        />
      ),
    },
    {
      accessorKey: "name",
      header: "Name",
      cell: ({ row }: any) => <span>{row.original.name}</span>,
    },
    {
      accessorKey: "size",
      header: "Size",
      cell: ({ row }: any) =>
        row.original.type === "file"
          ? formatFileSize((row.original as FileItem).size)
          : "",
    },
    {
      id: "actions",
      header: "Actions",
      cell: ({ row }: any) => (
        <Button
          variant="ghost"
          size="icon"
          onClick={() =>
            setSelectedIds((prev) =>
              prev.filter((id) => id !== row.original.id),
            )
          }
        >
          <IconTrash className="w-4 h-4" />
        </Button>
      ),
    },
  ];

  return (
    <div className="flex flex-col h-full w-full bg-gray-100">
      {/* Header */}
      <div className="flex items-center justify-between px-8 py-4 border-b bg-white">
        <span className="text-lg font-semibold">Assign Knowledge Sources</span>
      </div>
      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left: Library & Upload */}
        <div className="flex flex-col flex-1 p-8 gap-4 overflow-hidden">
          {/* Upload */}
          <div className="mb-4">
            <FileUpload
              onFilesSelected={() => {
                /* handle upload */
              }}
            />
          </div>
          {/* Search */}
          <div className="mb-2">
            <Input
              placeholder="Search"
              value={filters.search}
              onChange={(e) => updateFilters({ search: e.target.value })}
              className="w-64"
            />
          </div>
          {/* Library Table */}
          <div className="flex-1 min-h-0">
            <DataTable columns={columns} data={filteredData} loading={false} />
          </div>
        </div>
        {/* Right: Selected Sidebar */}
        <div className="w-80 border-l bg-white flex flex-col p-6">
          <span className="font-semibold mb-2">Selected File</span>
          <Input
            placeholder="Search"
            value={sidebarSearch}
            onChange={(e) => setSidebarSearch(e.target.value)}
            className="mb-4"
          />
          <div className="flex-1 overflow-y-auto">
            {selectedItems.length === 0 ? (
              <span className="text-gray-400">No file selected</span>
            ) : (
              <ul className="space-y-2">
                {selectedItems.map((item) => (
                  <li
                    key={item.id}
                    className="flex items-center justify-between p-2 rounded hover:bg-gray-50"
                  >
                    <span className="truncate">{item.name}</span>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() =>
                        setSelectedIds((prev) =>
                          prev.filter((id) => id !== item.id),
                        )
                      }
                    >
                      <IconTrash className="w-4 h-4" />
                    </Button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
      {/* Footer */}
      <div className="flex justify-end gap-4 px-8 py-4 border-t bg-white">
        <Button variant="ghost">Cancel</Button>
        <Button variant="default">Save & Finish</Button>
      </div>
    </div>
  );
}
