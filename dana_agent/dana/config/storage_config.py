# Storage configuration
from enum import StrEnum
from pathlib import Path

from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings


class StorageType(StrEnum):
    """
    Use StrEnum to avoid issues with string comparison.
    """
    NULL = "null"
    FILE = "file"
    # TODO: Implement other storage types
    # S3 = "s3" 
    # GCS = "gcs"
    # AZURE = "azure"
    # LOCAL = "local"

class StorageConfig(BaseSettings):
    type: StorageType = StorageType.NULL
    model_config = ConfigDict(use_enum_values=True)

class FileStorageConfig(StorageConfig):
    type: StorageType = StorageType.FILE
    workspace_folder: str = Field(default=str(Path.cwd()/".dana/dana_agent"))

def get_storage_config(mode: StorageType | str) -> StorageConfig:
    if mode == StorageType.FILE:
        return FileStorageConfig()
    else:
        raise ValueError(f"Invalid storage mode: {mode}")