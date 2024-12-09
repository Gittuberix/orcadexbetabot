from token_fetcher import TokenFetcher
from typing import Dict, List, Optional
import asyncio
import logging
from datetime import datetime
import json
from pathlib import Path
import yaml
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn
import time
from test_wallet import TestWallet
from performance import PerformanceAnalyzer
from rich.layout import Layout
from rich.style import Style
from rich.align import Align
from solana_rpc import SolanaRPC

class EnhancedTokenMonitor:
    def __init__(self, config_path: str = 'config.yaml'):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
            
        self.fetcher = TokenFetcher()
        self.console = Console()
        self.watchlist = {}
        self.top_tokens = {}
        
        # Emojis für verschiedene Stati
        self.emojis = {
            'up': '🚀',
            'down': '📉',
            'neutral': '➖',
            'alert': '⚠️',
            'success': '✅',
            'error': '❌',
            'hot': '🔥',
            'cold': '❄️',
            'whale': '🐋',
            'money': '💰',
            'chart': '📊',
            'time': '⏰',
            'lock': '🔒',
            'unlock': '🔓',
            'wallet': '👛',
            'profit': '💵',
            'loss': '📉',
            'trade': '🔄',
            'balance': '💰',
            'pending': '⏳',
            'completed': '✅',
            'failed': '❌',
            'warning': '⚠️'
        }
        
        self.performance = PerformanceAnalyzer()
        self.wallet = TestWallet("YOUR_PRIVATE_KEY")  # Für echtes Trading anpassen
        self.rpc = SolanaRPC()
        
    def create_token_table(self) -> Table:
        """Erstellt eine formatierte Tabelle für Token-Daten"""
        table = Table(
            title="🔥 Top Token Monitor 🔥",
            caption="Aktualisiert alle 60 Sekunden",
            caption_style="dim"
        )
        
        table.add_column("Symbol", style="cyan bold")
        table.add_column("Preis ($)", justify="right", style="green")
        table.add_column("24h %", justify="right")
        table.add_column("Volume", justify="right", style="blue")
        table.add_column("Liquidität", justify="right", style="magenta")
        table.add_column("Signal", justify="center")
        table.add_column("Status", justify="center")
        
        return table
        
    def format_price_change(self, change: float) -> Text:
        """Formatiert Preisänderungen mit Farben und Emojis"""
        if change > 5:
            return Text(f"+{change:.1f}% {self.emojis['up']}", style="bold green")
        elif change < -5:
            return Text(f"{change:.1f}% {self.emojis['down']}", style="bold red")
        else:
            return Text(f"{change:.1f}% {self.emojis['neutral']}", style="yellow")
            
    def format_volume(self, volume: float) -> str:
        """Formatiert Volumenwerte lesbar"""
        if volume >= 1_000_000:
            return f"${volume/1_000_000:.1f}M"
        elif volume >= 1_000:
            return f"${volume/1_000:.1f}K"
        else:
            return f"${volume:.0f}"
            
    def get_signal_indicator(self, token_data: Dict) -> Text:
        """Generiert Signal-Indikatoren basierend auf Token-Daten"""
        signals = []
        
        # Volume Signal
        if token_data.get('volume_24h', 0) > self.config['trading_params']['min_volume_24h']:
            signals.append(self.emojis['hot'])
            
        # Liquidität Signal
        if token_data.get('liquidity', 0) > self.config['trading_params']['min_liquidity']:
            signals.append(self.emojis['whale'])
            
        # Profit Signal
        if token_data.get('price_change_24h', 0) > 10:
            signals.append(self.emojis['money'])
            
        return Text("".join(signals) if signals else self.emojis['neutral'])
        
    def create_trading_panel(self) -> Panel:
        """Erstellt das Trading-Performance Panel"""
        if not self.performance.metrics:
            return Panel("Noch keine Trades", title="Trading Performance")
            
        content = f"""
{self.emojis['wallet']} Wallet Balance: ${self.wallet.get_balance():.2f}
{self.emojis['profit']} Gesamt Profit: ${self.performance.metrics.total_profit:.2f}
{self.emojis['chart']} Win Rate: {self.performance.metrics.win_rate:.1f}%
{self.emojis['trade']} Trades Heute: {self.performance.metrics.trades_count}
{self.emojis['money']} Bester Trade: ${self.performance.metrics.best_trade:.2f}
{self.emojis['warning']} Max Drawdown: {self.performance.metrics.max_drawdown:.1f}%
{self.emojis['chart']} Sharpe Ratio: {self.performance.metrics.sharpe_ratio:.2f}
        """
        return Panel(content, title="💹 Trading Performance", border_style="green")
        
    def create_active_trades_table(self) -> Table:
        """Erstellt eine Tabelle der aktiven Trades"""
        table = Table(title="🔄 Aktive Trades")
        
        table.add_column("Token", style="cyan")
        table.add_column("Einstieg", style="green")
        table.add_column("Aktuell", style="yellow")
        table.add_column("P/L", style="bold")
        table.add_column("Zeit", style="blue")
        table.add_column("Stop Loss", style="red")
        table.add_column("Take Profit", style="green")
        
        for position in self.wallet.open_positions.values():
            entry_price = position['entry_price']
            current_price = position.get('current_price', entry_price)
            profit_loss = ((current_price - entry_price) / entry_price) * 100
            
            table.add_row(
                position['symbol'],
                f"${entry_price:.6f}",
                f"${current_price:.6f}",
                self._format_pnl(profit_loss),
                self._format_time_in_trade(position['entry_time']),
                f"${position['stop_loss']:.6f}",
                f"${position['take_profit']:.6f}"
            )
            
        return table
        
    def create_recent_trades_table(self) -> Table:
        """Erstellt eine Tabelle der letzten Trades"""
        table = Table(title="📜 Letzte Trades")
        
        table.add_column("Zeit", style="dim")
        table.add_column("Token", style="cyan")
        table.add_column("Typ", justify="center")
        table.add_column("Preis", style="green")
        table.add_column("Menge", justify="right")
        table.add_column("Profit", style="bold")
        table.add_column("Status")
        
        for trade in reversed(self.performance.trades_history[-10:]):  # Letzte 10 Trades
            table.add_row(
                trade['timestamp'].strftime("%H:%M:%S"),
                trade['symbol'],
                "🔵 BUY" if trade['type'] == 'buy' else "🔴 SELL",
                f"${trade['price']:.6f}",
                f"{trade['amount']:.2f}",
                self._format_profit(trade.get('profit', 0)),
                self._get_trade_status(trade)
            )
            
        return table
        
    def create_market_overview(self) -> Panel:
        """Erstellt eine Marktübersicht"""
        stats = {
            'total_volume': sum(t['volume_24h'] for t in self.top_tokens.values()),
            'avg_liquidity': sum(t['liquidity'] for t in self.top_tokens.values()) / len(self.top_tokens) if self.top_tokens else 0,
            'opportunities': self._count_opportunities(),
            'active_pools': len(set(p for t in self.top_tokens.values() for p in t['pools']))
        }
        
        content = f"""
{self.emojis['chart']} 24h Volumen: ${self.format_volume(stats['total_volume'])}
{self.emojis['whale']} Durchschn. Liquidität: ${self.format_volume(stats['avg_liquidity'])}
{self.emojis['hot']} Trading Opportunities: {stats['opportunities']}
{self.emojis['money']} Aktive Pools: {stats['active_pools']}
        """
        
        return Panel(content, title="📊 Marktübersicht", border_style="blue")
        
    async def display_monitor(self):
        """Zeigt das erweiterte Live-Monitoring-Interface"""
        layout = Layout()
        layout.split_column(
            Layout(name="header"),
            Layout(name="body"),
            Layout(name="footer")
        )
        
        layout["body"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        
        with Live(layout, refresh_per_second=1) as live:
            while True:
                try:
                    # Daten aktualisieren
                    self.top_tokens = await self.fetcher.get_top_tokens()
                    
                    # Layout aktualisieren
                    layout["header"].update(
                        Panel(
                            f"{self.emojis['time']} {datetime.now().strftime('%H:%M:%S')} | "
                            f"{self.emojis['wallet']} Balance: ${self.wallet.get_balance():.2f}",
                            style="bold white on blue"
                        )
                    )
                    
                    layout["left"].update(
                        Layout(name="left_content").split_column(
                            self.create_trading_panel(),
                            self.create_active_trades_table()
                        )
                    )
                    
                    layout["right"].update(
                        Layout(name="right_content").split_column(
                            self.create_market_overview(),
                            self.create_token_table(self.top_tokens)
                        )
                    )
                    
                    layout["footer"].update(self.create_recent_trades_table())
                    
                except Exception as e:
                    self.console.print(f"[red]Update Fehler: {e}[/red]")
                    
                await asyncio.sleep(1)
                
    def _format_pnl(self, pnl: float) -> Text:
        """Formatiert Profit/Loss mit Farben"""
        if pnl > 0:
            return Text(f"+{pnl:.1f}%", style="bold green")
        elif pnl < 0:
            return Text(f"{pnl:.1f}%", style="bold red")
        return Text("0.0%", style="yellow")
        
    def _format_profit(self, profit: float) -> Text:
        """Formatiert Profit-Werte"""
        if profit > 0:
            return Text(f"+${profit:.2f}", style="bold green")
        elif profit < 0:
            return Text(f"-${abs(profit):.2f}", style="bold red")
        return Text("$0.00", style="yellow")
        
    def _format_time_in_trade(self, entry_time: datetime) -> str:
        """Formatiert die Zeit im Trade"""
        duration = datetime.now() - entry_time
        minutes = duration.total_seconds() / 60
        if minutes < 60:
            return f"{minutes:.0f}m"
        return f"{minutes/60:.1f}h"
        
    def _get_trade_status(self, trade: Dict) -> Text:
        """Gibt den formatierten Trade-Status zurück"""
        if trade.get('status') == 'completed':
            return Text(f"{self.emojis['completed']} Completed", style="green")
        elif trade.get('status') == 'failed':
            return Text(f"{self.emojis['failed']} Failed", style="red")
        return Text(f"{self.emojis['pending']} Pending", style="yellow")
        
    def _count_opportunities(self) -> int:
        """Zählt aktuelle Trading-Möglichkeiten"""
        return sum(1 for data in self.top_tokens.values() if self._is_tradeable(data))
        
    def _is_tradeable(self, token_data: Dict) -> bool:
        """Prüft, ob ein Token handelbar ist"""
        return (
            token_data.get('volume_24h', 0) > self.config['trading_params']['min_volume_24h'] and
            token_data.get('liquidity', 0) > self.config['trading_params']['min_liquidity'] and
            token_data.get('price_change_24h', -100) > -20
        )
        
    def _format_watchlist(self) -> str:
        """Formatiert die Watchlist für die Anzeige"""
        if not self.watchlist:
            return "Keine Tokens in der Watchlist"
            
        lines = []
        for address, data in self.watchlist.items():
            symbol = data['info'].get('symbol', 'Unknown')
            price = data['info'].get('price_usd', 0)
            change = data['info'].get('price_change_24h', 0)
            
            emoji = self.emojis['up'] if change > 0 else self.emojis['down']
            lines.append(f"{emoji} {symbol}: ${price:.6f} ({change:+.1f}%)")
            
        return "\n".join(lines)
        
    async def start_monitoring(self):
        """Startet das Token-Monitoring"""
        try:
            # Token-Daten Update Task
            update_task = asyncio.create_task(self._update_token_data())
            # Display Task
            display_task = asyncio.create_task(self.display_monitor())
            
            await asyncio.gather(update_task, display_task)
            
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Monitoring beendet![/yellow]")
        except Exception as e:
            self.console.print(f"\n[red]Fehler: {e}[/red]")
            
    async def _update_token_data(self):
        """Aktualisiert Token-Daten im Hintergrund"""
        while True:
            try:
                # Top Token aktualisieren
                new_tokens = await self.fetcher.get_top_tokens()
                if new_tokens:
                    self.top_tokens = new_tokens
                    
                # Watchlist aktualisieren
                for address in self.watchlist:
                    token_info = await self.fetcher.get_token_info(address)
                    if token_info:
                        self.watchlist[address]['info'] = token_info
                        
            except Exception as e:
                self.console.print(f"[red]Update Fehler: {e}[/red]")
                
            await asyncio.sleep(60)  # Alle 60 Sekunden aktualisieren
        
    async def get_wallet_info(self):
        sol_balance = await self.rpc.get_sol_balance(self.wallet.public_key)
        token_accounts = await self.rpc.get_token_accounts(self.wallet.public_key)
        return {
            'sol_balance': sol_balance,
            'token_accounts': token_accounts
        }

    def create_trade_details_panel(self) -> Panel:
        """Erstellt ein detailliertes Trade-Panel"""
        if not self.performance.trades_history:
            return Panel("Keine Trade-Details verfügbar")
        
        # Tages-Performance
        today_trades = [t for t in self.performance.trades_history 
                       if t['timestamp'].date() == datetime.now().date()]
        
        daily_stats = {
            'profit': sum(t.get('profit', 0) for t in today_trades),
            'volume': sum(t.get('amount', 0) * t.get('price', 0) for t in today_trades),
            'trades': len(today_trades),
            'win_rate': sum(1 for t in today_trades if t.get('profit', 0) > 0) / len(today_trades) * 100 if today_trades else 0
        }
        
        # Pool-Performance
        pool_stats = {}
        for trade in self.performance.trades_history:
            pool = trade.get('pool_address')
            if pool not in pool_stats:
                pool_stats[pool] = {
                    'profit': 0,
                    'trades': 0,
                    'volume': 0
                }
            pool_stats[pool]['profit'] += trade.get('profit', 0)
            pool_stats[pool]['trades'] += 1
            pool_stats[pool]['volume'] += trade.get('amount', 0) * trade.get('price', 0)
        
        # Beste Pools
        best_pools = sorted(
            pool_stats.items(),
            key=lambda x: x[1]['profit'],
            reverse=True
        )[:3]
        
        content = f"""
{self.emojis['chart']} Tages-Performance
───────────────────
Profit: {self._format_profit(daily_stats['profit'])}
Volume: ${daily_stats['volume']:.2f}
Trades: {daily_stats['trades']}
Win Rate: {daily_stats['win_rate']:.1f}%

{self.emojis['money']} Beste Pools
───────────────────
"""
        
        for pool, stats in best_pools:
            content += f"{self.emojis['hot']} {pool[:8]}...{pool[-4:]}\n"
            content += f"   Profit: {self._format_profit(stats['profit'])}\n"
            content += f"   Trades: {stats['trades']}\n"
        
        return Panel(content, title="📈 Trading Details", border_style="cyan")

    def create_risk_panel(self) -> Panel:
        """Erstellt ein Risiko-Management Panel"""
        active_positions = len(self.wallet.open_positions)
        total_exposure = sum(
            pos['amount'] * pos.get('current_price', pos['entry_price'])
            for pos in self.wallet.open_positions.values()
        )
        
        # Risiko-Metriken
        risk_metrics = {
            'exposure_ratio': total_exposure / self.wallet.get_balance() if self.wallet.get_balance() > 0 else 0,
            'max_drawdown': self.performance.metrics.max_drawdown if self.performance.metrics else 0,
            'active_positions': active_positions,
            'available_margin': self.wallet.get_balance() - total_exposure
        }
        
        content = f"""
{self.emojis['warning']} Risiko-Übersicht
───────────────────
Exposure: {risk_metrics['exposure_ratio']:.1%}
Verfügbar: ${risk_metrics['available_margin']:.2f}
Positionen: {risk_metrics['active_positions']}/{self.config['risk_management']['max_open_positions']}
Max Drawdown: {risk_metrics['max_drawdown']:.1f}%
"""
        
        return Panel(content, title="⚠️ Risiko Management", border_style="red")

async def main():
    monitor = EnhancedTokenMonitor()
    await monitor.start_monitoring()

if __name__ == "__main__":
    asyncio.run(main()) 