from typing import Optional, Dict, Any
import requests
import pandas as pd
from datetime import datetime
from colorama import init, Fore, Style
from config.connections import ENVIRONMENTS, API_HEADERS
import aiohttp
import logging
from .config.orca_config import WHIRLPOOL_CONFIGS, TOKEN_DECIMALS
import math
from decimal import Decimal

init()

class WhirlpoolClient:
    def __init__(self, env: str = 'mainnet'):
        self.config = ENVIRONMENTS[env]
        self.endpoints = self.config['endpoints']
        self.headers = API_HEADERS
        self.logger = logging.getLogger(__name__)
        self.configs = WHIRLPOOL_CONFIGS
        self.decimals = TOKEN_DECIMALS
        
    async def get_active_whirlpools(self) -> list:
        """Holt aktive Whirlpools von Orca"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.endpoints['whirlpool_list'],
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Filtere nach Aktivität und Volumen
                        active_pools = [
                            pool for pool in data
                            if float(pool.get('volume24h', 0)) > 0
                        ]
                        print(f"{Fore.GREEN}Found {len(active_pools)} active pools{Style.RESET_ALL}")
                        return active_pools

        except Exception as e:
            print(f"{Fore.RED}Error fetching whirlpools: {e}{Style.RESET_ALL}")

        return []

    async def get_pool_price_history(
        self,
        pool_address: str,
        start_time: datetime,
        end_time: datetime
    ) -> pd.DataFrame:
        """Holt historische Preisdaten für einen Pool"""
        try:
            async with aiohttp.ClientSession() as session:
                # Formatiere Zeitstempel
                start_ts = int(start_time.timestamp())
                end_ts = int(end_time.timestamp())

                # API-Anfrage
                url = f"{self.endpoints['whirlpool']}/{pool_address}/candles"
                params = {
                    'start': start_ts,
                    'end': end_ts,
                    'resolution': '1m'  # 1-Minuten-Kerzen
                }

                async with session.get(url, params=params, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Konvertiere zu DataFrame
                        df = pd.DataFrame(data)
                        if not df.empty:
                            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
                            df.set_index('timestamp', inplace=True)

                            # Berechne technische Indikatoren
                            df['sma_5'] = df['close'].rolling(window=5).mean()
                            df['sma_15'] = df['close'].rolling(window=15).mean()
                            df['volume_sma'] = df['volume'].rolling(window=15).mean()
                            
                            print(f"{Fore.GREEN}Loaded {len(df)} price points for {pool_address}{Style.RESET_ALL}")
                            return df

        except Exception as e:
            print(f"{Fore.RED}Error fetching price history for {pool_address}: {e}{Style.RESET_ALL}")

        return pd.DataFrame()

    async def get_pool_data(self, pool_id: str) -> Optional[Dict]:
        """Get detailed pool data with liquidity analysis"""
        try:
            pool_config = self.configs.get(pool_id)
            if not pool_config:
                logger.error(f"No config found for pool {pool_id}")
                return None
                
            data = await self._make_request(
                f"{self.endpoints['whirlpool']}/{pool_config.pool_address}"
            )
            
            if data:
                # Erweitere Pool-Daten mit wichtigen Metriken
                data.update({
                    'config': pool_config,
                    'liquidity_metrics': self._calculate_liquidity_metrics(data),
                    'price_metrics': self._calculate_price_metrics(data)
                })
                
            return data
            
        except Exception as e:
            logger.error(f"Failed to get pool data: {e}")
            return None
            
    def _calculate_liquidity_metrics(self, pool_data: Dict) -> Dict:
        """Calculate important liquidity metrics"""
        try:
            liquidity = Decimal(pool_data.get('liquidity', 0))
            volume_24h = Decimal(pool_data.get('volume24h', 0))
            
            return {
                'liquidity_usd': float(liquidity),
                'volume_to_liquidity_ratio': float(volume_24h / liquidity) if liquidity else 0,
                'is_liquid': liquidity > Decimal('10000'),  # Mindestliquidität $10k
                'depth_score': self._calculate_depth_score(pool_data)
            }
            
        except Exception as e:
            logger.error(f"Error calculating liquidity metrics: {e}")
            return {}
            
    def _calculate_depth_score(self, pool_data: Dict) -> float:
        """Calculate pool depth score (0-1)"""
        try:
            # Analyze order book depth
            bids = pool_data.get('bids', [])
            asks = pool_data.get('asks', [])
            
            total_bid_value = sum(bid['size'] * bid['price'] for bid in bids)
            total_ask_value = sum(ask['size'] * ask['price'] for ask in asks)
            
            # Score based on depth and balance
            depth = (total_bid_value + total_ask_value) / 2
            balance = min(total_bid_value, total_ask_value) / max(total_bid_value, total_ask_value)
            
            return (math.log10(depth) * balance) / 10  # Normalized score
            
        except Exception as e:
            logger.error(f"Error calculating depth score: {e}")
            return 0
            
    def _calculate_price_metrics(self, pool_data: Dict) -> Dict:
        """Calculate price-related metrics"""
        try:
            price = Decimal(pool_data.get('price', 0))
            price_24h_ago = Decimal(pool_data.get('price24h', 0))
            
            return {
                'current_price': float(price),
                'price_change_24h': float((price - price_24h_ago) / price_24h_ago * 100),
                'volatility_24h': self._calculate_volatility(pool_data),
                'price_impact_score': self._estimate_price_impact(pool_data)
            }
            
        except Exception as e:
            logger.error(f"Error calculating price metrics: {e}")
            return {}
            
    def calculate_optimal_trade_size(self, pool_data: Dict) -> float:
        """Calculate optimal trade size based on liquidity"""
        try:
            liquidity = pool_data['liquidity_metrics']['liquidity_usd']
            depth_score = pool_data['liquidity_metrics']['depth_score']
            
            # Base size on liquidity and depth
            base_size = liquidity * 0.001  # 0.1% of liquidity
            
            # Adjust for depth score
            adjusted_size = base_size * depth_score
            
            # Apply limits
            min_size = 10  # Minimum $10
            max_size = liquidity * 0.05  # Maximum 5% of liquidity
            
            return max(min_size, min(adjusted_size, max_size))
            
        except Exception as e:
            logger.error(f"Error calculating optimal trade size: {e}")
            return 10  # Default minimum size

    def calculate_price_impact(self, pool_data: dict, amount: float) -> float:
        """Calculate price impact for a given trade amount"""
        try:
            liquidity = float(pool_data.get('liquidity', 0))
            if liquidity == 0:
                return float('inf')
                
            # Basic price impact calculation
            price_impact = (amount / liquidity) * 100
            
            # Apply exponential scaling for large trades
            if price_impact > 1:
                price_impact = price_impact * (1 + (price_impact - 1) * 0.1)
                
            return min(price_impact, 100.0)
            
        except (ValueError, TypeError) as e:
            self.logger.error(f"Price impact calculation failed: {e}")
            return float('inf')

    def calculate_slippage(self, pool_data: dict, amount: float) -> float:
        """Calculate expected slippage for a trade"""
        try:
            price_impact = self.calculate_price_impact(pool_data, amount)
            
            # Base slippage calculation
            base_slippage = 0.001  # 0.1% base slippage
            
            # Add dynamic component based on price impact
            dynamic_slippage = base_slippage * (1 + price_impact / 10)
            
            # Cap maximum slippage
            return min(dynamic_slippage, 0.05)  # Max 5% slippage
            
        except Exception as e:
            self.logger.error(f"Slippage calculation failed: {e}")
            return 0.05  # Return max slippage on error