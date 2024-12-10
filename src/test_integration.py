import sys
from pathlib import Path
root_dir = str(Path(__file__).parent.parent)
sys.path.insert(0, root_dir)

import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from rich.console import Console
from src.wallet_manager import WalletManager
from src.token_manager import TokenManager
from src.whirlpool.microscope import WhirlpoolMicroscope
from src.backtest.backtest_runner import BacktestRunner
from src.data.fetcher import DataFetcher
from src.config.network_config import WHIRLPOOL_CONFIGS
from orca_whirlpool.context import WhirlpoolContext
from orca_whirlpool.constants import ORCA_WHIRLPOOL_PROGRAM_ID

console = Console()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_full_integration():
    try:
        console.print("\n[cyan]=== Teste Komplette Integration ===[/cyan]")
        
        # 1. Teste Wallet Verbindung
        console.print("\n1. Teste Wallet Verbindung...")
        wallet = WalletManager()
        sol_balance = await wallet.get_sol_balance()
        token_balances = await wallet.get_token_balances()
        
        console.print(f"SOL Balance: {sol_balance:.4f}")
        for mint, amount in token_balances.items():
            console.print(f"Token {mint}: {amount}")
            
        # 2. Teste Whirlpool Verbindung
        console.print("\n2. Teste Whirlpool Verbindung...")
        ctx = WhirlpoolContext(ORCA_WHIRLPOOL_PROGRAM_ID, wallet.connection, wallet.keypair)
        token_manager = TokenManager(ctx)
        
        for pool_name, config in WHIRLPOOL_CONFIGS.items():
            console.print(f"\nTeste {pool_name}...")
            await token_manager.add_pool_to_watchlist(pool_name)
            price = await token_manager.get_pool_price(pool_name)
            liquidity = await token_manager.get_pool_liquidity(pool_name)
            console.print(f"Preis: ${price:.4f}")
            console.print(f"Liquidität: {liquidity:,}")
            
        # 3. Teste Live Data Fetching
        console.print("\n3. Teste Live Data Fetching (10 Sekunden)...")
        data_fetcher = DataFetcher(ctx)
        
        for _ in range(10):
            for pool_name in WHIRLPOOL_CONFIGS.keys():
                data = await data_fetcher.update_pool_data(pool_name)
                if data:
                    console.print(f"{pool_name}: ${data['price']:.4f}")
            await asyncio.sleep(1)
            
        # 4. Teste Backtest
        console.print("\n4. Teste Backtest (letzte Stunde)...")
        runner = BacktestRunner()
        
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=1)
        
        for pool_name, config in WHIRLPOOL_CONFIGS.items():
            console.print(f"\nBacktest für {pool_name}...")
            result = await runner.run_backtest(
                pool_address=config['address'],
                start_time=start_time,
                end_time=end_time,
                initial_capital=Decimal("1000"),
                trade_size=Decimal("0.1")
            )
            
            if result:
                console.print(f"Trades: {result.total_trades}")
                console.print(f"Win Rate: {(result.winning_trades/result.total_trades*100):.2f}%")
                console.print(f"ROI: {float(result.roi):.2f}%")
                
        console.print("\n[green]✓ Integration Test erfolgreich![/green]")
        
    except Exception as e:
        console.print(f"\n[red]✗ Fehler: {e}[/red]")
        import traceback
        traceback.print_exc()
    finally:
        await wallet.close()

if __name__ == "__main__":
    asyncio.run(test_full_integration())