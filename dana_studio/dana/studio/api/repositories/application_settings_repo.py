from abc import ABC, abstractmethod
from typing import Optional
from sqlalchemy.orm import Session
from dana.studio.api.core.models import ApplicationSettings
import logging

logger = logging.getLogger(__name__)


class AbstractApplicationSettingsRepo(ABC):
    @classmethod
    @abstractmethod
    async def get_setting(cls, category: str, key: str, db: Session) -> Optional[str]:
        """Get a setting value by category and key."""
        pass

    @classmethod
    @abstractmethod
    async def get_setting_with_metadata(cls, category: str, key: str, db: Session) -> Optional[ApplicationSettings]:
        """Get a setting with full metadata."""
        pass

    @classmethod
    @abstractmethod
    async def set_setting(
        cls,
        category: str,
        key: str,
        value: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        placeholders: Optional[list[str]] = None,
        placeholder_examples: Optional[dict[str, str]] = None,
        default_value: Optional[str] = None,
        db: Session = None,
    ) -> ApplicationSettings:
        """Set or update a setting value."""
        pass

    @classmethod
    @abstractmethod
    async def get_settings_by_category(cls, category: str, db: Session) -> list[ApplicationSettings]:
        """Get all settings for a category."""
        pass

    @classmethod
    @abstractmethod
    async def get_all_settings(cls, db: Session) -> dict[str, list[ApplicationSettings]]:
        """Get all settings organized by category."""
        pass


class SQLApplicationSettingsRepo(AbstractApplicationSettingsRepo):
    @classmethod
    async def get_setting(cls, category: str, key: str, db: Session) -> Optional[str]:
        """Get a setting value by category and key."""
        full_key = f"{category}.{key}"
        setting = db.query(ApplicationSettings).filter(ApplicationSettings.full_key == full_key).first()
        if setting and setting.is_active:
            return setting.value
        return None

    @classmethod
    async def get_setting_with_metadata(cls, category: str, key: str, db: Session) -> Optional[ApplicationSettings]:
        """Get a setting with full metadata."""
        full_key = f"{category}.{key}"
        return db.query(ApplicationSettings).filter(ApplicationSettings.full_key == full_key).first()

    @classmethod
    async def set_setting(
        cls,
        category: str,
        key: str,
        value: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        placeholders: Optional[list[str]] = None,
        placeholder_examples: Optional[dict[str, str]] = None,
        default_value: Optional[str] = None,
        db: Session = None,
    ) -> ApplicationSettings:
        """Set or update a setting value."""
        full_key = f"{category}.{key}"
        setting = db.query(ApplicationSettings).filter(ApplicationSettings.full_key == full_key).first()

        if setting:
            setting.value = value
            if name:
                setting.name = name
            if description:
                setting.description = description
            if placeholders is not None:
                setting.placeholders = placeholders
            if placeholder_examples is not None:
                setting.placeholder_examples = placeholder_examples
            if default_value:
                setting.default_value = default_value
        else:
            setting = ApplicationSettings(
                category=category,
                key=key,
                full_key=full_key,
                value=value,
                name=name or key.replace("_", " ").title(),
                description=description,
                placeholders=placeholders or [],
                placeholder_examples=placeholder_examples or {},
                default_value=default_value,
            )
            db.add(setting)

        db.commit()
        db.refresh(setting)
        return setting

    @classmethod
    async def get_settings_by_category(cls, category: str, db: Session) -> list[ApplicationSettings]:
        """Get all settings for a category."""
        return db.query(ApplicationSettings).filter(ApplicationSettings.category == category, ApplicationSettings.is_active.is_(True)).all()

    @classmethod
    async def get_all_settings(cls, db: Session) -> dict[str, list[ApplicationSettings]]:
        """Get all settings organized by category."""
        settings = db.query(ApplicationSettings).filter(ApplicationSettings.is_active.is_(True)).all()

        result = {}
        for setting in settings:
            if setting.category not in result:
                result[setting.category] = []
            result[setting.category].append(setting)

        return result
