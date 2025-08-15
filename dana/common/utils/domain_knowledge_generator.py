"""
Domain Knowledge Generator
Generates domain_knowledge.json files from knowledge file names for prebuilt agents.
"""

import json
import os


class DomainKnowledgeNode:
    """Represents a node in the domain knowledge tree."""

    def __init__(self, topic: str):
        self.topic = topic
        self.children: dict[str, DomainKnowledgeNode] = {}

    def add_child(self, child_topic: str) -> "DomainKnowledgeNode":
        """Add a child node and return it."""
        if child_topic not in self.children:
            self.children[child_topic] = DomainKnowledgeNode(child_topic)
        return self.children[child_topic]

    def to_dict(self) -> dict:
        """Convert the node to a dictionary representation."""
        return {"topic": self.topic, "children": [child.to_dict() for child in self.children.values()]}


class DomainKnowledgeGenerator:
    """Generates domain knowledge trees from knowledge file names."""

    def __init__(self):
        self.separator = "___"  # Separator used in knowledge file names

    def parse_knowledge_files(self, knows_folder: str) -> list[list[str]]:
        """
        Parse knowledge files and extract hierarchical paths.

        Args:
            knows_folder: Path to the knows folder containing knowledge files

        Returns:
            List of hierarchical paths (each path is a list of topic levels)
        """
        if not os.path.exists(knows_folder):
            return []

        paths = []
        for filename in os.listdir(knows_folder):
            if filename.endswith(".json") and filename != "knowledge_status.json":
                # Remove .json extension
                name_without_ext = filename[:-5]
                # Split by separator to get hierarchy levels
                path_parts = name_without_ext.split(self.separator)
                # Clean up and filter out empty parts
                clean_parts = [part.strip().replace("_", " ") for part in path_parts if part.strip()]
                if clean_parts:
                    paths.append(clean_parts)

        return paths

    def build_tree(self, paths: list[list[str]], root_topic: str) -> DomainKnowledgeNode:
        """
        Build a domain knowledge tree from hierarchical paths.

        Args:
            paths: List of hierarchical paths
            root_topic: The root topic name

        Returns:
            Root node of the domain knowledge tree
        """
        root = DomainKnowledgeNode(root_topic)

        for path in paths:
            current = root
            for topic in path:
                current = current.add_child(topic)

        return root

    def optimize_tree(self, node: DomainKnowledgeNode, max_depth: int = 3, current_depth: int = 0) -> DomainKnowledgeNode:
        """
        Optimize the tree by removing redundant levels and ensuring reasonable depth.

        Args:
            node: The node to optimize
            max_depth: Maximum depth allowed
            current_depth: Current depth in tree

        Returns:
            Optimized node
        """
        # Clean up topic name
        node.topic = self._clean_topic_name(node.topic)

        # If we're at max depth, make this a leaf node
        if current_depth >= max_depth:
            node.children = {}
            return node

        # If node has only one child, consider flattening
        if len(node.children) == 1:
            child = list(node.children.values())[0]
            # If the child has the same name as parent or is very similar, flatten
            if self._should_flatten(node.topic, child.topic):
                return self.optimize_tree(child, max_depth, current_depth)

        # Recursively optimize children
        optimized_children = {}
        for _topic, child in node.children.items():
            optimized_child = self.optimize_tree(child, max_depth, current_depth + 1)
            optimized_children[optimized_child.topic] = optimized_child

        node.children = optimized_children
        return node

    def _should_flatten(self, parent_topic: str, child_topic: str) -> bool:
        """Determine if a parent-child relationship should be flattened."""
        parent_words = set(parent_topic.lower().split())
        child_words = set(child_topic.lower().split())

        # If child topic contains all words from parent, consider flattening
        if parent_words.issubset(child_words):
            return True

        # If topics are very similar (>70% word overlap), consider flattening
        overlap = len(parent_words.intersection(child_words))
        total_unique = len(parent_words.union(child_words))
        if total_unique > 0 and overlap / total_unique > 0.7:
            return True

        return False

    def _clean_topic_name(self, topic: str) -> str:
        """Clean up topic names by shortening overly long names and improving readability."""
        # Replace underscores with spaces
        topic = topic.replace("_", " ")

        # Split very long topics and take the most relevant parts
        if len(topic) > 50:
            parts = topic.split(",")
            if len(parts) > 1:
                # Take first 2-3 most important parts
                topic = ", ".join(parts[:3])
            else:
                # If no commas, try splitting by other delimiters
                parts = topic.split(" and ")
                if len(parts) > 1:
                    topic = parts[0]  # Take the first main part

        # Capitalize properly
        words = topic.split()
        if words:
            # Capitalize each word except common articles/prepositions
            stop_words = {"and", "or", "the", "a", "an", "in", "on", "at", "to", "for", "of", "with"}
            topic = " ".join(
                [word.capitalize() if word.lower() not in stop_words or i == 0 else word.lower() for i, word in enumerate(words)]
            )

        return topic

    def generate_from_folder(self, knows_folder: str, domain: str) -> dict:
        """
        Generate domain knowledge JSON from a knows folder.

        Args:
            knows_folder: Path to the knows folder
            domain: The domain name (e.g., "Finance")

        Returns:
            Domain knowledge dictionary ready for JSON serialization
        """
        # Parse knowledge files
        paths = self.parse_knowledge_files(knows_folder)

        if not paths:
            # Return a minimal structure if no knowledge files found
            return {"root": {"topic": domain, "children": []}}

        # Build tree
        root = self.build_tree(paths, domain)

        # Optimize tree
        optimized_root = self.optimize_tree(root)

        return {"root": optimized_root.to_dict()}

    def save_domain_knowledge(self, knows_folder: str, domain: str, output_path: str) -> bool:
        """
        Generate and save domain knowledge file.

        Args:
            knows_folder: Path to the knows folder
            domain: The domain name
            output_path: Path where to save the domain_knowledge.json file

        Returns:
            True if successful, False otherwise
        """
        try:
            domain_knowledge = self.generate_from_folder(knows_folder, domain)

            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Save to file
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(domain_knowledge, f, indent=2, ensure_ascii=False)

            return True
        except Exception as e:
            print(f"Error generating domain knowledge file: {e}")
            return False


