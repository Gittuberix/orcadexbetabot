import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from rich.console import Console
from src.backtest.data_manager import BacktestDataManager
from src.whirlpool.microscope import WhirlpoolMicroscope

console = Console()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_data_collection():
    try:
        # Setup
        data_manager = BacktestDataManager()
        microscope = WhirlpoolMicroscope()
        
        # Teste SOL/USDC Pool
        pool_address = microscope.pools["SOL/USDC"]
        
        # Sammle 1 Stunde Daten
        console.print("\n=== Starte Datensammlung ===")
        pool_states = await data_manager.collect_backtest_data(
            pool_address=pool_address,
            duration_hours=1,
            interval_seconds=5  # 5 Sekunden Intervall
        )
        
        if pool_states:
            console.print(f"\nGesammelte Datenpunkte: {len(pool_states)}")
            
            # Zeige Preisbereich
            prices = [float(state.price) for state in pool_states]
            console.print(f"\nPreisbereich:")
            console.print(f"Min: ${min(prices):.4f}")
            console.print(f"Max: ${max(prices):.4f}")
            console.print(f"Aktuell: ${prices[-1]:.4f}")
            
            # Zeige Liquiditätsbereich
            liquidity = [state.liquidity for state in pool_states]
            console.print(f"\nLiquiditätsbereich:")
            console.print(f"Min: {min(liquidity):,}")
            console.print(f"Max: {max(liquidity):,}")
            
            # Zeige einige Datenpunkte
            console.print("\nLetzte 5 Datenpunkte:")
            for state in pool_states[-5:]:
                console.print(f"\nZeit: {state.timestamp}")
                console.print(f"Preis: ${float(state.price):.4f}")
                console.print(f"Liquidität: {state.liquidity:,}")
                
    except Exception as e:
        logger.error(f"Fehler: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_data_collection()) 