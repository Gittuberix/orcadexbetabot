import requests
import json
from datetime import datetime
import time
from pathlib import Path
from colorama import init, Fore, Style

init()

class MultiTokenCollector:
    def __init__(self):
        # Directories
        self.data_dir = Path("price_data")
        self.data_dir.mkdir(exist_ok=True)
        
        # APIs
        self.APIS = {
            'orca': "https://api.mainnet.orca.so",
            'jupiter': "https://price.jup.ag/v4/price",
            'birdeye': "https://public-api.birdeye.so/public"
        }
        
        # Load watchlist
        self.load_watchlist()

    def load_watchlist(self):
        """Load latest watchlist"""
        try:
            watchlist_dir = Path("token_data")
            files = sorted(watchlist_dir.glob("watchlist_*.json"))
            
            if not files:
                print(f"{Fore.RED}No watchlist found! Run token_manager.py first.{Style.RESET_ALL}")
                self.tokens = {'SOL': 'So11111111111111111111111111111111111111112'}  # Fallback to SOL
                return
                
            with open(files[-1], 'r') as f:
                data = json.load(f)
                self.tokens = {t['symbol']: t['address'] for t in data['tokens']}
                self.whirlpools = {t['symbol']: t['usdc_pool'] for t in data['tokens']}
                
            print(f"{Fore.GREEN}Loaded {len(self.tokens)} tokens and {len(self.whirlpools)} whirlpools from the latest watchlist.")
        except Exception as e:
            print(f"{Fore.RED}Failed to load watchlist: {e}{Style.RESET_ALL}") 