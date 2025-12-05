from enum import StrEnum
import os

from pydantic import BaseSettings, ConfigDict


# Storage configuration
class StorageType(StrEnum):
    """
    Use StrEnum to avoid issues with string comparison.
    """

    FILE = "file"
    # TODO: Implement other storage types
    # S3 = "s3"
    # GCS = "gcs"
    # AZURE = "azure"
    # LOCAL = "local"


class StorageConfig(BaseSettings):
    type: StorageType
    model_config = ConfigDict(use_enum_values=True)


class FileStorageConfig(StorageConfig):
    workspace_folder: str | None


# MAIN CONFIG
class Config(BaseSettings):
    storage_cfg: StorageConfig


storage_mode = os.getenv("DANA_STORAGE_MODE", "file")
if storage_mode == StorageType.FILE:
    storage_cfg = FileStorageConfig()
else:
    raise ValueError(f"Invalid storage mode: {storage_mode}")

config = Config()
