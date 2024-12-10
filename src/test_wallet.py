import sys
from pathlib import Path
root_dir = str(Path(__file__).parent.parent)
sys.path.insert(0, root_dir)

import asyncio
import logging
from rich.console import Console
from src.wallet_manager import WalletManager
from solders.pubkey import Pubkey

console = Console()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_wallet():
    wallet = None
    try:
        console.print("\n[cyan]=== Teste Phantom Wallet Integration ===[/cyan]")
        
        # 1. Initialisiere Wallet
        console.print("\n1. Initialisiere Wallet...")
        wallet = WalletManager()
        
        # 2. Verifiziere Public Key
        pubkey = wallet.get_public_key()
        console.print(f"\n2. Public Key: {pubkey}")
        
        # Prüfe bekannte Token Addresses
        USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
        SOL_MINT = "So11111111111111111111111111111111111111112"
        
        # 3. Hole SOL Balance
        sol_balance = await wallet.get_sol_balance()
        console.print(f"\n3. SOL Balance: {sol_balance:.4f} SOL")
        
        # 4. Hole Token Balances
        token_balances = await wallet.get_token_balances()
        console.print("\n4. Token Balances:")
        
        # Zeige bekannte Token zuerst
        if USDC_MINT in token_balances:
            console.print(f"USDC: ${token_balances[USDC_MINT]:.2f}")
        
        # Zeige andere Token
        for mint, amount in token_balances.items():
            if mint not in [USDC_MINT, SOL_MINT]:
                console.print(f"{mint}: {amount}")
                
        # 5. Teste RPC Verbindung
        console.print("\n5. RPC Verbindung:")
        slot = await wallet.connection.get_slot()
        console.print(f"Aktueller Slot: {slot}")
        
        console.print("\n[green]✓ Wallet Test erfolgreich![/green]")
            
    except Exception as e:
        console.print(f"\n[red]✗ Fehler: {e}[/red]")
        import traceback
        traceback.print_exc()
    finally:
        if wallet:
            await wallet.close()

if __name__ == "__main__":
    asyncio.run(test_wallet())