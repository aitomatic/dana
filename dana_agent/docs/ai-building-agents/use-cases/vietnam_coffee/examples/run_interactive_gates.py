"""
Example: Run Vietnam Coffee Research Agent with interactive approval gates.

This example demonstrates:
1. Human-in-loop approval at 3 gates
2. Gate 1: Approve discovered companies before enrichment
3. Gate 2: Review enrichment progress every 5 batches
4. Gate 3: Final approval before delivery
5. Ability to abort at any gate
"""

import json
from pathlib import Path
import sys


# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.vietnam_coffee_research import VietnamCoffeeResearchAgent


def main():
    """Run the agent with interactive approval gates."""

    print("=" * 80)
    print("Vietnam Coffee Research Agent - Interactive Gates Demo")
    print("=" * 80)
    print("\nThis demo showcases RICH INTERACTIVE GATES with multiple commands:")
    print("\n📍 Gate 1 (Discovery):")
    print("   • proceed, show more, limit <N>, filter <keyword>, add province, redo, abort")
    print("\n📍 Gate 2 (Enrichment Progress):")
    print("   • continue, show batch, show stats, show low quality, pause, abort")
    print("\n📍 Gate 3 (Final Approval):")
    print("   • approve, export csv, show low quality, re-enrich low quality, redo, abort")
    print("\n💡 TIP: Try commands like 'limit 15', 'show more', 'show stats' at each gate!")
    print("=" * 80)

    # Initialize agent
    agent = VietnamCoffeeResearchAgent()

    # Run research with interactive gates enabled
    print("\n📍 Starting research in Đắk Lắk province...")
    print("📦 Batch size: 10 companies")
    print("🎯 Max companies: 20 (for demo)")
    print("\n🔄 Running discovery phase...")

    result = agent.research_companies(
        provinces=["Đắk Lắk"],
        batch_size=10,
        max_companies_per_province=20,
        interactive=True,  # Enable approval gates
    )

    # Check if aborted
    if not result.get("success"):
        aborted_at = result.get("aborted_at")
        if aborted_at:
            print(f"\n❌ Research aborted at: {aborted_at}")
            print("💡 You can review partial results if available")

            # Show partial results if any
            batches = result.get("batches", [])
            if batches:
                total_partial = sum(b.get("count", 0) for b in batches)
                print(f"\n📊 Partial results: {total_partial} companies enriched before abort")
        else:
            print(f"\n❌ Error: {result.get('error', 'Unknown error')}")
        return

    # Success - show results
    print("\n" + "=" * 80)
    print("✅ RESEARCH COMPLETE!")
    print("=" * 80)

    # Collect all companies from batches
    all_companies = []
    batches = result.get("batches", [])

    for batch in batches:
        batch_companies = batch.get("companies", [])
        all_companies.extend(batch_companies)

    print(f"\n📊 Total companies enriched: {len(all_companies)}")

    # Sort by priority score
    all_companies.sort(key=lambda c: c.get("priority_score", 0), reverse=True)

    # Show top 10 by priority
    print("\n🏆 Top 10 by Priority Score:")
    for i, company in enumerate(all_companies[:10], 1):
        priority = company.get("priority_score", 0)
        confidence = company.get("confidence", 0)
        entity_type = company.get("entity_type", "Unknown")
        print(f"   {i}. {company['name']}")
        print(f"      Type: {entity_type}, Priority: {priority:.1f}, Confidence: {confidence:.2f}")

    # Display summary
    summary = result.get("summary", {})
    print("\n📈 Summary:")
    print(f"   Provinces covered: {', '.join(summary.get('provinces', []))}")
    print(f"   Batches created: {summary.get('batches_created', 0)}")

    # MECE validation
    mece_report = summary.get("mece_report", {})
    print("\n📋 MECE Validation:")
    print(f"   Compliant: {'✅ Yes' if mece_report.get('mece_compliant') else '❌ No'}")
    print(f"   Duplicates removed: {mece_report.get('duplicates_removed', 0)}")

    # Quality distribution
    high_conf = sum(1 for c in all_companies if c.get("confidence", 0) >= 0.8)
    medium_conf = sum(1 for c in all_companies if 0.5 <= c.get("confidence", 0) < 0.8)
    low_conf = sum(1 for c in all_companies if c.get("confidence", 0) < 0.5)

    print("\n📊 Quality Distribution:")
    print(f"   High confidence (≥0.8): {high_conf} companies ({high_conf / len(all_companies) * 100:.1f}%)")
    print(f"   Medium confidence (0.5-0.8): {medium_conf} companies ({medium_conf / len(all_companies) * 100:.1f}%)")
    print(f"   Low confidence (<0.5): {low_conf} companies ({low_conf / len(all_companies) * 100:.1f}%)")

    # Export results
    output_file = "vietnam_coffee_interactive_output.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Results exported to: {output_file}")

    print("\n" + "=" * 80)
    print("✅ Demo complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
