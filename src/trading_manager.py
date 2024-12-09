from typing import Dict, Any, Optional
import requests
from colorama import Fore, Style

class TradingManager:
    def __init__(self):
        print(f"{Fore.CYAN}Initializing Orca Whirlpool Data Manager...{Style.RESET_ALL}")
        
        # Primary Orca Endpoints
        self.ORCA_ENDPOINTS = {
            "api": "https://api.mainnet.orca.so",
            "whirlpool": "https://api.mainnet.orca.so/v1/whirlpool",
            "rpc": "https://api.mainnet.orca.so/rpc"
        }
        
        # Orca Whirlpool IDs
        self.WHIRLPOOL_IDS = {
            'SOL/USDC': 'HJPjoWUrhoZzkNfRpHuieeFk9WcZWjwy6PBjZ81ngndJ'
        }
        
        # Backup APIs nur wenn Orca nicht erreichbar
        self.BACKUP_APIS = {
            'jupiter': 'https://price.jup.ag/v4/price?ids=orcaPool',
            'birdeye': 'https://public-api.birdeye.so/public/pool'
        }
        
        self.headers = {
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0'
        }
        
        # Test Orca connection
        self.orca_available = self._test_orca_connection()

    def _test_orca_connection(self) -> bool:
        """Test primary Orca connection"""
        try:
            print(f"{Fore.YELLOW}Testing Orca connection...{Style.RESET_ALL}")
            
            # Test API
            api_response = requests.get(
                f"{self.ORCA_ENDPOINTS['whirlpool']}/list",
                headers=self.headers,
                timeout=10
            )
            
            # Test RPC
            rpc_response = requests.post(
                self.ORCA_ENDPOINTS['rpc'],
                json={"jsonrpc": "2.0", "id": 1, "method": "getHealth"},
                headers=self.headers,
                timeout=10
            )
            
            if api_response.status_code == 200 and rpc_response.status_code == 200:
                print(f"{Fore.GREEN}✓ Orca connection successful{Style.RESET_ALL}")
                return True
                
        except Exception as e:
            print(f"{Fore.RED}Orca connection error: {str(e)}{Style.RESET_ALL}")
            
        return False

    def get_whirlpool_data(self, pair: str) -> Optional[Dict[str, Any]]:
        """Get Orca Whirlpool data with backups"""
        if pair not in self.WHIRLPOOL_IDS:
            print(f"{Fore.RED}Unknown Whirlpool pair: {pair}{Style.RESET_ALL}")
            return None
            
        pool_id = self.WHIRLPOOL_IDS[pair]
        
        # Try primary Orca first
        if self.orca_available:
            try:
                print(f"{Fore.YELLOW}Using primary Orca connection...{Style.RESET_ALL}")
                response = requests.get(
                    f"{self.ORCA_ENDPOINTS['whirlpool']}/{pool_id}",
                    headers=self.headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    print(f"{Fore.GREEN}✓ Orca data received{Style.RESET_ALL}")
                    return {'source': 'orca', 'data': response.json()}
                    
            except Exception as e:
                print(f"{Fore.RED}Orca API error: {str(e)}{Style.RESET_ALL}") 