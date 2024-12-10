import asyncio
import logging
from datetime import datetime, timedelta
from rich.console import Console
from backtest_engine import BacktestEngine
from data_collector import DataCollector
from trading_manager import TradingManager
from risk_manager import RiskManager

console = Console()
logger = logging.getLogger(__name__)

async def run_24h_backtest():
    console.print("\n[bold cyan]Starting 24h Backtest[/bold cyan]")
    
    # Initialize components
    end_date = datetime.now()
    start_date = end_date - timedelta(days=1)
    
    backtest = BacktestEngine(
        start_date=start_date,
        end_date=end_date,
        initial_capital=1000  # USDC
    )
    
    # Run backtest
    console.print("\n[yellow]Running backtest simulation...[/yellow]")
    await backtest.run_backtest()
    
    # Generate report
    report = backtest.generate_report()
    
    # Display results
    console.print("\n[bold green]=== 24h Backtest Results ===[/bold green]")
    console.print(f"Total Return: {report['total_return']:.2f}%")
    console.print(f"Sharpe Ratio: {report['sharpe_ratio']:.2f}")
    console.print(f"Max Drawdown: {report['max_drawdown']:.2f}%")
    console.print(f"Win Rate: {report['win_rate']:.2f}%")
    console.print(f"Total Trades: {len(report['trades'])}")
    
    # Display trade breakdown
    console.print("\n[cyan]Trade Breakdown:[/cyan]")
    for trade in report['trades'][:5]:  # Show first 5 trades
        profit = trade.get('profit', 0)
        color = "green" if profit > 0 else "red"
        console.print(f"[{color}]Trade: {trade['type']} {trade['symbol']} - P/L: {profit:.2f}%[/{color}]")

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('backtest.log'),
            logging.StreamHandler()
        ]
    )
    
    try:
        asyncio.run(run_24h_backtest())
    except KeyboardInterrupt:
        console.print("\n[yellow]Backtest stopped by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Backtest error: {str(e)}[/red]")
        logger.exception("Backtest error occurred") 