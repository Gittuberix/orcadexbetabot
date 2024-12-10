import sys
from pathlib import Path
root_dir = str(Path(__file__).parent.parent)
sys.path.insert(0, root_dir)

import asyncio
import logging
from datetime import datetime
from rich.console import Console
from solders.keypair import Keypair
from solana.rpc.async_api import AsyncClient
from orca_whirlpool.context import WhirlpoolContext
from orca_whirlpool.constants import ORCA_WHIRLPOOL_PROGRAM_ID
from src.wallet_manager import WalletManager
from src.data_fetcher import DataFetcher
from src.token_manager import TokenManager

console = Console()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_integration():
    try:
        # 1. Setup Wallet & Context
        console.print("\n[cyan]=== Teste Orca Whirlpool Integration ===[/cyan]")
        
        console.print("\n1. Initialisiere Wallet...")
        wallet = WalletManager()
        connection = AsyncClient("https://api.mainnet-beta.solana.com")
        ctx = WhirlpoolContext(ORCA_WHIRLPOOL_PROGRAM_ID, connection, wallet.keypair)
        
        # 2. Setup Components
        console.print("\n2. Setup Components...")
        token_manager = TokenManager(ctx)
        data_fetcher = DataFetcher(ctx)
        
        # 3. Teste Pool-Daten
        console.print("\n3. Teste Whirlpool Daten...")
        pools_to_watch = ['SOL/USDC', 'SOL/USDT', 'BONK/SOL']
        
        for pool_name in pools_to_watch:
            console.print(f"\nLade {pool_name}...")
            await token_manager.add_pool_to_watchlist(pool_name)
            data = await data_fetcher.update_pool_data(pool_name)
            
            if data:
                console.print(f"[green]✓[/green] {pool_name}:")
                console.print(f"  Preis: ${data['price']:.4f}")
                console.print(f"  Liquidität: {data['liquidity']:,}")
            else:
                console.print(f"[red]✗[/red] Fehler beim Laden von {pool_name}")
                
        # 4. Starte Monitoring
        console.print("\n4. Starte Live Monitoring (30 Sekunden)...")
        monitor_task = asyncio.create_task(
            data_fetcher.start_monitoring(pools_to_watch)
        )
        
        await asyncio.sleep(30)
        monitor_task.cancel()
        
        console.print("\n[green]✓ Integration Test erfolgreich![/green]")
        
    except Exception as e:
        console.print(f"\n[red]✗ Fehler: {e}[/red]")
        import traceback
        traceback.print_exc()
    finally:
        await connection.close()

if __name__ == "__main__":
    asyncio.run(test_integration()) 