import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
from whirlpool_fetcher import WhirlpoolFetcher
from database.db_manager import DatabaseManager
from backtest.whirlpool_data_collector import WhirlpoolDataCollector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_backtest_with_db():
    # Initialisierung
    db = DatabaseManager()
    fetcher = WhirlpoolFetcher()
    collector = WhirlpoolDataCollector(fetcher)
    
    print("\n=== Datenbank-Test ===")
    await db.init_db()
    await fetcher.initialize()
    
    # Hole historische Daten
    print("\n=== Lade historische Daten ===")
    pools = await db.get_active_pools()
    if not pools:
        print("Keine Pools in der Datenbank, lade neue Daten...")
        await fetcher.fetch_and_store_pools()
        pools = await db.get_active_pools()
    
    print(f"Gefundene Pools: {len(pools)}")
    
    # Wähle SOL/USDC Pool für Backtest
    sol_usdc = next(
        (p for p in pools if p['token_a'] == fetcher.tokens["SOL"] and 
         p['token_b'] == fetcher.tokens["USDC"]),
        None
    )
    
    if not sol_usdc:
        print("SOL/USDC Pool nicht gefunden!")
        return
        
    print("\n=== Pool Details ===")
    print(f"Address: {sol_usdc['address']}")
    print(f"Aktueller Preis: ${sol_usdc['price']:.4f}")
    print(f"24h Volume: ${sol_usdc['volume_24h']:,.2f}")
    
    # Sammle neue Daten für Backtest
    print("\n=== Sammle neue Daten für Backtest ===")
    await collector.collect_pool_data(sol_usdc['address'], duration_hours=1)
    
    # Lade und analysiere Daten
    data_file = next(collector.data_dir.glob(f"pool_{sol_usdc['address']}_*.parquet"))
    df = pd.read_parquet(data_file)
    
    print("\n=== Backtest Daten ===")
    print(f"Datenpunkte: {len(df)}")
    print(f"Zeitraum: {df['timestamp'].min()} bis {df['timestamp'].max()}")
    print(f"Durchschnittspreis: ${df['price'].mean():.4f}")
    print(f"Min Preis: ${df['price'].min():.4f}")
    print(f"Max Preis: ${df['price'].max():.4f}")
    
    # Speichere Daten in der DB
    print("\n=== Speichere neue Preisdaten ===")
    for _, row in df.iterrows():
        await db.save_pool({
            'address': sol_usdc['address'],
            'tokenA': sol_usdc['token_a'],
            'tokenB': sol_usdc['token_b'],
            'price': row['price'],
            'liquidity': row['liquidity'],
            'volume24h': sol_usdc['volume_24h']
        })
    
    print("\n✅ Backtest-Daten erfolgreich geladen und gespeichert!")
    
    await fetcher.client.close()

if __name__ == "__main__":
    asyncio.run(run_backtest_with_db()) 