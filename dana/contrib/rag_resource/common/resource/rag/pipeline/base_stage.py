from dana.common.mixins import Loggable


class BaseStage(Loggable):
    """Base class for all stages in the RAG pipeline."""

    _NAME = "base_stage"

    def __init__(self):
        super().__init__()

    @property
    def name(self) -> str:
        return self._NAME

    @property
    def info(self) -> dict[str, any]:
        _info = self._get_info()
        return {k: _info[k] for k in sorted(_info.keys())}

    def _get_info(self) -> dict[str, any]:
        """Get all public instance attributes with basic types and their values from the current object.

        This method uses reflection to gather all instance attributes that don't start with
        underscore (private attributes) and have basic Python types.

        Returns:
            Dictionary containing all public instance attributes with basic types and their values.

        Note:
            - Excludes private attributes (starting with _)
            - Excludes methods and other callables
            - Excludes class attributes (only includes instance attributes)
            - Only includes basic types: int, str, bool, float, None, list, dict, tuple, set
            - Excludes complex objects, classes, and custom types
        """
        info = {}

        # Define basic types we want to include
        basic_types = (int, str, bool, float, type(None), list, dict, tuple, set)

        # Only look at instance attributes in __dict__ if it exists
        if hasattr(self, "__dict__"):
            for attr_name, attr_value in self.__dict__.items():
                if not attr_name.startswith("_"):
                    if isinstance(attr_value, basic_types):
                        info[attr_name] = attr_value

        return info
