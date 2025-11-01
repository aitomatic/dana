from abc import ABC, abstractmethod

from dana.common.base_war import BaseWAR
from dana.common.protocols import Persistable
from dana.common.storage import AbstractStorage
from hashlib import sha256
from .codecs import AbstractCodec, CSXMLCodec
import inspect
from pathlib import Path

import structlog


logger = structlog.get_logger("prompts")


class BasePromptEngineer(ABC, Persistable):
    def __init__(
        self,
        component: BaseWAR,
        storage: AbstractStorage | None = None,
        codec: type[AbstractCodec] | None = None,
        force_generate: bool = False,
        check_conflicts: bool = False,
        **kwargs,
    ):
        super().__init__(storage=storage)
        self._component = component
        self._codec = codec or CSXMLCodec
        self._force_generate = force_generate
        self._check_conflicts = check_conflicts
        self._prompt = None
        self._prefix = "default"

    @property
    def prompt(self) -> str:
        if self._prompt is None:
            self._prompt = self._get_prompt()
        return self._prompt

    def _get_prompt(self) -> str:
        """
        Get the prompt for the component.
        """
        prompt = self.load()
        if prompt is None or self._force_generate:
            prompt = self.construct_prompt()
            self._prompt = prompt
            self.persist()
        return prompt

    @abstractmethod
    def construct_prompt(self) -> str:
        """
        Construct the prompt for the component.
        """
        pass

    @abstractmethod
    def check_conflicts(self) -> bool:
        """
        Check for conflicts in the prompt for the component.
        """
        pass

    @property
    def key(self) -> str:
        # TODO : NEED BETTER KEY TO HANDLE COLLISIONS
        file = inspect.getfile(self._component.__class__)
        codec_name = self._codec.__qualname__ if inspect.isclass(self._codec) else self._codec.__class__.__qualname__
        filename = Path(file).stem
        return f"{self._prefix}/{self._component.__class__.__qualname__}/{filename}__{codec_name}.prompt"

    def persist(self) -> None:
        """
        Persist the prompt for the component.
        """
        if self._prompt is None:
            raise ValueError(f"[{self.__class__.__qualname__}] Prompt for {self._component.__class__.__qualname__} is not generated yet")
        self._storage.persist(self.key, self._prompt)
        logger.info(f"Prompt persisted for {self._component.__class__.__qualname__} with key {self.key}")

    def load(self) -> str | None:
        """
        Load the prompt for the component.
        """
        return self._storage.load(self.key)

    def with_prefix(self, prefix: str) -> "BasePromptEngineer":
        self._prefix = prefix
        return self

    
