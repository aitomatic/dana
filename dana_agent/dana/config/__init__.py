import os

from pydantic import Field
from pydantic_settings import BaseSettings

from .storage_config import StorageConfig, StorageType, get_storage_config


# MAIN CONFIG
_storage_mode = os.getenv("DANA_STORAGE_MODE", StorageType.FILE)


class Config(BaseSettings):
    storage_cfg: StorageConfig = Field(default_factory=lambda: get_storage_config(_storage_mode))


MAIN_CFG = Config()


__all__ = ["MAIN_CFG"]
