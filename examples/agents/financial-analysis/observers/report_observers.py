from dana.core.agent.components.observer import ObserverProtocol

from pathlib import Path
from typing import Any


class ReportsFolderObserver(ObserverProtocol):
    """
    Observer that tracks files in the reports folder and their sizes.
    
    Monitors the reports directory and returns information about all files
    including their names and sizes.
    """
    
    def __init__(self, reports_folder_path: str | Path):
        """
        Initialize the ReportsFolderObserver.
        
        Args:
            reports_folder_path: Path to the reports folder to monitor
        """
        self.reports_folder = Path(reports_folder_path)
        self._monitoring = False
    
    def observe(self) -> dict[str, Any]:
        """
        Observe the reports folder and return file information.
        
        Returns:
            Dictionary with folder path, file count, and file details including sizes
        """
        if not self.reports_folder.exists():
            return {
                "folder_path": str(self.reports_folder),
                "exists": False,
                "file_count": 0,
                "total_size_bytes": 0,
                "files": []
            }
        
        files_info = []
        total_size = 0
        file_count = 0
        
        # Iterate through all files in the reports folder
        for item in self.reports_folder.rglob("*"):
            if item.is_file():
                file_count += 1
                file_size = item.stat().st_size
                total_size += file_size
                
                files_info.append({
                    "name": item.name,
                    "path": str(item.relative_to(self.reports_folder)),
                    "size_bytes": file_size,
                    "size_kb": round(file_size / 1024, 2),
                    "size_mb": round(file_size / (1024 * 1024), 2) if file_size > 1024 * 1024 else 0,
                    "modified": item.stat().st_mtime
                })
        
        # Sort files by name for consistency
        files_info.sort(key=lambda x: x["name"])
        
        return {
            "folder_path": str(self.reports_folder),
            "exists": True,
            "file_count": file_count,
            "total_size_bytes": total_size,
            "total_size_kb": round(total_size / 1024, 2),
            "total_size_mb": round(total_size / (1024 * 1024), 2) if total_size > 1024 * 1024 else 0,
            "files": files_info
        }
    
    def start(self) -> None:
        """Start monitoring the reports folder."""
        self._monitoring = True
    
    def stop(self) -> None:
        """Stop monitoring the reports folder."""
        self._monitoring = False