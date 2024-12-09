from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.transaction import Transaction
from solana.rpc.commitment import Confirmed
from spl.token.instructions import get_associated_token_address
import base58
import json
from pathlib import Path
import logging
from typing import Optional, Dict
from dataclasses import dataclass
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

@dataclass
class TokenBalance:
    amount: float
    decimals: int
    
    @property
    def ui_amount(self) -> float:
        """Convert raw amount to human readable"""
        return self.amount / (10 ** self.decimals)

@dataclass
class WalletBalance:
    sol: TokenBalance
    tokens: Dict[str, TokenBalance]
    last_update: datetime

class PhantomWallet:
    def __init__(self, rpc_manager, config):
        self.rpc_manager = rpc_manager
        self.config = config
        self.keypair = None
        self.connected = False
        self.balance = None
        self.min_sol_balance = 0.05  # Minimum 0.05 SOL für Gas
        self.pending_transactions = {}
        self.token_accounts = {}
        
    async def connect(self, wallet_path: str = None) -> bool:
        """Connect and initialize wallet"""
        try:
            # Load wallet keypair
            if wallet_path:
                await self._load_wallet(wallet_path)
            else:
                # Use default path
                default_path = Path.home() / '.config/solana/phantom.json'
                await self._load_wallet(str(default_path))
                
            # Initialize RPC connection
            endpoint = await self.rpc_manager.get_healthy_endpoint()
            self.client = AsyncClient(endpoint.url, commitment=Confirmed)
            
            # Test connection and update balances
            await self.update_balances()
            logger.info(f"Wallet connected successfully: {self.get_public_key()}")
            self.connected = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect wallet: {e}")
            return False
            
    async def ensure_connection(self) -> bool:
        """Ensure wallet is connected and healthy"""
        now = datetime.now()
        if (now - self.last_health_check).seconds > self.health_check_interval:
            self.connected = await self._check_connection_health()
            self.last_health_check = now
            
        if not self.connected:
            return await self.reconnect()
            
        return True