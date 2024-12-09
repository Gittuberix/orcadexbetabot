import asyncio
import sys
from pathlib import Path

# Fügen Sie das src Verzeichnis zum Python Path hinzu
src_path = str(Path(__file__).parent.parent)
if src_path not in sys.path:
    sys.path.append(src_path)

from src.backtest.engine import WhirlpoolBacktestEngine, BacktestPeriod
from rich.console import Console
import click

console = Console()

@click.command()
@click.option('--periods', '-p', multiple=True, 
              type=click.Choice(['1h', '8h', '1d', '2d', '3d', '7d', '30d', '90d']),
              default=['1d'],
              help='Backtest periods to run')
@click.option('--capital', '-c', default=1.0, help='Initial capital in SOL')
@click.option('--save-results/--no-save-results', default=True, help='Save results to file')
async def run_backtests(periods, capital, save_results):
    """Führt Backtests für gewählte Zeiträume aus"""
    
    # Perioden mapping
    period_map = {
        '1h': BacktestPeriod.HOUR_1,
        '8h': BacktestPeriod.HOUR_8,
        '1d': BacktestPeriod.DAY_1,
        '2d': BacktestPeriod.DAY_2,
        '3d': BacktestPeriod.DAY_3,
        '7d': BacktestPeriod.DAY_7,
        '30d': BacktestPeriod.DAY_30,
        '90d': BacktestPeriod.DAY_90
    }
    
    selected_periods = [period_map[p] for p in periods]
    results = {}
    
    for period in selected_periods:
        console.print(f"\n[bold cyan]{'='*50}[/bold cyan]")
        engine = WhirlpoolBacktestEngine(period, initial_capital=capital)
        await engine.run_backtest()
        
        # Ergebnisse sammeln
        results[engine._get_period_name()] = {
            'trades': len(engine.trades),
            'pnl': (engine.current_capital - engine.initial_capital) / engine.initial_capital * 100,
            'final_capital': engine.current_capital
        }
        
    # Zusammenfassung anzeigen
    console.print("\n[bold cyan] Backtest Summary[/bold cyan]")
    for period, result in results.items():
        pnl_color = "green" if result['pnl'] > 0 else "red"
        console.print(f"\n{period}:")
        console.print(f"Trades: {result['trades']}")
        console.print(f"Final Capital: {result['final_capital']:.4f} SOL")
        console.print(f"P/L: [{pnl_color}]{result['pnl']:+.2f}%[/{pnl_color}]")
        
    if save_results:
        save_path = Path('results') / f"backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(save_path, 'w') as f:
            json.dump(results, f, indent=2)
        console.print(f"\n[green]Results saved to {save_path}[/green]")

if __name__ == "__main__":
    asyncio.run(run_backtests()) 