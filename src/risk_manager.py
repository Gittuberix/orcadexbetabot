from models import Trade
import logging

logger = logging.getLogger(__name__)

class RiskManager:
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.max_position_size = self.config.get('max_position_size', 0.1)
        self.max_drawdown = self.config.get('max_drawdown', 0.2)
        self.stop_loss = self.config.get('stop_loss', 0.05)

    def check_trade(self, trade: Trade, current_price: float) -> bool:
        try:
            if not hasattr(trade, 'amount'):
                return False
                
            position_value = trade.amount * current_price
            
            if trade.entry_price:
                loss_percentage = (current_price - trade.entry_price) / trade.entry_price
                
            return True
            
        except Exception as e:
            logging.error(f"Risk check error: {e}")
            return False            
    def _calculate_price_impact(self, signal: Signal, pool: Pool) -> float:
        """Berechnet den erwarteten Price Impact"""
        try:
            # Vereinfachte Price Impact Berechnung
            impact = (signal.amount / pool.liquidity) ** 0.5
            return impact
        except:
            return float('inf')
            
    def update_position(self, trade: Trade):
        """Aktualisiert Position und P/L Tracking"""
        if trade.type == 'buy':
            self.open_positions[trade.pool_address] = trade
            self.token_exposure[trade.token_address] = (
                self.token_exposure.get(trade.token_address, 0) + trade.amount
            )
        else:  # sell
            if trade.pool_address in self.open_positions:
                del self.open_positions[trade.pool_address]
                self.token_exposure[trade.token_address] -= trade.amount
                
            # P/L Update
            if trade.profit:
                self.daily_loss += trade.profit
                
    def reset_daily_stats(self):
        """Setzt tägliche Statistiken zurück"""
        self.daily_loss = 0.0
