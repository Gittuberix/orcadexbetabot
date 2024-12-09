import asyncio
from rich.console import Console
from rich.table import Table
import aiohttp
from datetime import datetime, timedelta

console = Console()

class OrcaPoolTester:
    def __init__(self):
        self.base_url = "https://api.orca.so/v1"
        
    async def test_pools(self):
        """Testet Pool-spezifische Funktionen"""
        console.print("\n[cyan]🏊 Testing Orca Pool Functions...[/cyan]")
        
        async with aiohttp.ClientSession() as session:
            # 1. Pool Liste abrufen
            pools = await self._get_pools(session)
            if not pools:
                return
                
            # 2. USDC Pools filtern
            usdc_pools = [p for p in pools if p.get('tokenB', {}).get('symbol') == 'USDC']
            console.print(f"[green]Found {len(usdc_pools)} USDC pools[/green]")
            
            # 3. Top Pools nach Volumen
            top_pools = sorted(
                usdc_pools,
                key=lambda x: float(x.get('volume', {}).get('day', 0)),
                reverse=True
            )[:5]
            
            # 4. Pool Details anzeigen
            self._print_pool_details(top_pools)
            
            # 5. Preisdaten testen
            await self._test_price_data(session, top_pools[0]['address'])
            
    async def _get_pools(self, session: aiohttp.ClientSession) -> list:
        """Holt die Pool-Liste"""
        try:
            async with session.get(f"{self.base_url}/whirlpools") as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    console.print(f"[red]Error fetching pools: {response.status}[/red]")
                    return []
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")
            return []
            
    def _print_pool_details(self, pools: list):
        """Zeigt Pool-Details an"""
        table = Table(title="🔝 Top Pools by Volume")
        
        table.add_column("Pool", style="cyan")
        table.add_column("Token Pair", style="green")
        table.add_column("Volume 24h", justify="right", style="yellow")
        table.add_column("TVL", justify="right", style="blue")
        table.add_column("Fee", justify="right")
        
        for pool in pools:
            table.add_row(
                pool['address'][:8] + "...",
                f"{pool['tokenA']['symbol']}/{pool['tokenB']['symbol']}",
                f"${float(pool['volume']['day']):,.0f}",
                f"${float(pool['tvl']):,.0f}",
                f"{float(pool['fee'])/10000:.2f}%"
            )
            
        console.print(table)
        
    async def _test_price_data(self, session: aiohttp.ClientSession, pool_address: str):
        """Testet Preisdaten-Abruf"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=1)
        
        try:
            params = {
                'resolution': '1m',
                'start': int(start_time.timestamp()),
                'end': int(end_time.timestamp())
            }
            
            async with session.get(
                f"{self.base_url}/pool/{pool_address}/candles",
                params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    console.print(f"[green]✅ Successfully fetched {len(data)} price candles[/green]")
                else:
                    console.print(f"[red]❌ Error fetching price data: {response.status}[/red]")
                    
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")

async def main():
    tester = OrcaPoolTester()
    await tester.test_pools()

if __name__ == "__main__":
    asyncio.run(main()) 