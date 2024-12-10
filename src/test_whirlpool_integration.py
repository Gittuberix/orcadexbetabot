import asyncio
from data.orca_pipeline import OrcaWhirlpoolPipeline

async def test_whirlpool():
    pipeline = OrcaWhirlpoolPipeline()
    
    # Teste SOL/USDC Pool
    pool_data = await pipeline.fetch_pool_data(pipeline.known_pools["SOL/USDC"])
    
    print("\nSOL/USDC Pool Details:")
    print(f"Preis: ${pool_data['price']:.4f}")
    print(f"Tick Spacing: {pool_data['tick_spacing']}")
    print(f"Aktueller Tick: {pool_data['tick_current']}")
    print(f"Liquidität: {pool_data['liquidity']}")
    
    print("\nLiquiditätsverteilung:")
    for ld in pool_data['liquidity_distribution'][:5]:  # Zeige erste 5
        print(f"Ticks {ld['tick_lower']} - {ld['tick_upper']}: {ld['liquidity']}")

if __name__ == "__main__":
    asyncio.run(test_whirlpool()) 