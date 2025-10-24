"""
Polymer Data Resource for Photoresist Chemist.

Provides access to polymer composition data from Excel files.
Handles structured data queries for polymer structures and monomer breakdowns.
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Dict, List, Any

from dana.common.protocols.types import DictParams
from dana.common.protocols.war import tool_use
from dana.core.resource.base_resource import BaseResource


class PolymerDataResource(BaseResource):
    """
    Resource for accessing and querying polymer composition data.

    Features:
    - Load and query polymer Excel data
    - Search by lot number, composition, customer
    - Extract monomer breakdowns and ratios
    - Analyze polymer structures and properties
    """

    def __init__(self, resource_id: str | None = None, data_path: str | None = None, **kwargs):
        """
        Initialize the PolymerDataResource.

        Args:
            resource_id: Unique identifier for this resource
            data_path: Path to polymer Excel file
            **kwargs: Additional arguments passed to BaseResource
        """
        super().__init__(resource_type="polymer-data", resource_id=resource_id or "polymer-data", **kwargs)

        # Set default data path if not provided
        if data_path is None:
            current_dir = Path(__file__).parent
            data_path = current_dir / "Polymer_example_data.xlsx"

        self.data_path = Path(data_path)
        self._data = None
        self._load_data()

    def _load_data(self) -> None:
        """Load polymer data from Excel file."""
        try:
            if self.data_path.exists():
                self._data = pd.read_excel(self.data_path)
                print(f"Loaded polymer data: {len(self._data)} polymers, {len(self._data.columns)} columns")
            else:
                print(f"Warning: Polymer data file not found at {self.data_path}")
                self._data = pd.DataFrame()
        except Exception as e:
            print(f"Error loading polymer data: {e}")
            self._data = pd.DataFrame()

    @tool_use
    def search_by_lot_number(self, lot_number: str, **kwargs) -> DictParams:
        """
        Search for polymer data by lot number.

        Args:
            lot_number: Lot number to search for (e.g., "BS-1000")
            **kwargs: Additional parameters

        Returns:
            Dictionary with search results
        """
        try:
            if self._data is None or self._data.empty:
                return {
                    "success": False,
                    "results": [],
                    "error": "No polymer data available"
                }

            # Search for lot number
            matches = self._data[
                self._data['LotNo'].str.contains(lot_number, case=False, na=False)
            ]

            results = []
            for _, row in matches.iterrows():
                # Extract monomer information
                monomers = []
                ratios = []
                for i in range(1, 6):  # Monomer1 through Monomer5
                    monomer_name = row.get(f'Monomer{i}', '')
                    ratio = row.get(f'Ratio{i}', '')
                    if pd.notna(monomer_name) and monomer_name:
                        monomers.append(monomer_name)
                        ratios.append(ratio if pd.notna(ratio) else 0)

                result = {
                    "lot_number": row.get('LotNo', ''),
                    "composition": row.get('Composition', ''),
                    "customer": row.get('Customer', ''),
                    "theme": row.get('Theme', ''),
                    "pattern": row.get('Pattern', ''),
                    "note": row.get('Note', ''),
                    "pc_treat": row.get('PC_Treat', ''),
                    "monomers": monomers,
                    "ratios": ratios,
                    "monomer_count": len(monomers),
                    "total_ratio": sum(ratios) if ratios else 0
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
                "error": f"Lot number search failed: {str(e)}"
            }

    @tool_use
    def search_by_composition(self, composition: str, **kwargs) -> DictParams:
        """
        Search for polymer data by composition.

        Args:
            composition: Composition string to search for (e.g., "PS/Tcp/Fdp")
            **kwargs: Additional parameters

        Returns:
            Dictionary with search results
        """
        try:
            if self._data is None or self._data.empty:
                return {
                    "success": False,
                    "results": [],
                    "error": "No polymer data available"
                }

            # Search for composition
            matches = self._data[
                self._data['Composition'].str.contains(composition, case=False, na=False)
            ]

            results = []
            for _, row in matches.iterrows():
                # Extract monomer information
                monomers = []
                ratios = []
                for i in range(1, 6):  # Monomer1 through Monomer5
                    monomer_name = row.get(f'Monomer{i}', '')
                    ratio = row.get(f'Ratio{i}', '')
                    if pd.notna(monomer_name) and monomer_name:
                        monomers.append(monomer_name)
                        ratios.append(ratio if pd.notna(ratio) else 0)

                result = {
                    "lot_number": row.get('LotNo', ''),
                    "composition": row.get('Composition', ''),
                    "customer": row.get('Customer', ''),
                    "theme": row.get('Theme', ''),
                    "pattern": row.get('Pattern', ''),
                    "note": row.get('Note', ''),
                    "pc_treat": row.get('PC_Treat', ''),
                    "monomers": monomers,
                    "ratios": ratios,
                    "monomer_count": len(monomers),
                    "total_ratio": sum(ratios) if ratios else 0
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
                "error": f"Composition search failed: {str(e)}"
            }

    @tool_use
    def search_by_monomer(self, monomer_name: str, **kwargs) -> DictParams:
        """
        Search for polymers containing specific monomers.

        Args:
            monomer_name: Name of monomer to search for (e.g., "PS", "Tcp")
            **kwargs: Additional parameters

        Returns:
            Dictionary with search results
        """
        try:
            if self._data is None or self._data.empty:
                return {
                    "success": False,
                    "results": [],
                    "error": "No polymer data available"
                }

            # Search in all monomer columns
            monomer_columns = [f'Monomer{i}' for i in range(1, 6)]
            matches = pd.DataFrame()

            for col in monomer_columns:
                if col in self._data.columns:
                    col_matches = self._data[
                        self._data[col].str.contains(monomer_name, case=False, na=False)
                    ]
                    matches = pd.concat([matches, col_matches], ignore_index=True)

            # Remove duplicates
            matches = matches.drop_duplicates()

            results = []
            for _, row in matches.iterrows():
                # Extract monomer information
                monomers = []
                ratios = []
                for i in range(1, 6):  # Monomer1 through Monomer5
                    monomer = row.get(f'Monomer{i}', '')
                    ratio = row.get(f'Ratio{i}', '')
                    if pd.notna(monomer) and monomer:
                        monomers.append(monomer)
                        ratios.append(ratio if pd.notna(ratio) else 0)

                result = {
                    "lot_number": row.get('LotNo', ''),
                    "composition": row.get('Composition', ''),
                    "customer": row.get('Customer', ''),
                    "theme": row.get('Theme', ''),
                    "pattern": row.get('Pattern', ''),
                    "note": row.get('Note', ''),
                    "pc_treat": row.get('PC_Treat', ''),
                    "monomers": monomers,
                    "ratios": ratios,
                    "monomer_count": len(monomers),
                    "total_ratio": sum(ratios) if ratios else 0,
                    "found_monomer": monomer_name
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
                "error": f"Monomer search failed: {str(e)}"
            }

    @tool_use
    def get_all_polymers(self, **kwargs) -> DictParams:
        """
        Get all available polymers with basic information.

        Returns:
            Dictionary with all polymers
        """
        try:
            if self._data is None or self._data.empty:
                return {
                    "success": False,
                    "results": [],
                    "error": "No polymer data available"
                }

            results = []
            for _, row in self._data.iterrows():
                # Extract monomer information
                monomers = []
                ratios = []
                for i in range(1, 6):  # Monomer1 through Monomer5
                    monomer = row.get(f'Monomer{i}', '')
                    ratio = row.get(f'Ratio{i}', '')
                    if pd.notna(monomer) and monomer:
                        monomers.append(monomer)
                        ratios.append(ratio if pd.notna(ratio) else 0)

                result = {
                    "lot_number": row.get('LotNo', ''),
                    "composition": row.get('Composition', ''),
                    "customer": row.get('Customer', ''),
                    "theme": row.get('Theme', ''),
                    "pattern": row.get('Pattern', ''),
                    "note": row.get('Note', ''),
                    "pc_treat": row.get('PC_Treat', ''),
                    "monomers": monomers,
                    "ratios": ratios,
                    "monomer_count": len(monomers),
                    "total_ratio": sum(ratios) if ratios else 0
                }
                results.append(result)

            return {
                "success": True,
                "results": results,
                "total_polymers": len(results),
                "error": None
            }

        except Exception as e:
            return {
                "success": False,
                "results": [],
                "error": f"Failed to get polymers: {str(e)}"
            }

    @property
    def is_available(self) -> bool:
        """Check if polymer data is available."""
        return self._data is not None and not self._data.empty


if __name__ == "__main__":
    """
    Demo usage of PolymerDataResource.
    """
    print("=" * 80)
    print("PolymerDataResource Demo")
    print("=" * 80)
    print()

    # Initialize resource
    resource = PolymerDataResource()
    print(f"Data available: {resource.is_available}")
    print()

    if resource.is_available:
        # Test search by lot number
        print("Searching for lot 'BS-1000':")
        result = resource.search_by_lot_number("BS-1000")
        if result['success']:
            print(f"Found {result['total_matches']} matches")
            for match in result['results']:
                print(f"  Lot: {match['lot_number']}")
                print(f"  Composition: {match['composition']}")
                print(f"  Monomers: {match['monomers']} (ratios: {match['ratios']})")
        print()

        # Test search by composition
        print("Searching for composition 'PS/Tcp':")
        result = resource.search_by_composition("PS/Tcp")
        if result['success']:
            print(f"Found {result['total_matches']} matches")
            for match in result['results']:
                print(f"  Lot: {match['lot_number']} - {match['composition']}")
        print()

        # Test search by monomer
        print("Searching for monomer 'Tcp':")
        result = resource.search_by_monomer("Tcp")
        if result['success']:
            print(f"Found {result['total_matches']} matches")
            for match in result['results']:
                print(f"  Lot: {match['lot_number']} - {match['composition']}")
                print(f"  Monomers: {match['monomers']}")
        print()

        # Test get all polymers
        print("Getting all polymers:")
        result = resource.get_all_polymers()
        if result['success']:
            print(f"Total polymers: {result['total_polymers']}")
            for polymer in result['results']:
                print(f"  {polymer['lot_number']}: {polymer['composition']} ({polymer['monomer_count']} monomers)")
