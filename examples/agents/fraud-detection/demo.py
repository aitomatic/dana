"""
Demo script for Fraud Detection Application.

This script demonstrates the complete fraud detection pipeline:
1. CoordinatorAgent orchestrates the pipeline
2. DeepExtractor extracts text from PDF/image
3. FieldNormalizer converts text to JSON
4. FraudIndicator analyzes for fraud patterns

Usage:
    python demo.py [file_path]

Example:
    python demo.py sample_invoice.pdf
"""

import os
import sys
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))

from agents.coordinator_agent import CoordinatorAgent


def create_sample_document():
    """Create a sample text file for demonstration if no file is provided."""
    sample_content = """
    INVOICE
    
    Invoice #: INV-2024-001
    Date: 2024-01-15
    Due Date: 2024-02-15
    
    Bill To:
    Acme Corporation
    123 Business Street
    New York, NY 10001
    Phone: (555) 123-4567
    Email: billing@acme.com
    
    From:
    Tech Solutions Inc.
    456 Tech Avenue
    San Francisco, CA 94105
    Phone: (415) 555-0123
    Email: invoices@techsolutions.com
    
    Description: Software Development Services
    Amount: $15,000.00
    Tax (8.5%): $1,275.00
    Total: $16,275.00
    
    Payment Terms: Net 30
    """

    sample_file = "sample_invoice.txt"
    with open(sample_file, "w") as f:
        f.write(sample_content)

    return sample_file


def print_section(title, content, max_width=80):
    """Print a formatted section with title and content."""
    print(f"\n{'=' * max_width}")
    print(f"{title:^{max_width}}")
    print(f"{'=' * max_width}")
    print(content)


def print_json_section(title, data, max_width=80):
    """Print a formatted JSON section."""
    import json

    formatted_json = json.dumps(data, indent=2, default=str)
    print_section(title, formatted_json, max_width)


def main():
    """Main demo function."""
    parser = argparse.ArgumentParser(description="Fraud Detection Application Demo")
    parser.add_argument("file_path", nargs="?", help="Path to PDF or image file to analyze")
    parser.add_argument("--llm-provider", default="anthropic", help="LLM provider (default: anthropic)")
    parser.add_argument("--model", default="claude-3-5-sonnet-20241022", help="Model name")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    # Determine file path
    if args.file_path:
        file_path = args.file_path
        if not os.path.exists(file_path):
            print(f"Error: File '{file_path}' not found.")
            return 1
    else:
        print("No file provided. Creating sample document for demonstration...")
        file_path = create_sample_document()
        print(f"Created sample file: {file_path}")

    print_section(
        "FRAUD DETECTION APPLICATION DEMO", f"Analyzing file: {file_path}\nLLM Provider: {args.llm_provider}\nModel: {args.model}"
    )

    try:
        # Initialize the coordinator agent
        print("\nInitializing Fraud Detection Coordinator...")
        coordinator = CoordinatorAgent(agent_id="fraud-coordinator-demo", llm_provider=args.llm_provider, model=args.model)

        print("✓ Coordinator agent initialized successfully")
        print("✓ DeepExtractor agent registered")
        print("✓ FieldNormalizer agent registered")
        print("✓ FraudIndicator agent registered")
        print("✓ FraudDetectionWorkflow registered")

        # Execute fraud detection
        print_section("EXECUTING FRAUD DETECTION PIPELINE", "Starting comprehensive fraud analysis...")

        # Call the coordinator with the file path
        result = coordinator.converse(initial_message=f"Analyze this document for fraud: {file_path}", file_path=file_path)

        # Display results
        if result and isinstance(result, dict):
            print_section("PIPELINE EXECUTION COMPLETED", "Fraud detection pipeline executed successfully!")

            # Extract key information from result
            if "extracted_text" in result:
                print_section(
                    "EXTRACTED TEXT",
                    result["extracted_text"][:500] + "..." if len(result["extracted_text"]) > 500 else result["extracted_text"],
                )

            if "normalized_data" in result:
                print_json_section("NORMALIZED DATA", result["normalized_data"])

            if "fraud_result" in result:
                fraud_result = result["fraud_result"]
                print_json_section("FRAUD ANALYSIS RESULT", fraud_result)

                # Display risk assessment
                risk_score = fraud_result.get("risk_score", 0)
                risk_level = "LOW" if risk_score < 40 else "MEDIUM" if risk_score < 70 else "HIGH"

                print_section(
                    "RISK ASSESSMENT",
                    f"Risk Score: {risk_score}/100 ({risk_level} RISK)\n"
                    f"Fraud Indicators: {len(fraud_result.get('fraud_indicators', []))}\n"
                    f"Anomalies: {len(fraud_result.get('anomalies', []))}",
                )

            if "pipeline_metadata" in result:
                metadata = result["pipeline_metadata"]
                print_json_section("PIPELINE METADATA", metadata)

        else:
            print_section("ERROR", "Failed to get results from fraud detection pipeline")
            if args.verbose:
                print(f"Raw result: {result}")

        # Cleanup sample file if created
        if not args.file_path and os.path.exists("sample_invoice.txt"):
            os.remove("sample_invoice.txt")
            print(f"\nCleaned up sample file: sample_invoice.txt")

        print_section("DEMO COMPLETED", "Fraud detection analysis finished successfully!")
        return 0

    except Exception as e:
        print_section("ERROR", f"Demo failed with error: {str(e)}")
        if args.verbose:
            import traceback

            print(f"Full traceback:\n{traceback.format_exc()}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
