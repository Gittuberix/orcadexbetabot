import asyncio
import os
from solders.keypair import Keypair
from trading.orca_trader import OrcaTrader
from dotenv import load_dotenv

async def test_trading():
    load_dotenv()
    
    # Lade Wallet (NICHT den Private Key committen!)
    keypair = Keypair.from_bytes(bytes.fromhex(os.getenv("WALLET_PRIVATE_KEY")))
    
    # Initialisiere Trader
    trader = OrcaTrader(keypair)
    
    # SOL/USDC Pool
    pool_address = "HJPjoWUrhoZzkNfRpHuieeFk9WcZWjwy6PBjZ81ngndJ"
    
    # Hole Pool-Info
    pool_info = await trader.get_pool_info(pool_address)
    print("\nPool Details:")
    print(f"Aktueller Preis: ${pool_info['price']:.4f}")
    print(f"Liquidität: {pool_info['liquidity']}")
    
    # Simuliere Swap (0.1 SOL zu USDC)
    amount_in = int(0.1 * 1e9)  # 0.1 SOL in Lamports
    quote = await trader.simulate_swap(pool_address, amount_in, True)
    
    if quote:
        print("\nSwap Simulation:")
        print(f"Input: 0.1 SOL")
        print(f"Output: ${quote['amount_out']/1e6:.2f} USDC")
        print(f"Preis-Impact: {quote['price_impact']:.2%}")
        print(f"Gebühren: ${quote['fee']/1e6:.4f} USDC")
        
        # Führe echten Swap aus (nur wenn gewünscht)
        if input("\nSwap ausführen? (y/n): ").lower() == 'y':
            success = await trader.execute_swap(pool_address, amount_in, True)
            if success:
                print("✅ Swap erfolgreich!")
            else:
                print("❌ Swap fehlgeschlagen!")

async def test_advanced_trading():
    trader = OrcaTrader(keypair)
    pool = "HJPjoWUrhoZzkNfRpHuieeFk9WcZWjwy6PBjZ81ngndJ"  # SOL/USDC
    
    # Teste Pool-Gesundheit
    is_healthy, message = await trader.check_pool_health(pool)
    print(f"\nPool Gesundheit: {message}")
    
    if is_healthy:
        # Simuliere Swap
        quote = await trader.simulate_swap(pool, int(0.1 * 1e9), True)
        if quote:
            print("\nSimulation erfolgreich:")
            print(f"Erwarteter Output: ${quote['amount_out']/1e6:.2f} USDC")
            print(f"Preis-Impact: {quote['price_impact']:.2%}")
            
            # Teste Dry-Run
            result = await trader.execute_swap(pool, int(0.1 * 1e9), True, dry_run=True)
            print("\nDry-Run Ergebnis:", result)

if __name__ == "__main__":
    asyncio.run(test_trading()) 