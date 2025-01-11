"""Mock FDC data generator for RIE monitoring example."""

import asyncio
import random
from datetime import datetime
from typing import AsyncGenerator, Dict, Any

class MockFDC:
    """Generates mock FDC data streams for RIE parameters."""

    def __init__(self):
        # Base values for parameters
        self._base_values = {
            "forward_power": 1000,    # 1000W nominal
            "reflected_power": 5,      # 5W nominal
            "match_position_1": 50,    # 50% nominal
            "match_position_2": 50     # 50% nominal
        }
        self._fault_active = False

    async def generate_data(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate mock FDC data stream."""
        while True:
            # Randomly trigger fault condition (1% chance)
            if random.random() < 0.01:
                self._fault_active = True

            timestamp = datetime.now().isoformat()
            data = {
                "timestamp": timestamp,
                "values": {}
            }

            # Generate values for each parameter
            for param, base in self._base_values.items():
                if self._fault_active and param == "reflected_power":
                    # Simulate matching network fault
                    value = base + random.uniform(20, 30)
                else:
                    # Normal operation with noise
                    noise = random.uniform(-2, 2)
                    value = base + noise

                data["values"][param] = value

            # Clear fault after a few cycles
            if self._fault_active and random.random() < 0.1:
                self._fault_active = False

            yield data
            await asyncio.sleep(1)  # 1 Hz sample rate

async def main():
    """Test the mock FDC generator."""
    fdc = MockFDC()
    count = 0
    async for data in fdc.generate_data():
        print(f"Sample {count}: {data}")
        count += 1
        if count >= 10:  # Show 10 samples
            break

if __name__ == "__main__":
    asyncio.run(main()) 