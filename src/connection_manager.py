from config.connections import ENVIRONMENTS, API_HEADERS
from colorama import init, Fore, Style
import requests
import time

init()

class ConnectionManager:
    def __init__(self, env='mainnet'):
        print(f"{Fore.CYAN}Initializing Connection Manager...{Style.RESET_ALL}")
        self.config = ENVIRONMENTS[env]
        self.endpoints = self.config['endpoints']
        self.rpcs = self.config['rpcs']
        self.headers = API_HEADERS
        self.active_rpc = self.get_best_rpc()

    def get_best_rpc(self):
        """Find fastest RPC endpoint"""
        print(f"\n{Fore.YELLOW}Testing RPC endpoints...{Style.RESET_ALL}")
        
        best_rpc = None
        best_time = float('inf')
        
        for rpc in self.rpcs:
            try:
                start = time.time()
                response = requests.post(
                    rpc,
                    json={"jsonrpc": "2.0", "id": 1, "method": "getHealth"},
                    headers=self.headers,
                    timeout=5
                )
                elapsed = time.time() - start
                
                if response.status_code == 200:
                    print(f"{Fore.GREEN}✓ {rpc}: {elapsed:.2f}s{Style.RESET_ALL}")
                    if elapsed < best_time:
                        best_time = elapsed
                        best_rpc = rpc
            except Exception as e:
                print(f"{Fore.RED}✗ {rpc}: {str(e)}{Style.RESET_ALL}")
        
        return best_rpc

    def get_pool_data(self, pool_id):
        """Get Whirlpool data"""
        try:
            url = f"{self.endpoints['whirlpool']}/{pool_id}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                return response.json()
                
        except Exception as e:
            print(f"{Fore.RED}Pool data error: {str(e)}{Style.RESET_ALL}")
            
        return None