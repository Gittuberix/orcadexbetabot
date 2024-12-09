import asyncio
import logging
from datetime import datetime
from solana.rpc.async_api import AsyncClient
from orca_data import OrcaDataProvider
from interface import TerminalInterface
from config import BotConfig

async def test_connection():
    # Initialize configuration
    config = BotConfig()
    interface = TerminalInterface()
    
    # Initialize Solana RPC client
    rpc_client = AsyncClient(config.network_config.rpc_endpoint)
    data_provider = OrcaDataProvider(rpc_client, config)
    
    try:
        print("\n🔄 Initializing connection to Orca...")
        
        while True:
            # Get top pools
            pools = await data_provider.get_top_pools(limit=10)
            
            # Convert to display format
            display_pools = []
            for pool in pools:
                try:
                    # Get orderbook for spread calculation
                    orderbook = await data_provider.get_orderbook(pool['address'])
                    best_bid = orderbook['bids'][0]['price'] if orderbook and orderbook['bids'] else 0
                    best_ask = orderbook['asks'][0]['price'] if orderbook and orderbook['asks'] else 0
                    
                    display_pools.append({
                        'token_a': pool['tokenA']['symbol'],
                        'token_b': pool['tokenB']['symbol'],
                        'price': float(pool['price']),
                        'liquidity': float(pool['tvl']),
                        'volume_24h': float(pool['volume24h']),
                        'trades_24h': int(pool.get('numberOfTrades24h', 0)),
                        'price_change': float(pool.get('priceChange24h', 0)),
                        'best_bid': best_bid,
                        'best_ask': best_ask,
                        'last_update': datetime.now()
                    })
                except Exception as e:
                    logging.error(f"Error processing pool {pool.get('address')}: {e}")
                    continue
            
            # Update display
            await interface.update_display(display_pools)
            await asyncio.sleep(config.trading_params.update_interval)
            
    except KeyboardInterrupt:
        print("\n⚠️ Monitor stopped")
    except Exception as e:
        logging.error(f"\n❌ Error: {e}")
        raise
    finally:
        await rpc_client.close()

if __name__ == "__main__":
    try:
        asyncio.run(test_connection())
    except KeyboardInterrupt:
        print("\n⚠️ Monitor stopped") 