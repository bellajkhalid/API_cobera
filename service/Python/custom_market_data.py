"""
Custom market_data module to avoid circular imports with irVolatilitySurface
"""

import os
from xsigmamodules.Market import discountCurvePiecewiseConstant

class MarketData:
    """
    Simplified market_data implementation to avoid import issues
    """

    def __init__(self, data_root):
        self.data_root = data_root
        print(f"Initialized MarketData with root: {data_root}")

    def discountCurve(self):
        """Return the discount curve from the data root"""
        return discountCurvePiecewiseConstant.read_from_json(
            os.path.join(self.data_root, "Data/marketData/discount_curve_piecewise_constant.json")
        )

# Create a class that mimics the original market_data module
class MarketDataModule:
    def __init__(self):
        self.market_data = self.create_market_data

    def create_market_data(self, data_root):
        """Factory function to create a MarketData instance"""
        return MarketData(data_root)

# Create a singleton instance
market_data = MarketDataModule()
