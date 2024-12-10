import asyncio
from database.db_manager import DatabaseManager
from whirlpool_fetcher import WhirlpoolFetcher

async def test_database():
    # Initialisierung
    db = DatabaseManager()
    await db.init_db()
    
    # Teste Pool-Speicherung
    fetcher = WhirlpoolFetcher()
    await fetcher.initialize()
    await fetcher.fetch_and_store_pools()
    
    # Hole gespeicherte Pools
    pools = await db.get_active_pools()
    print(f"\nGespeicherte Pools: {len(pools)}")
    
    # Zeige Top 5 Pools nach Volumen
    sorted_pools = sorted(pools, key=lambda x: x['volume_24h'], reverse=True)
    print("\nTop 5 Pools nach Volumen:")
    for pool in sorted_pools[:5]:
        print(f"\nPool: SOL/{pool['token_b_symbol']}")
        print(f"Preis: ${pool['price']:.4f}")
        print(f"24h Volume: ${pool['volume_24h']:,.2f}")

if __name__ == "__main__":
    asyncio.run(test_database()) 