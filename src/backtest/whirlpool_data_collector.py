import asyncio
from pathlib import Path
from datetime import datetime
import pandas as pd
from typing import Dict

class WhirlpoolDataCollector:
    def __init__(self, fetcher: WhirlpoolFetcher):
        self.fetcher = fetcher
        self.data_dir = Path("data/historical")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    async def collect_pool_data(self, pool_address: str, duration_hours: int = 24):
        """Sammelt Pooldaten für Backtesting"""
        data_points = []
        interval = 60  # 1 Minute
        
        for _ in range(duration_hours * 60):
            pool_data = await self.fetcher.get_whirlpool_data(pool_address)
            if pool_data:
                data_points.append({
                    'timestamp': datetime.now().isoformat(),
                    **pool_data
                })
            await asyncio.sleep(interval)
            
        # Speichere Daten
        df = pd.DataFrame(data_points)
        df.to_parquet(self.data_dir / f"pool_{pool_address}_{datetime.now():%Y%m%d}.parquet") 
        
    async def collect_tick_data(self, pool_address: str):
        """Sammelt Tick-Daten für Backtesting"""
        ticks = await self.fetcher.get_pool_ticks(pool_address)
        if ticks:
            df = pd.DataFrame(ticks)
            df.to_parquet(
                self.data_dir / f"ticks_{pool_address}_{datetime.now():%Y%m%d}.parquet"
            )
            
    async def simulate_swap(self, 
        pool_data: Dict,
        amount_in: int,
        is_a_to_b: bool
    ) -> Dict:
        """Simuliert einen Swap für Backtesting"""
        sqrt_price = pool_data['sqrt_price']
        liquidity = pool_data['liquidity']
        
        # Simuliere Swap
        amount_out = self.fetcher._calculate_out_amount(
            sqrt_price,
            liquidity,
            amount_in,
            is_a_to_b
        )
        
        return {
            'amount_in': amount_in,
            'amount_out': amount_out,
            'price_before': (sqrt_price / (2 ** 64)) ** 2,
            'liquidity': liquidity
        } 