import aiohttp
import logging
from typing import Dict, Optional, List
from ..config.settings import DEX_ENDPOINTS, POOLS

logger = logging.getLogger(__name__)

class OrcaClient:
    def __init__(self):
        self.session = None
        self.pools = POOLS['orca']
        self.endpoints = DEX_ENDPOINTS['orca']
        
    async def connect(self) -> bool:
        """Initialize HTTP session"""
        try:
            self.session = aiohttp.ClientSession(
                base_url=self.endpoints['rest'],
                headers={"Accept": "application/json"}
            )
            # Test connection
            async with self.session.get("/v1/whirlpool/list") as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Failed to connect to Orca API: {e}")
            return False
            
    async def get_pool_data(self, pool_address: str) -> Optional[Dict]:
        """Get pool data"""
        try:
            async with self.session.get(f"{self.endpoints['whirlpool']}/{pool_address}") as response:
                if response.status == 200:
                    return await response.json()
                logger.warning(f"Failed to get pool data: HTTP {response.status}")
                return None
        except Exception as e:
            logger.error(f"Error getting pool data: {e}")
            return None
            
    async def get_pool_price(self, pool_address: str) -> Optional[float]:
        """Get current pool price"""
        pool_data = await self.get_pool_data(pool_address)
        if pool_data and 'price' in pool_data:
            return float(pool_data['price'])
        return None
        
    async def close(self):
        """Close session"""
        if self.session:
            await self.session.close() 