import asyncio
import logging
from datetime import datetime
from rich.console import Console
from rich.live import Live
from rich.table import Table
from whirlpool import WhirlpoolClient
from wallet_manager import WalletManager
from trade_executor import TradeExecutor
from strategies.meme_strategy import MemeStrategy
import yaml
from utils.connection_manager import ConnectionPool, ConnectionType
from data.data_processor import DataProcessor
from typing import Dict
from ui.status_manager import StatusManager

console = Console()
logger = logging.getLogger(__name__)

class OrcaBot:
    def __init__(self, config_path: str = 'config/config.yaml'):
        # Config laden
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
            
        # Core Components
        self.whirlpool = WhirlpoolClient()
        self.wallet = None
        self.executor = None
        self.strategy = MemeStrategy(self.config['meme_strategy'])
        
        # State
        self.running = False
        self.errors = []
        
        # Connection Pool initialisieren
        self.conn_pool = ConnectionPool()
        
        # Data Processor
        self.data_processor = DataProcessor(self.config)
        
        self.ui = StatusManager()
        
    async def initialize(self):
        """Initialisiert Bot"""
        try:
            # Verbindungen aufbauen
            self.orca_api = await self.conn_pool.get_connection(ConnectionType.ORCA_API)
            self.orca_rpc = await self.conn_pool.get_connection(ConnectionType.ORCA_RPC)
            
            # Backup RPC vorbereiten
            self.backup_rpc = await self.conn_pool.get_connection(ConnectionType.SERUM_RPC)
            
            # Wallet Setup mit primärem RPC
            self.wallet = WalletManager(self.orca_rpc)
            if not await self.wallet.connect():
                # Fallback auf Backup RPC
                self.wallet = WalletManager(self.backup_rpc)
                if not await self.wallet.connect():
                    raise Exception("Failed to connect wallet")
                    
            # Data Processor initialisieren
            if not await self.data_processor.initialize():
                raise Exception("Failed to initialize data processor")
                
            # Data Pipeline starten
            await self.data_processor.start_pipeline()
            
            return True
            
        except Exception as e:
            logger.error(f"Initialization error: {e}")
            return False
            
    async def start(self):
        """Startet Bot mit UI"""
        if not await self.initialize():
            return
            
        self.ui.build_layout()
        
        # UI Task starten
        asyncio.create_task(self.ui.update_display())
        
        # Trading Loop
        while self.running:
            try:
                # 1. Pools aktualisieren
                pools = await self.whirlpool.get_all_pools()
                usdc_pools = [p for p in pools if self._is_usdc_pool(p)]
                
                # 2. Top Pools analysieren
                for pool in sorted(usdc_pools, key=lambda x: float(x.get('volume', {}).get('day', 0)), reverse=True)[:10]:
                    await self._process_pool(pool)
                    
                # UI Updates
                self.ui.wallet_info = await self._get_wallet_info()
                self.ui.pool_status = await self._get_pool_status()
                self.ui.connections = self._get_connection_status()
                
            except Exception as e:
                self.ui.errors.append({
                    'time': datetime.now(),
                    'message': str(e)
                })
                
    def _is_usdc_pool(self, pool: dict) -> bool:
        """Prüft ob es ein USDC Pool ist"""
        try:
            usdc_address = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
            return pool.get('tokenB', {}).get('mint') == usdc_address
        except:
            return False
            
    async def _execute_trade(self, pool: dict, signal: dict):
        """Führt einen Trade aus"""
        try:
            # Trade erstellen
            trade = Trade(
                pool_address=pool['address'],
                token_address=pool['tokenA']['mint'],
                type=signal['type'],
                amount=signal['amount'],
                price=signal['price'],
                timestamp=datetime.now()
            )
            
            # Trade ausführen
            success = await self.executor.execute_trade(trade)
            
            if success:
                console.print(f"[green]Trade executed: {trade.type} {trade.amount} @ {trade.price}[/green]")
            else:
                console.print(f"[red]Trade failed[/red]")
                
        except Exception as e:
            logger.error(f"Trade execution error: {e}")
            
    def _generate_status(self) -> Table:
        """Generiert Status-Tabelle"""
        table = Table(title="🤖 Bot Status")
        
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right")
        
        # Wallet Info
        if self.wallet:
            balance = self.wallet.get_sol_balance()
            table.add_row("SOL Balance", f"{balance:.4f}")
            
        # Trading Stats
        if self.executor:
            trades = len(self.executor.trades)
            profit = sum(t.profit or 0 for t in self.executor.trades)
            table.add_row("Total Trades", str(trades))
            table.add_row("Total Profit", f"${profit:.2f}")
            
        return table
        
    async def _handle_connection_error(self, conn_type: ConnectionType):
        """Behandelt Verbindungsfehler"""
        try:
            # Verbindung neu aufbauen
            connection = await self.conn_pool.get_connection(conn_type)
            await connection.connect()
            
            if not connection.healthy:
                # Auf Backup wechseln
                if conn_type == ConnectionType.ORCA_RPC:
                    logger.warning("Switching to backup RPC")
                    return await self.conn_pool.get_connection(ConnectionType.SERUM_RPC)
                    
            return connection
            
        except Exception as e:
            logger.error(f"Connection recovery failed: {e}")
            return None
            
    async def _process_pool(self, pool: Dict):
        """Verarbeitet Pool-Daten mit Pipeline"""
        try:
            # 1. Rohdaten zur Pipeline hinzufügen
            await self.data_processor.processing_queue.put(pool)
            
            # 2. Warten auf Verarbeitung
            await self.data_processor.processing_queue.join()
            
            # 3. Verarbeitete Daten holen
            market_data = await self.data_processor.get_cached_data(pool['address'])
            
            if market_data and market_data.get('indicators'):
                # 4. Trading Signal generieren
                signal = self.strategy.analyze(market_data)
                
                if signal.get('should_trade'):
                    await self._execute_trade(pool, signal)
                    
        except Exception as e:
            logger.error(f"Pool processing error: {e}")

async def main():
    bot = OrcaBot()
    await bot.start()

if __name__ == "__main__":
    asyncio.run(main()) 