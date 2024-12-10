import logging
from typing import Dict, Optional
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient
from anchorpy import Wallet
from orca_whirlpool.context import WhirlpoolContext
from src.models import TradeData
from rich.console import Console

console = Console()
logger = logging.getLogger(__name__)

class WalletManager:
    def __init__(self, keypair_path: Optional[str] = None):
        self.connection = AsyncClient("https://api.mainnet-beta.solana.com")
        
        # Lade Keypair
        if keypair_path:
            with open(keypair_path, 'r') as f:
                secret = bytes([int(b) for b in f.read().strip('[]').split(',')])
                self.keypair = Keypair.from_bytes(secret)
        else:
            self.keypair = Keypair()
            
        self.wallet = Wallet(self.keypair)
        
    async def get_sol_balance(self) -> float:
        """Holt SOL Balance"""
        try:
            balance = await self.connection.get_balance(self.keypair.pubkey())
            return balance / 1e9  # Lamports zu SOL
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der SOL Balance: {e}")
            return 0.0
            
    async def get_token_balances(self) -> Dict[str, float]:
        """Holt Token Balances"""
        try:
            token_accounts = await self.connection.get_token_accounts_by_owner(
                self.keypair.pubkey(),
                {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"}
            )
            
            balances = {}
            for ta in token_accounts.value:
                mint = ta.account.data["mint"]
                amount = ta.account.data["amount"]
                decimals = ta.account.data["decimals"]
                balances[str(mint)] = amount / (10 ** decimals)
                
            return balances
            
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Token Balances: {e}")
            return {}
            
    async def execute_swap(self, trade_data: TradeData) -> bool:
        """Führt einen Swap aus"""
        try:
            # Hole Pool
            whirlpool = await self.ctx.fetcher.get_whirlpool(
                Pubkey.from_string(trade_data.pool_address)
            )
            
            # Berechne Swap
            quote = await self.ctx.fetcher.get_quote(
                whirlpool,
                trade_data.amount_in,
                trade_data.side == "buy"
            )
            
            # Führe Swap aus
            tx = await self.ctx.swap(
                whirlpool,
                quote,
                self.keypair.pubkey()
            )
            
            # Warte auf Bestätigung
            await self.connection.confirm_transaction(tx)
            
            logger.info(f"Swap erfolgreich: {tx}")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Swap: {e}")
            return False
            
    async def close(self):
        """Schließt die Verbindung"""
        await self.connection.close()