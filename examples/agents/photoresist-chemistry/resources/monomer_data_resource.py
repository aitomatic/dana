"""
Monomer Data Resource for Photoresist Chemist.

Provides access to monomer and additive data from Excel files.
Handles structured data queries for chemical properties and molecular information.
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Dict, List, Any

from dana.common.protocols.types import DictParams
from dana.common.protocols.war import tool_use
from dana.core.resource.base_resource import BaseResource


class MonomerDataResource(BaseResource):
    """
    Resource for accessing and querying monomer and additive data.

    Features:
    - Load and query monomer Excel data
    - Search by name, type, team, molecular weight
    - Extract chemical properties and SMILES structures
    - Analyze molecular characteristics and compatibility
    """

    def __init__(self, resource_id: str | None = None, data_path: str | None = None, **kwargs):
        """
        Initialize the MonomerDataResource.

        Args:
            resource_id: Unique identifier for this resource
            data_path: Path to monomer Excel file
            **kwargs: Additional arguments passed to BaseResource
        """
        super().__init__(resource_type="monomer-data", resource_id=resource_id or "monomer-data", **kwargs)

        # Set default data path if not provided
        if data_path is None:
            current_dir = Path(__file__).parent
            data_path = current_dir / "Monomer_example_data.xlsx"

        self.data_path = Path(data_path)
        self._data = None
        self._load_data()

    def _load_data(self) -> None:
        """Load monomer data from Excel file."""
        try:
            if self.data_path.exists():
                self._data = pd.read_excel(self.data_path)
                print(f"Loaded monomer data: {len(self._data)} monomers, {len(self._data.columns)} columns")
            else:
                print(f"Warning: Monomer data file not found at {self.data_path}")
                self._data = pd.DataFrame()
        except Exception as e:
            print(f"Error loading monomer data: {e}")
            self._data = pd.DataFrame()

    @tool_use
    def search_by_name(self, name: str, **kwargs) -> DictParams:
        """
        Search for monomer data by name.

        Args:
            name: Name to search for (e.g., "PS", "Tcp", "Fdp")
            **kwargs: Additional parameters

        Returns:
            Dictionary with search results
        """
        try:
            if self._data is None or self._data.empty:
                return {
                    "success": False,
                    "results": [],
                    "error": "No monomer data available"
                }

            # Search for name
            matches = self._data[
                self._data['Name'].str.contains(name, case=False, na=False)
            ]

            results = []
            for _, row in matches.iterrows():
                result = {
                    "name": row.get('Name', ''),
                    "smiles": row.get('SMILES', ''),
                    "type": row.get('Type', ''),
                    "team": row.get('Team', ''),
                    "anion": row.get('Anion', ''),
                    "cation": row.get('Cation', ''),
                    "molecular_weight": row.get('MW', ''),
                    "prop_a": row.get('PropA', ''),
                    "prop_b": row.get('PropB', ''),
                    "is_ionic": pd.notna(row.get('Anion', '')) or pd.notna(row.get('Cation', '')),
                    "has_properties": pd.notna(row.get('PropA', '')) and pd.notna(row.get('PropB', ''))
                }
                results.append(result)

            return {
                "success": True,
                "results": results,
                "total_matches": len(results),
                "error": None
            }

        except Exception as e:
            return {
                "success": False,
                "results": [],
                "error": f"Name search failed: {str(e)}"
            }

    @tool_use
    def search_by_type(self, monomer_type: str, **kwargs) -> DictParams:
        """
        Search for monomers by type.

        Args:
            monomer_type: Type to search for (e.g., "Monomer", "Monomer2", "GreatMonomer", "Additive")
            **kwargs: Additional parameters

        Returns:
            Dictionary with search results
        """
        try:
            if self._data is None or self._data.empty:
                return {
                    "success": False,
                    "results": [],
                    "error": "No monomer data available"
                }

            # Search for type (handle list format)
            matches = self._data[
                self._data['Type'].astype(str).str.contains(monomer_type, case=False, na=False)
            ]

            results = []
            for _, row in matches.iterrows():
                result = {
                    "name": row.get('Name', ''),
                    "smiles": row.get('SMILES', ''),
                    "type": row.get('Type', ''),
                    "team": row.get('Team', ''),
                    "anion": row.get('Anion', ''),
                    "cation": row.get('Cation', ''),
                    "molecular_weight": row.get('MW', ''),
                    "prop_a": row.get('PropA', ''),
                    "prop_b": row.get('PropB', ''),
                    "is_ionic": pd.notna(row.get('Anion', '')) or pd.notna(row.get('Cation', '')),
                    "has_properties": pd.notna(row.get('PropA', '')) and pd.notna(row.get('PropB', ''))
                }
                results.append(result)

            return {
                "success": True,
                "results": results,
                "total_matches": len(results),
                "error": None
            }

        except Exception as e:
            return {
                "success": False,
                "results": [],
                "error": f"Type search failed: {str(e)}"
            }

    @tool_use
    def search_by_team(self, team: str, **kwargs) -> DictParams:
        """
        Search for monomers by development team.

        Args:
            team: Team to search for (e.g., "E", "K", "A")
            **kwargs: Additional parameters

        Returns:
            Dictionary with search results
        """
        try:
            if self._data is None or self._data.empty:
                return {
                    "success": False,
                    "results": [],
                    "error": "No monomer data available"
                }

            # Search for team (handle list format)
            matches = self._data[
                self._data['Team'].astype(str).str.contains(team, case=False, na=False)
            ]

            results = []
            for _, row in matches.iterrows():
                result = {
                    "name": row.get('Name', ''),
                    "smiles": row.get('SMILES', ''),
                    "type": row.get('Type', ''),
                    "team": row.get('Team', ''),
                    "anion": row.get('Anion', ''),
                    "cation": row.get('Cation', ''),
                    "molecular_weight": row.get('MW', ''),
                    "prop_a": row.get('PropA', ''),
                    "prop_b": row.get('PropB', ''),
                    "is_ionic": pd.notna(row.get('Anion', '')) or pd.notna(row.get('Cation', '')),
                    "has_properties": pd.notna(row.get('PropA', '')) and pd.notna(row.get('PropB', ''))
                }
                results.append(result)

            return {
                "success": True,
                "results": results,
                "total_matches": len(results),
                "error": None
            }

        except Exception as e:
            return {
                "success": False,
                "results": [],
                "error": f"Team search failed: {str(e)}"
            }

    @tool_use
    def search_by_molecular_weight_range(self, min_mw: float, max_mw: float, **kwargs) -> DictParams:
        """
        Search for monomers by molecular weight range.

        Args:
            min_mw: Minimum molecular weight
            max_mw: Maximum molecular weight
            **kwargs: Additional parameters

        Returns:
            Dictionary with search results
        """
        try:
            if self._data is None or self._data.empty:
                return {
                    "success": False,
                    "results": [],
                    "error": "No monomer data available"
                }

            # Filter by molecular weight range
            matches = self._data[
                (self._data['MW'] >= min_mw) & (self._data['MW'] <= max_mw)
            ]

            results = []
            for _, row in matches.iterrows():
                result = {
                    "name": row.get('Name', ''),
                    "smiles": row.get('SMILES', ''),
                    "type": row.get('Type', ''),
                    "team": row.get('Team', ''),
                    "anion": row.get('Anion', ''),
                    "cation": row.get('Cation', ''),
                    "molecular_weight": row.get('MW', ''),
                    "prop_a": row.get('PropA', ''),
                    "prop_b": row.get('PropB', ''),
                    "is_ionic": pd.notna(row.get('Anion', '')) or pd.notna(row.get('Cation', '')),
                    "has_properties": pd.notna(row.get('PropA', '')) and pd.notna(row.get('PropB', ''))
                }
                results.append(result)

            return {
                "success": True,
                "results": results,
                "total_matches": len(results),
                "error": None
            }

        except Exception as e:
            return {
                "success": False,
                "results": [],
                "error": f"Molecular weight search failed: {str(e)}"
            }

    @tool_use
    def get_all_monomers(self, **kwargs) -> DictParams:
        """
        Get all available monomers with basic information.

        Returns:
            Dictionary with all monomers
        """
        try:
            if self._data is None or self._data.empty:
                return {
                    "success": False,
                    "results": [],
                    "error": "No monomer data available"
                }

            results = []
            for _, row in self._data.iterrows():
                result = {
                    "name": row.get('Name', ''),
                    "smiles": row.get('SMILES', ''),
                    "type": row.get('Type', ''),
                    "team": row.get('Team', ''),
                    "anion": row.get('Anion', ''),
                    "cation": row.get('Cation', ''),
                    "molecular_weight": row.get('MW', ''),
                    "prop_a": row.get('PropA', ''),
                    "prop_b": row.get('PropB', ''),
                    "is_ionic": pd.notna(row.get('Anion', '')) or pd.notna(row.get('Cation', '')),
                    "has_properties": pd.notna(row.get('PropA', '')) and pd.notna(row.get('PropB', ''))
                }
                results.append(result)

            return {
                "success": True,
                "results": results,
                "total_monomers": len(results),
                "error": None
            }

        except Exception as e:
            return {
                "success": False,
                "results": [],
                "error": f"Failed to get monomers: {str(e)}"
            }

    @property
    def is_available(self) -> bool:
        """Check if monomer data is available."""
        return self._data is not None and not self._data.empty


if __name__ == "__main__":
    """
    Demo usage of MonomerDataResource.
    """
    print("=" * 80)
    print("MonomerDataResource Demo")
    print("=" * 80)
    print()

    # Initialize resource
    resource = MonomerDataResource()
    print(f"Data available: {resource.is_available}")
    print()

    if resource.is_available:
        # Test search by name
        print("Searching for monomer 'PS':")
        result = resource.search_by_name("PS")
        if result['success']:
            print(f"Found {result['total_matches']} matches")
            for match in result['results']:
                print(f"  Name: {match['name']}")
                print(f"  Type: {match['type']}")
                print(f"  MW: {match['molecular_weight']}")
                print(f"  Properties: A={match['prop_a']}, B={match['prop_b']}")
        print()

        # Test search by type
        print("Searching for type 'Monomer':")
        result = resource.search_by_type("Monomer")
        if result['success']:
            print(f"Found {result['total_matches']} matches")
            for match in result['results']:
                print(f"  {match['name']}: {match['type']} (MW: {match['molecular_weight']})")
        print()

        # Test search by team
        print("Searching for team 'E':")
        result = resource.search_by_team("E")
        if result['success']:
            print(f"Found {result['total_matches']} matches")
            for match in result['results']:
                print(f"  {match['name']}: Team {match['team']}")
        print()

        # Test molecular weight range
        print("Searching for MW range 100-200:")
        result = resource.search_by_molecular_weight_range(100, 200)
        if result['success']:
            print(f"Found {result['total_matches']} matches")
            for match in result['results']:
                print(f"  {match['name']}: MW {match['molecular_weight']}")
        print()

        # Test get all monomers
        print("Getting all monomers:")
        result = resource.get_all_monomers()
        if result['success']:
            print(f"Total monomers: {result['total_monomers']}")
            for monomer in result['results']:
                print(f"  {monomer['name']}: {monomer['type']} (MW: {monomer['molecular_weight']})")
