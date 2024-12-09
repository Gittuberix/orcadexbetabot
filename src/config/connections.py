from typing import Dict, Any
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass
import aiohttp
import asyncio
import logging
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

@dataclass
class RPCEndpoint:
    url: str
    weight: int
    ws_url: str = None
    api_key: str = None

ORCA_ENDPOINTS = {
    "api": "https://api.mainnet.orca.so",
    "whirlpool": "https://api.orca.so/v1/whirlpool",
    "whirlpool_list": "https://api.orca.so/v1/whirlpool/list",
    "rpc": "https://api.mainnet.orca.so/rpc"
}

# QuickNode Configuration
QUICKNODE_RPC_URL = os.getenv('QUICKNODE_RPC_URL')
QUICKNODE_WS_URL = os.getenv('QUICKNODE_WS_URL')
QUICKNODE_API_KEY = os.getenv('QUICKNODE_API_KEY')

# Optimierte RPC-Endpoints mit Failover
SOLANA_RPC_ENDPOINTS = {
    'mainnet': [
        # Primary: QuickNode (Premium)
        RPCEndpoint(
            url=QUICKNODE_RPC_URL,
            ws_url=QUICKNODE_WS_URL,
            api_key=QUICKNODE_API_KEY,
            weight=1  # Highest priority
        ),
        # Backup: Orca's RPC
        RPCEndpoint(
            url="https://api.mainnet.orca.so/rpc",
            weight=2  # Second priority
        ),
        # Additional Fallbacks
        RPCEndpoint(
            url="https://rpc.ankr.com/solana",
            weight=3
        ),
        RPCEndpoint(
            url="https://api.mainnet-beta.solana.com",
            weight=4
        ),
        RPCEndpoint(
            url="https://solana-mainnet.rpc.extrnode.com",
            weight=5  # Lowest priority
        )
    ]
}

class RPCManager:
    def __init__(self, network: str = 'mainnet'):
        self.endpoints = SOLANA_RPC_ENDPOINTS[network]
        self.current_endpoint_index = 0
        self.health_check_interval = 30  # Sekunden
        self.session = None
        
    async def initialize(self):
        """Initialize RPC connection"""
        self.session = aiohttp.ClientSession()
        await self.check_endpoints_health()
        asyncio.create_task(self._periodic_health_check())
        
    async def get_healthy_endpoint(self) -> RPCEndpoint:
        """Get the best available RPC endpoint"""
        healthy_endpoints = [ep for ep in self.endpoints if ep.healthy]
        if not healthy_endpoints:
            # Reset health status if all endpoints are unhealthy
            for ep in self.endpoints:
                ep.healthy = True
            healthy_endpoints = self.endpoints
            
        # Sort by weight and response time
        return min(healthy_endpoints, key=lambda x: (x.weight, x.response_time))
        
    async def check_endpoints_health(self):
        """Check health of all endpoints"""
        for endpoint in self.endpoints:
            try:
                start_time = asyncio.get_event_loop().time()
                async with self.session.post(
                    endpoint.url,
                    json={"jsonrpc": "2.0", "id": 1, "method": "getHealth"},
                    timeout=5
                ) as response:
                    if response.status == 200:
                        endpoint.response_time = asyncio.get_event_loop().time() - start_time
                        endpoint.healthy = True
                        logger.debug(f"Endpoint {endpoint.url} healthy, response time: {endpoint.response_time:.3f}s")
                    else:
                        endpoint.healthy = False
                        logger.warning(f"Endpoint {endpoint.url} unhealthy: HTTP {response.status}")
            except Exception as e:
                endpoint.healthy = False
                logger.error(f"Endpoint {endpoint.url} check failed: {e}")
                
    async def _periodic_health_check(self):
        """Periodically check endpoint health"""
        while True:
            await asyncio.sleep(self.health_check_interval)
            await self.check_endpoints_health()
            
    async def close(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()

WHIRLPOOL_IDS = {
    'SOL/USDC': 'HJPjoWUrhoZzkNfRpHuieeFk9WcZWjwy6PBjZ81ngndJ'
}

API_HEADERS = {
    'Accept': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

ENVIRONMENTS = {
    'mainnet': {
        'endpoints': ORCA_ENDPOINTS,
        'rpcs': SOLANA_RPC_ENDPOINTS['mainnet']
    },
    'backtest': {
        'data_dir': Path('backtest_data'),
        'endpoints': ORCA_ENDPOINTS,
        'rpcs': SOLANA_RPC_ENDPOINTS['mainnet']
    }
}

# Rate Limiting Configuration
RATE_LIMITS = {
    'quicknode': {
        'requests_per_second': 100,
        'requests_per_minute': 6000,
        'concurrent_requests': 50
    },
    'orca': {
        'requests_per_second': 10,
        'requests_per_minute': 600,
        'concurrent_requests': 20
    },
    'ankr': {
        'requests_per_second': 5,
        'requests_per_minute': 300,
        'concurrent_requests': 15
    },
    'public': {
        'requests_per_second': 2,
        'requests_per_minute': 100,
        'concurrent_requests': 10
    }
}

# RPC Provider Types
RPC_PROVIDERS = {
    QUICKNODE_RPC_URL: 'quicknode',
    'api.mainnet.orca.so': 'orca',
    'rpc.ankr.com': 'ankr',
    'api.mainnet-beta.solana.com': 'public',
    'solana-mainnet.rpc.extrnode.com': 'public'
}