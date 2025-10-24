"""
Polymer Data Resource for Photoresist Chemist.

Provides access to polymer composition data from Excel files.
Handles structured data queries for polymer structures and monomer breakdowns.
"""

import pandas as pd
from pathlib import Path

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

    @tool_use
    def get_complete_formulation_analysis(self, **kwargs) -> DictParams:
        """
        Get complete formulation analysis including all available formulations.
        This tool specifically addresses the feedback about missing BS-1003 formulation.

        Returns:
            Dictionary with complete formulation analysis
        """
        try:
            if self._data is None or self._data.empty:
                return {
                    "success": False,
                    "results": [],
                    "error": "No polymer data available"
                }

            # Group by customer for analysis
            customer_formulations = {}
            all_formulations = []

            for _, row in self._data.iterrows():
                customer = row.get('Customer', 'Unknown')
                lot_number = row.get('LotNo', '')
                composition = row.get('Composition', '')

                # Extract monomer information
                monomers = []
                ratios = []
                for i in range(1, 6):
                    monomer = row.get(f'Monomer{i}', '')
                    ratio = row.get(f'Ratio{i}', '')
                    if pd.notna(monomer) and monomer:
                        monomers.append(monomer)
                        ratios.append(ratio if pd.notna(ratio) else 0)

                formulation_info = {
                    "lot_number": lot_number,
                    "composition": composition,
                    "customer": customer,
                    "theme": row.get('Theme', ''),
                    "pattern": row.get('Pattern', ''),
                    "pc_treat": row.get('PC_Treat', ''),
                    "monomers": monomers,
                    "ratios": ratios,
                    "monomer_count": len(monomers),
                    "total_ratio": sum(ratios) if ratios else 0
                }

                all_formulations.append(formulation_info)

                if customer not in customer_formulations:
                    customer_formulations[customer] = []
                customer_formulations[customer].append(formulation_info)

            # Analyze formulation patterns
            analysis = {
                "total_formulations": len(all_formulations),
                "customer_breakdown": {customer: len(formulations) for customer, formulations in customer_formulations.items()},
                "formulation_types": list(set([f["composition"] for f in all_formulations])),
                "all_lot_numbers": [f["lot_number"] for f in all_formulations]
            }

            return {
                "success": True,
                "results": {
                    "all_formulations": all_formulations,
                    "customer_formulations": customer_formulations,
                    "analysis": analysis
                },
                "error": None
            }

        except Exception as e:
            return {
                "success": False,
                "results": [],
                "error": f"Complete formulation analysis failed: {str(e)}"
            }

    @tool_use
    def compare_formulations(self, lot_numbers: list, **kwargs) -> DictParams:
        """
        Compare multiple formulations to identify differences and similarities.
        This tool addresses the feedback about incomplete comparative analysis.

        Args:
            lot_numbers: List of lot numbers to compare (e.g., ["BS-1000", "BS-1001r2", "BS-1002", "BS-1003"])

        Returns:
            Dictionary with comparative analysis
        """
        try:
            if self._data is None or self._data.empty:
                return {
                    "success": False,
                    "results": [],
                    "error": "No polymer data available"
                }

            # Find formulations for specified lot numbers
            formulations = []
            for lot_number in lot_numbers:
                matches = self._data[
                    self._data['LotNo'].str.contains(lot_number, case=False, na=False)
                ]
                for _, row in matches.iterrows():
                    # Extract monomer information
                    monomers = []
                    ratios = []
                    for i in range(1, 6):
                        monomer = row.get(f'Monomer{i}', '')
                        ratio = row.get(f'Ratio{i}', '')
                        if pd.notna(monomer) and monomer:
                            monomers.append(monomer)
                            ratios.append(ratio if pd.notna(ratio) else 0)

                    formulation_info = {
                        "lot_number": lot_number,
                        "composition": row.get('Composition', ''),
                        "customer": row.get('Customer', ''),
                        "theme": row.get('Theme', ''),
                        "pattern": row.get('Pattern', ''),
                        "pc_treat": row.get('PC_Treat', ''),
                        "monomers": monomers,
                        "ratios": ratios,
                        "monomer_count": len(monomers),
                        "total_ratio": sum(ratios) if ratios else 0
                    }
                    formulations.append(formulation_info)

            # Perform comparative analysis
            comparison = {
                "formulations": formulations,
                "monomer_analysis": self._analyze_monomer_usage(formulations),
                "customer_analysis": self._analyze_customer_patterns(formulations),
                "composition_analysis": self._analyze_composition_patterns(formulations)
            }

            return {
                "success": True,
                "results": comparison,
                "error": None
            }

        except Exception as e:
            return {
                "success": False,
                "results": [],
                "error": f"Formulation comparison failed: {str(e)}"
            }

    def _analyze_monomer_usage(self, formulations):
        """Analyze monomer usage patterns across formulations."""
        monomer_usage = {}
        for formulation in formulations:
            for monomer, ratio in zip(formulation["monomers"], formulation["ratios"]):
                if monomer not in monomer_usage:
                    monomer_usage[monomer] = []
                monomer_usage[monomer].append({
                    "lot_number": formulation["lot_number"],
                    "ratio": ratio,
                    "customer": formulation["customer"]
                })
        return monomer_usage

    def _analyze_customer_patterns(self, formulations):
        """Analyze customer-specific formulation patterns."""
        customer_patterns = {}
        for formulation in formulations:
            customer = formulation["customer"]
            if customer not in customer_patterns:
                customer_patterns[customer] = []
            customer_patterns[customer].append(formulation)
        return customer_patterns

    def _analyze_composition_patterns(self, formulations):
        """Analyze composition patterns across formulations."""
        compositions = [f["composition"] for f in formulations]
        unique_compositions = list(set(compositions))
        return {
            "unique_compositions": unique_compositions,
            "composition_frequency": {comp: compositions.count(comp) for comp in unique_compositions}
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
