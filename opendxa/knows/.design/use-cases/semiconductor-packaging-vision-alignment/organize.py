"""
Organize Phase: Knowledge Structure and Storage

Input: Knowledge content + storage structure decisions
Output: Knowledge units + organized knowledge base
"""

import uuid
from datetime import datetime
from typing import Any

from common.knowledge_units import KnowledgeUnit, P_T_Classification, Phase, SourceType, Type
from common.storage_types import KnowledgeStorage, StorageType


class OrganizePhase:
    """Implements the Organize phase of the CORRAL lifecycle."""

    def __init__(self):
        self.knowledge_units = []
        self.knowledge_base = {}
        self.storage_manager = KnowledgeStorage()

    def create_knowledge_units(self, knowledge_content: dict[str, Any], storage_decisions: dict[str, StorageType]) -> list[KnowledgeUnit]:
        """Create knowledge units from content and storage decisions."""

        print("🏗️  Creating knowledge units...")

        knowledge_units = []

        # Map knowledge types to P-T classifications
        p_t_mappings = {
            "equipment_specifications": P_T_Classification(Phase.DOCUMENTARY, Type.TOPICAL),
            "material_properties": P_T_Classification(Phase.PRIOR, Type.TOPICAL),
            "calibration_standards": P_T_Classification(Phase.DOCUMENTARY, Type.TOPICAL),
            "calibration_workflows": P_T_Classification(Phase.DOCUMENTARY, Type.PROCEDURAL),
            "troubleshooting_procedures": P_T_Classification(Phase.EXPERIENTIAL, Type.PROCEDURAL),
            "optimization_techniques": P_T_Classification(Phase.EXPERIENTIAL, Type.PROCEDURAL),
        }

        # Map knowledge types to source types
        source_mappings = {
            "equipment_specifications": SourceType.DOCUMENT,
            "material_properties": SourceType.HUMAN,
            "calibration_standards": SourceType.DOCUMENT,
            "calibration_workflows": SourceType.DOCUMENT,
            "troubleshooting_procedures": SourceType.HUMAN,
            "optimization_techniques": SourceType.HUMAN,
        }

        for knowledge_type, content_data in knowledge_content.items():
            # Create knowledge unit
            knowledge_unit = KnowledgeUnit(
                id=str(uuid.uuid4()),
                content=content_data["content"],
                p_t_classification=p_t_mappings[knowledge_type],
                source_type=source_mappings[knowledge_type],
                source_authority=content_data["source_authority"],
                confidence=content_data["confidence"],
                scope=content_data["scope"],
                status="raw",
                usage_count=0,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                metadata={
                    "knowledge_type": knowledge_type,
                    "storage_type": storage_decisions[knowledge_type].value,
                    "use_case": "semiconductor_packaging_vision_alignment",
                },
            )

            knowledge_units.append(knowledge_unit)
            print(f"  Created unit {knowledge_unit.id[:8]}... for {knowledge_type}")

        self.knowledge_units = knowledge_units
        print(f"✅ Created {len(knowledge_units)} knowledge units")

        return knowledge_units

    def store_knowledge(self, knowledge_units: list[KnowledgeUnit]) -> dict[str, Any]:
        """Store knowledge units in appropriate storage systems."""

        print("💾 Storing knowledge in organized structures...")

        knowledge_base = {"units": {}, "storage_systems": {}, "indexes": {}}

        # Store each knowledge unit
        for unit in knowledge_units:
            knowledge_base["units"][unit.id] = unit

            # Store in appropriate storage system
            storage_type = StorageType(unit.metadata["storage_type"])
            storage_key = f"{unit.metadata['knowledge_type']}_{unit.id[:8]}"

            # Convert to storage format
            storage_data = self._prepare_storage_data(unit, storage_type)

            # Store in storage system
            success = self.storage_manager.store_knowledge(storage_type, storage_key, storage_data)

            if success:
                # Track storage location
                if storage_type.value not in knowledge_base["storage_systems"]:
                    knowledge_base["storage_systems"][storage_type.value] = []
                knowledge_base["storage_systems"][storage_type.value].append(storage_key)

                # Update indexes
                self._update_indexes(knowledge_base, unit)

                print(f"  Stored {storage_key} in {storage_type.value}")

        self.knowledge_base = knowledge_base
        print(f"✅ Stored {len(knowledge_units)} units across {len(knowledge_base['storage_systems'])} storage systems")

        return knowledge_base

    def _prepare_storage_data(self, unit: KnowledgeUnit, storage_type: StorageType) -> dict[str, Any]:
        """Prepare knowledge unit data for specific storage type."""

        base_data = {
            "id": unit.id,
            "content": unit.content,
            "phase": unit.p_t_classification.phase.value,
            "type": unit.p_t_classification.type.value,
            "source_type": unit.source_type.value,
            "confidence": unit.confidence,
            "scope": unit.scope,
            "status": unit.status,
            "usage_count": unit.usage_count,
            "created_at": unit.created_at.isoformat(),
            "updated_at": unit.updated_at.isoformat(),
            "metadata": unit.metadata,
        }

        # Add storage-specific formatting
        if storage_type == StorageType.RELATIONAL:
            # Add structured fields for relational queries
            base_data.update(
                {
                    "knowledge_type": unit.metadata["knowledge_type"],
                    "accuracy_requirement": "±0.1mm",
                    "package_type": "BGA",
                    "substrate_material": "High-Tg FR4",
                }
            )

        elif storage_type == StorageType.SEMI_STRUCTURED:
            # Add tags and hierarchical structure
            base_data.update(
                {
                    "tags": unit.scope + [unit.metadata["knowledge_type"], unit.p_t_classification.phase.value],
                    "hierarchy": {
                        "domain": "semiconductor_packaging",
                        "subdomain": "vision_alignment",
                        "category": unit.metadata["knowledge_type"],
                    },
                }
            )

        elif storage_type == StorageType.VECTOR:
            # Add vector-specific metadata
            base_data.update(
                {"embedding_keywords": unit.scope + [unit.metadata["knowledge_type"]], "similarity_domain": "semiconductor_packaging"}
            )

        elif storage_type == StorageType.TIME_SERIES:
            # Add temporal metadata
            base_data.update({"temporal_pattern": "calibration_sequence", "frequency": "on_demand", "time_window": "24_hours"})

        return base_data

    def _update_indexes(self, knowledge_base: dict[str, Any], unit: KnowledgeUnit):
        """Update search indexes for the knowledge unit."""

        if "indexes" not in knowledge_base:
            knowledge_base["indexes"] = {}

        # Index by scope
        for scope_item in unit.scope:
            if scope_item not in knowledge_base["indexes"]:
                knowledge_base["indexes"][scope_item] = []
            knowledge_base["indexes"][scope_item].append(unit.id)

        # Index by phase
        phase = unit.p_t_classification.phase.value
        if f"phase_{phase}" not in knowledge_base["indexes"]:
            knowledge_base["indexes"][f"phase_{phase}"] = []
        knowledge_base["indexes"][f"phase_{phase}"].append(unit.id)

        # Index by type
        knowledge_type = unit.p_t_classification.type.value
        if f"type_{knowledge_type}" not in knowledge_base["indexes"]:
            knowledge_base["indexes"][f"type_{knowledge_type}"] = []
        knowledge_base["indexes"][f"type_{knowledge_type}"].append(unit.id)

        # Index by knowledge type
        k_type = unit.metadata["knowledge_type"]
        if f"knowledge_{k_type}" not in knowledge_base["indexes"]:
            knowledge_base["indexes"][f"knowledge_{k_type}"] = []
        knowledge_base["indexes"][f"knowledge_{k_type}"].append(unit.id)

    def get_storage_manager(self) -> KnowledgeStorage:
        """Get the storage manager for external access."""
        return self.storage_manager
