import logging
import asyncio
from typing import Dict, Optional
from orca_data import OrcaDataProvider
from performance import PerformanceAnalyzer
from risk_manager import RiskManager
from strategies.meme_sniper import MemeSniper
import yaml
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from rich.layout import Layout
from solana.rpc.async_api import AsyncClient
from orca_api import OrcaAPI

class TradingBot:
    def __init__(self, config_path: str = 'config/config.yaml'):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
            
        self.data_provider = None
        self.performance = PerformanceAnalyzer()
        self.risk_manager = RiskManager(config_path)
        self.strategy = MemeSniper(self.config['meme_strategy'])
        
    async def initialize(self):
        """Initialisiert den Bot"""
        try:
            from solana.rpc.async_api import AsyncClient
            rpc_client = AsyncClient(self.config['network_config']['rpc_endpoint'])
            self.data_provider = OrcaDataProvider(rpc_client, self.config)
            return True
        except Exception as e:
            logging.error(f"Initialisierungsfehler: {e}")
            return False
            
    async def start(self):
        """Startet den Trading Bot"""
        if not await self.initialize():
            return
            
        try:
            while True:
                await self._trading_loop()
                await asyncio.sleep(self.config['trading_params']['update_interval'])
        except KeyboardInterrupt:
            logging.info("Bot gestoppt")
        except Exception as e:
            logging.error(f"Bot Fehler: {e}")
            
    async def _trading_loop(self):
        """Haupttrading-Loop"""
        try:
            # Market Daten abrufen
            pools = await self.data_provider.get_top_pools()
            
            for pool in pools:
                # Strategie-Analyse
                signal = await self.strategy.analyze(pool)
                
                if signal.should_trade:
                    await self._execute_trade(pool, signal)
                    
        except Exception as e:
            logging.error(f"Trading Loop Fehler: {e}")
            
    async def _execute_trade(self, pool: Dict, signal: Dict):
        """Führt einen Trade aus"""
        try:
            # Risiko-Check
            if not self.risk_manager.check_trade(signal):
                return
                
            # Trade ausführen
            # Hier kommt später die echte Trading-Logik
            logging.info(f"Trade Signal: {signal}")
            
        except Exception as e:
            logging.error(f"Trade Ausführungsfehler: {e}")

class OrcaMarket:
    """Klasse für Orca-spezifische Marktdaten"""
    def __init__(self, config: Dict):
        self.config = config

