import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
from dataclasses import dataclass
from decimal import Decimal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

@dataclass
class WhirlpoolData:
    """Whirlpool state data"""
    address: str
    token_a: str
    token_b: str
    price: float
    liquidity: float
    volume_24h: float
    trades_24h: int
    price_change: float
    best_bid: float
    best_ask: float
    last_update: datetime
    
    def is_stale(self, max_age_seconds: int = 60) -> bool:
        """Check if data is stale"""
        return (datetime.now() - self.last_update).total_seconds() > max_age_seconds

class OrcaWhirlpoolClient:
    """Comprehensive Orca Whirlpool client"""
    
    def __init__(self, network: str = "mainnet"):
        # API endpoints
        self.network = network
        self.base_url = "https://api.orca.so"
        
        # Cache settings
        self.cache_duration = timedelta(seconds=30)
        self._pools_cache = {}
        self._price_cache = {}
        self._orderbook_cache = {}
        self._last_cache_update = None
        
        # Health monitoring
        self.health_check_interval = 60  # seconds
        self.last_health_check = None
        self.consecutive_failures = 0
        self.max_failures = 3
        self.is_healthy = True
        
        # Rate limiting
        self.request_semaphore = asyncio.Semaphore(5)
        self.last_request_time = {}
        self.min_request_interval = 0.2
        
        # Event callbacks
        self.on_health_change = None
        
        # Market depth tracking
        self.depth_levels = 10
        self.min_depth_update_interval = 1.0  # seconds
        self._depth_cache = {}
        
        # Active pools tracking
        self.whirlpools: Dict[str, WhirlpoolData] = {}
        self.update_interval = 1
        
        # Target tokens to track (major Solana tokens)
        self.tokens = [
            "SOL", "BONK", "JUP", "ORCA", "RAY", "MNGO", 
            "WIF", "SAMO", "BERN", "USDC", "USDH"
        ]
        
    async def start(self):
        """Start the client with health monitoring"""
        asyncio.create_task(self._health_monitor())
        asyncio.create_task(self._cache_cleanup())
        await self._initial_load()
        
    async def _initial_load(self):
        """Initial data load"""
        try:
            # Load top pools
            pools = await self.get_top_pools(limit=100)
            if not pools:
                raise Exception("Failed to load initial pool data")
                
            self.is_healthy = True
            if self.on_health_change:
                await self.on_health_change(True)
                
        except Exception as e:
            logging.error(f"Initial load failed: {e}")
            self.is_healthy = False
            if self.on_health_change:
                await self.on_health_change(False)
                
    async def _health_monitor(self):
        """Monitor API health"""
        while True:
            try:
                response = await self._fetch_with_retry(f"{self.base_url}/v1/health", retries=1)
                is_healthy = response is not None and response.get('status') == 'healthy'
                
                if is_healthy:
                    self.consecutive_failures = 0
                else:
                    self.consecutive_failures += 1
                    
                new_health_state = self.consecutive_failures < self.max_failures
                if new_health_state != self.is_healthy:
                    self.is_healthy = new_health_state
                    if self.on_health_change:
                        await self.on_health_change(new_health_state)
                        
            except Exception as e:
                logging.error(f"Health check failed: {e}")
                self.consecutive_failures += 1
                
            await asyncio.sleep(self.health_check_interval)
            
    async def _cache_cleanup(self):
        """Clean up stale cache entries"""
        while True:
            try:
                current_time = datetime.now()
                
                # Clean pool cache
                self._pools_cache = {
                    k: v for k, v in self._pools_cache.items()
                    if current_time - v['timestamp'] < self.cache_duration
                }
                
                # Clean price cache
                self._price_cache = {
                    k: v for k, v in self._price_cache.items()
                    if current_time - v['timestamp'] < self.cache_duration
                }
                
                # Clean orderbook cache
                self._orderbook_cache = {
                    k: v for k, v in self._orderbook_cache.items()
                    if current_time - v['timestamp'] < self.cache_duration
                }
                
            except Exception as e:
                logging.error(f"Cache cleanup error: {e}")
                
            await asyncio.sleep(30)  # Run cleanup every 30 seconds
        
    async def _fetch_with_retry(self, session: aiohttp.ClientSession, url: str, retries: int = 3) -> Optional[Dict]:
        """Fetch data with retry logic and rate limiting"""
        endpoint = url.split("/v1/")[1].split("?")[0]
        
        async with self.request_semaphore:
            if endpoint in self.last_request_time:
                time_since_last = datetime.now() - self.last_request_time[endpoint]
                if time_since_last.total_seconds() < self.min_request_interval:
                    await asyncio.sleep(self.min_request_interval - time_since_last.total_seconds())
            
            for attempt in range(retries):
                try:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                        self.last_request_time[endpoint] = datetime.now()
                        
                        if response.status == 200:
                            return await response.json()
                        elif response.status == 429:  # Rate limit
                            wait_time = float(response.headers.get('Retry-After', 1 * (attempt + 1)))
                            await asyncio.sleep(wait_time)
                        elif response.status == 404:
                            logging.warning(f"Resource not found: {url}")
                            return None
                        else:
                            logging.warning(f"Failed request to {url}. Status: {response.status}")
                            if attempt < retries - 1:
                                await asyncio.sleep(1 * (attempt + 1))
                except asyncio.TimeoutError:
                    logging.warning(f"Request timeout ({attempt+1}/{retries})")
                    if attempt < retries - 1:
                        await asyncio.sleep(1)
                except Exception as e:
                    logging.error(f"Request error ({attempt+1}/{retries}): {str(e)}")
                    if attempt < retries - 1:
                        await asyncio.sleep(1)
            return None
        
    async def get_pool_price(self, pool_address: str) -> Optional[float]:
        """Get current pool price with validation"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/v1/whirlpool/{pool_address}/price"
                data = await self._fetch_with_retry(session, url)
                if data and 'price' in data:
                    return float(data['price'])
        except Exception as e:
            logging.error(f"Error fetching pool price: {str(e)}")
        return None
        
    async def get_historical_prices(self, pool_address: str, interval: str = "1h", limit: int = 24) -> List[Dict]:
        """Get historical price data"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/v1/whirlpool/{pool_address}/candles"
                params = {
                    'interval': interval,
                    'limit': limit
                }
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('candles', [])
        except Exception as e:
            logging.error(f"Error fetching historical prices: {str(e)}")
        return []
        
    async def get_pool_stats(self, pool_address: str) -> Optional[Dict]:
        """Get comprehensive pool statistics"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/v1/whirlpool/{pool_address}/stats"
                data = await self._fetch_with_retry(session, url)
                if data:
                    return {
                        'price': float(data.get('price', 0)),
                        'price_change': float(data.get('priceChange24h', 0)),
                        'volume_24h': float(data.get('volume24h', 0)),
                        'tvl': float(data.get('tvl', 0)),
                        'fees_24h': float(data.get('fees24h', 0)),
                        'trades_24h': int(data.get('numberOfTrades24h', 0))
                    }
        except Exception as e:
            logging.error(f"Error fetching pool stats: {str(e)}")
        return None
        
    async def get_quote(self, input_token: str, output_token: str, amount: float, slippage: float = 0.5) -> Optional[Dict]:
        """Get swap quote from Orca"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/v1/quote"
                params = {
                    'inputToken': input_token,
                    'outputToken': output_token,
                    'amount': str(amount),
                    'slippage': slippage
                }
                data = await self._fetch_with_retry(session, url)
                if data:
                    return {
                        'input_amount': float(data['inAmount']),
                        'output_amount': float(data['outAmount']),
                        'price_impact': float(data['priceImpact']),
                        'fee_amount': float(data['fee']),
                        'route': data.get('route', [])
                    }
        except Exception as e:
            logging.error(f"Error getting swap quote: {str(e)}")
        return None
        
    async def get_top_pools(self, metric: str = 'volume', limit: int = 10) -> List[WhirlpoolData]:
        """Get top pools by specified metric (volume, tvl, etc)"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/v1/whirlpool/list"
                pools = await self._fetch_with_retry(session, url)
                
                if not pools:
                    return []
                    
                # Fetch stats for each pool
                pool_data = []
                for pool in pools:
                    if pool['tokenA']['symbol'] in self.tokens or pool['tokenB']['symbol'] in self.tokens:
                        stats = await self.get_pool_stats(pool['address'])
                        if stats:
                            price = stats['price']
                            pool_data.append(WhirlpoolData(
                                address=pool['address'],
                                token_a=pool['tokenA']['symbol'],
                                token_b=pool['tokenB']['symbol'],
                                price=price,
                                liquidity=stats['tvl'],
                                volume_24h=stats['volume_24h'],
                                trades_24h=stats['trades_24h'],
                                price_change=stats['price_change'],
                                best_bid=price * 0.995,  # Estimated
                                best_ask=price * 1.005,  # Estimated
                                last_update=datetime.now()
                            ))
                
                # Sort by specified metric
                if metric == 'volume':
                    pool_data.sort(key=lambda x: x.volume_24h, reverse=True)
                elif metric == 'tvl':
                    pool_data.sort(key=lambda x: x.liquidity, reverse=True)
                
                return pool_data[:limit]
                
        except Exception as e:
            logging.error(f"Error fetching top pools: {str(e)}")
            return []
            
    async def start_tracking(self):
        """Start tracking pool data"""
        while True:
            try:
                pools = await self.get_top_pools(limit=20)
                for pool in pools:
                    self.whirlpools[pool.address] = pool
                    
                active_pools = len([p for p in self.whirlpools.values() if p.volume_24h > 0])
                total_volume = sum(p.volume_24h for p in self.whirlpools.values())
                
                print(f"\rAktive Whirlpools: {active_pools} | "
                      f"24h Volume: ${total_volume:,.0f} | "
                      f"Update: {datetime.now().strftime('%H:%M:%S')}", 
                      end='')
                      
            except Exception as e:
                logging.error(f"Error in tracking loop: {str(e)}")
                
            await asyncio.sleep(self.update_interval)
            
    def get_tracked_pools(self, limit: Optional[int] = None) -> List[WhirlpoolData]:
        """Get currently tracked pools"""
        pools = sorted(
            self.whirlpools.values(),
            key=lambda x: x.volume_24h,
            reverse=True
        )
        return pools[:limit] if limit else pools 