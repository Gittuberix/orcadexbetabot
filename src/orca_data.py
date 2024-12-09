import logging
import aiohttp
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient
import base58
import json
import math
import statistics
from config import BotConfig, NetworkConfig, TradingParams
import time
import pandas as pd
import requests
from solana.rpc.commitment import Confirmed
from base58 import b58encode, b58decode
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from aiohttp import ClientTimeout
from asyncio import TimeoutError
from collections import defaultdict
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)

class RetryConfig:
    """Konfiguration für Retry-Mechanismen"""
    MAX_RETRIES = 3
    MIN_WAIT = 1  # Sekunden
    MAX_WAIT = 10  # Sekunden
    RPC_TIMEOUT = 30  # Sekunden
    API_TIMEOUT = 10  # Sekunden

class DataValidator:
    @staticmethod
    def validate_pool_data(data: Dict) -> bool:
        """Validiert Pool-Daten"""
        required_fields = ['liquidity', 'volume_24h', 'price', 'token_a', 'token_b']
        return all(field in data for field in required_fields)

    @staticmethod
    def validate_trade_params(params: Dict) -> bool:
        """Validiert Trade-Parameter"""
        required_fields = ['amount', 'slippage', 'token_address']
        return all(field in params for field in required_fields)

class EndpointConfig:
    """API und RPC Endpoint Konfiguration"""
    MAINNET_RPC = "https://api.mainnet-beta.solana.com"
    BACKUP_RPC = [
        "https://solana-api.projectserum.com",
        "https://rpc.ankr.com/solana"
    ]
    
    ORCA_API = "https://api.orca.so"
    ORCA_API_VERSION = "v1"
    
    @classmethod
    def get_pool_endpoint(cls, pool_address: str) -> str:
        return f"{cls.ORCA_API}/{cls.ORCA_API_VERSION}/pool/{pool_address}"
    
    @classmethod
    def get_whirlpool_endpoint(cls, pool_address: str) -> str:
        return f"{cls.ORCA_API}/{cls.ORCA_API_VERSION}/whirlpool/{pool_address}"

@retry(
    stop=stop_after_attempt(RetryConfig.MAX_RETRIES),
    wait=wait_exponential(multiplier=RetryConfig.MIN_WAIT, max=RetryConfig.MAX_WAIT),
    retry=retry_if_exception_type((TimeoutError, aiohttp.ClientError))
)
async def fetch_data_from_rpc(rpc_client: AsyncClient, method: str, params: List = None) -> Optional[Dict]:
    """
    Asynchrone RPC-Anfrage mit Retry-Mechanismus
    """
    try:
        response = await asyncio.wait_for(
            rpc_client.make_request(method, params or []),
            timeout=RetryConfig.RPC_TIMEOUT
        )
        
        if "result" in response:
            return response["result"]
        else:
            error = response.get('error', {})
            if error.get('code') == -32005:  # Rate limit error
                await asyncio.sleep(2)  # Spezielle Wartezeit für Rate Limits
                raise TimeoutError("Rate limit reached")
            logging.error(f"RPC-Anfrage fehlgeschlagen: {error}")
            return None
            
    except asyncio.TimeoutError:
        logging.warning(f"RPC Timeout für Methode {method}")
        raise TimeoutError(f"RPC Timeout: {method}")
    except Exception as e:
        logging.error(f"RPC-Anfrage fehlgeschlagen: {e}")
        return None

@retry(
    stop=stop_after_attempt(RetryConfig.MAX_RETRIES),
    wait=wait_exponential(multiplier=RetryConfig.MIN_WAIT, max=RetryConfig.MAX_WAIT),
    retry=retry_if_exception_type((TimeoutError, aiohttp.ClientError))
)
async def fetch_data_from_api(url: str, params: Dict = None) -> Optional[Dict]:
    """
    Asynchrone API-Anfrage mit Retry-Mechanismus
    """
    timeout = ClientTimeout(total=RetryConfig.API_TIMEOUT)
    
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:  # Rate limit
                    retry_after = int(response.headers.get('Retry-After', 1))
                    await asyncio.sleep(retry_after)
                    raise TimeoutError("Rate limit reached")
                else:
                    logging.error(f"API Status {response.status}: {url}")
                    return None
                    
    except asyncio.TimeoutError:
        logging.warning(f"API Timeout für URL {url}")
        raise TimeoutError(f"API Timeout: {url}")
    except Exception as e:
        logging.error(f"API-Anfrage fehlgeschlagen: {e}")
        return None

