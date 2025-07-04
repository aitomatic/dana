from dana.common.resource.base_resource import BaseResource
from dana.common.mixins.tool_callable import ToolCallable
import os, glob

class FileReaderResource(BaseResource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @ToolCallable.tool
    async def read_single_file(self, file_path: str) -> str:
        """Read a single file."""
        print(f"Reading file: {file_path}")
        with open(file_path, "r") as file:
            return file.read()
        
    @ToolCallable.tool
    async def list_files(self, directory: str) -> str:
        """List all files in a directory."""
        return "\n".join([f for f in glob.glob(os.path.join(directory, "**", "*"), recursive=True) if os.path.isfile(f)])
        
    def query(self, query: str):
        pass