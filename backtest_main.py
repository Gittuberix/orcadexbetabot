import asyncio
from datetime import datetime, timedelta
from rich.console import Console
from src.backtest.backtest_engine import BacktestEngine
from src.config.trading_config import TradingConfig
from src.strategies.meme_strategy import MemeStrategy

console = Console()

async def run_backtest():
    try:
        # Initialize
        config = TradingConfig()
        strategy = MemeStrategy()
        engine = BacktestEngine(config, strategy)
        
        # Set backtest period
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)  # 1 week backtest
        
        # Run backtest
        console.print("[cyan]Starting backtest...[/cyan]")
        results = await engine.run(start_date, end_date)
        
        # Print results
        console.print("\n[green]Backtest Results:[/green]")
        console.print(f"Total Trades: {results['total_trades']}")
        console.print(f"Win Rate: {results['win_rate']:.2f}%")
        console.print(f"Total Profit: {results['total_profit']:.2f} SOL")
        console.print(f"Max Drawdown: {results['max_drawdown']:.2f}%")
        
    except Exception as e:
        console.print(f"[red]Backtest error: {e}[/red]")
        raise

if __name__ == "__main__":
    asyncio.run(run_backtest()) 