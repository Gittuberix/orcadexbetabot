from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from solana.transaction import Transaction
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from cachetools import TTLCache
import logging
import asyncio
from typing import Optional, Dict
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class SolanaClient:
    def __init__(self, rpc_manager):
        self.rpc_manager = rpc_manager
        self.client = None
        self.cache = TTLCache(maxsize=100, ttl=5)
        
    async def initialize(self):
        """Initialize Solana client"""
        try:
            endpoint = await self.rpc_manager.get_healthy_endpoint()
            self.client = AsyncClient(
                endpoint=endpoint.url,
                commitment=Confirmed
            )
            logger.info("Solana client initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Solana client: {e}")
            return False
            
    async def get_token_balance(self, token_account: str) -> Optional[float]:
        """Get token account balance"""
        try:
            response = await self.client.get_token_account_balance(token_account)
            if response.value:
                return float(response.value.amount) / (10 ** response.value.decimals)
        except Exception as e:
            logger.error(f"Failed to get token balance: {e}")
        return None
        
    async def get_sol_balance(self, address: str) -> Optional[float]:
        """Get SOL balance"""
        try:
            response = await self.client.get_balance(address)
            if response.value is not None:
                return float(response.value) / 1e9  # Convert lamports to SOL
        except Exception as e:
            logger.error(f"Failed to get SOL balance: {e}")
        return None
        
    async def send_transaction(self, transaction: Transaction, signers: list) -> Optional[str]:
        """Send transaction to network"""
        try:
            # Get recent blockhash
            blockhash = await self.client.get_recent_blockhash()
            transaction.recent_blockhash = blockhash.value.blockhash
            
            # Sign transaction
            for signer in signers:
                transaction.sign(signer)
                
            # Send transaction
            result = await self.client.send_transaction(
                transaction,
                *signers,
                opts={"skip_preflight": True}
            )
            
            return result.value  # Return signature
            
        except Exception as e:
            logger.error(f"Failed to send transaction: {e}")
            return None
            
    async def confirm_transaction(self, signature: str, max_retries: int = 30) -> bool:
        """Wait for transaction confirmation"""
        try:
            for _ in range(max_retries):
                response = await self.client.confirm_transaction(signature)
                if response.value:
                    return True
                await asyncio.sleep(1)
            return False
        except Exception as e:
            logger.error(f"Failed to confirm transaction: {e}")
            return False 