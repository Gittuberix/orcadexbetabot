from config.connections import ENVIRONMENTS, WHIRLPOOL_IDS, API_HEADERS
from connection_manager import ConnectionManager
from pathlib import Path
from colorama import init, Fore, Style
import pandas as pd
import time

init()

class BacktestDataManager:
    def __init__(self):
        print(f"{Fore.CYAN}Initializing Backtest Data Manager...{Style.RESET_ALL}")
        self.config = ENVIRONMENTS['backtest']
        self.data_dir = Path(self.config['data_dir'])
        self.whirlpool_ids = WHIRLPOOL_IDS
        self.connection = ConnectionManager('backtest')
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def fetch_whirlpool_data(self, pair, start_time, end_time):
        if pair not in self.whirlpool_ids:
            return None
        return self.connection.get_pool_data(self.whirlpool_ids[pair])