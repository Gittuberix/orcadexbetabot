import asyncio
import aiohttp
from rich.console import Console
from config.config import load_config
from datetime import datetime

console = Console()

async def monitor_orca_pools():
    """Überwacht Orca Whirlpools in Echtzeit"""
    config = load_config()
    
    console.print("\n[cyan]Starting Orca Pool Monitor...[/cyan]")
    
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                # 1. Whirlpool Liste abrufen
                url = f"{config['network']['orca_whirlpool']}/list"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        pools = data.get('whirlpools', [])
                        
                        # Nach Volumen sortieren
                        active_pools = sorted(
                            [p for p in pools if float(p.get('volume24h', 0)) > config['pools']['min_volume']],
                            key=lambda x: float(x.get('volume24h', 0)),
                            reverse=True
                        )
                        
                        # Top Pools anzeigen
                        console.clear()
                        console.print(f"\n[cyan]Top Orca Pools - {datetime.now().strftime('%H:%M:%S')}[/cyan]")
                        
                        for i, pool in enumerate(active_pools[:5], 1):
                            console.print(f"\n{i}. {pool['tokenA']['symbol']}-{pool['tokenB']['symbol']}")
                            console.print(f"Price: ${float(pool['price']):,.4f}")
                            console.print(f"Volume 24h: ${float(pool['volume24h']):,.2f}")
                            console.print(f"TVL: ${float(pool['tvl']):,.2f}")
                
                # 2. Kurze Pause
                await asyncio.sleep(5)
                
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(monitor_orca_pools())
    except KeyboardInterrupt:
        console.print("\n[yellow]Monitor stopped by user[/yellow]") 