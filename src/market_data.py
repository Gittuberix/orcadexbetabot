import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import asyncio
from config import BotConfig
import json
from dataclasses import dataclass
from enum import Enum
import time
import statistics

class DataSource(Enum):
    ORCA = "orca"

@dataclass
class PriceData:
    price: float
    volume_24h: float
    liquidity: float
    timestamp: datetime
    source: DataSource
    confidence: float = 1.0
    latency: float = 0.0  # Latency in milliseconds
    sequence_number: int = 0  # Order in which this data was received

@dataclass
class SourceStats:
    avg_latency: float = 0.0
    min_latency: float = float('inf')
    max_latency: float = 0.0
    reliability: float = 1.0  # Percentage of successful responses
    sequence_position: float = 0.0  # Average position in update sequence
    requests: int = 0
    failures: int = 0
    last_latencies: List[float] = None
    
    def __post_init__(self):
        if self.last_latencies is None:
            self.last_latencies = []

class MarketDataProvider:
    def __init__(self, config: BotConfig):
        self.config = config
        self.cache = {}
        self.cache_duration = config.trading_params.cache_duration
        
        # API endpoints
        self.endpoints = {
            DataSource.ORCA: config.network_config.orca_api
        }
        
        # Source statistics
        self.source_stats = {source: SourceStats() for source in DataSource}
        
        # Dynamic source weights based on performance
        self.base_weights = {
            DataSource.ORCA: 1.0      # Primary DEX
        }
        
        self.logger = logging.getLogger(__name__)
        
    def _update_source_stats(self, source: DataSource, latency: float, success: bool, sequence_pos: int):
        """Updates statistics for a data source"""
        stats = self.source_stats[source]
        stats.requests += 1
        
        if success:
            # Update latency stats
            stats.last_latencies.append(latency)
            if len(stats.last_latencies) > 100:  # Keep last 100 measurements
                stats.last_latencies.pop(0)
                
            stats.avg_latency = statistics.mean(stats.last_latencies)
            stats.min_latency = min(stats.min_latency, latency)
            stats.max_latency = max(stats.max_latency, latency)
            
            # Update sequence position (order of arrival)
            stats.sequence_position = (stats.sequence_position * (stats.requests - 1) + sequence_pos) / stats.requests
        else:
            stats.failures += 1
            
        # Update reliability
        stats.reliability = (stats.requests - stats.failures) / stats.requests
        
    def _calculate_dynamic_weight(self, source: DataSource) -> float:
        """Calculates dynamic weight based on source performance"""
        stats = self.source_stats[source]
        base_weight = self.base_weights[source]
        
        if stats.requests < 10:  # Not enough data
            return base_weight
            
        # Speed bonus: faster sources get up to 20% bonus
        avg_latencies = [s.avg_latency for s in self.source_stats.values() if s.requests >= 10]
        if not avg_latencies:
            speed_bonus = 1.0
        else:
            min_latency = min(avg_latencies)
            speed_bonus = 1.0 + 0.2 * (1 - (stats.avg_latency - min_latency) / stats.avg_latency)
            
        # Sequence bonus: earlier sources get up to 20% bonus
        sequence_bonus = 1.0 + 0.2 * (1 - stats.sequence_position / len(DataSource))
        
        # Combine factors
        dynamic_weight = base_weight * stats.reliability * speed_bonus * sequence_bonus
        
        return dynamic_weight
        
    async def get_token_data(self, token_address: str) -> Optional[Dict]:
        """Gets token data from Orca API"""
        try:
            # Check cache first
            cached = self.cache.get(token_address)
            if cached and (datetime.now() - cached['timestamp']).seconds < self.cache_duration:
                return cached['data']
            
            # Get data from Orca
            start_time = time.time()
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.endpoints[DataSource.ORCA]}/v1/token/{token_address}"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        token_data = {
                            'price': float(data['price']),
                            'volume_24h': float(data['volume24h']),
                            'liquidity': float(data['tvl']),
                            'last_update': datetime.now(),
                            'source': DataSource.ORCA.value,
                            'timing': {
                                'latency': (time.time() - start_time) * 1000
                            }
                        }
                        
                        # Cache the result
                        self.cache[token_address] = {
                            'timestamp': datetime.now(),
                            'data': token_data
                        }
                        
                        return token_data
                        
            return None
            
        except Exception as e:
            self.logger.error(f"Error fetching token data: {e}")
            return None
            
    def get_source_statistics(self) -> Dict[str, Dict]:
        """Returns detailed statistics for the Orca data source"""
        return {
            source.value: {
                'avg_latency': stats.avg_latency,
                'min_latency': stats.min_latency,
                'max_latency': stats.max_latency,
                'reliability': stats.reliability,
                'requests': stats.requests,
                'failures': stats.failures
            }
            for source, stats in self.source_stats.items()
        }