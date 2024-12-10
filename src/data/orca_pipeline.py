import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import aiohttp
from rich.console import Console
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient
from orca_whirlpool.context import WhirlpoolContext
from orca_whirlpool.constants import ORCA_WHIRLPOOL_PROGRAM_ID
from orca_whirlpool.utils import PriceMath, DecimalUtil
from src.models import WhirlpoolData, TradeData
from src.config.network_config import get_rpc_client
import pandas as pd
import numpy as np

console = Console()
logger = logging.getLogger(__name__)

class OrcaPipeline:
    def __init__(self):
        self.connection = None
        self.ctx = None
        self.session = None
        self.whirlpools = {}
        self.historical_data = {}
        self.price_cache = {}
        self.is_running = False
        
    async def initialize(self):
        """Initialisiert die Pipeline mit QuickNode"""
        self.connection = await get_rpc_client()
        self.ctx = WhirlpoolContext(
            ORCA_WHIRLPOOL_PROGRAM_ID,
            self.connection,
            None
        )
        self.session = aiohttp.ClientSession()
        
        try:
            # Hole alle aktiven Whirlpools
            async with self.session.get("https://api.mainnet.orca.so/v1/whirlpool/list") as resp:
                if resp.status != 200:
                    logger.error(f"API Error: {resp.status}")
                    self.whirlpools = DEFAULT_WHIRLPOOLS
                    return
                    
                data = await resp.json()
                for pool in data["whirlpools"]:
                    if pool["whitelisted"]:
                        symbol = f"{pool['tokenA']['symbol']}/{pool['tokenB']['symbol']}"
                        self.whirlpools[symbol] = {
                            "address": pool["address"],
                            "token_a": pool["tokenA"]["mint"],
                            "token_b": pool["tokenB"]["mint"],
                            "decimals_a": pool["tokenA"]["decimals"],
                            "decimals_b": pool["tokenB"]["decimals"],
                            "fee_rate": pool["lpFeeRate"]
                        }
                        
            logger.info(f"✓ {len(self.whirlpools)} Whirlpools geladen")
            
        except Exception as e:
            logger.error(f"Fehler beim Laden der Whirlpools: {e}")
            self.whirlpools = DEFAULT_WHIRLPOOLS
            
    async def fetch_live_data(self, pool_name: str) -> Optional[WhirlpoolData]:
        """Holt Live-Daten via QuickNode"""
        if pool_name not in self.whirlpools:
            logger.error(f"Unbekannter Pool: {pool_name}")
            return None
            
        try:
            pool_config = self.whirlpools[pool_name]
            
            # Hole Pool Account via QuickNode
            account_info = await self.connection.get_account_info(
                Pubkey.from_string(pool_config["address"])
            )
            
            if not account_info or not account_info.value:
                logger.error(f"Keine Account-Daten für {pool_name}")
                return None
                
            # Parse Whirlpool Daten
            whirlpool = await self.ctx.fetcher.get_whirlpool(
                Pubkey.from_string(pool_config["address"])
            )
            
            # Berechne Preis
            price = PriceMath.sqrt_price_x64_to_price(
                whirlpool.sqrt_price,
                pool_config["decimals_a"],
                pool_config["decimals_b"]
            )
            
            # Hole zusätzliche Stats von Orca API
            async with self.session.get(
                f"https://api.mainnet.orca.so/v1/whirlpool/{pool_config['address']}/stats"
            ) as resp:
                stats = await resp.json()
                volume_24h = float(stats.get("volume24h", 0))
            
            whirlpool_data = WhirlpoolData(
                pool_name=pool_name,
                price=float(DecimalUtil.to_fixed(price, pool_config["decimals_b"])),
                liquidity=whirlpool.liquidity,
                volume_24h=volume_24h,
                fee_rate=pool_config["fee_rate"],
                timestamp=datetime.now()
            )
            
            self.update_price_cache(pool_name, whirlpool_data)
            return whirlpool_data
            
        except Exception as e:
            logger.error(f"Fehler beim Abrufen von Live-Daten für {pool_name}: {e}")
            return None
            
    def update_price_cache(self, pool_name: str, data: WhirlpoolData):
        """Aktualisiert den Preis-Cache"""
        if pool_name not in self.price_cache:
            self.price_cache[pool_name] = []
            
        self.price_cache[pool_name].append({
            'price': data.price,
            'timestamp': data.timestamp
        })
        
        # Behalte nur die letzten 24h
        cutoff = datetime.now() - timedelta(hours=24)
        self.price_cache[pool_name] = [
            p for p in self.price_cache[pool_name]
            if p['timestamp'] > cutoff
        ]
        
    def calculate_metrics(self, pool_name: str) -> Dict:
        """Berechnet wichtige Metriken"""
        if pool_name not in self.price_cache:
            return {}
            
        prices = [p['price'] for p in self.price_cache[pool_name]]
        if len(prices) < 2:
            return {}
            
        prices_array = np.array(prices)
        returns = np.diff(np.log(prices_array))
        
        return {
            'volatility': float(np.std(returns) * np.sqrt(len(returns))),
            'price_change_1h': (prices[-1] / prices[-60] - 1) if len(prices) >= 60 else 0,
            'price_change_24h': (prices[-1] / prices[0] - 1),
            'current_price': prices[-1],
            'min_price_24h': min(prices),
            'max_price_24h': max(prices)
        }
        
    async def start_monitoring(self, pool_names: List[str], interval: float = 1.0):
        """Startet kontinuierliches Monitoring"""
        self.is_running = True
        
        while self.is_running:
            for pool_name in pool_names:
                data = await self.fetch_live_data(pool_name)
                if data:
                    metrics = self.calculate_metrics(pool_name)
                    
                    # Log wichtige Änderungen
                    if metrics.get('price_change_1h', 0) > 0.01:  # 1% Änderung
                        logger.info(
                            f"{pool_name} 1h Änderung: "
                            f"{metrics['price_change_1h']:.2%}"
                        )
                        
            await asyncio.sleep(interval)
            
    async def stop_monitoring(self):
        """Stoppt das Monitoring"""
        self.is_running = False
        
    async def fetch_historical_data(
        self,
        pool_name: str,
        start_time: datetime,
        end_time: datetime = None
    ) -> List[TradeData]:
        """Holt historische Handelsdaten"""
        if not end_time:
            end_time = datetime.now()
            
        try:
            pool_address = self.whirlpools[pool_name]["address"]
            async with self.session.get(
                f"https://api.mainnet.orca.so/v1/whirlpool/{pool_address}/trades",
                params={
                    "start": int(start_time.timestamp()),
                    "end": int(end_time.timestamp())
                }
            ) as resp:
                data = await resp.json()
                
                trades = []
                for trade in data["trades"]:
                    trades.append(TradeData(
                        pool_name=pool_name,
                        price=float(trade["price"]),
                        amount=float(trade["amount"]),
                        side=trade["side"],
                        timestamp=datetime.fromtimestamp(trade["timestamp"])
                    ))
                    
                # Cache für Backtest
                key = f"{pool_name}_{start_time.timestamp()}_{end_time.timestamp()}"
                self.historical_data[key] = trades
                
                return trades
                
        except Exception as e:
            logger.error(f"Fehler beim Abrufen historischer Daten für {pool_name}: {e}")
            return []
            
    def get_cached_historical_data(
        self,
        pool_name: str,
        start_time: datetime,
        end_time: datetime
    ) -> Optional[List[TradeData]]:
        """Holt gecachte historische Daten"""
        key = f"{pool_name}_{start_time.timestamp()}_{end_time.timestamp()}"
        return self.historical_data.get(key)
        
    async def close(self):
        """Schließt die Pipeline"""
        if self.session:
            await self.session.close()