@dataclass
class OrcaPool:
    address: str
    token_a: str
    token_b: str
    token_a_symbol: str
    token_b_symbol: str
    liquidity: float
    volume_24h: float
    price: float
    fee: float
    price_change_24h: float
    created_at: datetime

class OrcaDataProvider:
    def __init__(self, config: Dict):
        self.config = config
        self.rpc = AsyncClient(
            config['network_config']['rpc_endpoint'],
            commitment=Confirmed
        )
        self.base_url = "https://api.orca.so"
        self.session = None
        self.pools: Dict[str, OrcaPool] = {}
        self.last_update = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def update_pools(self):
        """Aktualisiert alle Whirlpools"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
                
            async with self.session.get(f"{self.base_url}/v1/whirlpools") as response:
                if response.status == 200:
                    pools_data = await response.json()
                    
                    # Pools verarbeiten
                    for pool_data in pools_data:
                        if self._is_valid_pool(pool_data):
                            pool = OrcaPool(
                                address=pool_data['address'],
                                token_a=pool_data['tokenA']['mint'],
                                token_b=pool_data['tokenB']['mint'],
                                token_a_symbol=pool_data['tokenA'].get('symbol', 'Unknown'),
                                token_b_symbol=pool_data['tokenB'].get('symbol', 'Unknown'),
                                liquidity=float(pool_data.get('tvl', 0)),
                                volume_24h=float(pool_data.get('volume', {}).get('day', 0)),
                                price=float(pool_data.get('price', 0)),
                                fee=float(pool_data.get('fee', 0)) / 10000,
                                price_change_24h=float(pool_data.get('priceChange', {}).get('day', 0)),
                                created_at=datetime.fromtimestamp(pool_data.get('createdAt', 0))
                            )
                            self.pools[pool.address] = pool
                            
                    self.last_update = datetime.now()
                    logging.info(f"Updated {len(self.pools)} pools")
                    
                else:
                    logging.error(f"Pool update failed: {response.status}")
                    
        except Exception as e:
            logging.error(f"Error updating pools: {e}")
            
    def _is_valid_pool(self, pool_data: Dict) -> bool:
        """Prüft ob ein Pool für Trading relevant ist"""
        try:
            # USDC Pairs
            if pool_data.get('tokenB', {}).get('symbol') != 'USDC':
                return False
                
            # Minimum Liquidität
            if float(pool_data.get('tvl', 0)) < self.config['trading_params']['min_liquidity']:
                return False
                
            # Minimum Volumen
            if float(pool_data.get('volume', {}).get('day', 0)) < self.config['trading_params']['min_volume_24h']:
                return False
                
            return True
            
        except Exception as e:
            logging.error(f"Pool validation error: {e}")
            return False
            
    async def get_pool_price_history(
        self,
        pool_address: str,
        start_time: datetime,
        end_time: datetime
    ) -> pd.DataFrame:
        """Holt historische Preisdaten für einen Pool"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
                
            params = {
                'resolution': self.config['trading_params']['candle_interval'],
                'start': int(start_time.timestamp()),
                'end': int(end_time.timestamp())
            }
            
            url = f"{self.base_url}/v1/pool/{pool_address}/candles"
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data:
                        df = pd.DataFrame(data)
                        df['timestamp'] = pd.to_datetime(df['time'], unit='s')
                        return df
                        
            return pd.DataFrame()
            
        except Exception as e:
            logging.error(f"Error fetching price history: {e}")
            return pd.DataFrame()
            
    async def get_top_pools(self, limit: int = 10) -> List[OrcaPool]:
        """Holt Top Pools nach Volumen"""
        if datetime.now() - (self.last_update or datetime.min) > timedelta(minutes=1):
            await self.update_pools()
            
        return sorted(
            self.pools.values(),
            key=lambda x: x.volume_24h,
            reverse=True
        )[:limit]