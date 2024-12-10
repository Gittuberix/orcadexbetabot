import asyncio
import logging
from typing import Dict, Optional, List
import aiohttp
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
import base64
import struct
from src.database import DatabaseManager

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class WhirlpoolFetcher:
    def __init__(self):
        self.client = AsyncClient("https://api.mainnet-beta.solana.com")
        self.orca_api_url = "https://api.orca.so"
        self.whirlpool_program = "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc"
        
        # Bekannte Token Addresses
        self.tokens = {
            "SOL": "So11111111111111111111111111111111111111112",
            "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            "USDT": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"
        }
        
        # Wichtige Whirlpools
        self.main_pools = {
            "SOL/USDC": "HJPjoWUrhoZzkNfRpHuieeFk9WcZWjwy6PBjZ81ngndJ",
            "SOL/USDT": "4GpUivZ2jvZqQ3vJRsoq5PwnYv6gdV9fJ9BzHT2JcRr7"
        }
        
        # Füge wichtige Konstanten hinzu
        self.TICK_SPACING = 64
        self.PROTOCOL_FEE_RATE = 300  # 0.3%
        self.FEE_RATE = 3000  # 0.3%
        self.db = DatabaseManager()
        
    async def initialize(self):
        """Initialisiert Fetcher und Datenbank"""
        await self.connect()
        await self.db.init_db()
        
    async def fetch_and_store_pools(self):
        """Holt und speichert alle SOL-Pools"""
        pools = await self.get_all_whirlpools()
        for pool in pools:
            await self.db.save_pool(pool)
            
    async def get_stored_pools(self):
        """Holt gespeicherte Pools aus der DB"""
        return await self.db.get_active_pools()

    async def get_whirlpool_data(self, pool_address: str) -> Optional[Dict]:
        """Holt Rohdaten eines Whirlpools"""
        try:
            response = await self.client.get_account_info(
                Pubkey(pool_address),
                commitment="confirmed",
                encoding="base64"
            )
            
            if not response["result"]["value"]:
                return None
                
            raw_data = base64.b64decode(response["result"]["value"]["data"][0])
            return self._decode_whirlpool_data(raw_data)
            
        except Exception as e:
            logger.error(f"Fehler beim Abrufen von Whirlpool {pool_address}: {e}")
            return None

    def _decode_whirlpool_data(self, data: bytes) -> Dict:
        """Dekodiert Whirlpool-Daten nach Orca-Spezifikation"""
        try:
            # Whirlpool Layout Dekodierung
            # https://orca-so.github.io/whirlpools/classes/WhirlpoolData.html
            (
                sqrt_price,
                tick_current_index,
                protocol_fee_rate,
                liquidity,
                fee_growth_global_a,
                fee_growth_global_b,
                *rest
            ) = struct.unpack("<QqHQQQ", data[:42])
            
            # Berechne aktuellen Preis
            price = (sqrt_price / (2 ** 64)) ** 2
            
            return {
                "sqrt_price": sqrt_price,
                "tick_current_index": tick_current_index,
                "protocol_fee_rate": protocol_fee_rate,
                "liquidity": liquidity,
                "fee_growth_global_a": fee_growth_global_a,
                "fee_growth_global_b": fee_growth_global_b,
                "price": price
            }
            
        except Exception as e:
            logger.error(f"Fehler bei der Whirlpool-Dekodierung: {e}")
            return {}

    async def get_all_whirlpools(self) -> List[Dict]:
        """Holt alle aktiven Whirlpools von Orca"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.orca_api_url}/v1/whirlpool/list") as response:
                    if response.status == 200:
                        pools = await response.json()
                        return self._filter_active_pools(pools)
                    return []
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Whirlpools: {e}")
            return []

    def _filter_active_pools(self, pools: List[Dict]) -> List[Dict]:
        """Filtert aktive Pools nach Volumen und Liquidität"""
        MIN_VOLUME = 10000  # $10k Mindestvolumen
        MIN_LIQUIDITY = 50000  # $50k Mindestliquidität
        
        return [
            pool for pool in pools
            if float(pool.get('volume24h', 0)) >= MIN_VOLUME
            and float(pool.get('liquidity', 0)) >= MIN_LIQUIDITY
        ]

    async def monitor_pools(self, pool_addresses: List[str], interval: int = 5):
        """Überwacht ausgewählte Pools kontinuierlich"""
        while True:
            for address in pool_addresses:
                pool_data = await self.get_whirlpool_data(address)
                if pool_data:
                    logger.info(f"Pool {address}: Preis=${pool_data['price']:.4f}, "
                              f"Liquidität={pool_data['liquidity']}")
            await asyncio.sleep(interval)

    async def get_pool_ticks(self, pool_address: str) -> Dict:
        """Holt Tick-Daten für einen Pool"""
        try:
            response = await self.client.get_program_accounts(
                Pubkey(self.whirlpool_program),
                commitment="confirmed",
                encoding="base64",
                filters=[
                    {"memcmp": {
                        "offset": 0,
                        "bytes": pool_address
                    }}
                ]
            )
            return self._process_tick_data(response)
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Ticks: {e}")
            return {}
            
    async def calculate_swap_quote(self, 
        pool_address: str,
        amount_in: int,
        is_a_to_b: bool,
        slippage: float = 0.01
    ) -> Dict:
        """Berechnet ein Swap-Quote mit Slippage"""
        pool_data = await self.get_whirlpool_data(pool_address)
        if not pool_data:
            return None
            
        sqrt_price = pool_data['sqrt_price']
        liquidity = pool_data['liquidity']
        
        # Berechne Quote
        try:
            amount_out = self._calculate_out_amount(
                sqrt_price,
                liquidity,
                amount_in,
                is_a_to_b
            )
            
            min_amount_out = int(amount_out * (1 - slippage))
            
            return {
                'amount_in': amount_in,
                'amount_out': amount_out,
                'min_amount_out': min_amount_out,
                'price_impact': self._calculate_price_impact(
                    sqrt_price,
                    liquidity,
                    amount_in,
                    is_a_to_b
                )
            }
        except Exception as e:
            logger.error(f"Fehler bei Quote-Berechnung: {e}")
            return None

async def main():
    fetcher = WhirlpoolFetcher()
    
    # Teste einzelnen Pool
    print("\n=== SOL/USDC Pool Test ===")
    sol_usdc_data = await fetcher.get_whirlpool_data(fetcher.main_pools["SOL/USDC"])
    if sol_usdc_data:
        print(f"SOL/USDC Preis: ${sol_usdc_data['price']:.4f}")
        print(f"Liquidität: {sol_usdc_data['liquidity']}")
    
    # Hole alle aktiven Pools
    print("\n=== Aktive Whirlpools ===")
    all_pools = await fetcher.get_all_whirlpools()
    print(f"Gefundene aktive Pools: {len(all_pools)}")
    
    # Top 5 Pools nach Volumen
    sorted_pools = sorted(all_pools, key=lambda x: float(x.get('volume24h', 0)), reverse=True)
    print("\n=== Top 5 Pools nach Volumen ===")
    for pool in sorted_pools[:5]:
        print(f"\nPool: {pool['tokenA']['symbol']}/{pool['tokenB']['symbol']}")
        print(f"Address: {pool['address']}")
        print(f"24h Volume: ${float(pool['volume24h']):,.2f}")
        print(f"TVL: ${float(pool['liquidity']):,.2f}")
    
    await fetcher.client.close()

if __name__ == "__main__":
    asyncio.run(main()) 