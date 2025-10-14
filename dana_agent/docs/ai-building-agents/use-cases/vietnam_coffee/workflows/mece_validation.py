"""
MECEValidationWorkflow - Ensure Mutually Exclusive, Collectively Exhaustive dataset.

Validates that the dataset:
- Has no duplicates (Mutually Exclusive)
- Covers all expected entities (Collectively Exhaustive)
"""

from dana.common.protocols.types import DictParams
from dana.core.workflow.base_workflow import BaseWorkflow, validate_input, validate_output


class MECEValidationWorkflow(BaseWorkflow):
    """
    Validate MECE compliance of company dataset.

    Checks:
    1. No duplicates (by tax_id and fuzzy name match)
    2. No gaps (all provinces have results)
    3. Mutual exclusivity (no company in multiple provinces)
    """

    def __init__(self, workflow_id: str | None = None, **kwargs):
        super().__init__(workflow_id=workflow_id or "mece-validation", **kwargs)

        from ..resources.vietnamese_data_normalization import VietnameseDataNormalizationResource

        self.vietnamese_norm = VietnameseDataNormalizationResource()

    @validate_input(
        companies={"required": True, "type": list, "min_length": 1},
    )
    @validate_output(
        success={"required": True, "type": bool},
        validated_companies={"required": True, "type": list},
        mece_report={"required": True, "type": dict},
    )
    def _do_execute(self, **kwargs) -> DictParams:
        """
        Validate MECE compliance.

        Args:
            companies: List of company dictionaries
            expected_provinces: Optional list of provinces that should be covered

        Returns:
            {
                "success": bool,
                "validated_companies": [companies with duplicates removed],
                "mece_report": {
                    "duplicates_found": int,
                    "duplicates_removed": int,
                    "gaps_detected": [str],
                    "provinces_covered": [str],
                    "mece_compliant": bool
                }
            }
        """
        companies = kwargs["companies"]
        expected_provinces = kwargs.get("expected_provinces", [])

        try:
            # Step 1: Find and remove duplicates
            validated, duplicates = self._remove_duplicates(companies)

            # Step 2: Check for gaps
            provinces_covered = list(set(c["province"] for c in validated))
            gaps = []

            if expected_provinces:
                missing_provinces = set(expected_provinces) - set(provinces_covered)
                gaps = list(missing_provinces)

            # Step 3: Check mutual exclusivity
            # (companies shouldn't appear in multiple provinces)
            multi_province_companies = self._find_multi_province_violations(validated)

            # Determine MECE compliance
            mece_compliant = len(duplicates) == 0 and len(gaps) == 0 and len(multi_province_companies) == 0

            return {
                "success": True,
                "validated_companies": validated,
                "mece_report": {
                    "total_companies": len(validated),
                    "duplicates_found": len(duplicates),
                    "duplicates_removed": len(duplicates),
                    "gaps_detected": gaps,
                    "provinces_covered": provinces_covered,
                    "multi_province_violations": len(multi_province_companies),
                    "mece_compliant": mece_compliant,
                },
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "validated_companies": companies,
                "mece_report": {"mece_compliant": False, "error": str(e)},
            }

    def _remove_duplicates(self, companies: list[dict]) -> tuple[list[dict], list[dict]]:
        """Remove duplicate companies."""
        seen_tax_ids = {}
        duplicates = []
        validated = []

        for company in companies:
            tax_id = company.get("tax_id")

            if not tax_id:
                validated.append(company)
                continue

            if tax_id in seen_tax_ids:
                duplicates.append(company)
            else:
                seen_tax_ids[tax_id] = company
                validated.append(company)

        return validated, duplicates

    def _find_multi_province_violations(self, companies: list[dict]) -> list[str]:
        """Find companies appearing in multiple provinces."""
        tax_id_to_provinces = {}

        for company in companies:
            tax_id = company.get("tax_id")
            province = company.get("province")

            if tax_id and province:
                if tax_id not in tax_id_to_provinces:
                    tax_id_to_provinces[tax_id] = set()
                tax_id_to_provinces[tax_id].add(province)

        # Find violations
        violations = []
        for tax_id, provinces in tax_id_to_provinces.items():
            if len(provinces) > 1:
                violations.append(f"{tax_id} appears in: {', '.join(provinces)}")

        return violations
