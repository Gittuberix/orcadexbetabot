import os
import time
from datetime import datetime
from tabulate import tabulate
from typing import Dict, List
import asyncio
import logging
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
import sys
from pathlib import Path

from .data.orca_pipeline import OrcaPipeline
from .config.connections import WHIRLPOOL_IDS
from .data.monitoring import SystemMonitor
from .backtest.backtest_engine import BacktestEngine
from .trading.trading_engine import TradingEngine

console = Console()
monitor = SystemMonitor("TradingInterface")

class TerminalInterface:
    def __init__(self):
        self.last_update = datetime.now()
        self.update_interval = 1
        self.stats = {
            'total_volume': 0,
            'total_pools': 0,
            'tracked_tokens': 0
        }
        
    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        
    def display_header(self):
        print("\n" + "="*120)
        print("🚀 ORCA DEX LIVE MONITOR 🚀".center(120))
        print("="*120 + "\n")
        
        # Stats anzeigen
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".center(120))
        print(f"📊 Pools: {self.stats['total_pools']} | 💎 Token: {self.stats['tracked_tokens']} | 💰 24h Volume: ${self.stats['total_volume']:,.0f}".center(120))
        print("\n" + "="*120 + "\n")
        
    def display_pools(self, pools: List[Dict]):
        if not pools:
            print("Keine Pool Daten verfügbar...")
            return
            
        # Stats aktualisieren
        self.stats['total_pools'] = len(pools)
        self.stats['total_volume'] = sum(p.get('volume_24h', 0) for p in pools)
        self.stats['tracked_tokens'] = len(set([p.get('token_a', '') for p in pools] + [p.get('token_b', '') for p in pools]))
        
        # Pool Daten formatieren
        pool_data = []
        for pool in pools:
            try:
                # Farbige Preisänderungen
                price_color = '\033[92m' if pool.get('price_change', 0) > 0 else '\033[91m'
                volume_color = '\033[92m' if pool.get('volume_24h', 0) > 100000 else '\033[0m'
                
                # Spread berechnen
                best_bid = pool.get('best_bid', 0) or 0
                best_ask = pool.get('best_ask', 0) or 0
                spread = ((best_ask - best_bid) / best_bid * 100) if best_bid > 0 else 0
                
                pool_data.append([
                    f"{pool.get('token_a', '???')}/{pool.get('token_b', '???')}",
                    f"${pool.get('price', 0):.6f}",
                    f"{price_color}{pool.get('price_change', 0):+.2f}%\033[0m",
                    f"${pool.get('liquidity', 0):,.0f}",
                    f"{volume_color}${pool.get('volume_24h', 0):,.0f}\033[0m",
                    f"{pool.get('trades_24h', 0):,}",
                    f"${best_bid:.6f}",
                    f"${best_ask:.6f}",
                    f"{spread:.2f}%"
                ])
            except Exception as e:
                logging.error(f"Error formatting pool data: {e}")
                continue
            
        print("📈 TOP ORCA POOLS:")
        print(tabulate(pool_data,
            headers=['Pool', 'Preis', '24h %', 'Liquidität', 'Volume 24h', 'Trades', 'Bid', 'Ask', 'Spread'],
            tablefmt='fancy_grid',
            numalign='right'))
            
    async def update_display(self, pools: List[Dict]):
        """Aktualisiert das Display"""
        try:
            self.clear_screen()
            self.display_header()
            self.display_pools(pools)  # Top 10 Pools
        except Exception as e:
            logging.error(f"Display update error: {e}")
            print("\n❌ Error updating display. Check logs for details.")

