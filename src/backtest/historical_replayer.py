import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd
from pathlib import Path
import subprocess
import json
from colorama import init, Fore, Style
from solders.pubkey import Pubkey
from orca_whirlpool.context import WhirlpoolContext
from orca_whirlpool.utils import PriceMath, DecimalUtil

init()
logger = logging.getLogger(__name__)

class WhirlpoolReplayer:
    def __init__(self, data_dir: Path = Path("data/historical")):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.replayer_path = Path("whirlpool-tx-replayer")
        
    async def setup_replayer(self):
        """Klont und setzt den Replayer auf"""
        if not self.replayer_path.exists():
            print(f"{Fore.CYAN}Klone Whirlpool-TX-Replayer...{Style.RESET_ALL}")
            subprocess.run([
                "git", "clone", 
                "https://github.com/orca-so/whirlpool-tx-replayer.git"
            ])
            
            # Setup
            subprocess.run(["npm", "install"], cwd=self.replayer_path)
            subprocess.run(["npm", "run", "build"], cwd=self.replayer_path)

    async def fetch_historical_data(self, 
        pool_address: str,
        start_time: datetime,
        end_time: datetime
    ) -> pd.DataFrame:
        """Holt historische Daten mit dem Replayer und Whirlpool SDK"""
        try:
            # Hole Pool-Konfiguration
            whirlpool = await self.ctx.fetcher.get_whirlpool(Pubkey.from_string(pool_address))
            decimals_a = (await self.ctx.fetcher.get_token_mint(whirlpool.token_mint_a)).decimals
            decimals_b = (await self.ctx.fetcher.get_token_mint(whirlpool.token_mint_b)).decimals
            
            # Hole historische Trades
            trades = await self.replayer.get_historical_trades(
                pool_address,
                start_time,
                end_time
            )
            
            # Konvertiere zu DataFrame
            df = pd.DataFrame(trades)
            if df.empty:
                return df
                
            # Berechne Preise
            df['price'] = df['sqrt_price'].apply(
                lambda x: float(DecimalUtil.to_fixed(
                    PriceMath.sqrt_price_x64_to_price(x, decimals_a, decimals_b),
                    decimals_b
                ))
            )
            
            return df
            
        except Exception as e:
            logger.error(f"Fehler beim Abrufen historischer Daten: {e}")
            return pd.DataFrame()

    def process_replay_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Verarbeitet die Replay-Daten für den Backtest"""
        if df.empty:
            return df
            
        # Berechne zusätzliche Metriken
        df['price'] = df['sqrtPrice'].apply(lambda x: (x / (2 ** 64)) ** 2)
        df['volume'] = df.apply(
            lambda row: abs(row['tokenAAmount'] * row['price']) 
            if row['tokenAAmount'] else abs(row['tokenBAmount']),
            axis=1
        )
        
        # Resampling auf 1-Minuten-Candlesticks
        ohlc = df.resample('1T', on='timestamp').agg({
            'price': ['first', 'max', 'min', 'last'],
            'volume': 'sum',
            'liquidity': 'last'
        })
        
        ohlc.columns = ['open', 'high', 'low', 'close', 'volume', 'liquidity']
        return ohlc.reset_index() 