import logging
from typing import Dict, List
from solders.pubkey import Pubkey
from orca_whirlpool.context import WhirlpoolContext
from src.config.network_config import WHIRLPOOL_CONFIGS
from rich.console import Console

console = Console()
logger = logging.getLogger(__name__)

class TokenManager:
    def __init__(self, ctx: WhirlpoolContext):
        self.ctx = ctx
        self.WHIRLPOOLS = WHIRLPOOL_CONFIGS
        self.watched_pools = {}
        
    async def add_pool_to_watchlist(self, pool_name: str):
        """Fügt einen Pool zur Watchlist hinzu"""
        if pool_name not in self.WHIRLPOOLS:
            raise ValueError(f"Unbekanntes Pool-Paar: {pool_name}")
            
        pool_config = self.WHIRLPOOLS[pool_name]
        pool_address = pool_config['address']
        
        # Hole Pool-Daten mit High-Level SDK
        whirlpool = await self.ctx.fetcher.get_whirlpool(
            Pubkey.from_string(pool_address)
        )
        
        # Speichere wichtige Pool-Daten
        self.watched_pools[pool_name] = {
            'address': pool_address,
            'token_a': pool_config['token_a'],
            'token_b': pool_config['token_b'],
            'whirlpool': whirlpool
        }
        
        logger.info(f"Pool {pool_name} zur Watchlist hinzugefügt")
        
    async def get_pool_price(self, pool_name: str) -> float:
        """Holt den aktuellen Pool-Preis"""
        if pool_name not in self.watched_pools:
            await self.add_pool_to_watchlist(pool_name)
            
        pool = self.watched_pools[pool_name]
        whirlpool = await self.ctx.fetcher.get_whirlpool(
            Pubkey.from_string(pool['address'])
        )
        
        return float(whirlpool.sqrt_price) ** 2 / (2 ** 64)
        
    async def get_pool_liquidity(self, pool_name: str) -> int:
        """Holt die aktuelle Pool-Liquidität"""
        if pool_name not in self.watched_pools:
            await self.add_pool_to_watchlist(pool_name)
            
        pool = self.watched_pools[pool_name]
        whirlpool = await self.ctx.fetcher.get_whirlpool(
            Pubkey.from_string(pool['address'])
        )
        
        return whirlpool.liquidity