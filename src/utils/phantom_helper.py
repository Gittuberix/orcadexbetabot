import json
from pathlib import Path
from rich.console import Console

console = Console()

def get_phantom_credentials():
    """Hilft bei der Einrichtung der Phantom Credentials"""
    console.print("\n[yellow]Phantom Wallet Setup[/yellow]")
    console.print("\n1. Öffne Phantom Wallet")
    console.print("2. Gehe zu Einstellungen -> Exportiere Private Key")
    console.print("3. Kopiere Public Key und Private Key")
    
    public_key = input("\nGib deine Public Key ein: ")
    private_key = input("Gib deinen Private Key ein: ")
    
    # Erstelle .env Datei
    env_content = f"""# Phantom Wallet Credentials
PHANTOM_PUBLIC_KEY={public_key}
PHANTOM_PRIVATE_KEY={private_key}

# RPC Endpoints
RPC_ENDPOINT=https://api.mainnet-beta.solana.com

# Backtest Settings
INITIAL_CAPITAL=1000
TRADE_SIZE=0.1
MAX_SLIPPAGE=0.01
"""
    
    with open(".env", "w") as f:
        f.write(env_content)
        
    console.print("\n[green]Credentials gespeichert in .env![/green]")

if __name__ == "__main__":
    get_phantom_credentials() 