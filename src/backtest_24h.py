from datetime import datetime, timedelta
import asyncio
from colorama import init, Fore, Style
from config.trading_config import TradingConfig
from backtest.backtest_engine import WhirlpoolBacktestEngine, BacktestPeriod
from whirlpool import WhirlpoolClient
import pandas as pd
from pathlib import Path
import json

init()

class Backtest24h:
    def __init__(self):
        self.config = TradingConfig()
        self.whirlpool = WhirlpoolClient()
        self.results_dir = Path('data/backtest_results')
        self.results_dir.mkdir(parents=True, exist_ok=True)

    async def run_backtest(self):
        """Führt 24h Backtest mit realen Orca-Daten durch"""
        print(f"{Fore.CYAN}Starting 24h Backtest...{Style.RESET_ALL}")

        # Zeitraum definieren
        end_time = datetime.now()
        start_time = end_time - timedelta(days=1)
        
        print(f"Period: {start_time} to {end_time}")

        try:
            # 1. Hole aktive Pools
            pools = await self.whirlpool.get_active_whirlpools()
            if not pools:
                print(f"{Fore.RED}No active pools found{Style.RESET_ALL}")
                return

            print(f"{Fore.GREEN}Found {len(pools)} active pools{Style.RESET_ALL}")

            # 2. Führe Backtest für jeden Pool durch
            results = []
            for pool in pools[:5]:  # Top 5 Pools nach Volumen
                pool_address = pool['address']
                print(f"\n{Fore.YELLOW}Testing pool: {pool_address}{Style.RESET_ALL}")
                
                # Hole historische Daten
                df = await self.whirlpool.get_pool_price_history(
                    pool_address, 
                    start_time, 
                    end_time
                )
                
                if df.empty:
                    print(f"{Fore.RED}No data for pool {pool_address}{Style.RESET_ALL}")
                    continue

                # Initialisiere Backtest Engine
                engine = WhirlpoolBacktestEngine(
                    config=self.config,
                    period=BacktestPeriod.DAY_1
                )
                
                # Führe Backtest durch
                result = await engine.run_backtest()
                if result:
                    results.append({
                        'pool_address': pool_address,
                        'initial_capital': engine.initial_capital,
                        'final_capital': engine.current_capital,
                        'total_trades': len(engine.trades),
                        'roi': ((engine.current_capital - engine.initial_capital) / 
                               engine.initial_capital * 100)
                    })

            # 3. Speichere Ergebnisse
            self._save_results(results)
            
            # 4. Zeige Zusammenfassung
            self._print_summary(results)

        except Exception as e:
            print(f"{Fore.RED}Backtest error: {str(e)}{Style.RESET_ALL}")

    def _save_results(self, results: list):
        """Speichert Backtest-Ergebnisse"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = self.results_dir / f'backtest_24h_{timestamp}.json'
        
        with open(file_path, 'w') as f:
            json.dump(results, f, indent=4, default=str)
            
        print(f"\n{Fore.GREEN}Results saved to {file_path}{Style.RESET_ALL}")

    def _print_summary(self, results: list):
        """Zeigt Zusammenfassung der Backtest-Ergebnisse"""
        print(f"\n{Fore.CYAN}=== Backtest Summary ==={Style.RESET_ALL}")
        
        if not results:
            print(f"{Fore.YELLOW}No results to display{Style.RESET_ALL}")
            return
            
        # Berechne Gesamtperformance
        total_roi = sum(r['roi'] for r in results) / len(results)
        total_trades = sum(r['total_trades'] for r in results)
        
        print(f"Total Pools Tested: {len(results)}")
        print(f"Total Trades: {total_trades}")
        print(f"Average ROI: {total_roi:.2f}%")
        
        # Zeige beste Pools
        print(f"\n{Fore.CYAN}Top Performing Pools:{Style.RESET_ALL}")
        sorted_results = sorted(results, key=lambda x: x['roi'], reverse=True)
        
        for r in sorted_results[:3]:
            print(f"\nPool: {r['pool_address']}")
            print(f"ROI: {r['roi']:.2f}%")
            print(f"Trades: {r['total_trades']}")

async def main():
    backtest = Backtest24h()
    await backtest.run_backtest()

if __name__ == "__main__":
    asyncio.run(main()) 