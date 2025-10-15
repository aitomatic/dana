"""
Example: Run Vietnam Coffee Research Agent with enhanced formatting.

This example demonstrates:
1. Running the research agent with enhanced schema
2. Displaying results in formatted table view
3. Exporting to CSV with all fields
4. Showing priority scores on 0-5 scale with notes
"""

import json
from pathlib import Path
import sys


# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.vietnam_coffee_research import VietnamCoffeeResearchAgent


def format_export_status(status: bool | None) -> str:
    """Format export status as checkbox."""
    if status is None:
        return "❓"
    return "✅ Yes" if status else "❌ No"


def format_revenue(revenue: int | None) -> str:
    """Format revenue with comma separators."""
    if revenue is None:
        return "N/A"
    return f"{revenue:,}"


def format_pic(name: str | None, title: str | None) -> str:
    """Format PIC with title."""
    if not name:
        return "N/A"
    if title:
        return f"{name} ({title})"
    return name


def print_table_view(companies: list[dict]):
    """
    Print companies in formatted table view.

    Matches the format from ryan.md example.
    """
    print("\n" + "=" * 160)
    print("VIETNAM COFFEE PRODUCERS - ENRICHED DATASET")
    print("=" * 160)

    # Header
    headers = [
        "#",
        "Company Name",
        "Entity Type",
        "Product Categories",
        "Est. Volume (tons)",
        "Est. Revenue (USD)",
        "Revenue Source",
        "Years Inc.",
        "Export",
        "Key Markets",
        "Certifications",
        "PIC (Verified)",
        "Affiliate / Group",
        "Priority",
        "Notes",
    ]

    # Column widths
    widths = [3, 30, 15, 30, 15, 15, 18, 8, 8, 20, 25, 25, 20, 8, 60]

    # Print header
    header_row = "  ".join(h.ljust(w)[:w] for h, w in zip(headers, widths, strict=False))
    print(header_row)
    print("-" * 160)

    # Print each company
    for idx, company in enumerate(companies, 1):
        row = [
            str(idx),
            company.get("name", "")[:30],
            company.get("entity_type", "")[:15],
            company.get("product_category", "")[:30],
            company.get("volume_tons", "N/A")[:15],
            format_revenue(company.get("revenue"))[:15],
            company.get("revenue_source", "")[:18],
            str(company.get("years_incorporated", "N/A"))[:8],
            format_export_status(company.get("export_status"))[:8],
            (company.get("key_markets") or "N/A")[:20],
            ", ".join(company.get("certifications", []))[:25],
            format_pic(company.get("pic"), company.get("pic_title"))[:25],
            (company.get("affiliate") or "None")[:20],
            f"{company.get('priority_score', 0):.1f}",
            company.get("notes", "")[:60],
        ]

        row_str = "  ".join(val.ljust(w)[:w] for val, w in zip(row, widths, strict=False))
        print(row_str)

    print("=" * 160)


def export_to_csv(companies: list[dict], filename: str):
    """
    Export companies to CSV file.

    Includes all fields with proper UTF-8 encoding.
    """
    import csv

    fieldnames = [
        "company_name",
        "tax_id",
        "entity_type",
        "product_category",
        "volume_tons",
        "revenue_usd",
        "revenue_source",
        "years_incorporated",
        "export_status",
        "key_markets",
        "certifications",
        "address",
        "district",
        "province",
        "pic_name",
        "pic_title",
        "affiliate",
        "priority_score",
        "notes",
        "confidence",
    ]

    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for company in companies:
            row = {
                "company_name": company.get("name", ""),
                "tax_id": company.get("tax_id", ""),
                "entity_type": company.get("entity_type", ""),
                "product_category": company.get("product_category", ""),
                "volume_tons": company.get("volume_tons", ""),
                "revenue_usd": company.get("revenue", ""),
                "revenue_source": company.get("revenue_source", ""),
                "years_incorporated": company.get("years_incorporated", ""),
                "export_status": "Yes" if company.get("export_status") else "No",
                "key_markets": company.get("key_markets", ""),
                "certifications": ", ".join(company.get("certifications", [])),
                "address": company.get("address", ""),
                "district": company.get("district", ""),
                "province": company.get("province", ""),
                "pic_name": company.get("pic", ""),
                "pic_title": company.get("pic_title", ""),
                "affiliate": company.get("affiliate", ""),
                "priority_score": company.get("priority_score", 0),
                "notes": company.get("notes", ""),
                "confidence": company.get("confidence", 0),
            }
            writer.writerow(row)

    print(f"\n✅ CSV exported to: {filename}")


def main():
    """Run the agent and display results with enhanced formatting."""

    print("=" * 80)
    print("Vietnam Coffee Research Agent - Enhanced Output Example")
    print("=" * 80)

    # Initialize agent
    agent = VietnamCoffeeResearchAgent()

    # Run research (MVP: single province, small batch)
    print("\n📍 Researching companies in Đắk Lắk province...")
    print("📦 Batch size: 10 companies")
    print("🎯 Max companies: 20 (for demo)")

    result = agent.research_companies(provinces=["Đắk Lắk"], batch_size=10, max_companies_per_province=20)

    # Check success
    if not result.get("success"):
        print(f"\n❌ Error: {result.get('error')}")
        return

    # Collect all companies from batches
    all_companies = []
    batches = result.get("batches", [])

    print(f"\n✅ Received {len(batches)} batches")

    for batch in batches:
        batch_companies = batch.get("companies", [])
        all_companies.extend(batch_companies)
        print(f"   Batch {batch['batch_number']}: {len(batch_companies)} companies")

    # Sort by priority score (descending)
    all_companies.sort(key=lambda c: c.get("priority_score", 0), reverse=True)

    # Display in table format
    print_table_view(all_companies)

    # Display summary
    summary = result.get("summary", {})
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total companies: {summary.get('total_companies', 0)}")
    print(f"Provinces covered: {', '.join(summary.get('provinces', []))}")
    print(f"Batches created: {summary.get('batches_created', 0)}")

    # MECE validation
    mece_report = summary.get("mece_report", {})
    print("\nMECE Validation:")
    print(f"  Compliant: {mece_report.get('mece_compliant', False)}")
    print(f"  Duplicates removed: {mece_report.get('duplicates_removed', 0)}")
    print(f"  Gaps detected: {len(mece_report.get('gaps_detected', []))}")

    # Priority score distribution
    high_priority = sum(1 for c in all_companies if c.get("priority_score", 0) >= 4.5)
    medium_priority = sum(1 for c in all_companies if 3.0 <= c.get("priority_score", 0) < 4.5)
    low_priority = sum(1 for c in all_companies if c.get("priority_score", 0) < 3.0)

    print("\nPriority Score Distribution:")
    print(f"  High (4.5-5.0): {high_priority} companies")
    print(f"  Medium (3.0-4.4): {medium_priority} companies")
    print(f"  Low (0-2.9): {low_priority} companies")

    # Export to CSV
    csv_filename = "vietnam_coffee_enhanced_output.csv"
    export_to_csv(all_companies, csv_filename)

    # Export to JSON (with full metadata)
    json_filename = "vietnam_coffee_enhanced_output.json"
    with open(json_filename, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"✅ JSON exported to: {json_filename}")

    print("\n" + "=" * 80)
    print("✅ Research complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
