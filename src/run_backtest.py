import asyncio
import logging
from datetime import datetime, timedelta
from rich.console import Console
from data.orca_client import OrcaClient
from wallet_manager import WalletManager
from strategies.meme_strategy import MemeStrategy
from solana.rpc.async_api import AsyncClient

console = Console()
logger = logging.getLogger(__name__)

async def run_backtest():
    """Führt Backtest mit Mainnet Wallet durch"""
    console.print("\n[cyan]Starting Orca DEX Backtest...[/cyan]")
    
    # 1. Wallet Setup
    rpc = AsyncClient("https://api.mainnet-beta.solana.com")
    wallet = WalletManager(rpc)
    
    if not await wallet.connect():
        console.print("[red]Failed to connect wallet[/red]")
        return
        
    # 2. Orca Client
    async with OrcaClient() as orca:
        # 3. Strategie
        config = {
            'min_volume': 10000,
            'min_liquidity': 50000,
            'max_slippage': 0.01,
            'position_size': 0.1
        }
        strategy = MemeStrategy(config)
        
        # 4. Pools laden
        pools = await orca.get_whirlpools()
        if not pools:
            console.print("[red]No pools found[/red]")
            return
            
        console.print(f"[green]Found {len(pools)} pools[/green]")
        
        # 5. Top Pools testen
        for pool in pools[:10]:  # Top 10
            console.print(f"\nAnalyzing {pool.token_a['symbol']}-{pool.token_b['symbol']}")
            
            # Signal generieren
            signal = await strategy.analyze_pool({
                'address': pool.address,
                'price': pool.price,
                'volume24h': pool.volume_24h,
                'liquidity': pool.liquidity,
                'price_history': pool.price_history
            })
            
            if signal['should_trade']:
                console.print("[green]Trade Signal:[/green]")
                console.print(f"Type: {signal['type']}")
                console.print(f"Amount: {signal['amount']:.4f}")
                console.print(f"Price: ${signal['price']:.4f}")
                console.print(f"Confidence: {signal['confidence']:.2%}")

if __name__ == "__main__":
    try:
        asyncio.run(run_backtest())
    except KeyboardInterrupt:
        console.print("\n[yellow]Backtest stopped by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Backtest error: {e}[/red]") 