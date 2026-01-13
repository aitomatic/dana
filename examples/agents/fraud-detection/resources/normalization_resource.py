"""
NormalizationResource - Converts extracted text to structured JSON data.

This resource handles:
- Text parsing and field extraction
- Data normalization (dates, amounts, names, etc.)
- LLM-powered intelligent field extraction
- Returns structured JSON data
"""

import os
import sys
import re
from datetime import datetime
from typing import Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dana.common.protocols.types import DictParams
from dana.common.protocols.war import tool_use
from dana.core.resource.base_resource import BaseResource


class NormalizationResource(BaseResource):
    """
    Resource for normalizing extracted text into structured JSON data.

    Features:
    - Intelligent field extraction using LLM
    - Data normalization (dates, currency, phone numbers)
    - Pattern recognition for common document types
    - Error handling and validation
    """

    def __init__(self, resource_id: str | None = None, **kwargs):
        """Initialize the NormalizationResource."""
        super().__init__(resource_type="field-normalization", resource_id=resource_id or "field-normalization", **kwargs)

    @tool_use
    def normalize(self, extracted_text: str, **kwargs) -> DictParams:
        """
        Normalize extracted text into structured JSON data.

        Args:
            extracted_text: Raw text extracted from document
            **kwargs: Additional parameters (document_type, etc.)

        Returns:
            {
                "success": bool,
                "normalized_data": dict,
                "error": str (if failed)
            }
        """
        try:
            if not extracted_text or not extracted_text.strip():
                return {"success": False, "normalized_data": {}, "error": "No text provided for normalization"}

            # Use LLM for intelligent field extraction
            normalized_data = self._extract_fields_with_llm(extracted_text)

            # Apply additional normalization rules
            normalized_data = self._apply_normalization_rules(normalized_data)

            return {"success": True, "normalized_data": normalized_data, "error": None}

        except Exception as e:
            return {"success": False, "normalized_data": {}, "error": f"Normalization failed: {str(e)}"}

    def _extract_fields_with_llm(self, text: str) -> dict[str, Any]:
        """Use LLM to intelligently extract fields from text."""
        try:
            # Use the reason() method for LLM-powered extraction
            result = self.reason(
                {
                    "task": "Extract structured fields from document text",
                    "input": {
                        "text": text[:2000],  # Limit text length for LLM
                        "text_length": len(text),
                    },
                    "output_schema": {
                        "document_type": "str (invoice, receipt, contract, statement, other)",
                        "fields": {
                            "invoice_id": "str | null",
                            "date": "str (YYYY-MM-DD format) | null",
                            "amount": "float | null",
                            "currency": "str (USD, EUR, etc.) | null",
                            "vendor_name": "str | null",
                            "customer_name": "str | null",
                            "address": "str | null",
                            "phone": "str | null",
                            "email": "str | null",
                            "description": "str | null",
                            "tax_amount": "float | null",
                            "total_amount": "float | null",
                        },
                        "confidence": "float (0.0-1.0)",
                        "extraction_notes": "str",
                    },
                    "context": {
                        "common_patterns": {
                            "invoice_id": ["Invoice #", "INV-", "Invoice No", "Ref:"],
                            "date": ["Date:", "Invoice Date:", "Due Date:"],
                            "amount": ["Total:", "Amount:", "$", "€", "£"],
                            "vendor": ["From:", "Vendor:", "Company:", "Bill To:"],
                        }
                    },
                }
            )

            return result.get("fields", {})

        except Exception:
            # Fallback to rule-based extraction
            return self._extract_fields_rule_based(text)

    def _extract_fields_rule_based(self, text: str) -> dict[str, Any]:
        """Fallback rule-based field extraction."""
        fields = {}

        # Extract invoice ID
        invoice_patterns = [r"Invoice\s*#?\s*:?\s*([A-Z0-9-]+)", r"INV-([A-Z0-9-]+)", r"Invoice\s+No\.?\s*:?\s*([A-Z0-9-]+)"]
        for pattern in invoice_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                fields["invoice_id"] = match.group(1)
                break

        # Extract date
        date_patterns = [r"Date\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", r"Invoice\s+Date\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"]
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                fields["date"] = self._normalize_date(match.group(1))
                break

        # Extract amount
        amount_patterns = [r"Total\s*:?\s*\$?([0-9,]+\.?\d*)", r"Amount\s*:?\s*\$?([0-9,]+\.?\d*)", r"\$([0-9,]+\.?\d*)"]
        for pattern in amount_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    amount = float(match.group(1).replace(",", ""))
                    fields["amount"] = amount
                    break
                except ValueError:
                    continue

        # Extract vendor name (simple heuristic)
        lines = text.split("\n")
        for line in lines[:10]:  # Check first 10 lines
            if any(keyword in line.lower() for keyword in ["company", "inc", "llc", "corp", "ltd"]):
                fields["vendor_name"] = line.strip()
                break

        return fields

    def _apply_normalization_rules(self, data: dict[str, Any]) -> dict[str, Any]:
        """Apply normalization rules to extracted data."""
        normalized = data.copy()

        # Normalize date format
        if "date" in normalized and normalized["date"]:
            normalized["date"] = self._normalize_date(normalized["date"])

        # Normalize currency
        if "currency" not in normalized:
            normalized["currency"] = "USD"  # Default currency

        # Normalize phone numbers
        if "phone" in normalized and normalized["phone"]:
            normalized["phone"] = self._normalize_phone(normalized["phone"])

        # Normalize email
        if "email" in normalized and normalized["email"]:
            normalized["email"] = normalized["email"].lower().strip()

        # Ensure numeric fields are properly typed
        numeric_fields = ["amount", "tax_amount", "total_amount"]
        for field in numeric_fields:
            if field in normalized and normalized[field]:
                try:
                    normalized[field] = float(normalized[field])
                except (ValueError, TypeError):
                    normalized[field] = None

        return normalized

    def _normalize_date(self, date_str: str) -> str:
        """Normalize date string to YYYY-MM-DD format."""
        try:
            # Try common date formats
            formats = ["%m/%d/%Y", "%m-%d-%Y", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%y", "%m-%d-%y", "%d/%m/%y", "%d-%m-%y"]

            for fmt in formats:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    continue

            # If no format matches, return original
            return date_str

        except Exception:
            return date_str

    def _normalize_phone(self, phone_str: str) -> str:
        """Normalize phone number format."""
        # Remove all non-digit characters except + and -
        cleaned = re.sub(r"[^\d+\-]", "", phone_str)

        # Basic formatting
        if len(cleaned) == 10:
            return f"({cleaned[:3]}) {cleaned[3:6]}-{cleaned[6:]}"
        elif len(cleaned) == 11 and cleaned.startswith("1"):
            return f"+1 ({cleaned[1:4]}) {cleaned[4:7]}-{cleaned[7:]}"
        else:
            return cleaned
