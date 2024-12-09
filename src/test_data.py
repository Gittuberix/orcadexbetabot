import asyncio
import yaml
from data_fetcher import OrcaDataFetcher
from utils.logger import setup_logger
import os
from datetime import datetime, timedelta

logger = setup_logger()

async def test_data_fetching():
    """Testet das Abrufen und Validieren der Daten"""
    try:
        # Config laden und prüfen
        if not os.path.exists('config/config.yaml'):
            logger.error("Config file missing! Run setup.py first.")
            return
            
        with open('config/config.yaml', 'r') as f:
            config = yaml.safe_load(f)
            
        # API Endpoints prüfen
        logger.info("Testing API endpoints...")
        logger.info(f"RPC endpoint: {config['network_config']['rpc_endpoint']}")
        logger.info(f"Orca API: {config['network_config']['orca_api']}")
        
        # DataFetcher initialisieren
        async with OrcaDataFetcher(config) as fetcher:
            # 1. RPC Test
            logger.info("Testing Solana RPC...")
            slot = await fetcher.rpc.get_slot()
            logger.info(f"Current slot: {slot}")
            
            # 2. Pool Liste abrufen
            logger.info("Fetching pool list...")
            pools = await fetcher._get_all_pools()
            
            if not pools:
                logger.error("No pools returned!")
                return
                
            logger.info(f"Found {len(pools)} pools")
            
            # 3. Ersten Pool analysieren
            sample_pool = pools[0]
            logger.info(f"""
            Sample Pool:
            Address: {sample_pool.get('address')}
            Token A: {sample_pool.get('tokenA', {}).get('mint')}
            Token B: {sample_pool.get('tokenB', {}).get('mint')}
            TVL: {sample_pool.get('tvl')}
            Volume: {sample_pool.get('volume', {}).get('day')}
            """)
            
            # 4. Historische Daten für diesen Pool
            logger.info("Fetching historical data...")
            history = await fetcher._fetch_pool_history(
                sample_pool['address'],
                datetime.now() - timedelta(days=1),
                datetime.now()
            )
            
            if not history.empty:
                logger.info(f"""
                Historical Data:
                Shape: {history.shape}
                Columns: {history.columns.tolist()}
                Time Range: {history['timestamp'].min()} to {history['timestamp'].max()}
                Sample Data:
                {history.head()}
                """)
            else:
                logger.error("No historical data returned!")
                
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
        raise  # Re-raise für detaillierte Fehlerinfo

if __name__ == "__main__":
    try:
        asyncio.run(test_data_fetching())
    except KeyboardInterrupt:
        logger.info("Test manually stopped")
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}") 