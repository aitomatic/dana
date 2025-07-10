import { useState, useCallback, useMemo } from "react";
import type {
  LibraryItem,
  FolderItem,
  BreadcrumbItem,
  FolderViewState,
} from "@/types/library";

export function useFolderNavigation() {
  const [currentPath, setCurrentPath] = useState("/");
  const [currentFolderId, setCurrentFolderId] = useState<string | undefined>();

  const breadcrumbs = useMemo((): BreadcrumbItem[] => {
    if (currentPath === "/") {
      return [{ id: "root", name: "Library", path: "/", type: "root" }];
    }

    const parts = currentPath.split("/").filter(Boolean);
    const crumbs: BreadcrumbItem[] = [
      { id: "root", name: "Library", path: "/", type: "root" },
    ];

    let path = "";
    parts.forEach((part, index) => {
      path += `/${part}`;
      crumbs.push({
        id: `folder-${index}`,
        name: part,
        path,
        type: "folder",
      });
    });

    return crumbs;
  }, [currentPath]);

  const folderState: FolderViewState = useMemo(
    () => ({
      currentPath,
      breadcrumbs,
      currentFolderId,
      isInFolder: currentPath !== "/",
    }),
    [currentPath, breadcrumbs, currentFolderId],
  );

  const navigateToFolder = useCallback((folder: FolderItem) => {
    console.log("🚀 Navigating to folder:", folder);
    setCurrentPath(folder.path);
    setCurrentFolderId(folder.id);
  }, []);

  const navigateToPath = useCallback((path: string) => {
    setCurrentPath(path);
    if (path === "/") {
      setCurrentFolderId(undefined);
    } else {
      // Extract folder ID from path if needed
      const parts = path.split("/").filter(Boolean);
      if (parts.length > 0) {
        setCurrentFolderId(`topic-${parts[parts.length - 1]}`);
      }
    }
  }, []);

  const navigateToRoot = useCallback(() => {
    setCurrentPath("/");
    setCurrentFolderId(undefined);
  }, []);

  const getItemsInCurrentFolder = useCallback(
    (allItems: LibraryItem[]): LibraryItem[] => {
      console.log("🔍 getItemsInCurrentFolder called:", {
        currentPath,
        currentFolderId,
        allItemsCount: allItems.length,
      });

      if (currentPath === "/") {
        // Root level - show all folders and files not in any folder
        const rootItems = allItems.filter((item) => {
          if (item.type === "folder") return true;
          // For files, show only those not associated with any topic
          return !item.topicId;
        });
        console.log("📁 Root level items:", rootItems.length);
        return rootItems;
      }

      // Inside a folder - show only items in this folder (not the folder itself)
      if (currentFolderId) {
        const topicId = currentFolderId.replace("topic-", "");
        const folderItems = allItems.filter((item) => {
          // Don't show folders when inside a folder - only show files
          if (item.type === "folder") {
            return false; // Hide folders when inside a folder
          }
          // Show only files that belong to this topic
          return item.topicId === parseInt(topicId);
        });
        console.log(
          "📂 Folder items for topic",
          topicId,
          ":",
          folderItems.length,
        );
        return folderItems;
      }

      console.log("❌ No folder ID found, returning empty array");
      return [];
    },
    [currentPath, currentFolderId],
  );

  return {
    folderState,
    navigateToFolder,
    navigateToPath,
    navigateToRoot,
    getItemsInCurrentFolder,
  };
}
