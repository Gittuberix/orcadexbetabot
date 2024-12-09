from abc import ABC, abstractmethod
from typing import Dict, List
from models import Trade, Pool, Signal

class BaseTrader(ABC):
    def __init__(self, config: Dict):
        self.config = config
        self.trades: List[Trade] = []
        self.active_positions: Dict[str, Trade] = {}
        
    @abstractmethod
    async def execute_trade(self, signal: Signal) -> Trade:
        """Führt einen Trade aus"""
        pass
        
    @abstractmethod
    async def get_pool_data(self, pool_address: str) -> Pool:
        """Holt Pool Daten"""
        pass
        
    @abstractmethod
    async def get_price(self, token_address: str) -> float:
        """Holt den aktuellen Preis"""
        pass
        
    def validate_trade(self, signal: Signal) -> bool:
        """Validiert ein Trading Signal"""
        # Gemeinsame Validierungslogik
        if signal.type not in ['buy', 'sell']:
            return False
            
        if signal.amount <= 0 or signal.price <= 0:
            return False
            
        # Position Size Check
        if signal.amount > self.config['max_position_size']:
            return False
            
        return True 