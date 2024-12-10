import asyncio
import logging
from datetime import datetime, timedelta
from backtest.data_manager import HistoricalDataManager
from backtest.strategy_manager import BacktestStrategy
from colorama import init, Fore, Style

init()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_replay_backtest():
    try:
        print(f"{Fore.CYAN}=== Starte Backtest mit Replay-Daten ==={Style.RESET_ALL}")
        
        # Zeitraum definieren
        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)  # 1 Woche Backtest
        
        # Initialisierung
        data_manager = HistoricalDataManager()
        strategy = BacktestStrategy(initial_balance=1000)
        
        print(f"\n{Fore.YELLOW}Zeitraum: {start_time} bis {end_time}{Style.RESET_ALL}")
        
        # Hole historische Daten via Replayer
        pool_data = await data_manager.prepare_backtest_data(
            start_time,
            end_time,
            min_volume=100000
        )
        
        print(f"\nGefundene Pools mit Daten: {len(pool_data)}")
        
        # Backtest für jeden Pool
        total_profit = 0
        successful_pools = 0
        
        for pool_address, df in pool_data.items():
            try:
                print(f"\n{Fore.CYAN}=== Teste Pool {pool_address} ==={Style.RESET_ALL}")
                print(f"Datenpunkte: {len(df)}")
                
                # Berechne Indikatoren
                df = strategy.calculate_indicators(df)
                
                # Generiere Signale
                signals = strategy.generate_signals(df)
                signal_counts = signals.value_counts()
                print("\nSignal-Verteilung:")
                for signal, count in signal_counts.items():
                    print(f"{signal}: {count}")
                
                # Führe Trades aus
                for idx, row in df.iterrows():
                    signal = signals[idx]
                    if strategy.execute_trade(
                        timestamp=row['timestamp'],
                        signal=signal,
                        price=row['close'],  # Nutze Schlusskurs
                        liquidity=row['liquidity']
                    ):
                        continue
                
                # Performance für diesen Pool
                metrics = strategy.get_performance_metrics()
                total_profit += metrics['profit_loss']
                
                if metrics['profit_loss'] > 0:
                    successful_pools += 1
                
                print(f"\n{Fore.GREEN if metrics['profit_loss'] > 0 else Fore.RED}Performance:{Style.RESET_ALL}")
                print(f"Trades: {metrics['total_trades']}")
                print(f"Gewinnende Trades: {metrics['winning_trades']}")
                print(f"Profit/Loss: ${metrics['profit_loss']:.2f}")
                print(f"ROI: {metrics['roi']:.2f}%")
                
            except Exception as e:
                logger.error(f"Fehler bei Pool {pool_address}: {e}")
                continue
        
        # Gesamtergebnis
        print(f"\n{Fore.GREEN}=== Gesamtergebnis ==={Style.RESET_ALL}")
        print(f"Getestete Pools: {len(pool_data)}")
        print(f"Erfolgreiche Pools: {successful_pools}")
        print(f"Gesamtprofit: ${total_profit:.2f}")
        print(f"Durchschnittlicher Profit pro Pool: ${total_profit/len(pool_data):.2f}")
        
    except Exception as e:
        logger.error(f"Kritischer Fehler: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_replay_backtest()) 