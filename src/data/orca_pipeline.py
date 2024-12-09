import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from rich.console import Console
import sys
from pathlib import Path
from colorama import init, Fore, Style
import pandas as pd
from ..config.connections import ENVIRONMENTS, API_HEADERS, WHIRLPOOL_IDS
from logging.handlers import RotatingFileHandler
import os
from .monitoring import SystemMonitor
import time
from ..connection.quicknode_client import QuickNodeWebSocket

init()
console = Console()

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Configure logging with both file and console handlers
def setup_logging():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    
    # Format for logs
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # File Handler with rotation
    file_handler = RotatingFileHandler(
        'logs/orca_pipeline.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

# Initialize logger
logger = setup_logging()

class RateLimiter:
    def __init__(self, calls_per_second: int = 2):
        self.calls_per_second = calls_per_second
        self.last_call = time.time()
        self.lock = asyncio.Lock()

    async def wait(self):
        async with self.lock:
            now = time.time()
            time_since_last = now - self.last_call
            if time_since_last < (1.0 / self.calls_per_second):
                await asyncio.sleep((1.0 / self.calls_per_second) - time_since_last)
            self.last_call = time.time()

class OrcaPipeline:
    def __init__(self, env: str = 'mainnet'):
        self.monitor = SystemMonitor("OrcaPipeline")
        logger.debug(f"Initializing OrcaPipeline with environment: {env}")
        self.config = ENVIRONMENTS[env]
        self.endpoints = self.config['endpoints']
        self.headers = API_HEADERS
        self.cache = {}
        self.active_pools = []
        self.min_volume = 1000
        self.session = None
        self.watchlist_pools = WHIRLPOOL_IDS
        logger.debug(f"Watchlist pools configured: {self.watchlist_pools}")
        logger.debug(f"Endpoints configured: {self.endpoints}")
        self.rate_limiter = RateLimiter()
        self.retry_attempts = 3
        self.retry_delay = 1  # seconds
        self.price_subscribers = {}
        self.last_prices = {}
        
    async def _make_request(self, url: str, method: str = "GET", **kwargs) -> Optional[dict]:
        """Make API request with retry logic and rate limiting"""
        await self.rate_limiter.wait()
        
        for attempt in range(self.retry_attempts):
            try:
                async with self.session.request(method, url, **kwargs) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 429:  # Rate limit
                        retry_after = int(response.headers.get('Retry-After', self.retry_delay))
                        logger.warning(f"Rate limited, waiting {retry_after}s")
                        await asyncio.sleep(retry_after)
                    elif response.status >= 500:
                        logger.error(f"Server error: {response.status}")
                        await asyncio.sleep(self.retry_delay * (attempt + 1))
                    else:
                        logger.error(f"Request failed: {response.status}")
                        return None
                        
            except aiohttp.ClientError as e:
                logger.error(f"Network error: {e}")
                await asyncio.sleep(self.retry_delay * (attempt + 1))
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                return None
                
        return None

    async def update_pools(self):
        """Update pool list with improved error handling"""
        try:
            data = await self._make_request(
                self.endpoints['whirlpool_list'],
                headers=self.headers
            )
            
            if not data:
                logger.error("Failed to fetch pool data")
                return
                
            # Process valid pools
            valid_pools = []
            for pool in data:
                try:
                    volume = float(pool.get('volume24h', 0))
                    if volume > self.min_volume:
                        valid_pools.append(pool)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid pool data: {e}")
                    continue
                    
            self.active_pools = sorted(
                valid_pools,
                key=lambda x: float(x.get('volume24h', 0)),
                reverse=True
            )
            
            logger.info(f"Successfully updated {len(self.active_pools)} pools")
            
        except Exception as e:
            logger.error(f"Pool update failed: {e}", exc_info=True)

    def _monitor_pool_health(self):
        """Monitor pool health metrics"""
        try:
            total_volume = sum(float(p.get('volume24h', 0)) for p in self.active_pools)
            avg_volume = total_volume / len(self.active_pools) if self.active_pools else 0
            
            logger.info(f"Total 24h Volume: ${total_volume:,.2f}")
            logger.info(f"Average Pool Volume: ${avg_volume:,.2f}")
            
            # Alert on suspicious changes
            if avg_volume < 1000:  # Example threshold
                logger.warning("Average pool volume is unusually low")
            
            # Monitor update frequency
            for pool in self.active_pools:
                cache_data = self.cache.get(pool['address'])
                if cache_data:
                    last_update = cache_data['last_update']
                    time_since_update = (datetime.now() - last_update).seconds
                    if time_since_update > 10:  # Alert if data is stale
                        logger.warning(f"Pool {pool['address']} data is stale ({time_since_update}s old)")
        
        except Exception as e:
            logger.error(f"Error in pool health monitoring: {e}", exc_info=True)

    async def subscribe_to_price(self, pool_address: str, callback):
        """Subscribe to price updates for a pool"""
        if pool_address not in self.price_subscribers:
            self.price_subscribers[pool_address] = []
        self.price_subscribers[pool_address].append(callback)
        logger.debug(f"Added price subscriber for pool {pool_address}")
        
    async def _notify_price_update(self, pool_address: str, price_data: dict):
        """Notify subscribers of price updates"""
        if pool_address in self.price_subscribers:
            for callback in self.price_subscribers[pool_address]:
                try:
                    await callback(price_data)
                except Exception as e:
                    logger.error(f"Error in price subscriber callback: {e}")

    async def update_pool_data(self, pool_address: str):
        """Update pool data with price notifications"""
        try:
            url = f"{self.endpoints['whirlpool']}/{pool_address}"
            async with self.session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Cache update
                    self.cache[pool_address] = {
                        'last_update': datetime.now(),
                        'data': data
                    }
                    
                    # Check for significant price changes
                    last_price = self.last_prices.get(pool_address)
                    current_price = float(data.get('price', 0))
                    
                    if last_price:
                        price_change = abs(current_price - last_price) / last_price
                        if price_change > 0.001:  # 0.1% change
                            await self._notify_price_update(pool_address, data)
                    
                    self.last_prices[pool_address] = current_price
                    logger.debug(f"Updated data for pool {pool_address}")
                else:
                    logger.warning(f"Failed to fetch pool {pool_address}: HTTP {response.status}")

        except aiohttp.ClientError as e:
            logger.error(f"Network error updating pool {pool_address}: {e}")
        except Exception as e:
            logger.error(f"Error updating pool {pool_address}: {e}", exc_info=True)

    async def update_pool_history(self, pool_address: str):
        """Holt historische Daten für einen Pool"""
        try:
            # Letzte 24 Stunden
            end_time = datetime.now()
            start_time = end_time - timedelta(days=1)
            
            url = f"{self.endpoints['whirlpool']}/{pool_address}/candles"
            params = {
                'start': int(start_time.timestamp()),
                'end': int(end_time.timestamp()),
                'resolution': '1m'
            }
            
            async with self.session.get(url, params=params, headers=self.headers) as response:
                if response.status == 200:
                    data = await response.json()
                    self.cache[pool_address]['history'] = data
                    logger.debug(f"Updated history for pool {pool_address}")
                else:
                    logger.warning(f"Failed to fetch pool history {pool_address}: HTTP {response.status}")

        except aiohttp.ClientError as e:
            logger.error(f"Network error updating pool history {pool_address}: {e}")
        except Exception as e:
            logger.error(f"Error updating pool history {pool_address}: {e}", exc_info=True)

    def get_pool_data(self, pool_address: str) -> Optional[Dict]:
        """Holt gecachte Pool-Daten"""
        cache_data = self.cache.get(pool_address)
        if cache_data:
            # Prüfen ob Daten noch frisch sind (max 5 Sekunden alt)
            if (datetime.now() - cache_data['last_update']).seconds < 5:
                return cache_data['data']
        return None
        
    def _print_status(self):
        """Zeigt Pipeline-Status"""
        console.clear()
        console.print(f"\n[cyan]Orca Pipeline Status - {datetime.now().strftime('%H:%M:%S')}[/cyan]")
        
        try:
            console.print(f"Active Pools: {len(self.active_pools)}")
            console.print(f"Cached Pools: {len(self.cache)}")
            console.print(f"Watchlist Pools: {len(self.watchlist_pools)}")
            
            if self.active_pools:
                console.print("\n[yellow]Top 5 Pools by Volume:[/yellow]")
                for i, pool in enumerate(self.active_pools[:5], 1):
                    is_watchlist = pool['address'] in self.watchlist_pools.values()
                    symbol_prefix = "[red]*[/red] " if is_watchlist else ""
                    
                    console.print(f"\n{i}. {symbol_prefix}{pool['tokenA']['symbol']}-{pool['tokenB']['symbol']}")
                    console.print(f"Volume 24h: ${float(pool['volume24h']):,.2f}")
                    console.print(f"Address: {pool['address']}")
                    
                    pool_data = self.get_pool_data(pool['address'])
                    if pool_data:
                        console.print(f"Price: ${float(pool_data.get('price', 0)):,.4f}")
        except Exception as e:
            logger.error(f"Error displaying status: {e}")

    async def start_pipeline(self):
        """Startet die Datenpipeline"""
        self.monitor.logger.info("Starting Orca Data Pipeline...")
        
        try:
            # Initialize WebSocket connection
            self.ws = QuickNodeWebSocket()
            await self.ws.connect()
            
            # Subscribe to Orca program updates
            await self.ws.subscribe_to_program(
                "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc",  # Orca program ID
                self._handle_program_update
            )
            
            # Subscribe to pool logs
            for pool in self.watchlist_pools.values():
                await self.ws.subscribe_to_logs(
                    pool,
                    self._handle_pool_update
                )
            
            async with aiohttp.ClientSession() as session:
                self.session = session
                while True:
                    try:
                        cycle_start = time.time()
                        await self.update_pools()
                        
                        cycle_time = time.time() - cycle_start
                        self.monitor.metrics['cycle_times'].append(cycle_time)
                        self.monitor.update_metrics()
                        
                        if self.monitor.get_health_report()['status'] != 'healthy':
                            logger.warning(f"Pipeline health degraded")
                        
                        await asyncio.sleep(1)
                        
                    except asyncio.CancelledError:
                        raise
                    except Exception as e:
                        self.monitor.log_error(e, "pipeline_cycle", "ERROR")
                        await asyncio.sleep(5)
                        
        except Exception as e:
            self.monitor.log_error(e, "pipeline_main", "CRITICAL")
        finally:
            if self.ws:
                await self.ws.close()
            self.session = None

    async def _handle_program_update(self, data: Dict):
        """Handle Orca program updates"""
        try:
            if 'transaction' in data:
                # Process swap transaction
                swap_info = self.ws._extract_swap_info(data)
                if swap_info:
                    logger.info(f"New swap detected: {swap_info}")
                    
                    # Update pool data if needed
                    pool_address = swap_info.get('pool')
                    if pool_address in self.watchlist_pools.values():
                        await self.update_pool_data(pool_address)
                        
        except Exception as e:
            logger.error(f"Error handling program update: {e}")

    async def _handle_pool_update(self, data: Dict):
        """Handle pool-specific updates"""
        try:
            pool_address = data.get('accountId')
            if pool_address in self.watchlist_pools.values():
                # Immediate pool update on activity
                await self.update_pool_data(pool_address)
                
        except Exception as e:
            logger.error(f"Error handling pool update: {e}")

async def main():
    try:
        logger.info("Starting main pipeline process")
        pipeline = OrcaPipeline()
        logger.debug("Pipeline instance created")
        await pipeline.start_pipeline()
    except KeyboardInterrupt:
        logger.info("Pipeline stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        logger.info("Pipeline shutdown complete")

if __name__ == "__main__":
    # Set logging to DEBUG level to see more detailed information
    logging.getLogger(__name__).setLevel(logging.DEBUG)
    
    try:
        logger.info("Starting Orca Pipeline application")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True) 