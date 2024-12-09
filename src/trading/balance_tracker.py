from dataclasses import dataclass
from datetime import datetime
import logging
from typing import Dict, Optional
import asyncio

logger = logging.getLogger(__name__)

@dataclass
class Balance:
    sol: float
    usdc: float
    last_update: datetime

class BalanceTracker:
    def __init__(self, wallet_config, solana_client):
        self.wallet_config = wallet_config
        self.solana = solana_client
        self.balance = Balance(0.0, 0.0, datetime.now())
        self.update_interval = 5  # Sekunden
        self.running = False
        
    async def start(self):
        """Start balance tracking"""
        try:
            # Validate wallet first
            if not await self.validate_wallet():
                raise ValueError("Wallet validation failed")
                
            self.running = True
            while self.running:
                await self.update_balances()
                await asyncio.sleep(self.update_interval)
                
        except Exception as e:
            logger.error(f"Balance tracker failed: {e}")
            self.running = False
                
    async def update_balances(self):
        """Update current balances"""
        try:
            # Get SOL balance using RPC call
            response = await self.solana.client.get_balance(
                self.wallet_config.get_pubkey(),
                commitment="confirmed"
            )
            sol_balance = float(response.value) / 1e9  # Convert lamports to SOL
            
            # Get USDC token account info
            usdc_response = await self.solana.client.get_token_account_balance(
                self.wallet_config.get_token_account('USDC')
            )
            usdc_balance = float(usdc_response.value.amount) / 1e6  # USDC has 6 decimals
            
            self.balance = Balance(
                sol=sol_balance,
                usdc=usdc_balance,
                last_update=datetime.now()
            )
            
            logger.info(f"Wallet {self.wallet_config.get_pubkey()}")
            logger.info(f"Balances updated - SOL: {sol_balance:.4f}, USDC: {usdc_balance:.2f}")
            
        except Exception as e:
            logger.error(f"Failed to update balances: {e}", exc_info=True)
            
    def get_available_sol(self) -> float:
        """Get available SOL for trading (minus gas reserve)"""
        return max(0, self.balance.sol - 0.01)  # Keep 0.01 SOL for gas
        
    def get_available_usdc(self) -> float:
        """Get available USDC for trading"""
        return self.balance.usdc
        
    def stop(self):
        """Stop balance tracking"""
        self.running = False 
        
    async def validate_wallet(self) -> bool:
        """Validate wallet configuration and accessibility"""
        try:
            pubkey = self.wallet_config.get_pubkey()
            logger.info(f"Checking wallet: {pubkey}")
            
            # Check if wallet exists
            response = await self.solana.client.get_account_info(pubkey)
            if not response.value:
                logger.error(f"Wallet not found: {pubkey}")
                return False
                
            # Check USDC token account
            usdc_account = self.wallet_config.get_token_account('USDC')
            token_response = await self.solana.client.get_account_info(usdc_account)
            if not token_response.value:
                logger.error(f"USDC token account not found: {usdc_account}")
                return False
                
            logger.info("Wallet validation successful")
            return True
            
        except Exception as e:
            logger.error(f"Wallet validation failed: {e}")
            return False 