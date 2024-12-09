from .quicknode_client import QuickNodeClient

class RPCManager:
    def __init__(self, network: str = 'mainnet'):
        self.quicknode = QuickNodeClient()
        self.endpoints = SOLANA_RPC_ENDPOINTS[network]
        self.current_endpoint = None
        self.session = None
        
    async def initialize(self):
        """Initialize connections"""
        # First try QuickNode
        if await self.quicknode.connect():
            self.current_endpoint = self.endpoints[0]  # QuickNode endpoint
        else:
            # Fallback to other endpoints
            await self._initialize_fallback()
            
    async def _initialize_fallback(self):
        """Initialize fallback endpoints"""
        self.session = aiohttp.ClientSession()
        await self.check_endpoints_health()
        asyncio.create_task(self._periodic_health_check()) 