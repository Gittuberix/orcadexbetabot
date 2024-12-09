from colorama import init, Fore, Style
from datetime import datetime, timedelta
import asyncio
from connection_manager import ConnectionManager
from trading.trading_engine import TradingEngine
from backtest.backtest_engine import WhirlpoolBacktestEngine, BacktestPeriod
from config.trading_config import TradingConfig

init()

async def test_full_system():
    print(f"{Fore.CYAN}=== Full System Test ==={Style.RESET_ALL}")
    
    # 1. Load trading config
    config = TradingConfig()
    
    # 2. Test Connection Manager
    print("\n1. Testing Connection Manager...")
    conn = ConnectionManager()
    
    # Test Whirlpool connection
    pool_id = 'HJPjoWUrhoZzkNfRpHuieeFk9WcZWjwy6PBjZ81ngndJ'  # SOL/USDC
    pool_data = conn.get_pool_data(pool_id)
    if pool_data:
        print(f"{Fore.GREEN}✓ Whirlpool connection successful{Style.RESET_ALL}")
    
    # 3. Test Trading Engine
    print("\n2. Testing Trading Engine...")
    trading = TradingEngine(config)
    
    # Test trade execution
    test_amount = config.parameters.min_trade_size
    trade_result = trading.execute_trade(pool_id, test_amount, 'BUY')
    if trade_result:
        print(f"{Fore.GREEN}✓ Trading engine test successful{Style.RESET_ALL}")
    
    # 4. Test Backtest Engine
    print("\n3. Testing Backtest Engine...")
    period = BacktestPeriod.HOUR_1
    backtest = WhirlpoolBacktestEngine(config, period=period)
    
    try:
        await backtest.run_backtest()
        print(f"{Fore.GREEN}✓ Backtest completed successfully!{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Backtest error: {str(e)}{Style.RESET_ALL}")

if __name__ == "__main__":
    asyncio.run(test_full_system()) 