class TradingInterface:
    def __init__(self):
        self.pipeline = None
        self.running = False
        self.backtest_engine = BacktestEngine()
        self.trading_engine = TradingEngine()
        
    def create_status_table(self) -> Table:
        """Create status display table"""
        table = Table(title="System Status")
        table.add_column("Component")
        table.add_column("Status")
        table.add_column("Details")
        
        # Add system health
        if self.pipeline:
            health = self.pipeline.monitor.get_health_report()
            table.add_row(
                "Pipeline",
                "[green]Active[/green]" if health['status'] == 'healthy' else "[red]Degraded[/red]",
                f"Uptime: {health['uptime_seconds']:.0f}s"
            )
            
            # Add pool status
            active_pools = len(self.pipeline.active_pools) if self.pipeline.active_pools else 0
            table.add_row(
                "Pools",
                "[green]OK[/green]" if active_pools > 0 else "[red]No Data[/red]",
                f"Active: {active_pools}"
            )
        else:
            table.add_row("Pipeline", "[red]Inactive[/red]", "Not started")
            
        return table

    async def start_live_trading(self):
        """Start live trading system"""
        try:
            console.print("\n[bold cyan]Starting Live Trading System...[/bold cyan]")
            
            # Initialize pipeline and trading engine
            self.pipeline = OrcaPipeline()
            await self.trading_engine.initialize(self.pipeline)
            
            # Create status display
            with Live(self.create_status_table(), refresh_per_second=1) as live:
                while True:
                    try:
                        # Update trading engine
                        await self.trading_engine.update()
                        
                        # Update status display
                        live.update(self.create_trading_status())
                        
                        # Check for user input
                        if sys.stdin in asyncio.select([sys.stdin], [], [], 0)[0]:
                            cmd = input().strip().lower()
                            if cmd == 'q':
                                break
                            elif cmd == 'p':  # Show positions
                                await self._show_positions()
                            elif cmd == 'o':  # Show open orders
                                await self._show_orders()
                            
                        await asyncio.sleep(1)
                        
                    except KeyboardInterrupt:
                        break
                    except Exception as e:
                        monitor.log_error(e, "live_trading_loop")
                        console.print(f"[red]Error in trading loop: {e}[/red]")
                        
        except Exception as e:
            monitor.log_error(e, "start_live_trading")
            console.print(f"[red]Failed to start trading: {e}[/red]")
        finally:
            await self._cleanup()
            console.print("\n[yellow]Shutting down trading system...[/yellow]")
            self.running = False

    def run_backtest(self):
        """Run backtest simulation"""
        try:
            console.print("\n[bold cyan]Starting Backtest Configuration...[/bold cyan]")
            
            # Predefined timeframes
            timeframes = {
                "1": ("Last 24 Hours", 1),
                "2": ("Last 7 Days", 7),
                "3": ("Last 30 Days", 30),
                "4": ("Custom Period", 0)
            }
            
            # Show timeframe options
            timeframe_table = Table(title="Select Timeframe")
            timeframe_table.add_column("Option")
            timeframe_table.add_column("Period")
            
            for key, (name, _) in timeframes.items():
                timeframe_table.add_row(f"[cyan]{key}[/cyan]", name)
            
            console.print(timeframe_table)
            timeframe_choice = Prompt.ask(
                "Select timeframe", 
                choices=list(timeframes.keys())
            )
            
            # Handle custom period
            if timeframe_choice == "4":
                days = int(Prompt.ask("Enter number of days to backtest"))
            else:
                days = timeframes[timeframe_choice][1]
            
            # Pool selection
            pool_table = Table(title="Select Trading Pool")
            pool_table.add_column("Option")
            pool_table.add_column("Pool")
            pool_table.add_column("Address")
            
            pool_options = {
                "1": ("SOL/USDC", WHIRLPOOL_IDS['SOL/USDC']),
                "2": ("Custom Pool", "")
            }
            
            for key, (name, address) in pool_options.items():
                pool_table.add_row(
                    f"[cyan]{key}[/cyan]", 
                    name,
                    address[:8] + "..." if address else ""
                )
            
            console.print(pool_table)
            pool_choice = Prompt.ask(
                "Select pool",
                choices=list(pool_options.keys())
            )
            
            if pool_choice == "2":
                pool_id = Prompt.ask("Enter pool address")
            else:
                pool_id = pool_options[pool_choice][1]
            
            # Trading parameters
            params_table = Table(title="Trading Parameters")
            params_table.add_column("Parameter")
            params_table.add_column("Value")
            
            initial_capital = float(Prompt.ask(
                "Enter initial capital (USDC)", 
                default="1000"
            ))
            
            take_profit = float(Prompt.ask(
                "Take Profit %", 
                default="1.0"
            ))
            
            stop_loss = float(Prompt.ask(
                "Stop Loss %", 
                default="0.5"
            ))
            
            params_table.add_row("Initial Capital", f"${initial_capital:,.2f}")
            params_table.add_row("Take Profit", f"{take_profit}%")
            params_table.add_row("Stop Loss", f"{stop_loss}%")
            
            # Show configuration summary
            console.print("\n[bold cyan]Backtest Configuration Summary:[/bold cyan]")
            console.print(params_table)
            console.print(f"Timeframe: {timeframes[timeframe_choice][0]}")
            console.print(f"Pool: {pool_options[pool_choice][0]}")
            
            if Prompt.ask("\nStart backtest?", choices=["y", "n"]) == "y":
                console.print("\n[bold green]Running backtest...[/bold green]")
                
                # Create progress bar
                with console.status("[bold green]Running backtest...") as status:
                    # Run backtest
                    results = await self.backtest_engine.run(
                        pool_id=pool_id,
                        days=days,
                        initial_capital=initial_capital,
                        take_profit=take_profit/100,  # Convert to decimal
                        stop_loss=stop_loss/100      # Convert to decimal
                    )
                    
                    # Display results
                    self._display_backtest_results(results)
                
        except Exception as e:
            monitor.log_error(e, "run_backtest")
            console.print(f"[red]Backtest failed: {e}[/red]")

    def _display_backtest_results(self, results: dict):
        """Display backtest results in a formatted table"""
        results_table = Table(title="Backtest Results")
        results_table.add_column("Metric")
        results_table.add_column("Value")
        
        # Add key metrics
        results_table.add_row(
            "Total Return",
            f"[{'green' if results['total_return'] > 0 else 'red'}]{results['total_return']:.2f}%[/]"
        )
        results_table.add_row("Win Rate", f"{results['win_rate']:.1f}%")
        results_table.add_row("Total Trades", str(results['total_trades']))
        results_table.add_row("Profit Factor", f"{results['profit_factor']:.2f}")
        results_table.add_row("Max Drawdown", f"{results['max_drawdown']:.2f}%")
        
        console.print(results_table)

    def create_trading_menu(self) -> Table:
        """Create trading configuration menu"""
        menu = Table(title="Trading Configuration")
        menu.add_column("Setting")
        menu.add_column("Value")
        menu.add_column("Status")

        # Load current config
        config = self.load_trading_config()
        
        menu.add_row(
            "Trading Mode",
            config.get('mode', 'Manual'),
            self._get_status_icon(self.running)
        )
        menu.add_row(
            "Active Pairs",
            str(len(config.get('pairs', []))),
            "[green]✓[/green]" if config.get('pairs') else "[red]×[/red]"
        )
        menu.add_row(
            "Risk Level",
            config.get('risk_level', 'Medium'),
            self._get_risk_icon(config.get('risk_level'))
        )
        return menu

    def _get_status_icon(self, active: bool) -> str:
        return "[green]Active[/green]" if active else "[red]Inactive[/red]"

    def _get_risk_icon(self, risk: str) -> str:
        icons = {
            'Low': "[green]●[/green]",
            'Medium': "[yellow]●[/yellow]",
            'High': "[red]●[/red]"
        }
        return icons.get(risk, "[grey]●[/grey]")

    def load_trading_config(self):
        """Load trading configuration"""
        try:
            return {
                'mode': 'Automatic',
                'pairs': ['SOL/USDC', 'ORCA/USDC'],
                'risk_level': 'Medium',
                'take_profit': 1.0,
                'stop_loss': 0.5,
                'max_trades': 3
            }
        except Exception as e:
            monitor.log_error(e, "load_config")
            return {}

    async def show_system_status(self):
        """Show detailed system status"""
        try:
            status_layout = Layout()
            status_layout.split_column(
                Layout(name="header"),
                Layout(name="stats"),
                Layout(name="pools"),
                Layout(name="performance")
            )

            # Header
            header = Panel(
                "[bold cyan]System Status Overview[/bold cyan]",
                style="cyan"
            )
            status_layout["header"].update(header)

            # Stats
            stats_table = Table(title="System Statistics")
            stats_table.add_column("Metric")
            stats_table.add_column("Value")

            if self.pipeline:
                health = self.pipeline.monitor.get_health_report()
                stats_table.add_row("Status", self._get_health_status(health['status']))
                stats_table.add_row("Uptime", f"{health['uptime_seconds']/3600:.1f}h")
                stats_table.add_row("CPU Usage", f"{health['metrics']['cpu_usage_avg']:.1f}%")
                stats_table.add_row("Memory", f"{health['metrics']['memory_mb_avg']:.0f}MB")
            else:
                stats_table.add_row("Status", "[red]Offline[/red]")

            status_layout["stats"].update(stats_table)

            # Active pools
            if self.pipeline and self.pipeline.active_pools:
                pools_table = Table(title="Active Pools")
                pools_table.add_column("Pool")
                pools_table.add_column("Volume 24h")
                pools_table.add_column("Status")

                for pool in self.pipeline.active_pools[:5]:
                    pools_table.add_row(
                        f"{pool['tokenA']['symbol']}/{pool['tokenB']['symbol']}",
                        f"${float(pool['volume24h']):,.0f}",
                        "[green]Active[/green]"
                    )
                status_layout["pools"].update(pools_table)

            console.print(status_layout)
            
            if Prompt.ask("\nReturn to main menu?", choices=["y", "n"]) == "y":
                return

        except Exception as e:
            monitor.log_error(e, "system_status")
            console.print(f"[red]Error displaying status: {e}[/red]")

    def _get_health_status(self, status: str) -> str:
        colors = {
            'healthy': '[green]Healthy[/green]',
            'degraded': '[yellow]Degraded[/yellow]',
            'critical': '[red]Critical[/red]'
        }
        return colors.get(status.lower(), '[grey]Unknown[/grey]')

    def create_trading_status(self) -> Table:
        """Create live trading status display"""
        table = Table(title="Trading Status")
        table.add_column("Metric")
        table.add_column("Value")
        
        # Get trading stats
        stats = self.trading_engine.get_stats()
        
        table.add_row("Active Positions", str(stats['active_positions']))
        table.add_row("Daily P/L", f"{stats['daily_pnl']:.2f}%")
        table.add_row("Open Orders", str(stats['open_orders']))
        table.add_row(
            "Status", 
            "[green]Trading[/green]" if self.trading_engine.is_trading else "[red]Paused[/red]"
        )
        
        return table

    async def _show_positions(self):
        """Display current positions"""
        positions = await self.trading_engine.get_positions()
        
        if not positions:
            console.print("[yellow]No open positions[/yellow]")
            return
            
        pos_table = Table(title="Open Positions")
        pos_table.add_column("Pool")
        pos_table.add_column("Size")
        pos_table.add_column("Entry")
        pos_table.add_column("Current")
        pos_table.add_column("P/L")
        
        for pos in positions:
            pnl_color = "green" if pos['unrealized_pnl'] > 0 else "red"
            pos_table.add_row(
                pos['pool'],
                f"${pos['size']:.2f}",
                f"${pos['entry_price']:.4f}",
                f"${pos['current_price']:.4f}",
                f"[{pnl_color}]{pos['unrealized_pnl']:.2f}%[/]"
            )
            
        console.print(pos_table)

    async def _cleanup(self):
        """Cleanup resources"""
        if self.trading_engine:
            await self.trading_engine.shutdown()
        if self.pipeline:
            # Cleanup pipeline resources
            pass

