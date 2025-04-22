from opendxa.base.resource import BaseResource as BadBaseResource
from opendxa.common.mixins.loggable import Loggable
from opendxa.common.mixins.configurable import Configurable
from opendxa.common.mixins.queryable import Queryable, QueryStrategy, QueryResponse
from typing import Optional, Dict, Any

class BaseResource(BadBaseResource):
    """Base resource for all resources."""

    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize resource.

        Args:
            name: Resource name
            description: Optional resource description
            config: Optional additional configuration
        """
        # Initialize Loggable first to ensure logger is available
        Loggable.__init__(self)

        # Initialize Configurable with the provided config
        config_dict = config or {}
        if name:
            config_dict["name"] = name
        if description:
            config_dict["description"] = description
        Configurable.__init__(self, **config_dict)
        self._query_strategy = self.config.get("query_strategy", QueryStrategy.ONCE)
        self._query_max_iterations = self.config.get("query_max_iterations", 3)
        Queryable.__init__(self) # NOTE : This __init__ will override the description and name to None

        self._is_available = False  # will only be True after initialization

        self.name = self.config["name"]
        self.description = self.config["description"] or "No description provided"


        
