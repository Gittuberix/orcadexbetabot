import asyncio
import logging
from datetime import datetime, timedelta
from solana.rpc.async_api import AsyncClient
from src.orca_data import OrcaDataProvider
from src.backtest import Backtester
from src.strategy import TradingStrategy
from config import BotConfig

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def main():
    # Initialize components
    rpc_client = AsyncClient('https://api.mainnet-beta.solana.com')
    config = BotConfig()
    data_provider = OrcaDataProvider(rpc_client, config)
    strategy = TradingStrategy(config)
    
    # Create backtester
    backtester = Backtester(config, data_provider, strategy)
    
    # Test period
    end_time = datetime.now()
    start_time = end_time - timedelta(days=1)  # 24h test
    
    # Get test pools
    pools = await data_provider.get_top_pools(limit=5)  # Get top 5 pools
    if not pools:
        logging.error("No pools found")
        return
        
    logging.info("\nTop Pools by Volume:")
    for i, pool in enumerate(pools, 1):
        logging.info(
            f"{i}. {pool['tokenA']['symbol']}/{pool['tokenB']['symbol']} - "
            f"TVL: ${float(pool['tvl']):,.2f} - "
            f"24h Volume: ${float(pool['volume']['day']):,.2f}"
        )
        
    # Run backtest on first pool
    test_pool = pools[0]
    logging.info(f"\nRunning backtest on {test_pool['tokenA']['symbol']}/{test_pool['tokenB']['symbol']} pool")
    logging.info(f"Period: {start_time.strftime('%Y-%m-%d %H:%M')} to {end_time.strftime('%Y-%m-%d %H:%M')}")
    
    results = await backtester.run(test_pool['address'], start_time, end_time)
    
    if results:
        logging.info("\nBacktest Results:")
        logging.info(f"Total Trades: {results['total_trades']}")
        logging.info(f"Win Rate: {results['win_rate']*100:.1f}%")
        logging.info(f"Total Return: {results['total_return']:.2f}%")
        logging.info(f"Total Fees: ${results['total_fees']:.2f}")
        logging.info(f"Avg Price Impact: {results['avg_price_impact']*100:.2f}%")
        
        if results['trades']:
            logging.info("\nSample Trades:")
            for i, trade in enumerate(results['trades'][:5], 1):  # Show first 5 trades
                logging.info(
                    f"{i}. {trade['timestamp'].strftime('%Y-%m-%d %H:%M')} | "
                    f"{trade['type'].upper()} | "
                    f"Price: ${trade['price']:.6f} | "
                    f"Amount: {trade['amount']:.4f} | "
                    f"Impact: {trade['price_impact']*100:.2f}%"
                )
    else:
        logging.error("Backtest failed")
        
    await rpc_client.close()

if __name__ == "__main__":
    asyncio.run(main()) 