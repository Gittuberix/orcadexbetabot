import requests
import time
from colorama import init, Fore, Style

init()

class DexDataFetcher:
    def __init__(self):
        # Primary APIs
        self.ORCA_APIS = {
            "v1": "https://api.mainnet.orca.so/v1",
            "whirlpool": "https://api.mainnet.orca.so/v1/whirlpool"
        }
        
        # Backup APIs
        self.BACKUP_APIS = {
            "jupiter": "https://price.jup.ag/v4",
            "serum": "https://api.projectserum.com/v1",
            "birdeye": "https://public-api.birdeye.so/public"
        }
        
        # RPC Endpoints
        self.RPC_ENDPOINTS = [
            "https://api.mainnet-beta.solana.com",
            "https://solana-api.projectserum.com",
            "https://rpc.ankr.com/solana"
        ]
        
        # Headers
        self.headers = {
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0'
        }

    def get_pool_data(self, pool_id="HJPjoWUrhoZzkNfRpHuieeFk9WcZWjwy6PBjZ81ngndJ"):
        """Get pool data with fallback sources"""
        print(f"\n{Fore.CYAN}=== Fetching Pool Data ==={Style.RESET_ALL}")
        
        # Try Orca first
        try:
            url = f"{self.ORCA_APIS['whirlpool']}/{pool_id}"
            print(f"\n{Fore.YELLOW}Trying Orca API...{Style.RESET_ALL}")
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                print(f"{Fore.GREEN}✓ Orca data received{Style.RESET_ALL}")
                return response.json()
                
        except Exception as e:
            print(f"{Fore.RED}Orca API error: {str(e)}{Style.RESET_ALL}")

        # Try Jupiter as backup
        try:
            url = f"{self.BACKUP_APIS['jupiter']}/price?ids=SOL"
            print(f"\n{Fore.YELLOW}Trying Jupiter API...{Style.RESET_ALL}")
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                print(f"{Fore.GREEN}✓ Jupiter data received{Style.RESET_ALL}")
                return response.json()
                
        except Exception as e:
            print(f"{Fore.RED}Jupiter API error: {str(e)}{Style.RESET_ALL}")

        # Try Serum as last resort
        try:
            url = f"{self.BACKUP_APIS['serum']}/markets"
            print(f"\n{Fore.YELLOW}Trying Serum API...{Style.RESET_ALL}")
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                print(f"{Fore.GREEN}✓ Serum data received{Style.RESET_ALL}")
                return response.json()
                
        except Exception as e:
            print(f"{Fore.RED}Serum API error: {str(e)}{Style.RESET_ALL}")

        return None

    def get_best_rpc(self):
        """Find fastest responding RPC endpoint"""
        print(f"\n{Fore.CYAN}=== Testing RPC Endpoints ==={Style.RESET_ALL}")
        
        best_rpc = None
        best_time = float('inf')
        
        for rpc in self.RPC_ENDPOINTS:
            try:
                print(f"\n{Fore.YELLOW}Testing {rpc}{Style.RESET_ALL}")
                start_time = time.time()
                
                response = requests.post(
                    rpc,
                    json={"jsonrpc": "2.0", "id": 1, "method": "getHealth"},
                    headers=self.headers,
                    timeout=5
                )
                
                end_time = time.time()
                response_time = end_time - start_time
                
                if response.status_code == 200:
                    print(f"{Fore.GREEN}✓ Response time: {response_time:.2f}s{Style.RESET_ALL}")
                    
                    if response_time < best_time:
                        best_time = response_time
                        best_rpc = rpc
                        
            except Exception as e:
                print(f"{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")

        if best_rpc:
            print(f"\n{Fore.GREEN}Best RPC: {best_rpc} ({best_time:.2f}s){Style.RESET_ALL}")
        return best_rpc

def main():
    print(f"{Fore.CYAN}=== Orca DEX Data Fetcher ==={Style.RESET_ALL}")
    
    fetcher = DexDataFetcher()
    
    # Get best RPC
    best_rpc = fetcher.get_best_rpc()
    
    # Get pool data
    pool_data = fetcher.get_pool_data()
    
    if pool_data:
        print(f"\n{Fore.GREEN}Successfully fetched pool data!{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.RED}Failed to fetch pool data.{Style.RESET_ALL}") 