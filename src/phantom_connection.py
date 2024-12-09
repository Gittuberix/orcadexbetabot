import asyncio
from solana.rpc.async_api import AsyncClient
from rich.console import Console
import json

console = Console()

class PhantomConnector:
    def __init__(self):
        self.rpc = AsyncClient("https://api.mainnet-beta.solana.com")
        
    async def connect(self):
        """
        Verbindet mit Phantom Wallet über Browser Extension
        Erfordert dass Phantom installiert ist
        """
        try:
            # Phantom Connection Code hier
            # Dies erfordert Browser Integration
            pass
            
    async def get_wallet_data(self):
        """Holt Wallet Daten von Phantom"""
        try:
            # Wallet Address von Phantom holen
            # Dies würde normalerweise über Browser Extension gehen
            phantom_address = "YOUR_PHANTOM_WALLET_ADDRESS"
            
            # Balance prüfen
            response = await self.rpc.get_balance(phantom_address)
            balance = response['result']['value'] / 10**9
            
            console.print(f"[green]Connected to Phantom Wallet[/green]")
            console.print(f"Address: {phantom_address}")
            console.print(f"Balance: {balance} SOL")
            
            return {
                'address': phantom_address,
                'balance': balance
            }
            
        except Exception as e:
            console.print(f"[red]Error connecting to Phantom: {str(e)}[/red]")
            return None

async def main():
    phantom = PhantomConnector()
    await phantom.get_wallet_data()

if __name__ == "__main__":
    asyncio.run(main()) 