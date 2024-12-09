import aiohttp
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from rich.console import Console
import asyncio
from dataclasses import dataclass

console = Console()
logger = logging.getLogger(__name__)

@dataclass
class WhirlpoolInfo:
    address: str
    token_a: Dict
    token_b: Dict
    fee_rate: float
    liquidity: float
    price: float
    volume_24h: float
    price_range: Dict
    price_history: List[Dict]

class OrcaClient:
    """Spezialisierter Client für Orca DEX API"""
    
    def __init__(self):
        self.base_url = "https://api.orca.so"
        self.api_version = "v1"
        self.session = None
        self.retry_attempts = 3
        self.retry_delay = 1
        
    async def __aenter__(self):
        """Context Manager Entry"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context Manager Exit"""
        if self.session:
            await self.session.close()
            
    async def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Macht API Request mit Retry"""
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        for attempt in range(self.retry_attempts):
            try:
                url = f"{self.base_url}/{self.api_version}/{endpoint}"
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 429:  # Rate Limit
                        wait_time = int(response.headers.get('Retry-After', self.retry_delay))
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"API error: {response.status} for {url}")
                        
            except Exception as e:
                logger.error(f"Request failed: {e}")
                
            await asyncio.sleep(self.retry_delay * (attempt + 1))
            
        return None
        
    async def get_whirlpools(self) -> List[WhirlpoolInfo]:
        """Holt alle aktiven Whirlpools"""
        try:
            data = await self._make_request("whirlpool/list")
            if not data:
                return []
                
            pools = []
            for pool_data in data.get('whirlpools', []):
                # Zusätzliche Pool-Details holen
                details = await self.get_pool_details(pool_data['address'])
                if details:
                    pool_data.update(details)
                    
                # Preishistorie holen
                history = await self.get_price_history(pool_data['address'])
                if history:
                    pool_data['price_history'] = history
                    
                pools.append(WhirlpoolInfo(
                    address=pool_data['address'],
                    token_a=pool_data['tokenA'],
                    token_b=pool_data['tokenB'],
                    fee_rate=float(pool_data.get('feeRate', 0)),
                    liquidity=float(pool_data.get('liquidity', 0)),
                    price=float(pool_data.get('price', 0)),
                    volume_24h=float(pool_data.get('volume24h', 0)),
                    price_range={
                        'min': float(pool_data.get('minPrice', 0)),
                        'max': float(pool_data.get('maxPrice', 0))
                    },
                    price_history=pool_data.get('price_history', [])
                ))
                
            return sorted(pools, key=lambda x: x.volume_24h, reverse=True)
            
        except Exception as e:
            logger.error(f"Failed to get whirlpools: {e}")
            return []
            
    async def get_pool_details(self, pool_address: str) -> Optional[Dict]:
        """Holt detaillierte Pool-Informationen"""
        return await self._make_request(f"whirlpool/{pool_address}")
        
    async def get_price_history(self, pool_address: str, 
                              interval: str = '1m',
                              limit: int = 1440) -> List[Dict]:
        """Holt Preishistorie für einen Pool"""
        try:
            params = {
                'interval': interval,
                'limit': limit
            }
            data = await self._make_request(f"whirlpool/{pool_address}/candles", params)
            return data if data else []
        except Exception as e:
            logger.error(f"Failed to get price history: {e}")
            return []
            
    async def get_token_info(self, token_address: str) -> Optional[Dict]:
        """Holt Token-Informationen"""
        return await self._make_request(f"token/{token_address}")
        
    async def monitor_price(self, pool_address: str):
        """Echtzeit-Preisüberwachung"""
        while True:
            try:
                price_data = await self._make_request(f"whirlpool/{pool_address}/price")
                if price_data:
                    yield price_data
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Price monitoring error: {e}")
                await asyncio.sleep(5)

# Test
async def main():
    async with OrcaClient() as client:
        # 1. Alle Whirlpools holen
        pools = await client.get_whirlpools()
        console.print(f"\n[green]Found {len(pools)} active whirlpools[/green]")
        
        if pools:
            # Top 5 Pools anzeigen
            console.print("\n[cyan]Top 5 Pools by Volume:[/cyan]")
            for i, pool in enumerate(pools[:5], 1):
                console.print(f"\n{i}. {pool.token_a['symbol']}-{pool.token_b['symbol']}")
                console.print(f"Address: {pool.address}")
                console.print(f"Price: ${pool.price:.4f}")
                console.print(f"Volume 24h: ${pool.volume_24h:,.2f}")
                console.print(f"Liquidity: ${pool.liquidity:,.2f}")
                
            # 2. Preis-Monitor für Top Pool
            top_pool = pools[0]
            console.print(f"\n[cyan]Monitoring {top_pool.token_a['symbol']}-{top_pool.token_b['symbol']} prices:[/cyan]")
            
            count = 0
            async for price_update in client.monitor_price(top_pool.address):
                console.print(f"Price: ${float(price_update['price']):.4f}")
                count += 1
                if count >= 5:  # 5 Updates zeigen
                    break

if __name__ == "__main__":
    asyncio.run(main()) 