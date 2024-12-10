import asyncio
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
import os
from dotenv import load_dotenv

async def test_wallet():
    load_dotenv()
    wallet_address = os.getenv("WALLET_PUBLIC_KEY")
    client = AsyncClient("https://api.mainnet-beta.solana.com")
    
    try:
        print(f"\nTeste Wallet: {wallet_address}")
        
        # SOL Balance
        pubkey = Pubkey.from_string(wallet_address)
        balance = await client.get_balance(pubkey)
        sol_balance = balance.value / 1e9
        print(f"\nSOL Balance: {sol_balance:.4f} SOL")
        
        # Token Accounts mit korrekter Konfiguration
        token_program = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
        token_accounts = await client.get_token_accounts_by_owner(
            pubkey,
            {'programId': token_program},
            encoding="jsonParsed",  # Wichtig: Spezifiziere das Encoding
            commitment=Confirmed
        )
        
        print("\nToken Accounts:")
        if token_accounts and hasattr(token_accounts, 'value'):
            accounts = token_accounts.value
            if accounts:
                for account in accounts:
                    # Sicherer Zugriff auf die Daten
                    try:
                        parsed_info = account.account.data.parsed['info']
                        mint = parsed_info.get('mint', 'Unbekannt')
                        amount = parsed_info.get('tokenAmount', {}).get('uiAmount', 0)
                        print(f"Token: {mint}")
                        print(f"Balance: {amount}")
                        print("---")
                    except (AttributeError, KeyError) as e:
                        print(f"Fehler beim Parsen des Accounts: {e}")
            else:
                print("Keine Token Accounts gefunden")
        else:
            print("Keine Token-Daten verfügbar")
            
    except Exception as e:
        print(f"Fehler: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(test_wallet()) 