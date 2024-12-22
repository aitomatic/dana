class CapabilityFactory:
    @classmethod
    def create_capability(cls, capability_type: str) -> BaseCapability:
        """Create capability instance."""
        if capability_type == "research":
            return ResearchCapability()
        raise ValueError(f"Unknown capability: {capability_type}") 