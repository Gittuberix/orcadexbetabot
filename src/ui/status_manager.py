from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.progress import Progress, SpinnerColumn
from datetime import datetime
from typing import Dict, List
import asyncio

console = Console()

class StatusManager:
    def __init__(self):
        self.layout = Layout()
        self.connections = {}
        self.trades = []
        self.errors = []
        self.wallet_info = {}
        self.pool_status = {}
        
    def build_layout(self):
        """Erstellt Layout mit mehreren Panels"""
        self.layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1).split_row(
                Layout(name="left").split(
                    Layout(name="connections"),
                    Layout(name="wallet"),
                ),
                Layout(name="right").split(
                    Layout(name="trades"),
                    Layout(name="pools"),
                )
            ),
            Layout(name="footer", size=3)
        )
        
    def generate_header(self) -> Panel:
        """Generiert Header mit Bot Status"""
        return Panel(
            f"🤖 Orca Trading Bot - Running since {self.start_time}\n"
            f"Status: {'🟢 Online' if self.is_healthy else '🔴 Issues Detected'}",
            style="bold white on blue"
        )
        
    def generate_connection_status(self) -> Panel:
        """Zeigt Verbindungsstatus"""
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Service")
        table.add_column("Status")
        table.add_column("Latency")
        
        for service, info in self.connections.items():
            status = "🟢" if info['healthy'] else "🔴"
            latency = f"{info['latency']:.2f}ms" if info['latency'] else "N/A"
            table.add_row(service, status, latency)
            
        return Panel(table, title="🔌 Connections")
        
    def generate_wallet_info(self) -> Panel:
        """Zeigt Wallet Informationen"""
        if not self.wallet_info:
            return Panel("No wallet connected", title="👛 Wallet")
            
        content = [
            f"Address: {self.wallet_info['address'][:8]}...",
            f"SOL Balance: {self.wallet_info['sol_balance']:.4f}",
            "\n[bold]Token Balances:[/bold]"
        ]
        
        for token, balance in self.wallet_info.get('tokens', {}).items():
            content.append(f"{token}: {balance:.2f}")
            
        return Panel("\n".join(content), title="👛 Wallet")
        
    def generate_trade_history(self) -> Panel:
        """Zeigt Trade Historie"""
        table = Table(show_header=True)
        table.add_column("Time")
        table.add_column("Type")
        table.add_column("Amount")
        table.add_column("Price")
        table.add_column("Status")
        
        for trade in self.trades[-5:]:  # Letzte 5 Trades
            status = "✅" if trade['success'] else "❌"
            table.add_row(
                trade['time'].strftime("%H:%M:%S"),
                "🟢 Buy" if trade['type'] == 'buy' else "🔴 Sell",
                f"{trade['amount']:.4f}",
                f"${trade['price']:.2f}",
                status
            )
            
        return Panel(table, title="📊 Recent Trades")
        
    def generate_pool_status(self) -> Panel:
        """Zeigt Pool Status"""
        table = Table(show_header=True)
        table.add_column("Pool")
        table.add_column("Price")
        table.add_column("24h Change")
        table.add_column("Volume")
        
        for pool, info in self.pool_status.items():
            price_change = info.get('price_change_24h', 0)
            change_color = "green" if price_change > 0 else "red"
            
            table.add_row(
                pool[:8] + "...",
                f"${info['price']:.4f}",
                f"[{change_color}]{price_change:+.2f}%[/{change_color}]",
                f"${info['volume_24h']:,.0f}"
            )
            
        return Panel(table, title="🌊 Whirlpools")
        
    def generate_error_log(self) -> Panel:
        """Zeigt Fehlerlog"""
        if not self.errors:
            return Panel("No errors", title="🚨 Errors", style="green")
            
        content = "\n".join(
            f"[red]{error['time'].strftime('%H:%M:%S')} - {error['message']}[/red]"
            for error in self.errors[-3:]  # Letzte 3 Fehler
        )
        return Panel(content, title="🚨 Errors", style="red")
        
    async def update_display(self):
        """Aktualisiert Display"""
        with Live(self.layout, refresh_per_second=1) as live:
            while True:
                # Layout aktualisieren
                self.layout["header"].update(self.generate_header())
                self.layout["connections"].update(self.generate_connection_status())
                self.layout["wallet"].update(self.generate_wallet_info())
                self.layout["trades"].update(self.generate_trade_history())
                self.layout["pools"].update(self.generate_pool_status())
                self.layout["footer"].update(self.generate_error_log())
                
                await asyncio.sleep(1) 