

from abc import ABC, abstractmethod

from dana.common.base_war import BaseWAR
from dana.common.protocols import Persistable
from dana.common.storage import AbstractStorage

from .codecs import AbstractCodec, CSXMLCodec


class BasePromptEngineer(ABC, Persistable):
    def __init__(self, component: BaseWAR, 
                    storage: AbstractStorage | None = None,
                    codec: type[AbstractCodec] | None = None,
                    force_generate: bool = False,
                    check_conflicts: bool = False,
                    **kwargs):
        super().__init__(storage=storage)
        self._component = component
        self._codec = codec or CSXMLCodec
        self._force_generate = force_generate
        self._check_conflicts = check_conflicts
        self._prompt = None


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
        return f"{self._component.__class__.__qualname__}{self._component.object_id}.prompt"

    def persist(self) -> None:
        """
        Persist the prompt for the component.
        """
        prompt = self._prompt
        if prompt is None:
            prompt = self.construct_prompt()
        self._storage.persist(self.key, prompt)

    def load(self) -> str | None:
        """
        Load the prompt for the component.
        """
        return self._storage.load(self.key)