def main_menu():
    """Display main menu"""
    console.clear()
    console.print("\n[bold cyan]🚀 ORCA DEX TRADING BOT 🚀[/bold cyan]")
    
    menu = Table(show_header=False, box=None)
    menu.add_row("[1] Start Live Trading")
    menu.add_row("[2] Run Backtest")
    menu.add_row("[3] System Status")
    menu.add_row("[4] Trading Configuration")
    menu.add_row("[5] View Logs")
    menu.add_row("[6] Exit")
    
    console.print(Panel(menu, title="Main Menu"))
    
    choice = Prompt.ask(
        "Please select an option", 
        choices=["1", "2", "3", "4", "5", "6"]
    )
    return choice

async def main():
    interface = TradingInterface()
    
    while True:
        try:
            choice = main_menu()
            
            if choice == "1":
                await interface.start_live_trading()
            elif choice == "2":
                interface.run_backtest()
            elif choice == "3":
                await interface.show_system_status()
            elif choice == "4":
                console.print(interface.create_trading_menu())
                input("\nPress Enter to continue...")
            elif choice == "5":
                interface.view_logs()
            elif choice == "6":
                break
                
        except KeyboardInterrupt:
            console.print("\n[yellow]Operation cancelled by user[/yellow]")
        except Exception as e:
            monitor.log_error(e, "main_menu")
            console.print(f"[red]Error: {e}[/red]")
            
    console.print("\n[cyan]Goodbye! 👋[/cyan]")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Application terminated by user[/yellow]")
    except Exception as e:
        monitor.log_error(e, "main")
        console.print(f"[red]Fatal error: {e}[/red]")