import asyncio
import logging
from solana.rpc.async_api import AsyncClient
from rich.console import Console
from typing import Dict, Optional
from datetime import datetime

from wallet_manager import WalletManager
from trade_executor import TradeExecutor
from strategies.meme_strategy import MemeStrategy
from data.token_fetcher import OrcaTokenFetcher

console = Console()
logger = logging.getLogger(__name__)

class OrcaTrader:
    def __init__(self, config: Dict):
        self.config = config
        self.rpc = AsyncClient(config['rpc_url'])
        self.wallet = WalletManager(self.rpc)
        self.token_fetcher = OrcaTokenFetcher()
        self.executor = None
        self.strategy = MemeStrategy(config['strategy'])
        self.running = False
        
    async def initialize(self):
        """Initialisiert den Trader"""
        try:
            # 1. Wallet verbinden
            if not await self.wallet.connect(self.config['wallet_path']):
                raise Exception("Failed to connect wallet")
                
            # 2. Trade Executor initialisieren
            self.executor = TradeExecutor(self.wallet, self.rpc, self.config)
            
            # 3. Initial Token-Daten laden
            await self.token_fetcher.fetch_all_tokens()
            
            return True
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return False
            
    async def start_trading(self):
        """Startet den Trading Loop"""
        if not self.executor:
            raise Exception("Trader not initialized")
            
        self.running = True
        console.print("[green]Starting trading bot...[/green]")
        
        try:
            while self.running:
                try:
                    # 1. Top Pools aktualisieren
                    pools = await self.token_fetcher.get_active_whirlpools()
                    
                    for pool in pools[:10]:  # Top 10 Pools
                        # 2. Pool analysieren
                        signal = await self.strategy.analyze_pool(pool)
                        
                        if signal['should_trade']:
                            # 3. Trade ausführen
                            success = await self.executor.execute_trade(
                                pool['address'],
                                signal['amount'],
                                signal['type']
                            )
                            
                            if success:
                                console.print(f"[green]Trade executed: {signal['type']} {signal['amount']} {pool['symbol']}[/green]")
                            else:
                                console.print("[red]Trade failed[/red]")
                                
                    # 4. Kurze Pause
                    await asyncio.sleep(self.config['update_interval'])
                    
                except Exception as e:
                    logger.error(f"Error in trading loop: {e}")
                    await asyncio.sleep(5)
                    
        except KeyboardInterrupt:
            console.print("[yellow]Stopping trading bot...[/yellow]")
        finally:
            self.running = False
            
    def stop(self):
        """Stoppt den Trading Bot"""
        self.running = False
        console.print("[yellow]Stopping bot...[/yellow]")

async def main():
    # Konfiguration
    config = {
        'rpc_url': 'https://api.mainnet-beta.solana.com',
        'wallet_path': 'config/wallet.json',
        'update_interval': 60,  # 1 Minute
        'strategy': {
            'min_volume': 10000,
            'min_liquidity': 50000,
            'max_slippage': 0.01
        }
    }
    
    # Bot starten
    trader = OrcaTrader(config)
    if await trader.initialize():
        await trader.start_trading()
    else:
        console.print("[red]Failed to initialize trader[/red]")

if __name__ == "__main__":
    asyncio.run(main()) 