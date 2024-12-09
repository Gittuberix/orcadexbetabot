import pandas as pd
from typing import Dict, Optional
from dataclasses import dataclass
import logging

@dataclass
class PerformanceMetrics:
    total_profit: float = 0.0
    win_rate: float = 0.0
    trades_count: int = 0
    profitable_trades: int = 0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0

class PerformanceAnalyzer:
    def __init__(self):
        self.trades = []
        self.metrics = PerformanceMetrics()
        
    def add_trade(self, trade: Dict):
        """Fügt einen Trade hinzu und aktualisiert Metriken"""
        self.trades.append(trade)
        self._update_metrics()
        
    def _update_metrics(self):
        """Aktualisiert Performance-Metriken"""
        if not self.trades:
            return
            
        df = pd.DataFrame(self.trades)
        
        self.metrics.total_profit = df['profit'].sum()
        self.metrics.trades_count = len(df)
        self.metrics.profitable_trades = len(df[df['profit'] > 0])
        self.metrics.win_rate = (self.metrics.profitable_trades / self.metrics.trades_count * 100)
        
        # Drawdown und Sharpe später implementieren 