def generate_for_prebuilt_agent(agent_id: str, prebuilt_assets_dir: str) -> bool:
    """
    Generate domain_knowledge.json for a specific prebuilt agent.

    Args:
        agent_id: The agent ID (e.g., "sofia_finance_expert")
        prebuilt_assets_dir: Path to the prebuilt assets directory

    Returns:
        True if successful, False otherwise
    """
    generator = DomainKnowledgeGenerator()

    # Paths
    agent_folder = os.path.join(prebuilt_assets_dir, agent_id)
    knows_folder = os.path.join(agent_folder, "knows")
    output_path = os.path.join(agent_folder, "domain_knowledge.json")

    # Load agent config to get domain
    prebuilt_agents_file = os.path.join(prebuilt_assets_dir, "prebuilt_agents.json")
    domain = "General"  # Default

    try:
        with open(prebuilt_agents_file, encoding="utf-8") as f:
            agents = json.load(f)
            for agent in agents:
                if agent.get("id") == agent_id:
                    domain = agent.get("config", {}).get("domain", "General")
                    break
    except Exception as e:
        print(f"Warning: Could not load agent config for {agent_id}: {e}")

    return generator.save_domain_knowledge(knows_folder, domain, output_path)


if __name__ == "__main__":
    # Example usage
    assets_dir = "/Users/vophihung/projects/aitomatic/opendxa/dana/api/server/assets"
    generate_for_prebuilt_agent("sofia_finance_expert", assets_dir)
