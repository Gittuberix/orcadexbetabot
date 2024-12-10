import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from rich.console import Console
from rich.table import Table
from src.data.orca_pipeline import OrcaPipeline
from src.wallet_manager import WalletManager
from src.backtest.data_manager import BacktestManager
from src.risk_manager import RiskManager

console = Console()
logger = logging.getLogger(__name__)

async def main():
    """Hauptmenü"""
    try:
        console.print("\n[cyan]🌊 Orca DEX Trading Bot[/cyan]")
        
        while True:
            console.print("\n1. Live Preise anzeigen")
            console.print("2. Wallet Status")
            console.print("3. Backtest durchführen")
            console.print("4. Trading starten")
            console.print("5. Beenden")
            
            choice = input("\nWähle eine Option (1-5): ")
            
            if choice == "1":
                await show_live_prices()
            elif choice == "2":
                await show_wallet_status()
            elif choice == "3":
                await run_backtest()
            elif choice == "4":
                await start_trading()
            elif choice == "5":
                break
                
    except KeyboardInterrupt:
        console.print("\n[yellow]Bot wird beendet...[/yellow]")
    except Exception as e:
        console.print(f"[red]Fehler: {e}[/red]")
        
async def show_live_prices():
    """Zeigt Live-Preise"""
    pipeline = OrcaPipeline()
    await pipeline.initialize()
    
    try:
        while True:
            table = Table(title="Live Preise")
            table.add_column("Pool")
            table.add_column("Preis")
            table.add_column("24h Vol")
            table.add_column("Liquidität")
            
            for pool_name in pipeline.whirlpools:
                data = await pipeline.fetch_live_data(pool_name)
                if data:
                    table.add_row(
                        pool_name,
                        f"${data.price:.4f}",
                        f"${data.volume_24h:,.0f}",
                        f"${data.liquidity:,.0f}"
                    )
                    
            console.clear()
            console.print(table)
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Preisanzeige beendet[/yellow]")
    finally:
        await pipeline.close()
        
async def show_wallet_status():
    """Zeigt Wallet Status"""
    wallet = WalletManager()
    
    try:
        sol_balance = await wallet.get_sol_balance()
        token_balances = await wallet.get_token_balances()
        
        table = Table(title="Wallet Status")
        table.add_column("Token")
        table.add_column("Balance")
        
        table.add_row("SOL", f"{sol_balance:.4f}")
        for token, balance in token_balances.items():
            table.add_row(token, f"{balance:.4f}")
            
        console.print(table)
        
    finally:
        await wallet.close()
        
async def run_backtest():
    """Führt Backtest durch"""
    manager = BacktestManager()
    await manager.initialize()
    
    try:
        # Parameter
        pool_name = input("Pool (z.B. SOL/USDC): ")
        days = int(input("Tage zurück: "))
        capital = Decimal(input("Startkapital ($): "))
        trade_size = Decimal(input("Trade Größe ($): "))
        
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        # Backtest
        result = await manager.run_backtest(
            pool_name,
            start_time,
            end_time,
            None,  # TODO: Strategy
            capital,
            trade_size
        )
        
        if result:
            table = Table(title="Backtest Ergebnis")
            table.add_column("Metrik")
            table.add_column("Wert")
            
            table.add_row("Trades", str(result.total_trades))
            table.add_row("Gewinner", str(result.winning_trades))
            table.add_row("Verlierer", str(result.losing_trades))
            table.add_row("ROI", f"{float(result.roi):.2f}%")
            table.add_row("Max Drawdown", f"{float(result.max_drawdown):.2f}%")
            table.add_row("Sharpe Ratio", f"{result.sharpe_ratio:.2f}")
            
            console.print(table)
            
    finally:
        await manager.close()
        
async def start_trading():
    """Startet Trading"""
    # TODO: Implementiere Trading Logik
    console.print("[yellow]Trading noch nicht implementiert[/yellow]")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main()) 