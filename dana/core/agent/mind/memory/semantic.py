"""
Semantic memory for facts and domain knowledge.
"""

from datetime import datetime
from typing import Any
import json
from pathlib import Path


class SemanticMemory:
    """Semantic memory for storing facts, concepts, and domain knowledge."""

    def __init__(self, storage_dir: str | None = None):
        """Initialize semantic memory.

        Args:
            storage_dir: Directory for persistent storage
        """
        self.storage_dir = Path(storage_dir) if storage_dir else Path("~/.dana/memory/semantic").expanduser()
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self._facts: dict[str, dict[str, Any]] = {}
        self._concepts: dict[str, dict[str, Any]] = {}
        self._domains: dict[str, dict[str, Any]] = {}
        self._load_knowledge()

    def store_fact(self, key: str, fact: Any, domain: str = "general", confidence: float = 1.0, **metadata) -> None:
        """Store a fact in semantic memory.

        Args:
            key: Fact identifier
            fact: The fact data
            domain: Knowledge domain
            confidence: Confidence in the fact (0.0 to 1.0)
            **metadata: Additional metadata
        """
        self._facts[key] = {
            "fact": fact,
            "domain": domain,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata,
        }

        # Update domain index
        if domain not in self._domains:
            self._domains[domain] = {"facts": [], "concepts": []}
        if key not in self._domains[domain]["facts"]:
            self._domains[domain]["facts"].append(key)

        self._save_knowledge()

    def store_concept(self, key: str, concept: Any, domain: str = "general", **metadata) -> None:
        """Store a concept in semantic memory.

        Args:
            key: Concept identifier
            concept: The concept data
            domain: Knowledge domain
            **metadata: Additional metadata
        """
        self._concepts[key] = {
            "concept": concept,
            "domain": domain,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata,
        }

        # Update domain index
        if domain not in self._domains:
            self._domains[domain] = {"facts": [], "concepts": []}
        if key not in self._domains[domain]["concepts"]:
            self._domains[domain]["concepts"].append(key)

        self._save_knowledge()

    def query(self, query: str, domain: str | None = None) -> dict[str, Any]:
        """Query semantic memory for relevant knowledge.

        Args:
            query: Query string
            domain: Specific domain to search (optional)

        Returns:
            Dictionary with relevant facts and concepts
        """
        results = {"facts": [], "concepts": []}
        query_lower = query.lower()

        # Search facts
        facts_to_search = self._facts
        if domain:
            domain_facts = self._domains.get(domain, {}).get("facts", [])
            facts_to_search = {k: v for k, v in self._facts.items() if k in domain_facts}

        for key, fact_data in facts_to_search.items():
            if self._matches_query(key, fact_data, query_lower):
                results["facts"].append(
                    {
                        "key": key,
                        "fact": fact_data["fact"],
                        "confidence": fact_data["confidence"],
                        "domain": fact_data["domain"],
                    }
                )

        # Search concepts
        concepts_to_search = self._concepts
        if domain:
            domain_concepts = self._domains.get(domain, {}).get("concepts", [])
            concepts_to_search = {k: v for k, v in self._concepts.items() if k in domain_concepts}

        for key, concept_data in concepts_to_search.items():
            if self._matches_query(key, concept_data, query_lower):
                results["concepts"].append(
                    {
                        "key": key,
                        "concept": concept_data["concept"],
                        "domain": concept_data["domain"],
                    }
                )

        return results

    def has_knowledge(self, query: str) -> bool:
        """Check if semantic memory has relevant knowledge.

        Args:
            query: Query string

        Returns:
            True if relevant knowledge found
        """
        result = self.query(query)
        return len(result["facts"]) > 0 or len(result["concepts"]) > 0

    def get_domain_knowledge(self, domain: str) -> dict[str, Any]:
        """Get all knowledge for a specific domain.

        Args:
            domain: Domain name

        Returns:
            Dictionary with domain facts and concepts
        """
        if domain not in self._domains:
            return {"facts": [], "concepts": []}

        domain_data = self._domains[domain]

        facts = []
        for fact_key in domain_data["facts"]:
            if fact_key in self._facts:
                fact_data = self._facts[fact_key]
                facts.append(
                    {
                        "key": fact_key,
                        "fact": fact_data["fact"],
                        "confidence": fact_data["confidence"],
                    }
                )

        concepts = []
        for concept_key in domain_data["concepts"]:
            if concept_key in self._concepts:
                concept_data = self._concepts[concept_key]
                concepts.append(
                    {
                        "key": concept_key,
                        "concept": concept_data["concept"],
                    }
                )

        return {"facts": facts, "concepts": concepts}

    def get_domains(self) -> list[str]:
        """Get list of all knowledge domains.

        Returns:
            List of domain names
        """
        return list(self._domains.keys())

    def count(self) -> int:
        """Get total count of stored knowledge.

        Returns:
            Total number of facts and concepts
        """
        return len(self._facts) + len(self._concepts)

    def _matches_query(self, key: str, data: dict[str, Any], query_lower: str) -> bool:
        """Check if a knowledge item matches the query.

        Args:
            key: Knowledge key
            data: Knowledge data
            query_lower: Lowercase query string

        Returns:
            True if matches
        """
        # Check key
        if query_lower in key.lower():
            return True

        # Check content
        content = data.get("fact", data.get("concept", ""))
        if query_lower in str(content).lower():
            return True

        # Check metadata
        metadata = data.get("metadata", {})
        if "tags" in metadata:
            for tag in metadata["tags"]:
                if query_lower in tag.lower():
                    return True

        return False

    def _save_knowledge(self) -> None:
        """Save knowledge to persistent storage."""
        knowledge_file = self.storage_dir / "knowledge.json"

        try:
            with open(knowledge_file, "w") as f:
                json.dump(
                    {
                        "facts": self._facts,
                        "concepts": self._concepts,
                        "domains": self._domains,
                    },
                    f,
                    indent=2,
                    default=str,
                )
        except Exception as e:
            print(f"Error saving semantic memory: {e}")

    def _load_knowledge(self) -> None:
        """Load knowledge from persistent storage."""
        knowledge_file = self.storage_dir / "knowledge.json"

        if knowledge_file.exists():
            try:
                with open(knowledge_file) as f:
                    data = json.load(f)
                    self._facts = data.get("facts", {})
                    self._concepts = data.get("concepts", {})
                    self._domains = data.get("domains", {})
            except Exception as e:
                print(f"Error loading semantic memory: {e}")
                self._facts = {}
                self._concepts = {}
                self._domains = {}
