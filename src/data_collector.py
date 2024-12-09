import aiohttp
import asyncio
import pandas as pd
from datetime import datetime, timedelta
import json
from colorama import init, Fore, Style

init()

class HistoricalDataCollector:
    def __init__(self):
        self.ENDPOINTS = {
            'orca': "https://api.mainnet.orca.so",
            'jupiter': "https://price.jup.ag/v4",
            'birdeye': "https://public-api.birdeye.so"
        }
        
        self.WHIRLPOOL_ID = "7qbRF6YsyGuLUVs6Y1q64bdVrfe4ZcUUz1JRdoVNUJpi"  # SOL/USDC
        
    async def fetch_historical_data(self, days: int = 30):
        """Fetch historical price data"""
        print(f"{Fore.YELLOW}Fetching {days} days of historical data...{Style.RESET_ALL}")
        
        all_data = []
        
        async with aiohttp.ClientSession() as session:
            # Fetch from multiple sources for redundancy
            tasks = [
                self.fetch_orca_data(session, days),
                self.fetch_jupiter_data(session, days),
                self.fetch_birdeye_data(session, days)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for data in results:
                if isinstance(data, list) and data:
                    all_data.extend(data)
        
        if all_data:
            # Convert to DataFrame and clean
            df = pd.DataFrame(all_data)
            df = self.clean_and_process_data(df)
            
            # Save to file
            self.save_data(df)
            
            print(f"{Fore.GREEN}✅ Collected {len(df)} price points{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}❌ Failed to collect historical data{Style.RESET_ALL}")

    def clean_and_process_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and process the data"""
        # Remove duplicates
        df = df.drop_duplicates()
        
        # Sort by timestamp
        df = df.sort_values('timestamp')
        
        # Calculate additional metrics
        df['returns'] = df['price'].pct_change()
        df['volatility'] = df['returns'].rolling(window=24).std()
        
        return df

    def save_data(self, df: pd.DataFrame):
        """Save data to file"""
        filename = f"historical_data_{datetime.now().strftime('%Y%m%d')}.json"
        df.to_json(filename)
        print(f"{Fore.GREEN}Data saved to {filename}{Style.RESET_ALL}")

async def main():
    print(f"{Fore.MAGENTA}🔍 Starting Historical Data Collection{Style.RESET_ALL}")
    
    collector = HistoricalDataCollector()
    await collector.fetch_historical_data()

if __name__ == "__main__":
    asyncio.run(main()) 