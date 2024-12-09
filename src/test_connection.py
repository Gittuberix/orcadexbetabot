import asyncio
from solders.keypair import Keypair
from solana.rpc.async_api import AsyncClient
from rich.console import Console
import base58

console = Console()

async def test_with_wallet():
    # Private Key (NICHT den echten Key committen!)
    private_key = "YOUR_PRIVATE_KEY_HERE"  # Base58 encoded
    
    try:
        # Wallet erstellen
        keypair = Keypair.from_base58_string(private_key)
        
        # RPC Client
        rpc = AsyncClient("https://api.mainnet-beta.solana.com")
        
        # Balance prüfen
        response = await rpc.get_balance(keypair.pubkey())
        balance = response['result']['value'] / 10**9  # Convert lamports to SOL
        console.print(f"[green]Wallet Balance: {balance} SOL[/green]")
        
        # Whirlpool Daten abrufen
        sol_usdc_pool = "7qbRF6YsyGuLUVs6Y1q64bdVrfe4ZcUUz1JRdoVNUJpi"
        response = await rpc.get_account_info(sol_usdc_pool)
        if response['result']['value']:
            console.print("[green]✓ SOL-USDC pool data available[/green]")
            
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")

if __name__ == "__main__":
    asyncio.run(test_with_wallet()) 