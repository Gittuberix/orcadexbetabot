import sys
from pathlib import Path
root_dir = str(Path(__file__).parent.parent)
sys.path.insert(0, root_dir)

import asyncio
import logging
from datetime import datetime
from rich.console import Console
from orca_whirlpool.context import WhirlpoolContext
from orca_whirlpool.constants import ORCA_WHIRLPOOL_PROGRAM_ID

from src.data.fetcher import DataFetcher
from src.token_manager import TokenManager
from src.utils.data_validator import DataValidator
from src.utils.logger import setup_logging
from src.wallet_manager import WalletManager

console = Console()
setup_logging()
logger = logging.getLogger(__name__)

async def test_data_processing():
    try:
        # Setup
        wallet = WalletManager()
        ctx = WhirlpoolContext(ORCA_WHIRLPOOL_PROGRAM_ID, wallet.connection, wallet.keypair)
        token_manager = TokenManager(ctx)
        data_fetcher = DataFetcher(ctx)
        
        # Teste Pool-Daten
        pools_to_test = ['SOL/USDC', 'SOL/USDT', 'BONK/SOL']
        
        for pool_name in pools_to_test:
            console.print(f"\nTeste {pool_name} Datenverarbeitung...")
            
            # 1. Hole Pool-Daten
            data = await data_fetcher.update_pool_data(pool_name)
            if data:
                # 2. Validiere Daten
                if DataValidator.validate_pool_data(data):
                    console.print(f"[green]✓[/green] Pool-Daten valid:")
                    console.print(f"  Preis: ${data['price']:.4f}")
                    console.print(f"  Liquidität: {data['liquidity']:,}")
                else:
                    console.print(f"[red]✗[/red] Ungültige Pool-Daten")
                    
            # 3. Teste Daten-Updates (5 Sekunden)
            console.print("\nTeste Live-Updates...")
            for _ in range(5):
                data = await data_fetcher.update_pool_data(pool_name)
                if data:
                    console.print(f"Update: ${data['price']:.4f}")
                await asyncio.sleep(1)
                
    except Exception as e:
        logger.error(f"Fehler bei Datenverarbeitung: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_data_processing()) 