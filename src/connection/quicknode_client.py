from typing import Optional, Callable, Dict
import asyncio
import json
import logging
from solana.rpc.async_api import AsyncClient
from solana.publickey import PublicKey
from dotenv import load_dotenv
import os

logger = logging.getLogger(__name__)

class QuickNodeClient:
    def __init__(self):
        load_dotenv()
        self.rpc_url = os.getenv("QUICKNODE_RPC_URL")
        if not self.rpc_url:
            raise ValueError("QUICKNODE_RPC_URL nicht in .env gefunden")
            
        self.client: Optional[AsyncClient] = None
        self.whirlpool_program_id = PublicKey("whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc")
        self.subscriptions = {}
        
    async def connect(self):
        """Verbindung zu QuickNode herstellen"""
        try:
            self.client = AsyncClient(self.rpc_url)
            # Teste Verbindung
            response = await self.client.get_block_height()
            logger.info(f"QuickNode verbunden. Blockhöhe: {response['result']}")
            return True
        except Exception as e:
            logger.error(f"QuickNode Verbindungsfehler: {e}")
            return False
            
    async def get_pool_data(self, pool_address: str) -> Dict:
        """Hole Daten eines spezifischen Whirlpools"""
        try:
            pool_pubkey = PublicKey(pool_address)
            response = await self.client.get_account_info(pool_pubkey)
            
            if response['result']['value']:
                return self._decode_pool_data(response['result']['value']['data'])
            return None
        except Exception as e:
            logger.error(f"Fehler beim Abrufen von Pool {pool_address}: {e}")
            return None
            
    async def subscribe_to_pool(self, pool_address: str, callback: Callable):
        """Subscribe zu Updates eines Pools"""
        try:
            pool_pubkey = PublicKey(pool_address)
            sub_id = await self.client.account_subscribe(
                pool_pubkey,
                commitment="confirmed",
                encoding="jsonParsed"
            )
            
            self.subscriptions[pool_address] = {
                'sub_id': sub_id['result'],
                'callback': callback
            }
            
            logger.info(f"Subscribed zu Pool {pool_address}")
            return sub_id['result']
        except Exception as e:
            logger.error(f"Subscribe-Fehler für Pool {pool_address}: {e}")
            return None
            
    def _decode_pool_data(self, raw_data: bytes) -> Dict:
        """Decodiert die Whirlpool-Daten"""
        try:
            # Whirlpool-Layout-Dekodierung
            data = {
                'sqrtPrice': int.from_bytes(raw_data[0:8], 'little'),
                'tickCurrentIndex': int.from_bytes(raw_data[8:16], 'little'),
                'liquidity': int.from_bytes(raw_data[16:24], 'little'),
                'feeGrowthGlobalA': int.from_bytes(raw_data[24:32], 'little'),
                'feeGrowthGlobalB': int.from_bytes(raw_data[32:40], 'little')
            }
            
            # Berechne den aktuellen Preis
            price = (data['sqrtPrice'] / (2 ** 64)) ** 2
            
            return {
                'price': price,
                'liquidity': data['liquidity'] / (2 ** 64),
                'tick_current': data['tickCurrentIndex'],
                'fee_growth_a': data['feeGrowthGlobalA'],
                'fee_growth_b': data['feeGrowthGlobalB']
            }
        except Exception as e:
            logger.error(f"Fehler bei der Pool-Daten-Dekodierung: {e}")
            return {}
            
    async def close(self):
        """Verbindung schließen"""
        if self.client:
            await self.client.close()
            
    async def test_connection(self) -> bool:
        """Testet die QuickNode-Verbindung und Whirlpool-Zugriff"""
        try:
            # Test 1: Basis-RPC-Verbindung
            response = await self.client.get_block_height()
            if not response['result']:
                logger.error("Konnte keine Blockhöhe abrufen")
                return False
            
            # Test 2: Whirlpool-Programm-Zugriff
            sol_usdc_pool = "HJPjoWUrhoZzkNfRpHuieeFk9WcZWjwy6PBjZ81ngndJ"
            pool_data = await self.get_pool_data(sol_usdc_pool)
            if not pool_data:
                logger.error("Konnte keine Whirlpool-Daten abrufen")
                return False
            
            logger.info("QuickNode-Verbindung erfolgreich getestet")
            return True
        
        except Exception as e:
            logger.error(f"Verbindungstest fehlgeschlagen: {e}")
            return False