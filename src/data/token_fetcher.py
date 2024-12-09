import aiohttp
import logging
from typing import Dict, List, Optional
from datetime import datetime
from rich.console import Console

console = Console()
logger = logging.getLogger(__name__)

class OrcaTokenFetcher:
    def __init__(self):
        self.base_url = "https://api.orca.so/v1"
        self.whirlpool_url = f"{self.base_url}/whirlpool"
        self.cache = {}
        self.last_update = None
        
    async def fetch_all_tokens(self) -> List[Dict]:
        """Holt alle aktiven Whirlpools"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.whirlpool_url}/list"
                console.print(f"Fetching whirlpools from {url}")
                
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        pools = data.get('whirlpools', [])
                        
                        # Nach Volumen sortieren
                        active_pools = sorted(
                            [p for p in pools if float(p.get('volume24h', 0)) > 0],
                            key=lambda x: float(x.get('volume24h', 0)),
                            reverse=True
                        )
                        
                        # Cache aktualisieren
                        self.cache['pools'] = active_pools
                        self.last_update = datetime.now()
                        
                        console.print(f"[green]Found {len(active_pools)} active pools[/green]")
                        return active_pools
                        
            return []
            
        except Exception as e:
            logger.error(f"Failed to fetch pools: {e}")
            return []
            
    async def get_pool_price(self, pool_address: str) -> Optional[float]:
        """Holt aktuellen Pool-Preis"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.whirlpool_url}/{pool_address}/price"
                
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return float(data.get('price', 0))
                        
            return None
            
        except Exception as e:
            logger.error(f"Failed to get price: {e}")
            return None
            
    async def get_pool_stats(self, pool_address: str) -> Optional[Dict]:
        """Holt Pool-Statistiken"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.whirlpool_url}/{pool_address}"
                
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                        
            return None
            
        except Exception as e:
            logger.error(f"Failed to get pool stats: {e}")
            return None
            
    async def get_active_whirlpools(self) -> List[Dict]:
        """Holt aktive Whirlpools mit Cache"""
        # Cache prüfen
        if (
            self.cache.get('pools') and 
            self.last_update and 
            (datetime.now() - self.last_update).seconds < 60
        ):
            return self.cache['pools']
            
        return await self.fetch_all_tokens()

# Test
async def main():
    fetcher = OrcaTokenFetcher()
    pools = await fetcher.fetch_all_tokens()
    
    if pools:
        # Top 5 Pools anzeigen
        console.print("\n[cyan]Top 5 Pools by Volume:[/cyan]")
        for i, pool in enumerate(pools[:5], 1):
            console.print(f"\n{i}. {pool['tokenA']['symbol']}-{pool['tokenB']['symbol']}")
            console.print(f"Address: {pool['address']}")
            console.print(f"Volume 24h: ${float(pool['volume24h']):,.2f}")
            console.print(f"TVL: ${float(pool['tvl']):,.2f}")
            
            # Aktueller Preis
            price = await fetcher.get_pool_price(pool['address'])
            if price:
                console.print(f"Current Price: ${price:,.4f}")

if __name__ == "__main__":
    asyncio.run(main()) 