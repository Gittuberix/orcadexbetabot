import asyncio
from phantom_connector import PhantomConnector
from wallet_manager import WalletManager
import threading
import time

async def test_phantom_connection():
    # Starte Phantom Connector in separatem Thread
    connector = PhantomConnector()
    thread = threading.Thread(target=connector.start)
    thread.daemon = True
    thread.start()
    
    print("\n=== Phantom Wallet Verbindung ===")
    print("1. Öffne http://localhost:5000 im Browser")
    print("2. Klicke auf 'Wallet verbinden'")
    print("3. Bestätige in Phantom\n")
    
    # Warte auf Verbindung
    for _ in range(30):  # 30 Sekunden Timeout
        if connector.get_public_key():
            break
        await asyncio.sleep(1)
        
    if not connector.get_public_key():
        print("❌ Timeout: Keine Verbindung hergestellt")
        return
        
    # Teste Wallet Manager mit Phantom Key
    wallet = WalletManager()
    success = await wallet.connect_phantom()
    
    if success:
        print("\n✅ Wallet erfolgreich verbunden!")
        accounts = await wallet.get_token_accounts()
        print(f"\nGefundene Token Accounts: {len(accounts)}")
    else:
        print("\n❌ Wallet-Verbindung fehlgeschlagen")

if __name__ == "__main__":
    asyncio.run(test_phantom_connection()) 