import asyncio
import logging
from rich.console import Console
from data.orca_client import OrcaClient
from wallet_manager import WalletManager
from strategies.meme_strategy import MemeStrategy
from solana.rpc.async_api import AsyncClient
from datetime import datetime, timedelta

console = Console()
logger = logging.getLogger(__name__)

async def test_backtest_data():
    """Testet Datenladung für Backtest mit spezifischen Parametern"""
    console.print("\n[cyan]Testing Backtest Data Load...[/cyan]")
    
    # Konfiguration
    config = {
        'initial_capital': 1.0,     # 1 SOL
        'position_size': 0.01,      # 0.01 SOL pro Trade
        'min_volume': 10000,        # Min $10k Volumen
        'min_liquidity': 50000,     # Min $50k Liquidität
        'max_slippage': 0.01        # Max 1% Slippage
    }
    
    try:
        # 1. Wallet Connection testen
        rpc = AsyncClient("https://api.mainnet-beta.solana.com")
        wallet = WalletManager(rpc)
        
        if await wallet.connect():
            console.print(f"[green]✓ Wallet connected: {wallet.get_public_key()}[/green]")
            console.print(f"SOL Balance: {wallet.get_balance():.4f}")
        else:
            console.print("[red]× Failed to connect wallet[/red]")
            return
            
        # 2. Orca Daten laden
        async with OrcaClient() as orca:
            # Pools laden
            console.print("\n[cyan]Loading Whirlpools...[/cyan]")
            pools = await orca.get_whirlpools()
            
            if not pools:
                console.print("[red]× No pools found[/red]")
                return
                
            console.print(f"[green]✓ Found {len(pools)} pools[/green]")
            
            # Top 10 Pools analysieren
            console.print("\n[cyan]Analyzing Top 10 Pools:[/cyan]")
            viable_pools = 0
            total_signals = 0
            
            for pool in pools[:10]:
                console.print(f"\nPool: {pool.token_a['symbol']}-{pool.token_b['symbol']}")
                console.print(f"Address: {pool.address}")
                console.print(f"Price: ${pool.price:.4f}")
                console.print(f"Volume 24h: ${pool.volume_24h:,.2f}")
                console.print(f"Liquidity: ${pool.liquidity:,.2f}")
                
                # Validierung
                if pool.volume_24h >= config['min_volume'] and pool.liquidity >= config['min_liquidity']:
                    viable_pools += 1
                    
                    # Preishistorie prüfen
                    if pool.price_history:
                        console.print(f"[green]✓ Has price history ({len(pool.price_history)} points)[/green]")
                        
                        # Beispiel-Trade berechnen
                        max_trade_value = min(
                            config['position_size'] * pool.price,  # Unser Limit
                            pool.liquidity * 0.001  # 0.1% der Pool-Liquidität
                        )
                        
                        console.print(f"Max trade value: ${max_trade_value:.2f}")
                        
                        # Trading Signal testen
                        strategy = MemeStrategy(config)
                        signal = await strategy.analyze_pool({
                            'address': pool.address,
                            'price': pool.price,
                            'volume24h': pool.volume_24h,
                            'liquidity': pool.liquidity,
                            'price_history': pool.price_history
                        })
                        
                        if signal['should_trade']:
                            total_signals += 1
                            console.print("[green]✓ Generated trading signal:[/green]")
                            console.print(f"  Type: {signal['type']}")
                            console.print(f"  Amount: {signal['amount']:.4f} SOL")
                            console.print(f"  Price: ${signal['price']:.4f}")
                            console.print(f"  Confidence: {signal['confidence']:.2%}")
                    else:
                        console.print("[red]× No price history available[/red]")
                else:
                    console.print("[yellow]! Pool does not meet criteria[/yellow]")
                    
            # Zusammenfassung
            console.print("\n[cyan]Summary:[/cyan]")
            console.print(f"Viable pools: {viable_pools}/10")
            console.print(f"Trading signals: {total_signals}")
            console.print(f"Initial capital: {config['initial_capital']} SOL")
            console.print(f"Max trade size: {config['position_size']} SOL")
            
    except Exception as e:
        console.print(f"[red]Error testing backtest data: {e}[/red]")
        logger.exception("Backtest data test failed")

if __name__ == "__main__":
    try:
        asyncio.run(test_backtest_data())
    except KeyboardInterrupt:
        console.print("\n[yellow]Test stopped by user[/yellow]") 