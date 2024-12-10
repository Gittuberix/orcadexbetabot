import asyncio
import logging
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from src.data.orca_pipeline import OrcaPipeline

console = Console()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_pipeline():
    """Testet die Orca Pipeline"""
    pipeline = OrcaPipeline()
    
    try:
        # 1. Test Initialisierung
        console.print("\n[cyan]1. Initialisiere Pipeline...[/cyan]")
        await pipeline.initialize()
        
        if not pipeline.whirlpools:
            console.print("[red]❌ Keine Whirlpools geladen![/red]")
            return
            
        # Zeige verfügbare Pools
        console.print("\nVerfügbare Pools:")
        for pool_name in pipeline.whirlpools:
            console.print(f"- {pool_name}")
            
        console.print(f"\n[green]✓ {len(pipeline.whirlpools)} Whirlpools geladen[/green]")
        
        # 2. Test Live-Daten
        console.print("\n[cyan]2. Teste Live-Daten...[/cyan]")
        test_pools = ["SOL/USDC", "SOL/USDT", "BONK/SOL"]
        
        table = Table(title="Live Whirlpool Daten")
        table.add_column("Pool")
        table.add_column("Preis")
        table.add_column("24h Volumen")
        table.add_column("Liquidität")
        table.add_column("Fee Rate")
        
        for pool_name in test_pools:
            data = await pipeline.fetch_live_data(pool_name)
            if data:
                table.add_row(
                    pool_name,
                    f"${data.price:.4f}",
                    f"${data.volume_24h:,.0f}",
                    f"${data.liquidity:,.0f}",
                    f"{data.fee_rate:.4%}"
                )
                console.print(f"[green]✓ {pool_name} Daten empfangen[/green]")
            else:
                console.print(f"[red]❌ Keine Daten für {pool_name}[/red]")
                
        console.print(table)
        
        # 3. Test Historische Daten
        console.print("\n[cyan]3. Teste Historische Daten...[/cyan]")
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        for pool_name in test_pools:
            trades = await pipeline.fetch_historical_data(
                pool_name,
                start_time,
                end_time
            )
            
            if trades:
                console.print(
                    f"[green]✓ {pool_name}: {len(trades)} Trades in den letzten 24h[/green]"
                )
                
                # Zeige einige Statistiken
                prices = [t.price for t in trades]
                if prices:
                    console.print(
                        f"   Min Preis: ${min(prices):.4f}\n"
                        f"   Max Preis: ${max(prices):.4f}\n"
                        f"   Aktuell: ${prices[-1]:.4f}"
                    )
            else:
                console.print(f"[red]❌ Keine historischen Daten für {pool_name}[/red]")
                
        # 4. Test Monitoring
        console.print("\n[cyan]4. Teste Live Monitoring (10 Sekunden)...[/cyan]")
        monitor_task = asyncio.create_task(
            pipeline.start_monitoring(test_pools, interval=1.0)
        )
        
        await asyncio.sleep(10)
        await pipeline.stop_monitoring()
        
        # Zeige Metriken
        for pool_name in test_pools:
            metrics = pipeline.calculate_metrics(pool_name)
            if metrics:
                console.print(f"\nMetriken für {pool_name}:")
                console.print(f"Volatilität: {metrics['volatility']:.2%}")
                console.print(f"1h Änderung: {metrics['price_change_1h']:.2%}")
                console.print(f"24h Änderung: {metrics['price_change_24h']:.2%}")
                
    except Exception as e:
        console.print(f"[red]Fehler: {e}[/red]")
        raise
    finally:
        await pipeline.close()

if __name__ == "__main__":
    asyncio.run(test_pipeline()) 