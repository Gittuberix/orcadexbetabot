import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from data_fetcher import DataFetcher

async def test_orca_connection():
    print("\n=== Testing Orca Connection ===")
    fetcher = DataFetcher()
    
    # Test pool data
    print("\nFetching pool data...")
    pool_data = await fetcher.get_pool_data()
    if pool_data:
        print("✅ Pool data fetched successfully")
        print(f"Current price: {pool_data.get('price', 'N/A')}")
    
    # Test historical data
    print("\nFetching historical data...")
    hist_data = await fetcher.get_historical_data(days=1)
    if hist_data is not None:
        print("✅ Historical data fetched successfully")
        print(f"Number of candles: {len(hist_data)}")
    
    # Test liquidity data
    print("\nFetching liquidity data...")
    liq_data = await fetcher.get_liquidity_data()
    if liq_data:
        print("✅ Liquidity data fetched successfully")

if __name__ == "__main__":
    asyncio.run(test_orca_connection()) 