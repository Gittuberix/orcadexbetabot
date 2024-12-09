import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from rich.console import Console
from rich.live import Live
from rich.table import Table
from whirlpool import WhirlpoolClient
from models import Trade
import pandas as pd
import json
from config.connections import ENVIRONMENTS, WHIRLPOOL_IDS

console = Console()
logger = logging.getLogger(__name__)

class BacktestPeriod:
    HOUR_1 = timedelta(hours=1)
    HOUR_8 = timedelta(hours=8)
    DAY_1 = timedelta(days=1)
    DAY_2 = timedelta(days=2)
    DAY_3 = timedelta(days=3)
    DAY_7 = timedelta(days=7)
    DAY_30 = timedelta(days=30)
    DAY_90 = timedelta(days=90)

class WhirlpoolBacktestEngine:
    def __init__(self, period: timedelta, initial_capital: float = 1.0):
        self.whirlpool = WhirlpoolClient()
        self.period = period
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.trades = []
        self.pool_data = {}
        self.config = ENVIRONMENTS['backtest']
        self.data_dir = self.config['data_dir']
        self.whirlpool_ids = WHIRLPOOL_IDS
        
    async def run_backtest(self):
        """Führt Backtest für den gewählten Zeitraum aus"""
        end_time = datetime.now()
        start_time = end_time - self.period
        
        period_name = self._get_period_name()
        console.print(f"\n[cyan]Starting {period_name} Backtest[/cyan]")
        console.print(f"Period: {start_time} to {end_time}")
        
        try:
            # 1. Historische Daten laden
            await self._load_historical_data(start_time, end_time)
            
            # 2. Live Status anzeigen
            with Live(self._generate_status(), refresh_per_second=1) as live:
                # Zeitpunkte simulieren
                current_time = start_time
                while current_time <= end_time:
                    await self._process_timepoint(current_time)
                    live.update(self._generate_status())
                    current_time += timedelta(minutes=1)
                    
            # 3. Ergebnisse speichern
            self._save_results(period_name)
            
        except Exception as e:
            logger.error(f"Backtest failed: {e}")
            
        finally:
            self._print_results()
            
    async def _load_historical_data(self, start_time: datetime, end_time: datetime):
        """Lädt historische Daten für den Zeitraum"""
        try:
            # 1. Aktive Pools laden
            pools = await self.whirlpool.get_active_whirlpools()
            
            # 2. Top Pools nach Volumen filtern
            top_pools = sorted(
                pools,
                key=lambda x: float(x.get('volume24h', 0)),
                reverse=True
            )[:10]
            
            # 3. Historische Daten für jeden Pool laden
            for pool in top_pools:
                pool_data = await self.whirlpool.get_pool_price_history(
                    pool['address'],
                    start_time,
                    end_time
                )
                if not pool_data.empty:
                    self.pool_data[pool['address']] = pool_data
                    
            console.print(f"[green]Loaded data for {len(self.pool_data)} pools[/green]")
            
        except Exception as e:
            logger.error(f"Failed to load historical data: {e}")
            
    async def _process_timepoint(self, timestamp: datetime):
        """Verarbeitet einen Zeitpunkt"""
        for pool_address, data in self.pool_data.items():
            try:
                # Daten für den Zeitpunkt extrahieren
                point_data = data[data.index == timestamp]
                if point_data.empty:
                    continue
                    
                price = point_data['close'].iloc[0]
                volume = point_data['volume'].iloc[0]
                
                # Trading Signale prüfen
                if self._should_trade(pool_address, price, volume):
                    trade = self._execute_trade(pool_address, price, timestamp)
                    if trade:
                        self.trades.append(trade)
                        
            except Exception as e:
                logger.error(f"Error processing timepoint {timestamp} for pool {pool_address}: {e}")
                
    def _should_trade(self, pool_address: str, price: float, volume: float) -> bool:
        """Trading Strategie basierend auf Zeitraum"""
        try:
            data = self.pool_data[pool_address]
            
            # Verschiedene Strategien je nach Zeitraum
            if self.period <= BacktestPeriod.HOUR_1:
                # Kurzfristige Momentum-Strategie
                return self._check_short_term_momentum(data, price)
                
            elif self.period <= BacktestPeriod.DAY_1:
                # Intraday-Strategie
                return self._check_intraday_opportunity(data, price, volume)
                
            else:
                # Längerfristige Trend-Strategie
                return self._check_long_term_trend(data, price)
                
        except Exception:
            return False
            
    def _get_period_name(self) -> str:
        """Gibt lesbaren Namen für den Zeitraum zurück"""
        if self.period == BacktestPeriod.HOUR_1:
            return "1 Hour"
        elif self.period == BacktestPeriod.HOUR_8:
            return "8 Hours"
        elif self.period == BacktestPeriod.DAY_1:
            return "1 Day"
        elif self.period == BacktestPeriod.DAY_2:
            return "2 Days"
        elif self.period == BacktestPeriod.DAY_3:
            return "3 Days"
        elif self.period == BacktestPeriod.DAY_7:
            return "7 Days"
        elif self.period == BacktestPeriod.DAY_30:
            return "30 Days"
        elif self.period == BacktestPeriod.DAY_90:
            return "90 Days"
        return "Custom Period" 