import time


# External tool to search vector DB for similar products (assume this exists)
def search_vector_db(product_id: str) -> str:
    # This would be replaced with an actual vector DB query
    # For demo purposes, we'll simulate a response
    time.sleep(5)
    return (
        """
        Query: Product ID CM-2501

Product A Details:
Product ID: CM-2501
Product Name: ProStrength Portland Cement
Product Description: High-strength Portland cement Type I/II, 94lb bag
Use Cases: Foundation pouring, concrete slabs, sidewalk construction, \
general construction
Cost per Unit: 12.50 per bag
Availability: Out of Stock

Top 5 Matches by Product Description:

1. Product ID: CM-2502
   Similarity Score: 0.89
   Product Name: EcoBlend PLC Cement
   Product Description: Portland-limestone cement, eco-friendly formula, \
94lb bag
   Use Cases: Foundation pouring, concrete slabs, sidewalk construction, \
sustainable construction
   Cost per Unit: 14.75 per bag
   Availability: In Stock

2. Product ID: CM-2504
   Similarity Score: 0.87
   Product Name: StructureCrete Cement
   Product Description: High-performance Portland cement with additives, \
94lb bag
   Use Cases: Foundation pouring, concrete slabs, heavy-duty construction, \
infrastructure projects
   Cost per Unit: 22.50 per bag
   Availability: In Stock

3. Product ID: CM-2503
   Similarity Score: 0.85
   Product Name: QuickSet Cement Mix
   Product Description: Rapid-setting Portland cement, 50lb bag
   Use Cases: Foundation pouring, concrete slabs, emergency repairs, \
time-sensitive projects
   Cost per Unit: 18.25 per bag
   Availability: In Stock

4. Product ID: CM-2505
   Similarity Score: 0.79
   Product Name: MasonMix Portland Cement
   Product Description: Modified Portland cement with improved workability, \
94lb bag
   Use Cases: Masonry work, brick laying, block work, stone setting
   Cost per Unit: 19.99 per bag
   Availability: In Stock

5. Product ID: CM-2506
   Similarity Score: 0.76
   Product Name: DuraBuild Cement
   Product Description: Premium Portland cement with durability enhancers, \
94lb bag
   Use Cases: Exterior facades, weather-exposed structures, high-traffic areas
   Cost per Unit: 24.50 per bag
   Availability: Low Stock
        """
    )