from base_trader import BaseTrader
from models import Trade, Pool, Signal
from trade_executor import OrcaTradeExecutor
from datetime import datetime
from typing import Dict

class MainnetTrader(BaseTrader):
    def __init__(self, config: Dict, rpc_client, wallet):
        super().__init__(config)
        self.executor = OrcaTradeExecutor(rpc_client, wallet, config)
        
    async def execute_trade(self, signal: Signal) -> Trade:
        """Führt einen echten Trade aus"""
        if not self.validate_trade(signal):
            return None
            
        # Trade ausführen
        result = await self.executor.execute_trade(signal)
        
        trade = Trade(
            pool_address=signal.pool_address,
            token_address=signal.token_address,
            type=signal.type,
            amount=signal.amount,
            price=signal.price,
            timestamp=datetime.now(),
            tx_id=result.tx_id,
            slippage=result.slippage,
            status='completed' if result.success else 'failed',
            source='mainnet'
        )
        
        # Trade zur History hinzufügen
        self.trades.append(trade)
        
        return trade 