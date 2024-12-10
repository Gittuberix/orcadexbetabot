import aiohttp
import asyncio
import pandas as pd
from datetime import datetime, timedelta
import json
from colorama import init, Fore, Style

init()

class DataCollector:
    def __init__(self):
        self.orca_api = "https://api.mainnet.orca.so"
        self.cache = {}
        
    async def get_historical_data(self, date: datetime, pool_ids: list):
        """Fetch historical data for backtesting"""
        results = {}
        
        async with aiohttp.ClientSession() as session:
            for pool_id in pool_ids:
                # Check cache first
                cache_key = f"{pool_id}_{date.date()}"
                if cache_key in self.cache:
                    results[pool_id] = self.cache[cache_key]
                    continue
                    
                # Fetch from API
                url = f"{self.orca_api}/v1/whirlpool/{pool_id}/candles"
                params = {
                    'resolution': '1m',
                    'start': int(date.timestamp()),
                    'end': int((date + timedelta(days=1)).timestamp())
                }
                
                try:
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            processed_data = self._process_candle_data(data)
                            self.cache[cache_key] = processed_data
                            results[pool_id] = processed_data
                except Exception as e:
                    logger.error(f"Error fetching historical data: {e}")
                    
        return results
        
    def _process_candle_data(self, raw_data):
        """Process raw candle data into usable format"""
        df = pd.DataFrame(raw_data)
        df['timestamp'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('timestamp', inplace=True)
        return df

async def main():
    print(f"{Fore.MAGENTA}🔍 Starting Historical Data Collection{Style.RESET_ALL}")
    
    collector = DataCollector()
    await collector.get_historical_data()

if __name__ == "__main__":
    asyncio.run(main()) 