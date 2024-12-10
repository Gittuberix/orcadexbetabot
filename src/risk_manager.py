import logging
from decimal import Decimal
from typing import Dict, Optional
from datetime import datetime, timedelta
from src.models import TradeData
from rich.console import Console

console = Console()
logger = logging.getLogger(__name__)

class RiskManager:
    def __init__(self):
        self.max_position_size = Decimal("1000")  # Max Position in USD
        self.max_daily_loss = Decimal("100")      # Max Tagesverlust in USD
        self.max_drawdown = Decimal("0.1")        # 10% max Drawdown
        
        self.positions = {}
        self.daily_pnl = Decimal("0")
        self.last_reset = datetime.now()
        
    def can_open_position(self, trade: TradeData) -> bool:
        """Prüft ob Position eröffnet werden kann"""
        try:
            # Prüfe Positionsgröße
            position_value = Decimal(str(trade.amount)) * Decimal(str(trade.price))
            if position_value > self.max_position_size:
                logger.warning(f"Position zu groß: ${position_value}")
                return False
                
            # Prüfe Tagesverlust
            if self.daily_pnl < -self.max_daily_loss:
                logger.warning(f"Maximaler Tagesverlust erreicht: ${self.daily_pnl}")
                return False
                
            # Prüfe Drawdown
            total_value = sum(
                Decimal(str(pos.amount)) * Decimal(str(pos.price))
                for pos in self.positions.values()
            )
            if total_value > 0:
                drawdown = (self.daily_pnl / total_value).abs()
                if drawdown > self.max_drawdown:
                    logger.warning(f"Maximaler Drawdown erreicht: {drawdown:.1%}")
                    return False
                    
            return True
            
        except Exception as e:
            logger.error(f"Fehler in der Risikoprüfung: {e}")
            return False
            
    def update_position(self, trade: TradeData):
        """Aktualisiert Position und P&L"""
        try:
            # Reset täglich
            if datetime.now() - self.last_reset > timedelta(days=1):
                self.daily_pnl = Decimal("0")
                self.last_reset = datetime.now()
                
            # Update Position
            if trade.pool_name in self.positions:
                old_pos = self.positions[trade.pool_name]
                pnl = (Decimal(str(trade.price)) - Decimal(str(old_pos.price))) * \
                      Decimal(str(old_pos.amount))
                self.daily_pnl += pnl
                
            self.positions[trade.pool_name] = trade
            
        except Exception as e:
            logger.error(f"Fehler beim Position Update: {e}")
            
    def get_position_size(self, pool_name: str) -> Decimal:
        """Holt Positionsgröße"""
        if pool_name not in self.positions:
            return Decimal("0")
            
        pos = self.positions[pool_name]
        return Decimal(str(pos.amount)) * Decimal(str(pos.price))
