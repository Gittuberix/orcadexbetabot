from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import asyncio
import aioredis
import logging
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)

@dataclass
class MarketData:
    pool_address: str
    price: float
    volume: float
    liquidity: float
    timestamp: datetime
    indicators: Dict = None

class DataProcessor:
    """Verarbeitet und cached Marktdaten"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.cache = {}
        self.redis = None
        self.processing_queue = asyncio.Queue()
        self.pipeline_running = False
        
    async def initialize(self):
        """Initialisiert Redis-Verbindung"""
        try:
            self.redis = await aioredis.create_redis_pool(
                self.config['redis_url'],
                encoding='utf-8'
            )
            # Start Background Tasks
            asyncio.create_task(self._process_queue())
            return True
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            return False
            
    async def process_market_data(self, raw_data: Dict) -> MarketData:
        """Verarbeitet Rohdaten"""
        try:
            # Queue für asynchrone Verarbeitung
            await self.processing_queue.put(raw_data)
            
            # Basis-Daten sofort zurückgeben
            return MarketData(
                pool_address=raw_data['address'],
                price=float(raw_data['price']),
                volume=float(raw_data.get('volume', 0)),
                liquidity=float(raw_data.get('liquidity', 0)),
                timestamp=datetime.now()
            )
        except Exception as e:
            logger.error(f"Data processing error: {e}")
            return None
            
    async def _process_queue(self):
        """Verarbeitet Queue im Hintergrund"""
        while True:
            try:
                raw_data = await self.processing_queue.get()
                
                # Technische Analyse
                indicators = await self._calculate_indicators(raw_data)
                
                # Cache aktualisieren
                await self._update_cache(raw_data['address'], {
                    **raw_data,
                    'indicators': indicators
                })
                
                self.processing_queue.task_done()
                
            except Exception as e:
                logger.error(f"Queue processing error: {e}")
            await asyncio.sleep(0.1)
            
    async def _calculate_indicators(self, data: Dict) -> Dict:
        """Berechnet technische Indikatoren"""
        try:
            # Historie laden
            history = await self._get_price_history(data['address'])
            df = pd.DataFrame(history)
            
            if len(df) > 0:
                # Indikatoren berechnen
                df['sma_20'] = df['price'].rolling(window=20).mean()
                df['ema_50'] = df['price'].ewm(span=50).mean()
                df['rsi'] = self._calculate_rsi(df['price'])
                df['volatility'] = df['price'].rolling(window=20).std()
                
                return {
                    'sma_20': df['sma_20'].iloc[-1],
                    'ema_50': df['ema_50'].iloc[-1],
                    'rsi': df['rsi'].iloc[-1],
                    'volatility': df['volatility'].iloc[-1]
                }
            return {}
            
        except Exception as e:
            logger.error(f"Indicator calculation error: {e}")
            return {}
            
    async def _update_cache(self, pool_address: str, data: Dict):
        """Aktualisiert Cache"""
        try:
            # Memory Cache
            self.cache[pool_address] = data
            
            # Redis Cache
            if self.redis:
                # Compress & Store
                await self.redis.hset(
                    f"pool:{pool_address}",
                    "latest",
                    self._compress_data(data)
                )
                
                # Historie aktualisieren
                await self.redis.zadd(
                    f"history:{pool_address}",
                    int(datetime.now().timestamp()),
                    self._compress_data(data)
                )
                
                # Alte Daten löschen
                cutoff = int((datetime.now() - timedelta(days=7)).timestamp())
                await self.redis.zremrangebyscore(
                    f"history:{pool_address}",
                    0,
                    cutoff
                )
                
        except Exception as e:
            logger.error(f"Cache update error: {e}")
            
    async def get_cached_data(self, pool_address: str) -> Optional[Dict]:
        """Holt gecachte Daten"""
        try:
            # Erst Memory Cache
            if pool_address in self.cache:
                return self.cache[pool_address]
                
            # Dann Redis
            if self.redis:
                data = await self.redis.hget(f"pool:{pool_address}", "latest")
                if data:
                    return self._decompress_data(data)
                    
            return None
            
        except Exception as e:
            logger.error(f"Cache retrieval error: {e}")
            return None
            
    async def _get_price_history(self, pool_address: str) -> List[Dict]:
        """Holt Preishistorie"""
        try:
            if self.redis:
                # Letzte 24h
                start = int((datetime.now() - timedelta(hours=24)).timestamp())
                end = int(datetime.now().timestamp())
                
                data = await self.redis.zrangebyscore(
                    f"history:{pool_address}",
                    start,
                    end
                )
                
                return [self._decompress_data(d) for d in data]
            return []
            
        except Exception as e:
            logger.error(f"History retrieval error: {e}")
            return [] 
            
    def _calculate_rsi(self, prices: pd.Series, periods: int = 14) -> pd.Series:
        """Berechnet RSI Indikator"""
        delta = prices.diff()
        
        # Gewinne und Verluste trennen
        gains = delta.copy()
        losses = delta.copy()
        gains[gains < 0] = 0
        losses[losses > 0] = 0
        losses = abs(losses)
        
        # Erste Durchschnitte
        avg_gain = gains.rolling(window=periods).mean()
        avg_loss = losses.rolling(window=periods).mean()
        
        # RSI Berechnung
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
        
    def _compress_data(self, data: Dict) -> str:
        """Komprimiert Daten für Redis"""
        try:
            # Nur wichtige Felder speichern
            compressed = {
                'price': float(data['price']),
                'volume': float(data.get('volume', 0)),
                'liquidity': float(data.get('liquidity', 0)),
                'timestamp': int(datetime.now().timestamp())
            }
            
            if 'indicators' in data:
                compressed['indicators'] = {
                    k: float(v) for k, v in data['indicators'].items()
                }
                
            return json.dumps(compressed)
            
        except Exception as e:
            logger.error(f"Compression error: {e}")
            return "{}"
            
    def _decompress_data(self, data_str: str) -> Dict:
        """Dekomprimiert Redis-Daten"""
        try:
            data = json.loads(data_str)
            data['timestamp'] = datetime.fromtimestamp(data['timestamp'])
            return data
        except Exception as e:
            logger.error(f"Decompression error: {e}")
            return {}
            
    async def start_pipeline(self):
        """Startet die Datenpipeline"""
        self.pipeline_running = True
        asyncio.create_task(self._run_pipeline())
        
    async def _run_pipeline(self):
        """Hauptpipeline für Datenverarbeitung"""
        while self.pipeline_running:
            try:
                # 1. Daten aus Queue holen
                while not self.processing_queue.empty():
                    raw_data = await self.processing_queue.get()
                    
                    # 2. Basis-Validierung
                    if not self._validate_raw_data(raw_data):
                        continue
                        
                    # 3. Technische Analyse
                    indicators = await self._calculate_indicators(raw_data)
                    
                    # 4. Daten anreichern
                    enriched_data = await self._enrich_market_data(raw_data, indicators)
                    
                    # 5. Cache aktualisieren
                    await self._update_cache(raw_data['address'], enriched_data)
                    
                    # 6. Cleanup
                    self.processing_queue.task_done()
                    
                # Warten auf neue Daten
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Pipeline error: {e}")
                await asyncio.sleep(1)
                
    def _validate_raw_data(self, data: Dict) -> bool:
        """Validiert Rohdaten"""
        required_fields = ['address', 'price']
        
        try:
            # Pflichtfelder prüfen
            if not all(field in data for field in required_fields):
                return False
                
            # Preisvalidierung
            price = float(data['price'])
            if price <= 0:
                return False
                
            # Volumen (optional)
            if 'volume' in data:
                volume = float(data['volume'])
                if volume < 0:
                    return False
                    
            return True
            
        except Exception:
            return False
            
    async def _enrich_market_data(self, raw_data: Dict, indicators: Dict) -> Dict:
        """Reichert Marktdaten an"""
        try:
            # Basis-Daten
            enriched = {
                'address': raw_data['address'],
                'price': float(raw_data['price']),
                'volume': float(raw_data.get('volume', 0)),
                'liquidity': float(raw_data.get('liquidity', 0)),
                'timestamp': datetime.now(),
                'indicators': indicators
            }
            
            # Zusätzliche Metriken
            if 'indicators' in indicators:
                rsi = indicators['rsi']
                enriched['market_state'] = {
                    'overbought': rsi > 70,
                    'oversold': rsi < 30,
                    'trend': 'up' if indicators['sma_20'] > indicators['ema_50'] else 'down',
                    'volatility': indicators['volatility']
                }
                
            return enriched
            
        except Exception as e:
            logger.error(f"Data enrichment error: {e}")
            return raw_data