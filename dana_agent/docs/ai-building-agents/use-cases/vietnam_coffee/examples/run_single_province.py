"""
Example: Research coffee companies in a single province (MVP).

This example demonstrates the basic usage of VietnamCoffeeResearchAgent
for researching companies in a single province.
"""

import json
from pathlib import Path
import sys


# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.vietnam_coffee_research import VietnamCoffeeResearchAgent


def main():
    """Run single-province research."""
    print("=" * 80)
    print("Vietnam Coffee Research Agent - Single Province Example")
    print("=" * 80)
    print()

    # Initialize agent
    print("Initializing agent...")
    agent = VietnamCoffeeResearchAgent()
    print("✓ Agent initialized")
    print()

    # Configure research
    province = "Đắk Lắk"
    batch_size = 10
    max_companies = 20  # MVP: Small dataset for testing

    print("Configuration:")
    print(f"  Province: {province}")
    print(f"  Batch size: {batch_size}")
    print(f"  Max companies: {max_companies}")
    print()

    # Run research
    print("Starting research...")
    print("-" * 80)

    result = agent.research_companies(provinces=[province], batch_size=batch_size, max_companies_per_province=max_companies)

    # Display results
    if result.get("success"):
        print("\n✓ Research completed successfully!\n")

        # Show batch-by-batch results
        batches = result.get("batches", [])
        print(f"Total batches: {len(batches)}")
        print()

        for batch in batches:
            batch_num = batch["batch_number"]
            count = batch["count"]
            companies = batch["companies"]

            print(f"Batch {batch_num}: {count} companies")
            print("-" * 40)

            for i, company in enumerate(companies, 1):
                print(f"  {i}. {company['name']}")
                print(f"     Tax ID: {company['tax_id']}")
                print(f"     Province: {company['province']}")
                print(f"     Products: {company.get('product_category', 'N/A')}")
                print(f"     Export: {company.get('export_status', 'N/A')}")
                print(f"     Priority Score: {company.get('priority_score', 0):.1f}/100")
                print(f"     Confidence: {company.get('confidence', 0):.0%}")
                print()

        # Show summary
        summary = result.get("summary", {})
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total companies: {summary.get('total_companies', 0)}")
        print(f"Provinces covered: {', '.join(summary.get('provinces', []))}")
        print()

        # Show MECE report
        mece_report = summary.get("mece_report", {})
        if mece_report:
            print("MECE Validation:")
            print(f"  Compliant: {mece_report.get('mece_compliant', False)}")
            print(f"  Duplicates removed: {mece_report.get('duplicates_removed', 0)}")
            print(f"  Gaps detected: {len(mece_report.get('gaps_detected', []))}")
            print()

        # Get quality report
        print("Data Quality Report:")
        quality_report = agent.get_quality_report()
        if quality_report.get("success"):
            report_data = quality_report["report"]
            print(f"  Data points tracked: {report_data.get('total_data_points', 0)}")
            print(f"  Average confidence: {report_data.get('average_confidence', 0):.0%}")
            conf_dist = report_data.get("confidence_distribution", {})
            print(f"  High confidence: {conf_dist.get('high (>=0.8)', 'N/A')}")
            print(f"  Medium confidence: {conf_dist.get('medium (0.5-0.8)', 'N/A')}")
            print(f"  Low confidence: {conf_dist.get('low (<0.5)', 'N/A')}")
            print()

        # Save to JSON
        output_file = "vietnam_coffee_research_output.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"✓ Results saved to {output_file}")

    else:
        print("\n✗ Research failed")
        print(f"Error: {result.get('error', 'Unknown error')}")

    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
