from .solana_client import SolanaClient
from .quicknode_client import QuickNodeClient

class ConnectionManager:
    def __init__(self, network='mainnet'):
        self.network = network
        self.solana = None
        self.quicknode = None
        
    async def initialize(self):
        """Initialize all connections"""
        # Initialize QuickNode
        self.quicknode = QuickNodeClient()
        await self.quicknode.connect()
        
        # Initialize Solana client
        self.solana = SolanaClient(self.quicknode)
        await self.solana.initialize()
        
    async def close(self):
        """Close all connections"""
        if self.quicknode:
            await self.quicknode.close()
        if self.solana:
            await self.solana.close() 