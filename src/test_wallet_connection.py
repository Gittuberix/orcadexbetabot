import asyncio
import logging
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient
import os
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WalletConnectionTester:
    def __init__(self):
        load_dotenv()
        self.wallet_address = os.getenv("WALLET_PUBLIC_KEY")
        if not self.wallet_address:
            raise ValueError("WALLET_PUBLIC_KEY nicht in .env gefunden")
            
        self.client = AsyncClient("https://api.mainnet-beta.solana.com")
        
    async def test_connection(self):
        """Testet die Verbindung zur Wallet"""
        try:
            # Test 1: Wallet-Balance
            print("\n=== Wallet Balance Test ===")
            balance = await self.client.get_balance(Pubkey(self.wallet_address))
            sol_balance = balance['result']['value'] / 1e9
            print(f"SOL Balance: {sol_balance:.4f} SOL")
            
            # Test 2: Token Accounts
            print("\n=== Token Accounts Test ===")
            token_accounts = await self.client.get_token_accounts_by_owner(
                Pubkey(self.wallet_address),
                {'programId': Pubkey('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')}
            )
            
            if token_accounts['result']['value']:
                print("\nGefundene Token Accounts:")
                for account in token_accounts['result']['value']:
                    mint = account['account']['data']['parsed']['info']['mint']
                    amount = account['account']['data']['parsed']['info']['tokenAmount']['uiAmount']
                    print(f"Token: {mint}")
                    print(f"Balance: {amount}")
                    print("---")
            else:
                print("Keine Token Accounts gefunden")
                
            # Test 3: Letzte Transaktionen
            print("\n=== Letzte Transaktionen ===")
            transactions = await self.client.get_signatures_for_address(
                Pubkey(self.wallet_address),
                limit=5
            )
            
            if transactions['result']:
                print("\nLetzte 5 Transaktionen:")
                for tx in transactions['result']:
                    print(f"Signature: {tx['signature']}")
                    print(f"Slot: {tx['slot']}")
                    print(f"Error: {tx.get('err', 'None')}")
                    print("---")
            else:
                print("Keine Transaktionen gefunden")
                
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Wallet-Test: {e}")
            return False
        
    async def close(self):
        await self.client.close()

async def main():
    tester = WalletConnectionTester()
    try:
        print(f"Teste Verbindung zu Wallet: {tester.wallet_address}")
        success = await tester.test_connection()
        if success:
            print("\n✅ Wallet-Verbindung erfolgreich getestet!")
        else:
            print("\n❌ Wallet-Verbindung fehlgeschlagen!")
    finally:
        await tester.close()

if __name__ == "__main__":
    asyncio.run(main()) 