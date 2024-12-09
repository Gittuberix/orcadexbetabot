from trading.trading_engine import TradingEngine
from backtest.data_manager import BacktestDataManager
from datetime import datetime, timedelta
from colorama import init, Fore, Style

init()

def test_integration():
    print(f"{Fore.CYAN}=== Testing Integration ==={Style.RESET_ALL}")
    
    # Test Trading Engine
    print("\nTesting Trading Engine...")
    trading = TradingEngine()
    
    # Test Backtest Data Manager
    print("\nTesting Backtest Data Manager...")
    backtest = BacktestDataManager()
    
    # Test data fetching
    pair = 'SOL/USDC'
    start = datetime.now() - timedelta(hours=1)
    end = datetime.now()
    
    print(f"\nFetching data for {pair}...")
    data = backtest.fetch_whirlpool_data(pair, start, end)
    
    if data is not None:
        print(f"{Fore.GREEN}Successfully fetched data!{Style.RESET_ALL}")
        print(f"Data points: {len(data)}")

if __name__ == "__main__":
    test_integration() 