from typing import Dict, List, Optional
import aiohttp
import logging
from datetime import datetime
import json
from pathlib import Path

class TokenFetcher:
    def __init__(self):
        self.base_url = "https://api.orca.so"
        self.cache_dir = Path("cache")
        self.cache_dir.mkdir(exist_ok=True)
        
    async def get_top_tokens(self) -> Dict:
        """Holt die Top Token von Orca"""
        try:
            async with aiohttp.ClientSession() as session:
                # Orca Whirlpools API für alle Pools
                async with session.get(f"{self.base_url}/v1/whirlpool/list") as response:
                    if response.status == 200:
                        pools = await response.json()
                        
                        # Token-Daten sammeln
                        tokens = {}
                        for pool in pools:
                            # Token A
                            token_a = pool.get('tokenA', {})
                            if token_a and token_a.get('mint'):
                                address = token_a['mint']
                                if address not in tokens:
                                    tokens[address] = {
                                        'symbol': token_a.get('symbol', 'Unknown'),
                                        'name': token_a.get('name', 'Unknown'),
                                        'price_usd': float(pool.get('tokenPrice', {}).get('tokenA', 0)),
                                        'volume_24h': float(pool.get('volume', {}).get('day', 0)),
                                        'liquidity': float(pool.get('tvl', 0)),
                                        'price_change_24h': float(pool.get('priceChange', {}).get('day', 0)),
                                        'pools': [pool['address']]
                                    }
                                else:
                                    tokens[address]['volume_24h'] += float(pool.get('volume', {}).get('day', 0))
                                    tokens[address]['pools'].append(pool['address'])
                            
                            # Token B
                            token_b = pool.get('tokenB', {})
                            if token_b and token_b.get('mint'):
                                address = token_b['mint']
                                if address not in tokens:
                                    tokens[address] = {
                                        'symbol': token_b.get('symbol', 'Unknown'),
                                        'name': token_b.get('name', 'Unknown'),
                                        'price_usd': float(pool.get('tokenPrice', {}).get('tokenB', 0)),
                                        'volume_24h': float(pool.get('volume', {}).get('day', 0)),
                                        'liquidity': float(pool.get('tvl', 0)),
                                        'price_change_24h': float(pool.get('priceChange', {}).get('day', 0)),
                                        'pools': [pool['address']]
                                    }
                                else:
                                    tokens[address]['volume_24h'] += float(pool.get('volume', {}).get('day', 0))
                                    tokens[address]['pools'].append(pool['address'])
                        
                        # Nach Volumen sortieren
                        sorted_tokens = dict(sorted(
                            tokens.items(),
                            key=lambda x: x[1]['volume_24h'],
                            reverse=True
                        ))
                        
                        return sorted_tokens
                        
            return {}
            
        except Exception as e:
            logging.error(f"Fehler beim Abrufen der Top Token: {e}")
            return {}
            
    async def get_token_info(self, token_address: str) -> Optional[Dict]:
        """Holt detaillierte Token-Informationen"""
        try:
            async with aiohttp.ClientSession() as session:
                # Token-Daten von Orca
                async with session.get(
                    f"{self.base_url}/v1/token/{token_address}"
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'symbol': data.get('symbol', 'Unknown'),
                            'name': data.get('name', 'Unknown'),
                            'price_usd': float(data.get('price', 0)),
                            'volume_24h': float(data.get('volume24h', 0)),
                            'liquidity': float(data.get('tvl', 0)),
                            'price_change_24h': float(data.get('priceChange24h', 0)),
                            'holders': int(data.get('holders', 0)),
                            'pools': data.get('pools', [])
                        }
                        
            return None
            
        except Exception as e:
            logging.error(f"Fehler beim Token-Info Abruf: {e}")
            return None
            
    def _save_to_cache(self, token_address: str, data: Dict):
        """Speichert Token-Daten im Cache"""
        try:
            cache_file = self.cache_dir / f"{token_address}.json"
            with open(cache_file, 'w') as f:
                json.dump({
                    'data': data,
                    'timestamp': datetime.now().isoformat()
                }, f)
        except Exception as e:
            logging.error(f"Cache Speicher-Fehler: {e}")

# Test-Funktion
async def test_fetcher():
    fetcher = TokenFetcher()
    tokens = await fetcher.get_top_tokens()
    print(json.dumps(tokens, indent=2))

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_fetcher()) 