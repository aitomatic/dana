"""
Example: Research coffee companies across multiple provinces (Production scale).

This example demonstrates using VietnamCoffeeResearchAgent for multi-province
research at production scale (1,000+ companies).
"""

import json
from pathlib import Path
import sys


# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.vietnam_coffee_research import VietnamCoffeeResearchAgent


def main():
    """Run multi-province research."""
    print("=" * 80)
    print("Vietnam Coffee Research Agent - Multi-Province Example")
    print("=" * 80)
    print()

    # Initialize agent
    print("Initializing agent...")
    agent = VietnamCoffeeResearchAgent()
    print("✓ Agent initialized")
    print()

    # Configure research for multiple provinces
    provinces = [
        "Đắk Lắk",
        "Gia Lai",
        "Lâm Đồng",
    ]
    batch_size = 15
    max_per_province = 50  # For demo; remove for full production

    print("Configuration:")
    print(f"  Provinces: {', '.join(provinces)}")
    print(f"  Batch size: {batch_size}")
    print(f"  Max per province: {max_per_province} (demo limit)")
    print()

    # Run research
    print("Starting multi-province research...")
    print("This may take several minutes...")
    print("-" * 80)

    result = agent.research_companies(provinces=provinces, batch_size=batch_size, max_companies_per_province=max_per_province)

    # Display results
    if result.get("success"):
        print("\n✓ Research completed successfully!\n")

        # Summary statistics
        summary = result.get("summary", {})
        total_companies = summary.get("total_companies", 0)
        batches = result.get("batches", [])

        print("=" * 80)
        print("RESULTS SUMMARY")
        print("=" * 80)
        print(f"Total companies researched: {total_companies}")
        print(f"Provinces covered: {len(summary.get('provinces', []))}")
        print(f"Batches created: {len(batches)}")
        print()

        # Province breakdown
        print("By Province:")
        province_counts = {}
        for batch in batches:
            for company in batch["companies"]:
                prov = company.get("province", "Unknown")
                province_counts[prov] = province_counts.get(prov, 0) + 1

        for prov, count in sorted(province_counts.items()):
            print(f"  {prov}: {count} companies")
        print()

        # MECE validation
        mece_report = summary.get("mece_report", {})
        print("MECE Validation:")
        print(f"  Status: {'✓ COMPLIANT' if mece_report.get('mece_compliant') else '✗ NON-COMPLIANT'}")
        print(f"  Duplicates found: {mece_report.get('duplicates_found', 0)}")
        print(f"  Duplicates removed: {mece_report.get('duplicates_removed', 0)}")

        gaps = mece_report.get("gaps_detected", [])
        if gaps:
            print(f"  Gaps detected: {', '.join(gaps)}")
        else:
            print("  Gaps detected: None")
        print()

        # Data quality
        quality_report = agent.get_quality_report()
        if quality_report.get("success"):
            report_data = quality_report["report"]
            print("Data Quality:")
            print(f"  Companies analyzed: {report_data.get('companies_analyzed', 0)}")
            print(f"  Total data points: {report_data.get('total_data_points', 0)}")
            print(f"  Average confidence: {report_data.get('average_confidence', 0):.1%}")

            conf_dist = report_data.get("confidence_distribution", {})
            print("  Confidence distribution:")
            print(f"    High (≥80%): {conf_dist.get('high (>=0.8)', 'N/A')}")
            print(f"    Medium (50-80%): {conf_dist.get('medium (0.5-0.8)', 'N/A')}")
            print(f"    Low (<50%): {conf_dist.get('low (<0.5)', 'N/A')}")
            print()

        # Top companies by priority score
        print("Top 10 Companies by Priority Score:")
        print("-" * 80)
        all_companies = []
        for batch in batches:
            all_companies.extend(batch["companies"])

        sorted_companies = sorted(all_companies, key=lambda c: c.get("priority_score", 0), reverse=True)

        for i, company in enumerate(sorted_companies[:10], 1):
            print(f"{i:2d}. {company['name']}")
            print(f"    Province: {company['province']}")
            print(f"    Products: {company.get('product_category', 'N/A')}")
            print(f"    Export: {'Yes' if company.get('export_status') else 'No'}")
            print(f"    Priority: {company.get('priority_score', 0):.1f}/100")
            print()

        # Save results
        output_file = "vietnam_coffee_multi_province_output.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"✓ Full results saved to {output_file}")

        # Save CSV
        csv_file = "vietnam_coffee_companies.csv"
        save_to_csv(all_companies, csv_file)
        print(f"✓ CSV export saved to {csv_file}")

    else:
        print("\n✗ Research failed")
        print(f"Error: {result.get('error', 'Unknown error')}")

    print()
    print("=" * 80)


def save_to_csv(companies: list[dict], filename: str):
    """Save companies to CSV file."""
    import csv

    if not companies:
        return

    # Define CSV columns
    columns = [
        "name",
        "tax_id",
        "province",
        "district",
        "address",
        "product_category",
        "export_status",
        "revenue",
        "revenue_source",
        "years_incorporated",
        "certifications",
        "pic",
        "affiliate",
        "priority_score",
        "confidence",
    ]

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()

        for company in companies:
            # Format certifications list as string
            row = {k: company.get(k, "") for k in columns}
            if isinstance(row.get("certifications"), list):
                row["certifications"] = ", ".join(row["certifications"])
            writer.writerow(row)


if __name__ == "__main__":
    main()
