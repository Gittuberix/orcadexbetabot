import asyncio
import logging
from datetime import datetime, timedelta
import pandas as pd
from pathlib import Path
from typing import Dict, List
from src.data.orca_pipeline import OrcaWhirlpoolPipeline

logger = logging.getLogger(__name__)

class HistoricalDataManager:
    def __init__(self):
        self.pipeline = OrcaWhirlpoolPipeline()
        self.data_dir = Path("data/historical")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.timeframes = {
            '1m': 60,
            '5m': 300,
            '15m': 900,
            '1h': 3600,
            '4h': 14400,
            '1d': 86400
        }
        
    def _get_historical_file_path(self, pool_address: str, timeframe: str, date: datetime) -> Path:
        """Generiert den Dateipfad für historische Daten"""
        return self.data_dir / f"pool_{pool_address}_{timeframe}_{date:%Y%m%d}.parquet"
        
    async def fast_forward_historical_data(self, 
        pool_address: str,
        start_time: datetime,
        end_time: datetime,
        timeframe: str = '1m'
    ) -> pd.DataFrame:
        """Simuliert historische Daten durch "Vorspulen" der Zeit"""
        interval_seconds = self.timeframes[timeframe]
        current_time = start_time
        data_points = []
        
        while current_time <= end_time:
            # Hole Pool-Daten
            pool_data = await self.pipeline.get_pool_data(pool_address)
            if pool_data:
                data_point = {
                    'timestamp': current_time.isoformat(),
                    'price': pool_data['price'],
                    'liquidity': pool_data['liquidity'],
                    'volume_24h': pool_data['volume_24h']
                }
                data_points.append(data_point)
            
            # Springe zum nächsten Zeitpunkt
            current_time += timedelta(seconds=interval_seconds)
            
        df = pd.DataFrame(data_points)
        
        # Speichere die Daten
        file_path = self._get_historical_file_path(pool_address, timeframe, start_time)
        df.to_parquet(file_path)
        
        return df
        
    async def get_historical_data(self,
        pool_address: str,
        start_time: datetime,
        end_time: datetime,
        timeframe: str = '1m'
    ) -> pd.DataFrame:
        """Holt historische Daten, entweder aus Cache oder durch Fast-Forward"""
        file_path = self._get_historical_file_path(pool_address, timeframe, start_time)
        
        if file_path.exists():
            # Lade aus Cache
            return pd.read_parquet(file_path)
        else:
            # Generiere neue Daten
            return await self.fast_forward_historical_data(
                pool_address,
                start_time,
                end_time,
                timeframe
            )
            
    async def prepare_backtest_data(self,
        start_time: datetime,
        end_time: datetime,
        min_volume: float = 100000,  # $100k Mindestvolumen
        timeframe: str = '1m'
    ) -> Dict[str, pd.DataFrame]:
        """Bereitet Backtest-Daten für alle relevanten Pools vor"""
        
        # Hole Top Pools
        top_pools = await self.pipeline.fetch_all_whirlpools()
        
        # Filtere nach Volumen
        active_pools = [
            pool for pool in top_pools
            if float(pool.get('volume24h', 0)) >= min_volume
        ]
        
        # Sammle Daten für jeden Pool
        pool_data = {}
        for pool in active_pools:
            try:
                df = await self.get_historical_data(
                    pool['address'],
                    start_time,
                    end_time,
                    timeframe
                )
                pool_data[pool['address']] = df
                logger.info(f"Daten geladen für {pool['tokenA']['symbol']}/{pool['tokenB']['symbol']}")
            except Exception as e:
                logger.error(f"Fehler beim Laden der Daten für Pool {pool['address']}: {e}")
                
        return pool_data 