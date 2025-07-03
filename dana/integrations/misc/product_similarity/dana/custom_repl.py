import asyncio
import time
from typing import Any

from opendxa.dana.exec.repl.dana_repl_app import DanaREPLApp
from opendxa.dana.sandbox.log_manager import LogLevel
from opendxa.dana.sandbox.parser.python_registry import PythonRegistry


def get_product_details(context: dict[str, Any], product_id: str):
    return "{'id': 'CM-2501', 'product_name': 'ProStrength Portland Cement', 'product_description': 'High-strength Portland cement Type I/II, 94lb bag', 'use_cases': 'Foundation pouring, concrete slabs, sidewalk construction, general construction', 'cost_per_unit': 12.50, 'availability': 'Out of Stock'}"


def vector_search_descriptions(context: dict[str, Any], product_description: str, top_k: int = 5) -> list[dict]:
    print("Searching database...")
    time.sleep(5)  # El fako!
    return [
        {
            "id": "CM-2502",
            "similarity_score": 0.89,
            "product_name": "EcoBlend PLC Cement",
            "product_description": "Portland-limestone cement, eco-friendly formula, 94lb bag",
            "use_cases": "Foundation pouring, concrete slabs, sidewalk construction, sustainable construction",
            "cost_per_unit": 14.75,
            "availability": "In Stock",
        },
        {
            "id": "CM-2504",
            "similarity_score": 0.87,
            "product_name": "StructureCrete Cement",
            "product_description": "High-performance Portland cement with additives, 94lb bag",
            "use_cases": "Foundation pouring, concrete slabs, heavy-duty construction, infrastructure projects",
            "cost_per_unit": 22.50,
            "availability": "In Stock",
        },
        {
            "id": "CM-2503",
            "similarity_score": 0.85,
            "product_name": "QuickSet Cement Mix",
            "product_description": "Rapid-setting Portland cement, 50lb bag",
            "use_cases": "Foundation pouring, concrete slabs, emergency repairs, time-sensitive projects",
            "cost_per_unit": 18.25,
            "availability": "In Stock",
        },
        {
            "id": "CM-2505",
            "similarity_score": 0.79,
            "product_name": "MasonMix Portland Cement",
            "product_description": "Modified Portland cement with improved workability, 94lb bag",
            "use_cases": "Masonry work, brick laying, block work, stone setting",
            "cost_per_unit": 19.99,
            "availability": "In Stock",
        },
        {
            "id": "CM-2506",
            "similarity_score": 0.76,
            "product_name": "DuraBuild Cement",
            "product_description": "Premium Portland cement with durability enhancers, 94lb bag",
            "use_cases": "Exterior facades, weather-exposed structures, high-traffic areas",
            "cost_per_unit": 24.50,
            "availability": "Low Stock",
        },
    ]


class ProductSimilarityREPL(DanaREPLApp):
    """Dana REPL with product similarity functions."""

    def __init__(self, log_level: LogLevel = LogLevel.DEBUG):
        """Initialize the REPL with product similarity functions."""
        # Register functions before initializing parent
        PythonRegistry.register("private:get_product_details", get_product_details)
        PythonRegistry.register("private:vector_search_descriptions", vector_search_descriptions)

        # Initialize parent class
        super().__init__(log_level=log_level)

    def _show_welcome(self) -> None:
        """Show welcome message with product similarity functions."""
        super()._show_welcome()  # Keep original welcome message
        print(
            "Product Similarity Functions:\n"
            "  - [private] get_product_details(product_id)\n"
            "  - [private] vector_search_descriptions(description)\n\n"
            "Example usage:\n"
            "  private:product = get_product_details('CM-2501')\n"
            "  private:results = vector_search_descriptions(private:product.description)\n"
        )


async def main():
    """Run the Dana REPL with product similarity functions."""
    app = ProductSimilarityREPL()
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
