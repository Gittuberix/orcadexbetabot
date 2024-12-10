import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List
from rich.console import Console
from src.whirlpool.microscope import WhirlpoolMicroscope
from src.models import Trade, PoolState, BacktestResult
from src.risk_manager import RiskManager, RiskParameters
from src.wallet_manager import WalletManager
from src.config.network_config import WHIRLPOOL_CONFIGS
from orca_whirlpool.context import WhirlpoolContext
from orca_whirlpool.constants import ORCA_WHIRLPOOL_PROGRAM_ID

console = Console()
logger = logging.getLogger(__name__)

class BacktestRunner:
    def __init__(self):
        self.wallet = WalletManager()
        self.ctx = WhirlpoolContext(
            ORCA_WHIRLPOOL_PROGRAM_ID, 
            self.wallet.connection, 
            self.wallet.keypair
        )
        self.microscope = WhirlpoolMicroscope()
        self.risk_manager = RiskManager()
        
    async def get_historical_fees(self, pool_address: str, timestamp: datetime) -> int:
        """Holt historische Fee-Daten"""
        try:
            # Hole historische Pool-Daten
            whirlpool = await self.ctx.fetcher.get_whirlpool(
                Pubkey.from_string(pool_address)
            )
            
            # Berechne historische Fee
            historical_fee = whirlpool.fee_rate
            
            # Hole historische Gas-Kosten
            historical_gas = await self.microscope.get_historical_gas_price(timestamp)
            
            return historical_fee, historical_gas
            
        except Exception as e:
            logger.error(f"Fehler beim Abrufen historischer Fees: {e}")
            return None, None
            
    async def run_backtest(self,
        pool_address: str,
        start_time: datetime,
        end_time: datetime,
        initial_capital: Decimal = Decimal("1000"),
        trade_size: Decimal = Decimal("0.1"),
        interval_minutes: int = 5
    ) -> BacktestResult:
        """Führt Backtest mit historischen Daten durch"""
        try:
            trades = []
            current_capital = initial_capital
            max_capital = initial_capital
            
            # Hole historische Daten
            historical_data = await self.microscope.get_historical_pool_data(
                pool_address, start_time, end_time
            )
            
            # Simuliere Trades
            for data in historical_data:
                # Hole historische Fees
                fee_rate, gas_cost = await self.get_historical_fees(
                    pool_address, data['timestamp']
                )
                
                if not fee_rate or not gas_cost:
                    continue
                    
                # Prüfe Risiko
                is_safe = self.risk_manager.check_trade(
                    price=float(data['price']),
                    amount=float(trade_size),
                    liquidity=data['liquidity']
                )
                
                if is_safe:
                    # Simuliere Trade
                    side = 'buy' if len(trades) % 2 == 0 else 'sell'
                    amount_in = int(trade_size * 1e9)  # Convert to lamports
                    
                    trade = Trade(
                        timestamp=data['timestamp'],
                        pool_address=pool_address,
                        side=side,
                        amount_in=amount_in,
                        amount_out=int(amount_in * float(data['price'])),
                        price=Decimal(str(data['price'])),
                        fee=int(amount_in * fee_rate / 10000),
                        slippage=Decimal("0.01"),
                        success=True,
                        gas_cost=gas_cost
                    )
                    
                    trades.append(trade)
                    
                    # Update Kapital
                    if side == 'buy':
                        current_capital -= (trade.amount_in + trade.fee + trade.gas_cost) / 1e6
                    else:
                        current_capital += (trade.amount_out - trade.fee - trade.gas_cost) / 1e6
                        
                    max_capital = max(max_capital, current_capital)
                    
            # Berechne Ergebnis
            return BacktestResult(
                pool_address=pool_address,
                start_time=start_time,
                end_time=end_time,
                total_trades=len(trades),
                winning_trades=len([t for t in trades if t.amount_out > t.amount_in]),
                total_volume=sum(t.amount_in for t in trades),
                total_fees_paid=sum(t.fee for t in trades),
                total_gas_cost=sum(t.gas_cost for t in trades),
                net_profit=current_capital - initial_capital,
                roi=((current_capital - initial_capital) / initial_capital) * 100,
                max_drawdown=((max_capital - current_capital) / max_capital) * 100,
                trades=trades
            )
            
        except Exception as e:
            logger.error(f"Fehler im Backtest: {e}")
            return None