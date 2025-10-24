"""
Recipe Data Resource for Photoresist Chemist.

Provides access to recipe/formulation data from CSV files.
Handles structured data queries for photoresist formulations.
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Dict, List, Any

from dana.common.protocols.types import DictParams
from dana.common.protocols.war import tool_use
from dana.core.resource.base_resource import BaseResource


class RecipeDataResource(BaseResource):
    """
    Resource for accessing and querying photoresist recipe data.

    Features:
    - Load and query recipe CSV data
    - Search by sample name, resin components, photosensitizers
    - Extract formulation details and concentrations
    - Filter by customer, theme, or preparation purpose
    """

    def __init__(self, resource_id: str | None = None, data_path: str | None = None, **kwargs):
        """
        Initialize the RecipeDataResource.

        Args:
            resource_id: Unique identifier for this resource
            data_path: Path to recipe CSV file
            **kwargs: Additional arguments passed to BaseResource
        """
        super().__init__(resource_type="recipe-data", resource_id=resource_id or "recipe-data", **kwargs)

        # Set default data path if not provided
        if data_path is None:
            current_dir = Path(__file__).parent
            data_path = current_dir / "Recipe_example_data.csv"

        self.data_path = Path(data_path)
        self._data = None
        self._load_data()

    def _load_data(self) -> None:
        """Load recipe data from CSV file."""
        try:
            if self.data_path.exists():
                self._data = pd.read_csv(self.data_path)
                print(f"Loaded recipe data: {len(self._data)} samples, {len(self._data.columns)} columns")
            else:
                print(f"Warning: Recipe data file not found at {self.data_path}")
                self._data = pd.DataFrame()
        except Exception as e:
            print(f"Error loading recipe data: {e}")
            self._data = pd.DataFrame()

    @tool_use
    def search_by_sample_name(self, sample_name: str, **kwargs) -> DictParams:
        """
        Search for recipe data by sample name.

        Args:
            sample_name: Sample name to search for (e.g., "AB01", "TEF0001")
            **kwargs: Additional parameters

        Returns:
            Dictionary with search results
        """
        try:
            if self._data is None or self._data.empty:
                return {
                    "success": False,
                    "results": [],
                    "error": "No recipe data available"
                }

            # Search in both Sample Name and Submitted Sample Name columns
            sample_matches = self._data[
                (self._data['Sample Name'].str.contains(sample_name, case=False, na=False)) |
                (self._data['Submitted Sample Name'].str.contains(sample_name, case=False, na=False))
            ]

            results = []
            for _, row in sample_matches.iterrows():
                # Extract key information
                result = {
                    "sample_name": row.get('Sample Name', ''),
                    "submitted_name": row.get('Submitted Sample Name', ''),
                    "creation_date": row.get('Creation Date', ''),
                    "creator": row.get('Creator', ''),
                    "preparation_purpose": row.get('Preparation Purpose', ''),
                    "theme": row.get('Theme', ''),
                    "lot_number": row.get('Lot Number', ''),
                    "basic_composition": row.get('Basic Composition', ''),
                    "target_film_thickness": row.get('Target Film Thickness', ''),
                    "features": row.get('Features', ''),
                    "preparation_amount": row.get('Preparation Amount', ''),
                    "tsc": row.get('TSC', ''),
                }

                # Extract resin information
                resins = []
                for i in range(1, 6):  # Resin1 through Resin5
                    resin_name = row.get(f'Resin{i} Name', '')
                    resin_phr = row.get(f'Resin{i} PHR', '')
                    if pd.notna(resin_name) and resin_name:
                        resins.append({
                            "name": resin_name,
                            "phr": resin_phr,
                            "purity": row.get(f'Resin{i} Purity', ''),
                            "charge": row.get(f'Resin{i} Charge', '')
                        })
                result["resins"] = resins

                # Extract photosensitizer information
                photosensitizers = []
                for i in range(1, 4):  # Photosensitizer1 through Photosensitizer3
                    ps_name = row.get(f'Photosensitizer{i} Name', '')
                    ps_phr = row.get(f'Photosensitizer{i} PHR', '')
                    if pd.notna(ps_name) and ps_name:
                        photosensitizers.append({
                            "name": ps_name,
                            "phr": ps_phr,
                            "mw": row.get(f'Photosensitizer{i} MW', ''),
                            "purity": row.get(f'Photosensitizer{i} Purity', ''),
                            "charge": row.get(f'Photosensitizer{i} Charge', '')
                        })
                result["photosensitizers"] = photosensitizers

                # Extract amine information
                amines = []
                for i in range(1, 4):  # Amine1 through Amine3
                    amine_name = row.get(f'Amine{i} Name', '')
                    amine_phr = row.get(f'Amine{i} PHR', '')
                    if pd.notna(amine_name) and amine_name:
                        amines.append({
                            "name": amine_name,
                            "phr": amine_phr,
                            "mw": row.get(f'Amine{i} MW', ''),
                            "purity": row.get(f'Amine{i} Purity', ''),
                            "charge": row.get(f'Amine{i} Charge', '')
                        })
                result["amines"] = amines

                # Extract additive information
                additives = []
                for i in range(1, 4):  # Additive1 through Additive3
                    additive_name = row.get(f'Additive{i} Name', '')
                    additive_phr = row.get(f'Additive{i} PHR', '')
                    if pd.notna(additive_name) and additive_name:
                        additives.append({
                            "name": additive_name,
                            "phr": additive_phr,
                            "purity": row.get(f'Additive{i} Purity', ''),
                            "charge": row.get(f'Additive{i} Charge', '')
                        })
                result["additives"] = additives

                # Extract solvent information
                solvents = []
                for i in range(1, 5):  # Solvent1 through Solvent4
                    solvent_name = row.get(f'Solvent{i} Name', '')
                    solvent_ratio = row.get(f'Solvent{i} Ratio', '')
                    if pd.notna(solvent_name) and solvent_name:
                        solvents.append({
                            "name": solvent_name,
                            "ratio": solvent_ratio,
                            "charge": row.get(f'Solvent{i} Charge', '')
                        })
                result["solvents"] = solvents

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
                "error": f"Search failed: {str(e)}"
            }

    @tool_use
    def search_by_component(self, component_name: str, component_type: str = "any", **kwargs) -> DictParams:
        """
        Search for recipes containing specific components.

        Args:
            component_name: Name of component to search for
            component_type: Type of component ("resin", "photosensitizer", "amine", "additive", "solvent", "any")
            **kwargs: Additional parameters

        Returns:
            Dictionary with search results
        """
        try:
            if self._data is None or self._data.empty:
                return {
                    "success": False,
                    "results": [],
                    "error": "No recipe data available"
                }

            # Determine which columns to search based on component type
            search_columns = []
            if component_type == "any" or component_type == "resin":
                search_columns.extend([f'Resin{i} Name' for i in range(1, 6)])
            if component_type == "any" or component_type == "photosensitizer":
                search_columns.extend([f'Photosensitizer{i} Name' for i in range(1, 4)])
            if component_type == "any" or component_type == "amine":
                search_columns.extend([f'Amine{i} Name' for i in range(1, 4)])
            if component_type == "any" or component_type == "additive":
                search_columns.extend([f'Additive{i} Name' for i in range(1, 4)])
            if component_type == "any" or component_type == "solvent":
                search_columns.extend([f'Solvent{i} Name' for i in range(1, 5)])

            # Search for component in specified columns
            matches = pd.DataFrame()
            for col in search_columns:
                if col in self._data.columns:
                    col_matches = self._data[
                        self._data[col].str.contains(component_name, case=False, na=False)
                    ]
                    matches = pd.concat([matches, col_matches], ignore_index=True)

            # Remove duplicates
            matches = matches.drop_duplicates()

            results = []
            for _, row in matches.iterrows():
                result = {
                    "sample_name": row.get('Sample Name', ''),
                    "submitted_name": row.get('Submitted Sample Name', ''),
                    "creation_date": row.get('Creation Date', ''),
                    "theme": row.get('Theme', ''),
                    "found_component": component_name,
                    "found_in_type": component_type
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
                "error": f"Component search failed: {str(e)}"
            }

    @tool_use
    def get_all_samples(self, **kwargs) -> DictParams:
        """
        Get all available samples with basic information.

        Returns:
            Dictionary with all samples
        """
        try:
            if self._data is None or self._data.empty:
                return {
                    "success": False,
                    "results": [],
                    "error": "No recipe data available"
                }

            results = []
            for _, row in self._data.iterrows():
                result = {
                    "sample_name": row.get('Sample Name', ''),
                    "submitted_name": row.get('Submitted Sample Name', ''),
                    "creation_date": row.get('Creation Date', ''),
                    "creator": row.get('Creator', ''),
                    "theme": row.get('Theme', ''),
                    "preparation_purpose": row.get('Preparation Purpose', ''),
                    "basic_composition": row.get('Basic Composition', ''),
                    "target_film_thickness": row.get('Target Film Thickness', ''),
                    "features": row.get('Features', '')
                }
                results.append(result)

            return {
                "success": True,
                "results": results,
                "total_samples": len(results),
                "error": None
            }

        except Exception as e:
            return {
                "success": False,
                "results": [],
                "error": f"Failed to get samples: {str(e)}"
            }

    @property
    def is_available(self) -> bool:
        """Check if recipe data is available."""
        return self._data is not None and not self._data.empty


if __name__ == "__main__":
    """
    Demo usage of RecipeDataResource.
    """
    print("=" * 80)
    print("RecipeDataResource Demo")
    print("=" * 80)
    print()

    # Initialize resource
    resource = RecipeDataResource()
    print(f"Data available: {resource.is_available}")
    print()

    if resource.is_available:
        # Test search by sample name
        print("Searching for sample 'AB01':")
        result = resource.search_by_sample_name("AB01")
        if result['success']:
            print(f"Found {result['total_matches']} matches")
            for match in result['results']:
                print(f"  Sample: {match['sample_name']} ({match['submitted_name']})")
                print(f"  Theme: {match['theme']}")
                print(f"  Resins: {[r['name'] for r in match['resins']]}")
        print()

        # Test search by component
        print("Searching for component 'PS':")
        result = resource.search_by_component("PS", "resin")
        if result['success']:
            print(f"Found {result['total_matches']} matches")
            for match in result['results']:
                print(f"  Sample: {match['sample_name']} - {match['found_component']}")
        print()

        # Test get all samples
        print("Getting all samples:")
        result = resource.get_all_samples()
        if result['success']:
            print(f"Total samples: {result['total_samples']}")
            for sample in result['results'][:3]:  # Show first 3
                print(f"  {sample['sample_name']}: {sample['theme']}")
