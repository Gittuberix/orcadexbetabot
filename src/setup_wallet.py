import asyncio
from solders.keypair import Keypair
from solana.rpc.async_api import AsyncClient
from rich.console import Console
from config.wallet_config import save_wallet_config

console = Console()

async def setup_wallet():
    """Initialisiert die Wallet"""
    console.print("\n[cyan]Setting up Solana Wallet...[/cyan]")
    
    # Private Key eingeben
    private_key = console.input("[yellow]Enter your private key (base58): [/yellow]")
    
    try:
        # Wallet testen
        keypair = Keypair.from_base58_string(private_key)
        rpc = AsyncClient("https://api.mainnet-beta.solana.com")
        
        # Balance prüfen
        response = await rpc.get_balance(keypair.pubkey())
        balance = response['result']['value'] / 10**9
        
        console.print(f"[green]✓ Wallet loaded successfully[/green]")
        console.print(f"Address: {keypair.pubkey()}")
        console.print(f"Balance: {balance} SOL")
        
        # Konfiguration speichern
        save_wallet_config(private_key)
        console.print("[green]✓ Wallet configuration saved[/green]")
        
    except Exception as e:
        console.print(f"[red]Error setting up wallet: {str(e)}[/red]")

if __name__ == "__main__":
    asyncio.run(setup_wallet()) 