class BacktestEngine:
    def __init__(self):
        self.token_manager = TokenManager()
        self.watchlist = self.token_manager.load_latest_watchlist()
        
        if not self.watchlist:
            print(f"{Fore.RED}No watchlist found! Run token_manager.py first.{Style.RESET_ALL}")
            return 