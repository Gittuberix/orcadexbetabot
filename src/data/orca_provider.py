import aiohttp
import logging
from typing import Dict, List, Optional
from datetime import datetime
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class OrcaDataProvider:
    """Zentrale Klasse für Orca DEX Daten"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.endpoints = {
            'main': 'https://api.orca.so',
            'rpc': 'https://api.mainnet.orca.so/v1/rpc',
            'backup': 'https://solana-api.projectserum.com'
        }
        self.cache = {}
        self.last_update = None
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1))
    async def get_pools(self) -> List[Dict]:
        """Holt aktive Pools mit Retry"""
        async with aiohttp.ClientSession() as session:
            url = f"{self.endpoints['main']}/v1/whirlpools"
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
        return []
        
    async def get_price_feed(self, pool_address: str):
        """Echtzeit-Preisdaten Stream"""
        while True:
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"{self.endpoints['main']}/v1/whirlpool/{pool_address}/price"
                    async with session.get(url) as response:
                        if response.status == 200:
                            yield await response.json()
            except Exception as e:
                logger.error(f"Price feed error: {e}")
            await asyncio.sleep(1) 