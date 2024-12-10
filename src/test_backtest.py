import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from rich.console import Console
from src.backtest.backtest_runner import BacktestRunner
from src.config.network_config import WHIRLPOOL_CONFIGS

console = Console()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_backtest():
    try:
        # Setup
        runner = BacktestRunner()
        
        # Zeitraum (letzte 7 Tage)
        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)
        
        # Teste SOL/USDC Pool
        pool_config = WHIRLPOOL_CONFIGS["SOL/USDC"]
        
        console.print("\n=== Starte Backtest ===")
        console.print(f"Pool: SOL/USDC")
        console.print(f"Zeitraum: {start_time} bis {end_time}")
        
        result = await runner.run_backtest(
            pool_address=pool_config["address"],
            start_time=start_time,
            end_time=end_time,
            initial_capital=Decimal("1000"),
            trade_size=Decimal("0.1"),
            interval_minutes=5
        )
        
        if result:
            console.print("\n=== Backtest Ergebnisse ===")
            console.print(f"Trades: {result.total_trades}")
            console.print(f"Gewonnene Trades: {result.winning_trades}")
            console.print(f"Win Rate: {(result.winning_trades/result.total_trades*100):.2f}%")
            console.print(f"Volumen: ${float(result.total_volume)/1e9:.2f}")
            console.print(f"Gebühren: ${float(result.total_fees_paid)/1e6:.4f}")
            console.print(f"Gas Kosten: ${float(result.total_gas_cost)/1e6:.4f}")
            console.print(f"Netto Profit: ${float(result.net_profit):.2f}")
            console.print(f"ROI: {float(result.roi):.2f}%")
            console.print(f"Max Drawdown: {float(result.max_drawdown):.2f}%")
            
    except Exception as e:
        logger.error(f"Fehler: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_backtest())