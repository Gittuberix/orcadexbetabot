import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional, List
from solders.pubkey import Pubkey
from orca_whirlpool.context import WhirlpoolContext
from orca_whirlpool.constants import ORCA_WHIRLPOOL_PROGRAM_ID
from orca_whirlpool.utils import PriceMath, DecimalUtil
from src.token_manager import TokenManager
from rich.console import Console

console = Console()
logger = logging.getLogger(__name__)

class DataFetcher:
    def __init__(self, ctx: WhirlpoolContext):
        self.ctx = ctx
        self.token_manager = TokenManager(ctx)
        self.cache = {}
        
    async def update_pool_data(self, pool_name: str) -> Optional[Dict]:
        """Aktualisiert Pool-Daten mit High-Level SDK"""
        try:
            # Hole Pool via SDK
            pool_address = self.token_manager.WHIRLPOOLS[pool_name]
            whirlpool = await self.ctx.fetcher.get_whirlpool(
                Pubkey.from_string(pool_address)
            )
            
            # Hole Token Decimals
            token_a = await self.ctx.fetcher.get_token_mint(whirlpool.token_mint_a)
            token_b = await self.ctx.fetcher.get_token_mint(whirlpool.token_mint_b)
            
            # Berechne Preis mit SDK Utils
            price = PriceMath.sqrt_price_x64_to_price(
                whirlpool.sqrt_price,
                token_a.decimals,
                token_b.decimals
            )
            
            pool_data = {
                'timestamp': datetime.now(),
                'price': float(DecimalUtil.to_fixed(price, token_b.decimals)),
                'liquidity': whirlpool.liquidity,
                'pool_name': pool_name,
                'address': pool_address
            }
            
            # Cache aktualisieren
            self.cache[pool_name] = pool_data
            
            # Log signifikante Änderungen
            if len(self.cache) > 1:
                last_price = self.cache[pool_name]['price']
                price_change = (price - last_price) / last_price
                if abs(price_change) > 0.001:  # 0.1% Änderung
                    logger.info(f"{pool_name} Preis: ${pool_data['price']:.4f} ({price_change:.2%})")
                    
            return pool_data
            
        except Exception as e:
            logger.error(f"Fehler beim Update von {pool_name}: {e}")
            return None
            
    async def start_monitoring(self, pool_names: List[str], interval: float = 1.0):
        """Startet kontinuierliches Monitoring"""
        while True:
            for pool_name in pool_names:
                await self.update_pool_data(pool_name)
            await asyncio.sleep(interval) 