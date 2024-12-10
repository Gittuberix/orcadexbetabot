import asyncio
from solana.rpc.async_api import AsyncClient
from src.whirlpool.microscope import WhirlpoolMicroscope
from src.config.orca_config import WHIRLPOOL_CONFIGS

async def test_microscope():
    connection = AsyncClient("https://api.mainnet-beta.solana.com")
    microscope = WhirlpoolMicroscope(connection)
    
    try:
        # 1. Teste Account Dump
        sol_usdc = WHIRLPOOL_CONFIGS["SOL/USDC"]["address"]
        account_data = await microscope.dump_account(
            sol_usdc,
            "sol_usdc_whirlpool.json"
        )
        print("\nAccount Data:", account_data)
        
        # 2. Teste Whirlpool Klonen
        success = await microscope.clone_whirlpool(
            sol_usdc,
            "cloned_pools"
        )
        print("\nWhirlpool Klon:", "Erfolgreich" if success else "Fehlgeschlagen")
        
        # 3. Teste Position Listing
        positions = await microscope.get_all_positions(sol_usdc)
        print(f"\nGefundene Positionen: {len(positions)}")
        for pos in positions[:3]:  # Zeige erste 3
            print(f"\nPosition {pos['address']}:")
            print(f"Token A Balance: {pos['token_a_balance']}")
            print(f"Token B Balance: {pos['token_b_balance']}")
            
        # 4. Teste Test-Token Erstellung
        success = await microscope.create_test_tokens(
            WHIRLPOOL_CONFIGS["SOL/USDC"]["token_a"],
            int(100 * 1e9)  # 100 SOL
        )
        print("\nTest-Token Erstellung:", "Erfolgreich" if success else "Fehlgeschlagen")
        
    finally:
        await connection.close()

if __name__ == "__main__":
    asyncio.run(test_microscope()) 