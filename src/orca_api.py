import aiohttp
import logging
from typing import Dict, List, Optional
from datetime import datetime
import asyncio
from dataclasses import dataclass

@dataclass
class OrcaPool:
    address: str
    token_a: str
    token_b: str
    liquidity: float
    volume_24h: float
    price: float
    fee_rate: float

class OrcaAPI:
    def __init__(self):
        self.base_url = "https://api.orca.so"
        self.version = "v1"
        self.session = None
        self.rate_limit_delay = 0.1  # 100ms zwischen Anfragen
        self.last_request_time = 0
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def get_pools(self) -> List[OrcaPool]:
        """Holt alle aktiven Pools von Orca"""
        try:
            data = await self._make_request("/pools/list")
            
            pools = []
            for pool_data in data:
                try:
                    pools.append(OrcaPool(
                        address=pool_data['address'],
                        token_a=pool_data['tokenA']['mint'],
                        token_b=pool_data['tokenB']['mint'],
                        liquidity=float(pool_data.get('tvl', 0)),
                        volume_24h=float(pool_data.get('volume', {}).get('day', 0)),
                        price=float(pool_data.get('price', 0)),
                        fee_rate=float(pool_data.get('fee', 0)) / 10000
                    ))
                except (KeyError, ValueError) as e:
                    logging.warning(f"Fehler beim Parsen von Pool {pool_data.get('address')}: {e}")
                    continue
                    
            return sorted(pools, key=lambda x: x.volume_24h, reverse=True)
            
        except Exception as e:
            logging.error(f"Fehler beim Abrufen der Pools: {e}")
            return []
            
    async def get_pool_info(self, pool_address: str) -> Optional[Dict]:
        """Holt detaillierte Informationen zu einem Pool"""
        try:
            return await self._make_request(f"/pool/{pool_address}")
        except Exception as e:
            logging.error(f"Fehler beim Abrufen der Pool-Info: {e}")
            return None
            
    async def get_token_price(self, token_mint: str) -> Optional[float]:
        """Holt den aktuellen Preis eines Tokens"""
        try:
            data = await self._make_request(f"/token/{token_mint}/price")
            return float(data['price'])
        except Exception as e:
            logging.error(f"Fehler beim Abrufen des Token-Preises: {e}")
            return None
            
    async def get_swap_quote(
        self,
        input_mint: str,
        output_mint: str,
        amount: float,
        slippage: float = 0.01
    ) -> Optional[Dict]:
        """Holt ein Swap Quote von Orca"""
        try:
            params = {
                'inputMint': input_mint,
                'outputMint': output_mint,
                'amount': str(amount),
                'slippage': slippage
            }
            return await self._make_request("/quote/swap", params=params)
        except Exception as e:
            logging.error(f"Fehler beim Abrufen des Swap Quotes: {e}")
            return None
            
    async def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Führt eine API-Anfrage aus mit Rate Limiting"""
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        # Rate Limiting
        now = datetime.now().timestamp()
        time_since_last = now - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - time_since_last)
            
        url = f"{self.base_url}/{self.version}{endpoint}"
        
        try:
            async with self.session.get(url, params=params) as response:
                self.last_request_time = datetime.now().timestamp()
                
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:  # Rate limit
                    retry_after = int(response.headers.get('Retry-After', '1'))
                    logging.warning(f"Rate limit erreicht. Warte {retry_after}s")
                    await asyncio.sleep(retry_after)
                    return await self._make_request(endpoint, params)
                else:
                    raise Exception(f"API Error: {response.status} - {await response.text()}")
                    
        except Exception as e:
            logging.error(f"Request Fehler: {e}")
            raise

# Beispiel Nutzung
async def main():
    async with OrcaAPI() as orca:
        # Top Pools abrufen
        pools = await orca.get_pools()
        print("\n🌊 Top Orca Pools:")
        for i, pool in enumerate(pools[:5], 1):
            print(f"{i}. {pool.address[:8]}... "
                  f"Vol: ${pool.volume_24h:,.0f} "
                  f"TVL: ${pool.liquidity:,.0f}")
            
        if pools:
            # Pool Details
            pool_info = await orca.get_pool_info(pools[0].address)
            print(f"\n📊 Details für Top Pool:")
            print(f"Token A: {pool_info['tokenA']['symbol']}")
            print(f"Token B: {pool_info['tokenB']['symbol']}")
            print(f"Preis: ${float(pool_info['price']):,.6f}")
            
            # Swap Quote
            quote = await orca.get_swap_quote(
                pools[0].token_a,
                pools[0].token_b,
                1.0
            )
            if quote:
                print(f"\n💱 Swap Quote für 1.0 Token:")
                print(f"Erwarteter Output: {quote['expectedOutput']}")
                print(f"Preis Impact: {quote['priceImpact']}%")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main()) 