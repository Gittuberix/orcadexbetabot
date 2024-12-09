import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from rich.console import Console
from rich.table import Table
from rich.progress import track
import pandas as pd
import numpy as np

console = Console()
logger = logging.getLogger(__name__)

@dataclass
class BacktestTrade:
    timestamp: datetime
    pool_address: str
    token: str
    type: str
    amount: float
    price: float
    slippage: float
    fees: float
    pnl: Optional[float] = None

class OrcaBacktester:
    def __init__(self, config: Dict):
        self.config = config
        self.initial_capital = float(config.get('initial_capital', 1.0))
        self.current_capital = self.initial_capital
        self.trades: List[BacktestTrade] = []
        self.positions = {}
        self.metrics = {
            'max_drawdown': 0,
            'best_trade': 0,
            'worst_trade': 0,
            'avg_trade_duration': timedelta(0)
        }
        
    async def run_backtest(self, start_date: datetime, end_date: datetime):
        """Führt Backtest für Zeitraum aus"""
        console.print(f"\n[cyan]Starting Backtest: {start_date} to {end_date}[/cyan]")
        
        try:
            # 1. Historische Daten laden
            historical_data = await self._load_historical_data(start_date, end_date)
            if not historical_data:
                raise Exception("No historical data available")
                
            # 2. Für jeden Zeitpunkt simulieren
            for timestamp in track(pd.date_range(start_date, end_date, freq='1min'),
                                description="Running backtest..."):
                await self._process_timepoint(timestamp, historical_data)
                
            # 3. Metriken berechnen
            self._calculate_metrics()
            
            # 4. Ergebnisse anzeigen
            self._print_results()
            
        except Exception as e:
            logger.error(f"Backtest failed: {e}")
            
    async def _load_historical_data(self, start_date: datetime, end_date: datetime) -> Dict:
        """Lädt historische Daten von Orca"""
        try:
            from src.data.orca_provider import OrcaDataProvider
            provider = OrcaDataProvider(self.config)
            
            # Top Pools laden
            pools = await provider.get_pools()
            data = {}
            
            for pool in pools[:10]:  # Top 10 Pools
                history = await provider.get_pool_price_history(
                    pool['address'],
                    start_date,
                    end_date
                )
                if not history.empty:
                    data[pool['address']] = {
                        'history': history,
                        'token': pool['tokenA']['symbol']
                    }
                    
            return data
            
        except Exception as e:
            logger.error(f"Failed to load historical data: {e}")
            return {}
            
    async def _process_timepoint(self, timestamp: datetime, data: Dict):
        """Verarbeitet einen Zeitpunkt"""
        for pool_address, pool_data in data.items():
            try:
                # Daten für den Zeitpunkt
                point_data = pool_data['history'][
                    pool_data['history'].index == timestamp
                ]
                if point_data.empty:
                    continue
                    
                price = point_data['close'].iloc[0]
                volume = point_data['volume'].iloc[0]
                
                # Trading Signale prüfen
                if self._should_enter(pool_address, price, volume):
                    await self._execute_trade(pool_address, price, True)
                    
                elif self._should_exit(pool_address, price):
                    await self._execute_trade(pool_address, price, False)
                    
            except Exception as e:
                logger.error(f"Error processing {timestamp}: {e}")
                
    def _should_enter(self, pool_address: str, price: float, volume: float) -> bool:
        """Entry Signal"""
        try:
            # Mindest-Volumen
            if volume < self.config.get('min_volume', 10000):
                return False
                
            # Position Size Check
            max_position = self.current_capital * self.config.get('max_position_size', 0.2)
            if price > max_position:
                return False
                
            # Technische Analyse
            return self._check_entry_signals(pool_address, price)
            
        except Exception:
            return False
            
    def _should_exit(self, pool_address: str, price: float) -> bool:
        """Exit Signal"""
        if pool_address not in self.positions:
            return False
            
        position = self.positions[pool_address]
        
        # Stop Loss
        if price <= position['stop_loss']:
            return True
            
        # Take Profit
        if price >= position['take_profit']:
            return True
            
        return False
        
    async def _execute_trade(self, pool_address: str, price: float, is_entry: bool):
        """Führt simulierten Trade aus"""
        try:
            if is_entry:
                # Entry Trade
                amount = self.current_capital * self.config.get('position_size', 0.1)
                slippage = self._calculate_slippage(amount, price)
                fees = amount * self.config.get('fee_rate', 0.003)
                
                actual_price = price * (1 + slippage)
                total_cost = amount * actual_price + fees
                
                if total_cost > self.current_capital:
                    return
                    
                self.current_capital -= total_cost
                self.positions[pool_address] = {
                    'amount': amount,
                    'entry_price': actual_price,
                    'stop_loss': actual_price * 0.95,
                    'take_profit': actual_price * 1.15
                }
                
            else:
                # Exit Trade
                position = self.positions[pool_address]
                amount = position['amount']
                slippage = self._calculate_slippage(amount, price)
                fees = amount * self.config.get('fee_rate', 0.003)
                
                actual_price = price * (1 - slippage)
                total_return = amount * actual_price - fees
                
                pnl = total_return - (amount * position['entry_price'])
                self.current_capital += total_return
                
                del self.positions[pool_address]
                
            # Trade aufzeichnen
            self.trades.append(BacktestTrade(
                timestamp=datetime.now(),
                pool_address=pool_address,
                token=pool_address,  # Vereinfacht
                type='buy' if is_entry else 'sell',
                amount=amount,
                price=actual_price,
                slippage=slippage,
                fees=fees,
                pnl=pnl if not is_entry else None
            ))
            
        except Exception as e:
            logger.error(f"Trade execution failed: {e}")
            
    def _calculate_metrics(self):
        """Berechnet Performance-Metriken"""
        if not self.trades:
            return
            
        # PnL Analyse
        pnls = [t.pnl for t in self.trades if t.pnl is not None]
        if pnls:
            self.metrics['best_trade'] = max(pnls)
            self.metrics['worst_trade'] = min(pnls)
            
        # Drawdown
        capital_history = []
        current = self.initial_capital
        for trade in self.trades:
            if trade.pnl:
                current += trade.pnl
                capital_history.append(current)
                
        if capital_history:
            peak = self.initial_capital
            for capital in capital_history:
                drawdown = (peak - capital) / peak
                self.metrics['max_drawdown'] = max(
                    self.metrics['max_drawdown'],
                    drawdown
                )
                peak = max(peak, capital)
                
    def _print_results(self):
        """Zeigt Backtest-Ergebnisse"""
        console.print("\n[bold cyan]📊 Backtest Results[/bold cyan]")
        
        # Performance Table
        table = Table(title="Performance Metrics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right")
        
        # Basis-Metriken
        initial = self.initial_capital
        final = self.current_capital
        pnl = final - initial
        pnl_pct = (pnl / initial) * 100
        
        table.add_row("Initial Capital", f"{initial:.4f} SOL")
        table.add_row("Final Capital", f"{final:.4f} SOL")
        table.add_row("Total P/L", f"{pnl:+.4f} SOL ({pnl_pct:+.2f}%)")
        
        # Trading Metriken
        total_trades = len(self.trades)
        profitable = len([t for t in self.trades if t.pnl and t.pnl > 0])
        win_rate = (profitable / total_trades * 100) if total_trades > 0 else 0
        
        table.add_row("Total Trades", str(total_trades))
        table.add_row("Win Rate", f"{win_rate:.1f}%")
        table.add_row("Max Drawdown", f"{self.metrics['max_drawdown']*100:.1f}%")
        table.add_row("Best Trade", f"{self.metrics['best_trade']:+.4f} SOL")
        table.add_row("Worst Trade", f"{self.metrics['worst_trade']:+.4f} SOL")
        
        console.print(table) 