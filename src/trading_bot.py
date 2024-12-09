from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from orca_api import OrcaAPI
from monitor import TradingMonitor
import logging
import asyncio
import yaml
from datetime import datetime, timedelta
from price_feed import SolanaPriceFeed
from trade_executor import OrcaTradeExecutor
from orca_data import OrcaDataProvider

class SolanaOrcaBot:
    def __init__(self, config_path: str = 'config/config.yaml'):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
            
        # RPC Setup
        self.rpc = AsyncClient(
            self.config['network_config']['rpc_endpoint'],
            commitment=Confirmed
        )
        
        # Orca API
        self.orca = OrcaAPI()
        
        # Monitor
        self.monitor = TradingMonitor(config_path)
        
        # Price Feed
        self.price_feed = SolanaPriceFeed(config_path)
        
        # Trade Executor
        self.executor = OrcaTradeExecutor(
            self.rpc,
            self.wallet_keypair,
            self.config
        )
        
        # Orca Data Provider
        self.orca = OrcaDataProvider(self.config)
        
    async def start(self):
        """Startet den Trading Bot"""
        try:
            # Orca Pools initialisieren
            await self.orca.update_pools()
            
            # Trading Loop
            while True:
                # Top Pools abrufen
                top_pools = await self.orca.get_top_pools()
                
                for pool in top_pools:
                    # Trading Signal prüfen
                    signal = await self.check_trading_signal(pool)
                    
                    if signal and self.risk_manager.check_trade(signal, pool):
                        await self.execute_trade(pool, signal)
                        
                # Warten
                await asyncio.sleep(self.config['trading_params']['update_interval'])
                
        except Exception as e:
            logging.error(f"Bot error: {e}")
            
    async def check_trading_signal(self, pool: OrcaPool) -> Optional[Dict]:
        """Prüft Trading Signale für einen Pool"""
        try:
            # Preishistorie abrufen
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=24)
            
            price_history = await self.orca.get_pool_price_history(
                pool.address,
                start_time,
                end_time
            )
            
            if price_history.empty:
                return None
                
            # Market Data für Strategie
            market_data = {
                'price': pool.price,
                'liquidity': pool.liquidity,
                'volume_24h': pool.volume_24h,
                'price_change_24h': pool.price_change_24h,
                'price_history': price_history
            }
            
            # Strategie analysieren
            return await self.strategy.analyze(market_data)
            
        except Exception as e:
            logging.error(f"Signal check error: {e}")
            return None

async def main():
    # Logging Setup
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/trading.log'),
            logging.StreamHandler()
        ]
    )
    
    # Bot starten
    bot = SolanaOrcaBot()
    await bot.start()

if __name__ == "__main__":
    asyncio.run(main()) 