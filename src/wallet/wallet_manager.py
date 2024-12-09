from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
import base58
from typing import Dict, Optional

class WalletManager:
    """Wallet Management & Interaktion"""
    
    def __init__(self, rpc_client: AsyncClient):
        self.rpc = rpc_client
        self.wallet = None
        self.balances = {}
        
    async def connect_wallet(self, private_key: str) -> bool:
        """Verbindet Wallet"""
        try:
            self.wallet = Keypair.from_base58_string(private_key)
            await self.update_balances()
            return True
        except Exception as e:
            logger.error(f"Wallet connection failed: {e}")
            return False
            
    async def update_balances(self):
        """Aktualisiert Wallet Balances"""
        try:
            sol_balance = await self.rpc.get_balance(self.wallet.pubkey())
            self.balances['SOL'] = sol_balance.value / 1e9
            
            # Token Balances
            token_accounts = await self.rpc.get_token_accounts_by_owner(
                self.wallet.pubkey(),
                {'programId': TOKEN_PROGRAM_ID}
            )
            
            for account in token_accounts.value:
                mint = account.account.data.parsed['info']['mint']
                amount = account.account.data.parsed['info']['tokenAmount']['uiAmount']
                self.balances[mint] = amount
                
        except Exception as e:
            logger.error(f"Balance update failed: {e}") 