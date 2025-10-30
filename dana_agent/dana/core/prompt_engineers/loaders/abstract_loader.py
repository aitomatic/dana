from abc import ABC, abstractmethod

from dana.common.base_war import BaseWAR

"""
AbstractLoader is an abstract base class for all prompt loaders.
It defines the interface for all prompt loaders.

This will help extend the capabilities of the prompt engineer when we need to load prompts from S3 or Database instead of local file system.
"""

class AbstractLoader(ABC):

    def __init__(self, component: BaseWAR):
        self._component = component

    @abstractmethod
    def get_xml(self) -> str:
        pass

    @abstractmethod
    def write_back(self, xml_string: str) -> None:
        pass