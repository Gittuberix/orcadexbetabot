import asyncio
import logging
from rich.console import Console
from .core.orca_client import OrcaClient
from .core.solana_client import SolanaClient
from .config.wallet_config import WalletConfig
from .core.retry_helper import async_retry

console = Console()
logger = logging.getLogger(__name__)

@async_retry(retries=3)
async def test_connections():
    """Test all connections with retry logic"""
    console.print("\n[cyan]Testing Connections...[/cyan]")
    
    # Test Orca
    orca = OrcaClient()
    if await orca.connect():
        console.print("✅ Orca API Connected")
        pool_data = await orca.get_pool_data(ORCA_POOLS['SOL/USDC'])
        if pool_data:
            console.print(f"✅ Pool Data: SOL/USDC Price = ${float(pool_data['price']):.4f}")
    
    # Test Solana
    solana = SolanaClient()
    if await solana.connect():
        console.print("✅ Solana RPC Connected")
        balance = await solana.get_sol_balance()
        if balance is not None:
            console.print(f"✅ Wallet Balance: {balance:.4f} SOL")

if __name__ == "__main__":
    asyncio.run(test_connections()) 