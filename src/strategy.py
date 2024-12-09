from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional
from config import BotConfig

@dataclass
class TradingSignal:
    should_trade: bool
    is_buy: bool
    confidence: float
    reason: str

class TradingStrategy:
    def __init__(self, config: BotConfig):
        self.config = config
        self.min_volume = config.trading_params.min_volume_24h
        self.min_liquidity = config.trading_params.min_liquidity
        self.max_price_impact = config.trading_params.max_price_impact
        self.min_profit = config.trading_params.min_profit
        
    async def analyze(self, price: float, volume: float, timestamp: datetime, additional_data: Dict) -> Optional[TradingSignal]:
        """Analyze market data and generate trading signals"""
        try:
            # Basic validation
            if volume < self.min_volume:
                return None
                
            if additional_data.get('liquidity', 0) < self.min_liquidity:
                return None
                
            if additional_data.get('price_impact', 0) > self.max_price_impact:
                return None
                
            # Simple example strategy (replace with your actual strategy)
            # Here we're just looking for high volume with reasonable price impact
            volume_threshold = self.min_volume * 2
            if volume > volume_threshold and additional_data.get('trades', 0) > 10:
                # Check if price is trending up
                if price > additional_data.get('high', price) * 0.99:  # Within 1% of high
                    return TradingSignal(
                        should_trade=True,
                        is_buy=True,
                        confidence=0.7,
                        reason="High volume with upward trend"
                    )
                # Check if price is trending down
                elif price < additional_data.get('low', price) * 1.01:  # Within 1% of low
                    return TradingSignal(
                        should_trade=True,
                        is_buy=False,
                        confidence=0.7,
                        reason="High volume with downward trend"
                    )
                    
            return None
            
        except Exception as e:
            logging.error(f"Strategy analysis error: {e}")
            return None
            
    def validate_signal(self, signal: TradingSignal, current_price: float, position: Optional[Dict]) -> bool:
        """Validate if a trading signal should be executed"""
        if not signal or not signal.should_trade:
            return False
            
        # Don't trade if confidence is too low
        if signal.confidence < 0.6:
            return False
            
        # If we have a position, only allow sell signals
        if position and signal.is_buy:
            return False
            
        # If we don't have a position, only allow buy signals
        if not position and not signal.is_buy:
            return False
            
        return True 