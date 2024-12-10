from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from solders.keypair import Keypair
from solders.pubkey import Pubkey
import logging
from typing import Optional
from ..config.settings import RPC_ENDPOINTS, WALLET_PUBLIC_KEY

logger = logging.getLogger(__name__)

class SolanaClient:
    def __init__(self):
        self.client = None
        self.pubkey = Pubkey.from_string(WALLET_PUBLIC_KEY)
        
    async def connect(self) -> bool:
        """Connect to Solana network"""
        try:
            # Try QuickNode first
            self.client = AsyncClient(
                RPC_ENDPOINTS['quicknode'],
                commitment=Confirmed
            )
            await self.client.get_health()
            logger.info("Connected to QuickNode")
            return True
            
        except Exception as e:
            logger.warning(f"QuickNode connection failed: {e}")
            try:
                # Fallback to backup RPC
                self.client = AsyncClient(
                    RPC_ENDPOINTS['backup'],
                    commitment=Confirmed
                )
                await self.client.get_health()
                logger.info("Connected to backup RPC")
                return True
                
            except Exception as e:
                logger.error(f"All RPC connections failed: {e}")
                return False
                
    async def get_sol_balance(self) -> Optional[float]:
        """Get SOL balance"""
        try:
            response = await self.client.get_balance(self.pubkey)
            return float(response.value) / 1e9  # Convert lamports to SOL
        except Exception as e:
            logger.error(f"Failed to get SOL balance: {e}")
            return None
            
    async def get_token_balance(self, token_account: str) -> Optional[float]:
        """Get token balance"""
        try:
            response = await self.client.get_token_account_balance(token_account)
            if response.value:
                return float(response.value.amount) / (10 ** response.value.decimals)
            return None
        except Exception as e:
            logger.error(f"Failed to get token balance: {e}")
            return None
            
    async def close(self):
        """Close connection"""
        if self.client:
            await self.client.close() 