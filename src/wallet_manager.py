import logging
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.transaction import Transaction
from solana.rpc.commitment import Confirmed
import json
from pathlib import Path
from rich.console import Console
from typing import Optional, Dict

console = Console()
logger = logging.getLogger(__name__)

class WalletManager:
    def __init__(self, rpc_client: AsyncClient):
        self.rpc = rpc_client
        self.public_key = None
        self.balances = {}
        self.token_accounts = {}
        
    async def connect(self, config_path: str = 'config/wallet_config.json') -> bool:
        """Verbindet mit Wallet über Konfiguration"""
        try:
            # Config laden
            config_file = Path(config_path)
            if not config_file.exists():
                raise Exception("Wallet config not found")
                
            with open(config_file) as f:
                config = json.load(f)
                
            # Public Key setzen
            self.public_key = Pubkey.from_string(config['public_key'])
            
            # Balance prüfen
            await self.update_balances()
            
            console.print(f"[green]Connected to wallet: {self.public_key}[/green]")
            console.print(f"SOL Balance: {self.balances.get('SOL', 0):.4f}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect wallet: {e}")
            return False
            
    async def update_balances(self):
        """Aktualisiert Wallet Balances"""
        if not self.public_key:
            return
            
        try:
            # SOL Balance
            response = await self.rpc.get_balance(self.public_key)
            self.balances['SOL'] = float(response.value) / 1e9  # Lamports zu SOL
            
            # Token Accounts
            response = await self.rpc.get_token_accounts_by_owner(
                self.public_key,
                {'programId': TOKEN_PROGRAM_ID}
            )
            
            for account in response.value:
                mint = account.account.data.parsed['info']['mint']
                amount = account.account.data.parsed['info']['tokenAmount']['uiAmount']
                self.token_accounts[mint] = account.pubkey
                self.balances[mint] = amount
                
        except Exception as e:
            logger.error(f"Failed to update balances: {e}")
            
    def get_public_key(self) -> Optional[Pubkey]:
        """Gibt Public Key zurück"""
        return self.public_key
        
    def get_balance(self, token: str = 'SOL') -> float:
        """Gibt Balance für Token zurück"""
        return self.balances.get(token, 0)

# Test
async def main():
    # RPC Client
    rpc = AsyncClient("https://api.mainnet-beta.solana.com")
    
    # Wallet Manager
    wallet = WalletManager(rpc)
    
    # Verbinden
    if await wallet.connect():
        # Balances anzeigen
        console.print("\n[cyan]Wallet Balances:[/cyan]")
        for token, balance in wallet.balances.items():
            console.print(f"{token}: {balance:.4f}")
    else:
        console.print("[red]Failed to connect wallet[/red]")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())