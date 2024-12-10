from typing import Optional
import asyncio
from data_fetcher import DataFetcher
from wallet_manager import WalletManager
from token_manager import TokenManager
from risk_manager import RiskManager
from data.orca_pipeline import OrcaPipeline
from models import TradingConfig, TradeStatus

class OrcaTradingBot:
    def __init__(self, config: TradingConfig):
        self.config = config
        self.data_fetcher = DataFetcher()
        self.wallet_manager = WalletManager()
        self.token_manager = TokenManager()
        self.risk_manager = RiskManager()
        self.pipeline = OrcaPipeline()
        
    async def initialize(self):
        """Bot-Initialisierung"""
        await self.data_fetcher.connect()
        await self.wallet_manager.connect_phantom()
        
    async def run_trading_loop(self):
        """Haupthandelszyklus"""
        while True:
            try:
                # Daten abrufen
                market_data = await self.data_fetcher.get_whirlpool_data()
                
                # Handelssignale analysieren
                signals = self.pipeline.analyze_data(market_data)
                
                # Risikobewertung
                if self.risk_manager.validate_trade(signals):
                    # Trade ausführen
                    await self.execute_trade(signals)
                    
                await asyncio.sleep(self.config.update_interval)
                
            except Exception as e:
                print(f"Fehler im Trading-Loop: {e}")
                await asyncio.sleep(5)
                
    async def execute_trade(self, signals):
        """Trade-Ausführung"""
        try:
            trade_status = await self.wallet_manager.execute_swap(
                token_in=signals.token_in,
                token_out=signals.token_out,
                amount=signals.amount
            )
            return trade_status
        except Exception as e:
            print(f"Trade-Ausführungsfehler: {e}")
            return TradeStatus.FAILED

async def main():
    config = TradingConfig()  # Standardkonfiguration laden
    bot = OrcaTradingBot(config)
    await bot.initialize()
    await bot.run_trading_loop()

if __name__ == "__main__":
    asyncio.run(main()) 