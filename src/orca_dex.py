from typing import Dict, Optional, List
import logging
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from anchorpy import Program, Provider, Wallet
import base58
from solana.transaction import Transaction
import json
from solders.keypair import Keypair
from solders.system_program import CreateAccountParams
from solana.spl.token.instructions import (
    initialize_account, InitializeAccountParams,
    create_associated_token_account, get_associated_token_address
)
import struct
import asyncio
from datetime import datetime, timedelta
import aiohttp

class OrcaDEX:
    def __init__(self, provider: Provider):
        self.provider = provider
        self.program_id = Pubkey.from_string("9W959DqEETiGZocYWCQPaJ6sBmUzgfxXfqGeTEdp3aQP")
        self.token_program = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
        self.pools: Dict[str, Dict] = {}
        self.whirlpools: Dict[str, Dict] = {}
        
    async def initialize(self):
        """Initialisiert die DEX-Verbindung"""
        try:
            # Lade alle aktiven Pools
            await self.load_pools()
            # Starte Pool-Monitoring
            asyncio.create_task(self.monitor_pools())
            return True
        except Exception as e:
            logging.error(f"DEX Initialisierung fehlgeschlagen: {e}")
            return False

    async def load_pools(self):
        """Lädt alle aktiven Pools von Orca"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://api.orca.so/v1/whirlpool/list') as response:
                    pools = await response.json()
                    
            for pool in pools:
                pool_address = pool['address']
                self.pools[pool_address] = {
                    'token_a': pool['tokenA'],
                    'token_b': pool['tokenB'],
                    'fee': pool['fee'],
                    'liquidity': pool['liquidity'],
                    'price': pool['price'],
                    'volume_24h': pool['volume24h'],
                    'last_update': datetime.now()
                }
                
        except Exception as e:
            logging.error(f"Fehler beim Laden der Pools: {e}")
            raise

    async def monitor_pools(self):
        """Überwacht Pools auf Änderungen"""
        while True:
            try:
                for pool_address in list(self.pools.keys()):
                    pool_data = await self.get_pool_data(pool_address)
                    if pool_data:
                        self.pools[pool_address].update(pool_data)
                        
                await asyncio.sleep(1)  # 1 Sekunde Pause zwischen Updates
                
            except Exception as e:
                logging.error(f"Fehler beim Pool-Monitoring: {e}")
                await asyncio.sleep(5)  # Längere Pause bei Fehler

    async def get_pool_data(self, pool_address: str) -> Optional[Dict]:
        """Holt aktuelle Pool-Daten"""
        try:
            account_info = await self.provider.connection.get_account_info(
                Pubkey.from_string(pool_address)
            )
            
            if not account_info or not account_info.data:
                return None
                
            # Pool-Daten parsen
            data = account_info.data
            
            # Whirlpool Layout parsen
            pool_data = self._parse_whirlpool_data(data)
            
            # Zusätzliche Marktdaten abrufen
            async with aiohttp.ClientSession() as session:
                url = f"https://api.orca.so/v1/whirlpool/{pool_address}/stats"
                async with session.get(url) as response:
                    market_stats = await response.json()
                    
            pool_data.update(market_stats)
            return pool_data
            
        except Exception as e:
            logging.error(f"Fehler beim Abrufen der Pool-Daten: {e}")
            return None

    def _parse_whirlpool_data(self, data: bytes) -> Dict:
        """Parst Whirlpool-Daten"""
        try:
            # Whirlpool Layout:
            # - Token A Mint (32)
            # - Token B Mint (32)
            # - Token A Vault (32)
            # - Token B Vault (32)
            # - Fee Rate (8)
            # - Tick Spacing (2)
            # - Tick Current Index (2)
            # - Sqrt Price (16)
            # - Liquidity (16)
            # ...
            
            offset = 0
            token_a_mint = Pubkey(data[offset:offset+32])
            offset += 32
            token_b_mint = Pubkey(data[offset:offset+32])
            offset += 32
            token_a_vault = Pubkey(data[offset:offset+32])
            offset += 32
            token_b_vault = Pubkey(data[offset:offset+32])
            offset += 32
            
            fee_rate = int.from_bytes(data[offset:offset+8], 'little')
            offset += 8
            
            tick_spacing = int.from_bytes(data[offset:offset+2], 'little')
            offset += 2
            
            tick_current = int.from_bytes(data[offset:offset+2], 'little')
            offset += 2
            
            sqrt_price = int.from_bytes(data[offset:offset+16], 'little')
            offset += 16
            
            liquidity = int.from_bytes(data[offset:offset+16], 'little')
            
            # Preis berechnen
            price = (sqrt_price / 2**64) ** 2
            
            return {
                'token_a_mint': str(token_a_mint),
                'token_b_mint': str(token_b_mint),
                'token_a_vault': str(token_a_vault),
                'token_b_vault': str(token_b_vault),
                'fee_rate': fee_rate / 1_000_000,  # Convert to percentage
                'tick_spacing': tick_spacing,
                'tick_current': tick_current,
                'price': price,
                'liquidity': liquidity,
                'last_update': datetime.now()
            }
            
        except Exception as e:
            logging.error(f"Fehler beim Parsen der Whirlpool-Daten: {e}")
            raise

    async def get_token_price(self, token_address: str) -> Optional[float]:
        """Ermittelt den Preis eines Tokens in USDC"""
        try:
            # Suche USDC Pool für den Token
            usdc_mint = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
            for pool in self.pools.values():
                if (pool['token_a'] == token_address and pool['token_b'] == usdc_mint) or \
                   (pool['token_b'] == token_address and pool['token_a'] == usdc_mint):
                    return pool['price']
            return None
        except Exception as e:
            logging.error(f"Fehler beim Abrufen des Token-Preises: {e}")
            return None

    async def get_pool_liquidity(self, pool_address: str) -> Optional[float]:
        """Ermittelt die Liquidität eines Pools in USD"""
        try:
            pool = self.pools.get(pool_address)
            if not pool:
                return None
                
            # Hole Preise beider Token
            token_a_price = await self.get_token_price(pool['token_a'])
            token_b_price = await self.get_token_price(pool['token_b'])
            
            if not token_a_price or not token_b_price:
                return None
                
            # Berechne Gesamtliquidität
            return pool['liquidity'] * (token_a_price + token_b_price)
            
        except Exception as e:
            logging.error(f"Fehler beim Abrufen der Pool-Liquidität: {e}")
            return None