class TradingMonitor:
    def __init__(self, config_path: str = 'config/config.yaml'):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
            
        # Core Setup
        self.rpc = AsyncClient(self.config['network_config']['rpc_endpoint'])
        self.orca_api = OrcaAPI()
        self.performance = PerformanceAnalyzer()
        self.console = Console()
        
        # Trading Data
        self.active_trades = {}
        self.completed_trades = []
        self.total_profit = 0.0
        self.win_rate = 0.0
        
        # UI Colors
        self.colors = {
            'profit': 'bold green',
            'loss': 'bold red',
            'neutral': 'yellow',
            'header': 'bold cyan',
            'warning': 'bold yellow'
        }
        
        # Emojis
        self.emojis = {
            'profit': '💰',
            'loss': '📉',
            'pending': '⏳',
            'completed': '✅',
            'failed': '❌',
            'buy': '🔵',
            'sell': '🔴',
            'volume': '📊',
            'pool': '🌊'
        }
        
    def create_active_trades_table(self) -> Table:
        """Erstellt Tabelle mit aktiven Trades"""
        table = Table(title="🔄 Active Trades")
        
        table.add_column("Pool", style="cyan")
        table.add_column("Type", justify="center")
        table.add_column("Entry Price", justify="right", style="yellow")
        table.add_column("Current P/L", justify="right")
        table.add_column("Stop Loss", justify="right", style="red")
        table.add_column("Take Profit", justify="right", style="green")
        table.add_column("Duration", justify="right")
        
        for trade_id, trade in self.active_trades.items():
            pl_color = "green" if trade['current_pl'] > 0 else "red"
            table.add_row(
                trade['pool_name'],
                f"{self.emojis['buy'] if trade['type'] == 'buy' else self.emojis['sell']}",
                f"${trade['entry_price']:.6f}",
                f"[{pl_color}]${trade['current_pl']:.2f}[/{pl_color}]",
                f"${trade['stop_loss']:.6f}",
                f"${trade['take_profit']:.6f}",
                str(datetime.now() - trade['entry_time']).split('.')[0]
            )
            
        return table
        
    def create_trade_history_table(self) -> Table:
        """Erstellt Tabelle mit abgeschlossenen Trades"""
        table = Table(title="📜 Trade History")
        
        table.add_column("Time", style="cyan")
        table.add_column("Pool", style="blue")
        table.add_column("Type", justify="center")
        table.add_column("Profit/Loss", justify="right")
        table.add_column("ROI %", justify="right")
        table.add_column("Duration", justify="right")
        table.add_column("Status", justify="center")
        
        for trade in reversed(self.completed_trades[-10:]):  # Letzte 10 Trades
            pl_color = "green" if trade['profit'] > 0 else "red"
            roi_color = "green" if trade['roi'] > 0 else "red"
            
            table.add_row(
                trade['exit_time'].strftime('%H:%M:%S'),
                trade['pool_name'],
                f"{self.emojis['buy'] if trade['type'] == 'buy' else self.emojis['sell']}",
                f"[{pl_color}]${trade['profit']:.2f}[/{pl_color}]",
                f"[{roi_color}]{trade['roi']:.1f}%[/{roi_color}]",
                str(trade['duration']).split('.')[0],
                self._get_status_text(trade['status'])
            )
            
        return table
        
    def create_performance_panel(self) -> Panel:
        """Erstellt Performance-Übersicht"""
        stats = self.performance.get_statistics()
        
        content = f"""
{self.emojis['profit']} Total Profit: ${stats['total_profit']:.2f}
📈 Win Rate: {stats['win_rate']:.1f}%
🎯 Total Trades: {stats['total_trades']}
⚡ Profitable Trades: {stats['profitable_trades']}
📉 Max Drawdown: {stats['max_drawdown']:.1f}%
⚖️ Sharpe Ratio: {stats['sharpe_ratio']:.2f}
"""
        return Panel(content, title="📊 Performance", border_style="green")
        
    def _get_status_text(self, status: str) -> Text:
        """Formatiert den Trade-Status"""
        if status == 'completed':
            return Text(f"{self.emojis['completed']} Completed", style="green")
        elif status == 'failed':
            return Text(f"{self.emojis['failed']} Failed", style="red")
        return Text(f"{self.emojis['pending']} Pending", style="yellow")
        
    async def start_monitoring(self):
        """Startet das Live-Monitoring"""
        self.console.print("[cyan]Starting Trading Monitor...[/cyan]")
        
        try:
            layout = Layout()
            layout.split_column(
                Layout(name="upper"),
                Layout(name="lower")
            )
            layout["upper"].split_row(
                Layout(name="performance"),
                Layout(name="active_trades")
            )
            
            with Live(layout, refresh_per_second=1) as live:
                while True:
                    # Performance Panel
                    layout["performance"].update(self.create_performance_panel())
                    
                    # Active Trades
                    layout["active_trades"].update(self.create_active_trades_table())
                    
                    # Trade History
                    layout["lower"].update(self.create_trade_history_table())
                    
                    # Warten bis zum nächsten Update
                    await asyncio.sleep(1)
                    
        except KeyboardInterrupt:
            self.console.print("[yellow]Monitor stopped by user[/yellow]")
        except Exception as e:
            self.console.print(f"[red]Monitor error: {e}[/red]")

async def main():
    monitor = TradingMonitor()
    await monitor.start_monitoring()

if __name__ == "__main__":
    asyncio.run(main())