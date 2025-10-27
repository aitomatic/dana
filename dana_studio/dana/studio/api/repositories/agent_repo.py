"""Agent repository for database operations."""

from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from dana.studio.api.core.models import Agent


class AbstractAgentRepo(ABC):
    """Abstract base class for agent repository."""

    @classmethod
    @abstractmethod
    async def get_agent(cls, agent_id: int, **kwargs) -> Agent | None:
        """Get an agent by ID."""
        pass

    @classmethod
    @abstractmethod
    async def update_agent_config(cls, agent_id: int, config_updates: dict, **kwargs) -> Agent:
        """Update agent config with new values."""
        pass


class SQLAgentRepo(AbstractAgentRepo):
    """SQL implementation of agent repository."""

    @classmethod
    def _get_db(cls, **kwargs) -> Session:
        """Extract database session from kwargs."""
        db = kwargs.get("db")
        if db is None:
            raise ValueError(f"Missing db of type {Session} in kwargs: {kwargs}")
        return db

    @classmethod
    async def get_agent(cls, agent_id: int, **kwargs) -> Agent | None:
        """Get an agent by ID."""
        db = cls._get_db(**kwargs)
        return db.query(Agent).filter(Agent.id == agent_id).first()

    @classmethod
    async def update_agent_config(cls, agent_id: int, config_updates: dict, **kwargs) -> Agent:
        """Update agent config with new values."""
        db = cls._get_db(**kwargs)
        agent = await cls.get_agent(agent_id, **kwargs)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")

        # Update config
        current_config = agent.config.copy() if agent.config else {}
        current_config.update(config_updates)
        agent.config = current_config

        flag_modified(agent, "config")
        db.commit()
        db.refresh(agent)
        return agent
