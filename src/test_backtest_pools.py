import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from rich.console import Console
from whirlpool.pool_fetcher import WhirlpoolFetcher
from src.models import Trade, PoolState

console = Console()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_backtest_data():
    fetcher = WhirlpoolFetcher()
    
    try:
        print("\n=== Teste Whirlpool Daten für Backtest ===")
        
        # 1. Teste einzelnen Pool
        sol_usdc = fetcher.pools["SOL/USDC"]
        pool_data = await fetcher.get_pool_data(sol_usdc)
        
        if pool_data:
            print("\nSOL/USDC Details:")
            print(f"Preis: ${pool_data['price']:.4f}")
            print(f"Liquidität: {pool_data['liquidity']}")
            print("\nTick Arrays:")
            for ta in pool_data['tick_arrays']:
                print(f"Start Tick: {ta['start_tick']}, Ticks: {ta['ticks']}")
                
            # Simuliere Trades
            print("\nSimuliere Trades...")
            
            # Beispiel Trade Parameter
            amount_in = Decimal("0.1")  # 0.1 SOL
            amount_in_lamports = int(amount_in * 1e9)  # Convert to lamports
            
            # Simuliere mehrere Trades
            trades = []
            
            # Long Trade (Buy SOL with USDC)
            long_trade = Trade(
                timestamp=datetime.now(),
                pool_address=sol_usdc,
                side='buy',
                amount_in=amount_in_lamports,
                amount_out=int(amount_in_lamports * pool_data['price']),  # Geschätzter USDC Output
                price=pool_data['price'],
                fee=pool_data['fee_rate'],
                slippage=Decimal("0.01"),  # 1% slippage
                success=True
            )
            trades.append(long_trade)
            
            # Short Trade (Sell SOL for USDC)
            short_trade = Trade(
                timestamp=datetime.now() + timedelta(minutes=5),
                pool_address=sol_usdc,
                side='sell',
                amount_in=amount_in_lamports,
                amount_out=int(amount_in_lamports * pool_data['price'] * Decimal("0.99")),  # Mit Slippage
                price=pool_data['price'],
                fee=pool_data['fee_rate'],
                slippage=Decimal("0.01"),
                success=True
            )
            trades.append(short_trade)
            
            print("\nSimulierte Trades:")
            for trade in trades:
                print(f"\nTrade {trade.side.upper()}:")
                print(f"Zeitpunkt: {trade.timestamp}")
                print(f"Amount In: {trade.amount_in / 1e9:.4f} SOL")
                print(f"Amount Out: ${trade.amount_out / 1e6:.2f} USDC")
                print(f"Preis: ${trade.price:.4f}")
                print(f"Fee: {trade.fee / 10000:.2%}")
                
        # 2. Teste alle Pools
        print("\nLade alle Pools...")
        all_pools = await fetcher.get_all_pools()
        
        print(f"\nGeladene Pools: {len(all_pools)}")
        
        # 3. Teste Position Tracking
        print("\nLade Pool Positionen...")
        for name, pool in all_pools.items():
            positions = await fetcher.get_pool_positions(pool['address'])
            print(f"\n{name} Positionen: {len(positions)}")
            
            # Zeige erste 3 Positionen
            for pos in positions[:3]:
                print(f"\nPosition {pos['address'][:8]}...")
                print(f"Liquidität: {pos['liquidity']}")
                print(f"Tick Range: {pos['tick_lower']} - {pos['tick_upper']}")
        
        # 4. Teste Preis-Monitoring
        print("\nStarte Preis-Monitoring (30 Sekunden)...")
        
        async def price_callback(name, data):
            print(f"{name}: ${data['price']:.4f}")
            
        monitor_task = asyncio.create_task(
            fetcher.monitor_pools(price_callback)
        )
        
        await asyncio.sleep(30)
        monitor_task.cancel()
        
    finally:
        await fetcher.connection.close()

if __name__ == "__main__":
    asyncio.run(test_backtest_data()) 