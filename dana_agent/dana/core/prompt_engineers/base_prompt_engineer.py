
from typing import override

from dana.common.base_war import BaseWAR

from .loaders.abstract_loader import AbstractLoader


class BasePromptEngineer:
    def __init__(self, component: BaseWAR, loader: AbstractLoader):
        self._loader = loader
        self._component = component

    @override
    def get_prompt(self) -> str:
        return self._loader.get_xml()

    