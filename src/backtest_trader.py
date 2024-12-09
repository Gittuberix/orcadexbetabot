from base_trader import BaseTrader
from models import Trade, Pool, Signal
from datetime import datetime

class BacktestTrader(BaseTrader):
    def __init__(self, config: Dict, historical_data: Dict):
        super().__init__(config)
        self.historical_data = historical_data
        self.current_time = None
        
    async def execute_trade(self, signal: Signal) -> Trade:
        """Simuliert einen Trade"""
        if not self.validate_trade(signal):
            return None
            
        trade = Trade(
            pool_address=signal.pool_address,
            token_address=signal.token_address,
            type=signal.type,
            amount=signal.amount,
            price=signal.price,
            timestamp=self.current_time,
            source='backtest'
        )
        
        # Simulierte Slippage
        trade.slippage = self._calculate_simulated_slippage(signal)
        
        # Trade zur History hinzufügen
        self.trades.append(trade)
        
        return trade
        
    async def get_pool_data(self, pool_address: str) -> Pool:
        """Holt historische Pool Daten"""
        if pool_address in self.historical_data:
            data = self.historical_data[pool_address]
            return Pool(
                address=pool_address,
                token_a=data['token_a'],
                token_b=data['token_b'],
                price=data['price'],
                liquidity=data['liquidity'],
                volume_24h=data['volume_24h'],
                price_change_24h=data['price_change_24h'],
                created_at=data['created_at']
            )
        return None 