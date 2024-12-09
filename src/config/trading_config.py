from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class TradingParameters:
    min_trade_size: float = 0.1  # Minimum SOL
    max_trade_size: float = 10.0  # Maximum SOL
    slippage_tolerance: float = 0.01  # 1%
    fee_percentage: float = 0.003  # 0.3%
    gas_buffer: float = 0.01  # Keep 0.01 SOL for gas

class TradingConfig:
    def __init__(self):
        self.parameters = TradingParameters()
        self.trade_size = 0.1  # Default trade size in SOL
        self.watchlist_pools = {
            'SOL/USDC': 'HJPjoWUrhoZzkNfRpHuieeFk9WcZWjwy6PBjZ81ngndJ'
        }
        
    def update_parameters(self, params: Dict[str, Any]):
        """Update trading parameters"""
        for key, value in params.items():
            if hasattr(self.parameters, key):
                setattr(self.parameters, key, value) 