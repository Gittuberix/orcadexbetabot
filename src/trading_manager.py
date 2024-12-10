from typing import Dict, Any, Optional
import requests
from colorama import Fore, Style
import asyncio
from src.wallet_manager import PhantomWalletManager

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
        
        self.min_profit_threshold = 0.5  # 0.5%
        self.max_slippage = 0.3  # 0.3%
        
        self.wallet_manager = PhantomWalletManager()
        
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

    async def optimize_execution(self, trade_params):
        # Smart Order Routing
        best_route = await self.calculate_optimal_route(
            trade_params['from_token'],
            trade_params['to_token'],
            trade_params['amount']
        )
        
        # MEV Protection
        if self._detect_sandwich_risk(best_route):
            trade_params['slippage'] = min(trade_params['slippage'] * 1.5, self.max_slippage)
            
        # Split large orders
        if trade_params['amount'] > self.large_order_threshold:
            return await self._split_and_execute(trade_params)
            
        return await self._execute_trade(best_route, trade_params)

    async def calculate_optimal_route(self, from_token, to_token, amount):
        routes = []
        
        # Direct route
        direct_pool = self._find_direct_pool(from_token, to_token)
        if direct_pool:
            routes.append({
                'path': [direct_pool],
                'expected_output': self._simulate_swap(direct_pool, amount)
            })
            
        # Multi-hop routes (max 2 hops)
        intermediate_tokens = self._get_common_pairs(from_token, to_token)
        for token in intermediate_tokens:
            first_hop = self._find_direct_pool(from_token, token)
            second_hop = self._find_direct_pool(token, to_token)
            
            if first_hop and second_hop:
                intermediate_amount = self._simulate_swap(first_hop, amount)
                final_amount = self._simulate_swap(second_hop, intermediate_amount)
                
                routes.append({
                    'path': [first_hop, second_hop],
                    'expected_output': final_amount
                })
                
        return max(routes, key=lambda x: x['expected_output'])

    def _detect_sandwich_risk(self, route):
        # Prüfe Liquiditätstiefe
        pool_liquidity = self._get_pool_liquidity(route['path'][0])
        trade_size = route['amount']
        return (trade_size / pool_liquidity) > 0.02  # 2% der Liquidität

    async def _split_and_execute(self, trade_params):
        chunk_size = self.large_order_threshold
        chunks = self._split_amount(trade_params['amount'], chunk_size)
        results = []
        
        for chunk in chunks:
            modified_params = trade_params.copy()
            modified_params['amount'] = chunk
            result = await self._execute_trade(modified_params)
            results.append(result)
            await asyncio.sleep(2)  # Zeitversatz zwischen Trades
        
        return self._aggregate_results(results)

    def _simulate_swap(self, pool, amount):
        reserves = self._get_pool_reserves(pool)
        return self._calculate_output_amount(amount, reserves)

    def _find_direct_pool(self, token_a, token_b):
        pool_key = f"{token_a}-{token_b}"
        return self.WHIRLPOOL_IDS.get(pool_key)

    async def initialize(self):
        """Initialize trading manager"""
        # Connect wallet
        wallet_connected = await self.wallet_manager.connect_phantom()
        if not wallet_connected:
            raise Exception("Failed to connect Phantom wallet")

    async def execute_trade(self, trade_params):
        """Execute trade with wallet"""
        try:
            return await self.wallet_manager.execute_swap(
                trade_params['pool_id'],
                trade_params['amount_in'],
                trade_params['min_amount_out']
            )
        except Exception as e:
            logger.error(f"Trade execution error: {e}")
            return None