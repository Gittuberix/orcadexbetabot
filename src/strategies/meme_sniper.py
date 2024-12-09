from dataclasses import dataclass
from typing import Dict, Optional
import logging

@dataclass
class StrategyResult:
    should_trade: bool
    trade_type: Optional[str] = None
    amount: Optional[float] = None
    price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    reason: Optional[str] = None

class MemeSniper:
    def __init__(self, config: Dict = None):
        self.config = config or {
            'min_momentum_score': 50,
            'entry_momentum_threshold': 70,
            'exit_momentum_threshold': 30,
            'min_liquidity_score': 60,
            'min_volume_score': 50,
            'base_position_size': 0.1,
            'max_position_size': 1.0,
            'stop_loss_percentage': 0.02,
            'take_profit_percentage': 0.05,
            'target_liquidity': 100000,
            'target_volume_24h': 50000
        }
        
    async def analyze(self, market_data: Dict) -> StrategyResult:
        """Analysiert Marktdaten für Trading-Signale"""
        try:
            # Momentum Score berechnen
            momentum_score = self._calculate_momentum_score(market_data)
            
            # Liquiditäts-Score berechnen
            liquidity_score = self._calculate_liquidity_score(market_data)
            
            # Volume Score berechnen
            volume_score = self._calculate_volume_score(market_data)
            
            # Entry Signal
            if momentum_score > self.config['entry_momentum_threshold']:
                if liquidity_score > self.config['min_liquidity_score']:
                    if volume_score > self.config['min_volume_score']:
                        price = market_data['price']
                        return StrategyResult(
                            should_trade=True,
                            trade_type='buy',
                            amount=self._calculate_position_size(market_data),
                            price=price,
                            stop_loss=price * (1 - self.config['stop_loss_percentage']),
                            take_profit=price * (1 + self.config['take_profit_percentage']),
                            reason=f"Strong momentum: {momentum_score:.1f}"
                        )
                        
            # Exit Signal
            if momentum_score < self.config['exit_momentum_threshold']:
                return StrategyResult(
                    should_trade=True,
                    trade_type='sell',
                    reason=f"Weak momentum: {momentum_score:.1f}"
                )
                
            return StrategyResult(should_trade=False)
            
        except Exception as e:
            logging.error(f"Strategy error: {e}")
            return StrategyResult(should_trade=False, reason=str(e))
            
    def _calculate_momentum_score(self, market_data: Dict) -> float:
        """Berechnet Momentum Score"""
        try:
            price_change = market_data.get('price_change_24h', 0)
            volume_change = market_data.get('volume_change_24h', 0)
            holder_change = market_data.get('holder_change_24h', 0)
            
            # Gewichtete Momentum-Berechnung
            momentum = (
                price_change * 0.4 +  # 40% Preis
                volume_change * 0.4 +  # 40% Volumen
                holder_change * 0.2    # 20% Holder
            )
            
            return max(0, momentum)  # Normalisiert auf 0-100
            
        except Exception as e:
            logging.error(f"Momentum calculation error: {e}")
            return 0
            
    def _calculate_liquidity_score(self, market_data: Dict) -> float:
        """Berechnet Liquiditäts-Score"""
        try:
            liquidity = float(market_data['liquidity'])
            min_liq = self.config['target_liquidity'] * 0.1  # 10% des Ziels
            target_liq = self.config['target_liquidity']
            
            if liquidity < min_liq:
                return 0
                
            return min(100, (liquidity - min_liq) / (target_liq - min_liq) * 100)
            
        except Exception as e:
            logging.error(f"Liquidity calculation error: {e}")
            return 0
            
    def _calculate_volume_score(self, market_data: Dict) -> float:
        """Berechnet Volume Score"""
        try:
            volume = float(market_data['volume_24h'])
            min_vol = self.config['target_volume_24h'] * 0.1  # 10% des Ziels
            target_vol = self.config['target_volume_24h']
            
            if volume < min_vol:
                return 0
                
            return min(100, (volume - min_vol) / (target_vol - min_vol) * 100)
            
        except Exception as e:
            logging.error(f"Volume calculation error: {e}")
            return 0
            
    def _calculate_position_size(self, market_data: Dict) -> float:
        """Berechnet optimale Position Size"""
        try:
            base_size = self.config['base_position_size']
            max_size = self.config['max_position_size']
            
            # Größere Position bei besseren Bedingungen
            momentum_score = self._calculate_momentum_score(market_data)
            liquidity_score = self._calculate_liquidity_score(market_data)
            
            size_multiplier = (momentum_score + liquidity_score) / 200  # 0-1
            position_size = base_size * (1 + size_multiplier)
            
            return min(position_size, max_size)
            
        except Exception as e:
            logging.error(f"Position size calculation error: {e}")
            return self.config['base_position_size']