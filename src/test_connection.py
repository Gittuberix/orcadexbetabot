import asyncio
import logging
from rich.console import Console
from .core.orca_client import OrcaClient
from .core.solana_client import SolanaClient
from .config.settings import ORCA_POOLS

console = Console()
logger = logging.getLogger(__name__)

async def test_orca_connection():
    """Test Orca DEX connection"""
    try:
        console.print("\n[yellow]Testing Orca DEX Connection...[/yellow]")
        orca = OrcaClient()
        
        # Test connection
        if await orca.connect():
            console.print("✅ Connected to Orca DEX")
            
            # Test SOL/USDC pool data
            pool_address = ORCA_POOLS['SOL/USDC']
            pool_data = await orca.get_pool_data(pool_address)
            
            if pool_data:
                console.print(f"✅ SOL/USDC Pool Data:")
                console.print(f"  Price: ${float(pool_data['price']):.4f}")
                console.print(f"  Volume: ${float(pool_data['volume24h']):,.2f}")
                return True
        
        console.print("❌ Failed to connect to Orca DEX")
        return False
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return False

async def main():
    """Run all connection tests"""
    try:
        if not await test_orca_connection():
            console.print("[red]Failed to establish Orca connection[/red]")
            return
            
        console.print("\n[green]All connection tests passed![/green]")
        
    except Exception as e:
        console.print(f"[red]Test failed: {e}[/red]")

if __name__ == "__main__":
    asyncio.run(main()) 