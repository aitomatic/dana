"""
VietnameseDataNormalizationResource - Handle Vietnamese language data.

Domain-agnostic resource for normalizing Vietnamese text, names, and addresses.
Useful for any project working with Vietnamese data requiring deduplication
and standardization.
"""

import re
import unicodedata

from dana.common.protocols.types import DictParams
from dana.common.protocols.war import tool_use
from dana.core.resource.base_resource import BaseResource


class VietnameseDataNormalizationResource(BaseResource):
    """
    <PUBLIC_DESCRIPTION>
    Normalizes Vietnamese language data for consistent processing.

    Handles:
    - Vietnamese diacritics (á, à, ả, ã, ạ, etc.)
    - Company name normalization (abbreviations, legal forms)
    - Address parsing and hierarchy (Province → District → Commune)
    - Name deduplication and fuzzy matching

    Essential for Vietnamese data projects requiring accurate
    entity resolution and deduplication.
    </PUBLIC_DESCRIPTION>
    """

    # Common Vietnamese company abbreviations
    COMPANY_ABBREVIATIONS = {
        "TNHH": "Trách nhiệm hữu hạn",  # Limited liability
        "CP": "Cổ phần",  # Joint stock
        "CT": "Công ty",  # Company
        "CTY": "Công ty",
        "DN": "Doanh nghiệp",  # Enterprise
        "HTX": "Hợp tác xã",  # Cooperative
    }

    # Vietnamese provinces (for validation)
    PROVINCES = {
        "Đắk Lắk",
        "Dak Lak",
        "Gia Lai",
        "Lâm Đồng",
        "Lam Dong",
        "Đắk Nông",
        "Dak Nong",
        "Sơn La",
        "Son La",
        "Hà Nội",
        "Ha Noi",
        "Hanoi",
        "Quảng Trị",
        "Quang Tri",
    }

    def __init__(self, resource_id: str | None = None, **kwargs):
        """Initialize the VietnameseDataNormalizationResource."""
        super().__init__(resource_type="vietnamese-normalization", resource_id=resource_id or "vietnamese-normalization", **kwargs)

    @tool_use
    def normalize_company_name(self, name: str, expand_abbreviations: bool = False, **kwargs) -> DictParams:
        """
        Normalize Vietnamese company names for deduplication.

        Args:
            name: Company name to normalize
            expand_abbreviations: Whether to expand abbreviations (TNHH → full form)

        Returns:
            Normalized name and metadata
        """
        if not name:
            return {"success": False, "error": "Empty company name", "normalized_name": None}

        try:
            # Step 1: Unicode normalization
            normalized = self._normalize_unicode(name)

            # Step 2: Remove extra whitespace
            normalized = re.sub(r"\s+", " ", normalized).strip()

            # Step 3: Standardize case (title case for Vietnamese names)
            normalized = normalized.title()

            # Step 4: Handle abbreviations
            if expand_abbreviations:
                for abbrev, full_form in self.COMPANY_ABBREVIATIONS.items():
                    pattern = r"\b" + re.escape(abbrev) + r"\b"
                    normalized = re.sub(pattern, full_form, normalized, flags=re.IGNORECASE)

            # Step 5: Remove common prefixes for deduplication (store original)
            dedup_name = self._remove_legal_forms(normalized)

            return {
                "success": True,
                "original_name": name,
                "normalized_name": normalized,
                "deduplication_key": dedup_name.lower(),
                "abbreviations_found": self._find_abbreviations(name),
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "normalized_name": name,  # Return original on error
            }

    @tool_use
    def parse_address(self, address: str, **kwargs) -> DictParams:
        """
        Parse Vietnamese addresses into hierarchical components.

        Args:
            address: Full address string

        Returns:
            Parsed components: {street, district, province, confidence}
        """
        if not address:
            return {"success": False, "error": "Empty address", "components": None}

        try:
            # Normalize unicode first
            normalized = self._normalize_unicode(address)

            # Extract components
            province = self._extract_province(normalized)
            district = self._extract_district(normalized)
            commune = self._extract_commune(normalized)
            street = self._extract_street(normalized, district, commune, province)

            # Calculate confidence based on what we found
            confidence = 0.0
            if province:
                confidence += 0.4
            if district:
                confidence += 0.3
            if street:
                confidence += 0.3

            return {
                "success": True,
                "original_address": address,
                "components": {"street": street, "commune": commune, "district": district, "province": province},
                "confidence": confidence,
            }

        except Exception as e:
            return {"success": False, "error": str(e), "components": None}

    @tool_use
    def fuzzy_match(self, name1: str, name2: str, threshold: float = 0.85, **kwargs) -> DictParams:
        """
        Fuzzy match two Vietnamese company names.

        Args:
            name1: First company name
            name2: Second company name
            threshold: Similarity threshold (0.0-1.0)

        Returns:
            Match result with similarity score
        """
        try:
            # Normalize both names
            norm1_result = self.normalize_company_name(name1)
            norm2_result = self.normalize_company_name(name2)

            if not norm1_result["success"] or not norm2_result["success"]:
                return {"success": False, "error": "Failed to normalize names", "is_match": False}

            # Use deduplication keys for comparison
            key1 = norm1_result["deduplication_key"]
            key2 = norm2_result["deduplication_key"]

            # Calculate similarity using Levenshtein-like approach
            similarity = self._calculate_similarity(key1, key2)

            is_match = similarity >= threshold

            return {"success": True, "name1": name1, "name2": name2, "similarity": similarity, "is_match": is_match, "threshold": threshold}

        except Exception as e:
            return {"success": False, "error": str(e), "is_match": False}

    # ============================================================================
    # HELPER METHODS
    # ============================================================================

    def _normalize_unicode(self, text: str) -> str:
        """Normalize Vietnamese Unicode (NFC normalization)"""
        return unicodedata.normalize("NFC", text)

    def _remove_legal_forms(self, name: str) -> str:
        """Remove legal form prefixes for deduplication"""
        # Remove common prefixes
        patterns = [
            r"^Công ty TNHH\s+",
            r"^Công ty Cổ phần\s+",
            r"^Công ty\s+",
            r"^Hợp tác xã\s+",
            r"^Doanh nghiệp\s+",
            r"^TNHH\s+",
            r"^CP\s+",
            r"^CT\s+",
            r"^HTX\s+",
        ]

        result = name
        for pattern in patterns:
            result = re.sub(pattern, "", result, flags=re.IGNORECASE)

        return result.strip()

    def _find_abbreviations(self, text: str) -> list[str]:
        """Find company abbreviations in text"""
        found = []
        for abbrev in self.COMPANY_ABBREVIATIONS.keys():
            if re.search(r"\b" + re.escape(abbrev) + r"\b", text, re.IGNORECASE):
                found.append(abbrev)
        return found

    def _extract_province(self, address: str) -> str | None:
        """Extract province from address"""
        # Look for province keywords
        for province in self.PROVINCES:
            # Try various patterns
            patterns = [
                f"tỉnh {province}",
                f"Tỉnh {province}",
                f"{province}",
                f"tp\. {province}",  # Thành phố (city)
            ]

            for pattern in patterns:
                if pattern.lower() in address.lower():
                    return province

        return None

    def _extract_district(self, address: str) -> str | None:
        """Extract district from address"""
        # Look for district keywords: "Quận", "Huyện"
        district_patterns = [
            r"(Quận|quận)\s+([A-Za-zÀ-ỹ0-9\s]+?)(?=,|\.|$|tỉnh|Tỉnh|thành phố)",
            r"(Huyện|huyện)\s+([A-Za-zÀ-ỹ\s]+?)(?=,|\.|$|tỉnh|Tỉnh)",
        ]

        for pattern in district_patterns:
            match = re.search(pattern, address)
            if match:
                return match.group(0).strip()

        return None

    def _extract_commune(self, address: str) -> str | None:
        """Extract commune/ward from address"""
        # Look for commune keywords: "Phường", "Xã", "Thị trấn"
        commune_patterns = [
            r"(Phường|phường)\s+([A-Za-zÀ-ỹ0-9\s]+?)(?=,|\.|$|quận|huyện)",
            r"(Xã|xã)\s+([A-Za-zÀ-ỹ\s]+?)(?=,|\.|$|huyện)",
            r"(Thị trấn|thị trấn)\s+([A-Za-zÀ-ỹ\s]+?)(?=,|\.|$)",
        ]

        for pattern in commune_patterns:
            match = re.search(pattern, address)
            if match:
                return match.group(0).strip()

        return None

    def _extract_street(self, address: str, district: str | None, commune: str | None, province: str | None) -> str | None:
        """Extract street address by removing district/commune/province"""
        street = address

        # Remove province, district, commune from address
        if province:
            street = re.sub(re.escape(province), "", street, flags=re.IGNORECASE)
            street = re.sub(r"tỉnh\s*", "", street, flags=re.IGNORECASE)
            street = re.sub(r"tp\.\s*", "", street, flags=re.IGNORECASE)

        if district:
            street = re.sub(re.escape(district), "", street, flags=re.IGNORECASE)

        if commune:
            street = re.sub(re.escape(commune), "", street, flags=re.IGNORECASE)

        # Clean up
        street = re.sub(r"\s*,\s*", ", ", street)
        street = re.sub(r",+", ",", street)
        street = street.strip(" ,.")

        return street if street else None

    def _calculate_similarity(self, s1: str, s2: str) -> float:
        """Calculate similarity between two strings (simple Levenshtein ratio)"""
        if s1 == s2:
            return 1.0

        if not s1 or not s2:
            return 0.0

        # Simple character-level similarity
        len1, len2 = len(s1), len(s2)
        max_len = max(len1, len2)

        if max_len == 0:
            return 1.0

        # Count matching characters in order
        matches = 0
        for i in range(min(len1, len2)):
            if s1[i] == s2[i]:
                matches += 1

        # Also count common substrings
        common = set(s1.split()) & set(s2.split())
        common_chars = sum(len(word) for word in common)

        # Weighted score
        position_score = matches / max_len
        content_score = (common_chars * 2) / (len1 + len2) if (len1 + len2) > 0 else 0

        return (position_score + content_score) / 2
