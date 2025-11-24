# Storage configuration
import os
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
    LANGFUSE = "langfuse"
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

class LangfuseStorageConfig(StorageConfig):
    type: StorageType = StorageType.LANGFUSE
    public_key: str | None = Field(default=os.getenv("LANGFUSE_PUBLIC_KEY"))
    secret_key: str | None = Field(default=os.getenv("LANGFUSE_SECRET_KEY"))
    host: str = Field(default=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"))
    project_id: str | None = Field(default=None)

def get_storage_config(mode: StorageType | str) -> StorageConfig:
    if mode == StorageType.FILE:
        return FileStorageConfig()
    elif mode == StorageType.LANGFUSE:
        return LangfuseStorageConfig()
    else:
        raise ValueError(f"Invalid storage mode: {mode}")