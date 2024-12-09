import requests
import json
from datetime import datetime
from pathlib import Path
from colorama import init, Fore, Style

init()

class TokenManager:
    def __init__(self):
        # APIs
        self.ORCA_API = "https://api.mainnet.orca.so"
        self.JUPITER_API = "https://price.jup.ag/v4"
        
        # Directories
        self.data_dir = Path("data/tokens")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Default tokens (immer verfügbar)
        self.DEFAULT_TOKENS = {
            'SOL': 'So11111111111111111111111111111111111111112',
            'USDC': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'
        }
        
        # Whirlpools
        self.WHIRLPOOLS = {
            'SOL-USDC': '7qbRF6YsyGuLUVs6Y1q64bdVrfe4ZcUUz1JRdoVNUJpi'
        }

    def get_orca_whirlpools(self):
        """Get all Orca Whirlpools"""
        try:
            print(f"{Fore.YELLOW}Fetching Orca Whirlpools...{Style.RESET_ALL}")
            response = requests.get(f"{self.ORCA_API}/v1/whirlpool/list")
            
            if response.status_code == 200:
                pools = response.json()
                print(f"{Fore.GREEN}Found {len(pools)} whirlpools{Style.RESET_ALL}")
                return pools
            else:
                print(f"{Fore.RED}Failed to fetch whirlpools: {response.status_code}{Style.RESET_ALL}")
                return []
                
        except Exception as e:
            print(f"{Fore.RED}Error fetching whirlpools: {str(e)}{Style.RESET_ALL}")
            return []

    def get_top_tokens(self):
        """Get top tokens from Jupiter"""
        try:
            print(f"{Fore.YELLOW}Fetching top tokens...{Style.RESET_ALL}")
            response = requests.get(f"{self.JUPITER_API}/tokens")
            
            if response.status_code == 200:
                tokens = response.json()
                print(f"{Fore.GREEN}Found {len(tokens)} tokens{Style.RESET_ALL}")
                return tokens
            else:
                print(f"{Fore.RED}Failed to fetch tokens: {response.status_code}{Style.RESET_ALL}")
                return []
                
        except Exception as e:
            print(f"{Fore.RED}Error fetching tokens: {str(e)}{Style.RESET_ALL}")
            return []

    def update_token_list(self):
        """Update token list with whirlpools"""
        # Get data
        whirlpools = self.get_orca_whirlpools()
        tokens = self.get_top_tokens()
        
        # Combine data
        token_data = {
            'timestamp': datetime.now().isoformat(),
            'default_tokens': self.DEFAULT_TOKENS,
            'whirlpools': self.WHIRLPOOLS,
            'all_whirlpools': whirlpools,
            'top_tokens': tokens
        }
        
        # Save data
        self.save_token_data(token_data)
        return token_data

    def save_token_data(self, data):
        """Save token data"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = self.data_dir / f"token_data_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"{Fore.GREEN}✅ Token data saved to {filename}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error saving token data: {str(e)}{Style.RESET_ALL}")

    def load_latest_data(self):
        """Load most recent token data"""
        try:
            files = sorted(self.data_dir.glob("token_data_*.json"))
            if files:
                latest = files[-1]
                with open(latest, 'r') as f:
                    data = json.load(f)
                print(f"{Fore.GREEN}Loaded token data from {latest}{Style.RESET_ALL}")
                return data
            else:
                print(f"{Fore.YELLOW}No token data found{Style.RESET_ALL}")
                return None
        except Exception as e:
            print(f"{Fore.RED}Error loading token data: {str(e)}{Style.RESET_ALL}")
            return None

def main():
    print(f"{Fore.CYAN}=== Token Manager ==={Style.RESET_ALL}")
    
    manager = TokenManager()
    token_data = manager.update_token_list()
    
    if token_data:
        print(f"\n{Fore.GREEN}Token update successful!{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.RED}Token update failed!{Style.RESET_ALL}")

if __name__ == "__main__":
    main() 