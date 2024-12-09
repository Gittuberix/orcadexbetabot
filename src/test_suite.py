import asyncio
import logging
from datetime import datetime, timedelta
from data_fetcher import OrcaDataFetcher
from utils.logger import setup_logger
import yaml
import os

logger = setup_logger()

class TestSuite:
    def __init__(self):
        self.load_config()
        
    def load_config(self):
        """Lädt die Konfiguration"""
        try:
            with open('config/config.yaml', 'r') as f:
                self.config = yaml.safe_load(f)
                logger.info("Config loaded successfully")
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            raise
            
    async def test_rpc_connection(self):
        """Testet die RPC-Verbindung"""
        logger.info("Testing RPC connection...")
        fetcher = OrcaDataFetcher(self.config)
        try:
            slot = await fetcher.rpc.get_slot()
            logger.info(f"Current slot: {slot}")
            return True
        except Exception as e:
            logger.error(f"RPC test failed: {e}")
            return False
            
    async def test_whirlpool_data(self):
        """Testet das Abrufen von Whirlpool-Daten"""
        logger.info("Testing Whirlpool data fetching...")
        async with OrcaDataFetcher(self.config) as fetcher:
            try:
                pools = await fetcher._get_all_pools()
                if pools:
                    logger.info(f"Found {len(pools)} whirlpools")
                    # Ersten Pool analysieren
                    sample = pools[0]
                    logger.info(f"""
                    Sample Whirlpool:
                    Address: {sample['address']}
                    Token A: {sample['tokenA']['symbol']} ({sample['tokenA']['mint']})
                    Token B: {sample['tokenB']['symbol']} ({sample['tokenB']['mint']})
                    Liquidity: {sample['liquidity']}
                    """)
                    return True
                else:
                    logger.error("No whirlpools found")
                    return False
            except Exception as e:
                logger.error(f"Whirlpool test failed: {e}")
                return False
                
    async def test_price_history(self):
        """Testet das Abrufen von Preisdaten"""
        logger.info("Testing price history fetching...")
        async with OrcaDataFetcher(self.config) as fetcher:
            try:
                # Erst Pools holen
                pools = await fetcher._get_all_pools()
                if not pools:
                    logger.error("No pools available for price test")
                    return False
                    
                # USDC Pool finden
                usdc_pool = next((p for p in pools if p['tokenB']['symbol'] == 'USDC'), None)
                if not usdc_pool:
                    logger.error("No USDC pool found")
                    return False
                    
                # Preisdaten abrufen
                end_time = datetime.now()
                start_time = end_time - timedelta(hours=1)  # Nur 1 Stunde zum Testen
                
                history = await fetcher._fetch_pool_history(
                    usdc_pool['address'],
                    start_time,
                    end_time
                )
                
                if not history.empty:
                    logger.info(f"""
                    Price History:
                    Timeframe: {history['timestamp'].min()} to {history['timestamp'].max()}
                    Candles: {len(history)}
                    Columns: {history.columns.tolist()}
                    Sample Data:
                    {history.head()}
                    """)
                    return True
                else:
                    logger.error("No price history data")
                    return False
                    
            except Exception as e:
                logger.error(f"Price history test failed: {e}")
                return False

async def run_tests():
    """Führt alle Tests aus"""
    suite = TestSuite()
    
    tests = [
        ('RPC Connection', suite.test_rpc_connection()),
        ('Whirlpool Data', suite.test_whirlpool_data()),
        ('Price History', suite.test_price_history())
    ]
    
    results = []
    for name, test in tests:
        try:
            logger.info(f"\n{'='*20} Testing {name} {'='*20}")
            result = await test
            results.append((name, result))
        except Exception as e:
            logger.error(f"Test {name} failed with error: {e}")
            results.append((name, False))
            
    # Ergebnisse ausgeben
    print("\n" + "="*50)
    print("Test Results:")
    print("="*50)
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:.<30}{status}")

if __name__ == "__main__":
    asyncio.run(run_tests()) 