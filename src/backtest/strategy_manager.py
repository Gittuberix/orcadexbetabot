from typing import List, Dict
import pandas as pd
import numpy as np
from datetime import datetime
from dataclasses import dataclass

@dataclass
class Trade:
    timestamp: datetime
    type: str  # 'BUY' oder 'SELL'
    price: float
    amount: float
    value: float
    fees: float = 0.0

class BacktestStrategy:
    def __init__(self, initial_balance: float = 1000):
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.position = None
        self.trades: List[Trade] = []
        
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Berechnet technische Indikatoren"""
        df = df.copy()
        
        # Moving Averages
        df['MA5'] = df['price'].rolling(window=5).mean()
        df['MA20'] = df['price'].rolling(window=20).mean()
        
        # Volatilität
        df['volatility'] = df['price'].rolling(window=20).std()
        
        # RSI
        delta = df['price'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        return df
        
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """Generiert Trading Signale"""
        signals = pd.Series(index=df.index, data='HOLD')
        
        # Beispiel-Strategie: MA Crossover + RSI
        buy_condition = (
            (df['MA5'] > df['MA20']) & 
            (df['RSI'] < 30) &
            (df['volatility'] < df['price'] * 0.02)  # Volatilität < 2%
        )
        sell_condition = (
            (df['MA5'] < df['MA20']) | 
            (df['RSI'] > 70)
        )
        
        signals[buy_condition] = 'BUY'
        signals[sell_condition] = 'SELL'
        
        return signals
        
    def execute_trade(self, 
        timestamp: datetime,
        signal: str,
        price: float,
        liquidity: float
    ) -> bool:
        """Führt einen Trade aus"""
        if signal == 'BUY' and not self.position:
            # Position Size: 10% des Kapitals
            amount = (self.current_balance * 0.1) / price
            value = amount * price
            fees = value * 0.003  # 0.3% Gebühren
            
            if value + fees <= self.current_balance:
                self.position = amount
                self.current_balance -= (value + fees)
                self.trades.append(Trade(
                    timestamp=timestamp,
                    type='BUY',
                    price=price,
                    amount=amount,
                    value=value,
                    fees=fees
                ))
                return True
                
        elif signal == 'SELL' and self.position:
            value = self.position * price
            fees = value * 0.003
            
            self.current_balance += (value - fees)
            self.trades.append(Trade(
                timestamp=timestamp,
                type='SELL',
                price=price,
                amount=self.position,
                value=value,
                fees=fees
            ))
            self.position = None
            return True
            
        return False
        
    def get_performance_metrics(self) -> Dict:
        """Berechnet Performance-Metriken"""
        if not self.trades:
            return {
                'total_trades': 0,
                'profit_loss': 0,
                'roi': 0
            }
            
        buy_trades = [t for t in self.trades if t.type == 'BUY']
        sell_trades = [t for t in self.trades if t.type == 'SELL']
        
        total_fees = sum(t.fees for t in self.trades)
        profit_loss = self.current_balance - self.initial_balance
        roi = (profit_loss / self.initial_balance) * 100
        
        return {
            'total_trades': len(self.trades),
            'winning_trades': len([t for t in sell_trades if t.value > t.amount * t.price]),
            'total_fees': total_fees,
            'profit_loss': profit_loss,
            'roi': roi,
            'final_balance': self.current_balance
        } 