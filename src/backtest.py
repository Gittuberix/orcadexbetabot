import requests
import json
from datetime import datetime, timedelta
from pathlib import Path
from colorama import init, Fore, Style
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from models import Trade, Pool, Signal

init()

class OrcaBacktester:
    def __init__(self):
        # Primary APIs
        self.ORCA_API = "https://api.mainnet.orca.so"
        self.ORCA_WHIRLPOOL = "7qbRF6YsyGuLUVs6Y1q64bdVrfe4ZcUUz1JRdoVNUJpi"  # SOL-USDC
        
        # Setup directories
        self.data_dir = Path("backtest_data")
        self.data_dir.mkdir(exist_ok=True)
        
        # Trading parameters
        self.INITIAL_CAPITAL = 1000  # USDC
        self.RISK_PER_TRADE = 0.02   # 2%
        self.SLIPPAGE = 0.001        # 0.1%
        
        # Performance tracking
        self.trades: List[Trade] = []
        self.balance = self.INITIAL_CAPITAL
        self.current_position = None
        
    def execute_trade(self, side: str, price: float, size: float) -> Trade:
        """Execute trade with slippage simulation"""
        slippage = self.SLIPPAGE if side == 'buy' else -self.SLIPPAGE
        executed_price = price * (1 + slippage)
        
        trade = Trade(
            pool_address=self.ORCA_WHIRLPOOL,
            token_address="SOL",
            type=side,
            amount=size,
            price=executed_price,
            timestamp=datetime.now(),
            slippage=slippage,
            source='backtest'
        )
        
        self.trades.append(trade)
        
        # Update balance
        trade_value = executed_price * size
        if side == 'buy':
            self.balance -= trade_value
            self.current_position = trade
        else:
            self.balance += trade_value
            if self.current_position:
                # Calculate profit/loss
                entry_value = self.current_position.price * self.current_position.amount
                exit_value = trade_value
                trade.profit = exit_value - entry_value
                self.current_position = None
                
        return trade
        
    def run_backtest(self, start_date: datetime, end_date: datetime, strategy) -> pd.DataFrame:
        """Run backtest with given strategy"""
        print(f"{Fore.CYAN}Starting backtest from {start_date} to {end_date}{Style.RESET_ALL}")
        
        # Load historical data
        historical_data = self._load_historical_data(start_date, end_date)
        if historical_data.empty:
            print(f"{Fore.RED}No historical data available{Style.RESET_ALL}")
            return pd.DataFrame()
            
        # Run strategy
        for idx, row in historical_data.iterrows():
            market_data = {
                'timestamp': row['timestamp'],
                'price': row['price'],
                'volume': row['volume'],
                'liquidity': row['liquidity']
            }
            
            signal = strategy.analyze(market_data)
            
            if signal and signal.should_trade:
                if signal.trade_type == 'buy' and not self.current_position:
                    self.execute_trade('buy', signal.price, signal.amount)
                elif signal.trade_type == 'sell' and self.current_position:
                    self.execute_trade('sell', signal.price, self.current_position.amount)
                    
        # Generate results
        return self._generate_results()
        
    def _load_historical_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Load historical price data"""
        try:
            # Load from local file if exists
            file_path = self.data_dir / f"historical_{start_date.date()}_{end_date.date()}.csv"
            if file_path.exists():
                return pd.read_csv(file_path, parse_dates=['timestamp'])
                
            # Otherwise fetch from API
            print(f"{Fore.YELLOW}Fetching historical data...{Style.RESET_ALL}")
            # API call implementation here
            return pd.DataFrame()
            
        except Exception as e:
            print(f"{Fore.RED}Error loading historical data: {e}{Style.RESET_ALL}")
            return pd.DataFrame()
            
    def _generate_results(self) -> pd.DataFrame:
        """Generate backtest results"""
        if not self.trades:
            return pd.DataFrame()
            
        results = []
        cumulative_profit = 0
        
        for trade in self.trades:
            if trade.profit:
                cumulative_profit += trade.profit
                
            results.append({
                'timestamp': trade.timestamp,
                'type': trade.type,
                'price': trade.price,
                'amount': trade.amount,
                'profit': trade.profit or 0,
                'cumulative_profit': cumulative_profit,
                'balance': self.balance
            })
            
        return pd.DataFrame(results)
        
    def plot_results(self, results: pd.DataFrame):
        """Plot backtest results"""
        try:
            import matplotlib.pyplot as plt
            
            plt.figure(figsize=(12, 6))
            plt.plot(results['timestamp'], results['cumulative_profit'], label='Cumulative P/L')
            plt.title('Backtest Results')
            plt.xlabel('Date')
            plt.ylabel('Profit/Loss (USDC)')
            plt.legend()
            plt.grid(True)
            plt.show()
            
        except Exception as e:
            print(f"{Fore.RED}Error plotting results: {e}{Style.RESET_ALL}")

def main():
    backtest = OrcaBacktester()
    
    # Example usage
    start_date = datetime.now() - timedelta(days=30)
    end_date = datetime.now()
    
    from strategies.example_strategy import ExampleStrategy
    strategy = ExampleStrategy()
    
    results = backtest.run_backtest(start_date, end_date, strategy)
    backtest.plot_results(results)

if __name__ == "__main__":
    main()