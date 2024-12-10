import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
import logging
from datetime import datetime, timedelta
import pandas as pd
from src.backtest.historical_data_manager import HistoricalDataManager
from src.backtest.strategy_manager import BacktestStrategy
from colorama import init, Fore, Style

init()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_backtest():
    try:
        print(f"{Fore.CYAN}=== Starte Multi-Pool Backtest ==={Style.RESET_ALL}")
        
        # Zeitraum definieren
        end_time = datetime.now()
        start_time = end_time - timedelta(days=1)  # 24h Backtest
        
        # Initialisierung
        data_manager = HistoricalDataManager()
        strategy = BacktestStrategy(initial_balance=1000)  # 1000 USDC pro Pool
        
        print(f"\n{Fore.YELLOW}=== Lade historische Daten ==={Style.RESET_ALL}")
        pool_data = await data_manager.prepare_backtest_data(
            start_time,
            end_time,
            min_volume=100000,  # $100k Mindestvolumen
            timeframe='1m'      # 1-Minuten-Candlesticks
        )
        
        print(f"\nGefundene Pools: {len(pool_data)}")
        
        # Backtest für jeden Pool
        total_profit = 0
        for pool_address, df in pool_data.items():
            print(f"\n{Fore.CYAN}=== Teste Pool {pool_address} ==={Style.RESET_ALL}")
            
            # Berechne Indikatoren
            df = strategy.calculate_indicators(df)
            
            # Generiere Signale
            signals = strategy.generate_signals(df)
            
            # Führe Backtest durch
            trade_count = 0
            for idx, row in df.iterrows():
                signal = signals[idx]
                if strategy.execute_trade(
                    timestamp=pd.to_datetime(row['timestamp']),
                    signal=signal,
                    price=row['price'],
                    liquidity=row['liquidity']
                ):
                    trade_count += 1
            
            # Performance für diesen Pool
            metrics = strategy.get_performance_metrics()
            total_profit += metrics['profit_loss']
            
            print(f"Trades: {metrics['total_trades']}")
            print(f"Gewinnende Trades: {metrics['winning_trades']}")
            print(f"Profit/Loss: ${metrics['profit_loss']:.2f}")
            print(f"ROI: {metrics['roi']:.2f}%")
            
        print(f"\n{Fore.GREEN}=== Gesamtergebnis ==={Style.RESET_ALL}")
        print(f"Getestete Pools: {len(pool_data)}")
        print(f"Gesamtprofit: ${total_profit:.2f}")
        print(f"Durchschnittlicher Profit pro Pool: ${total_profit/len(pool_data):.2f}")
        
    except Exception as e:
        print(f"{Fore.RED}Fehler im Backtest: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_backtest()) 