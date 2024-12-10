from dataclasses import dataclass
from typing import Dict, Optional
from decimal import Decimal

@dataclass
class StrategyConfig:
    min_volume: Decimal = Decimal('10000')  # Min pool volume
    min_liquidity: Decimal = Decimal('50000')  # Min pool liquidity
    max_slippage: Decimal = Decimal('0.01')  # 1% max slippage
    position_size: Decimal = Decimal('0.1')  # 10% of capital

class BaseStrategy:
    def __init__(self, config: StrategyConfig = None):
        self.config = config or StrategyConfig()
        
    async def analyze_candle(self, candle: Dict) -> Optional[str]:
        """Analyze a single candle for signals"""
        raise NotImplementedError("Subclass must implement analyze_candle")
        
    def calculate_position_size(self, capital: Decimal) -> Decimal:
        """Calculate position size based on capital"""
        return capital * self.config.position_size 