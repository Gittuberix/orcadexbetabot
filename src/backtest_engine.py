from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import logging
from typing import Dict, List
from data_collector import DataCollector
from risk_manager import RiskManager
from trading_manager import TradingManager
from models import Signal, Pool, Trade
import asyncio

logger = logging.getLogger(__name__)

class BacktestEngine:
    def __init__(self, start_date, end_date, initial_capital):
        self.start_date = start_date
        self.end_date = end_date
        self.capital = initial_capital
        self.positions = {}
        self.trades = []
        self.performance_metrics = {}
        
        # Initialize components
        self.data_collector = DataCollector()
        self.risk_manager = RiskManager()
        self.trading_manager = TradingManager()
        
        # Performance tracking
        self.daily_returns = []
        self.equity_curve = [initial_capital]

    async def _get_historical_data(self, date: datetime) -> Dict:
        """Fetch historical market data for given date"""
        try:
            pools = list(self.trading_manager.WHIRLPOOL_IDS.values())
            return await self.data_collector.get_historical_data(date, pools)
        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            return {}

    def _generate_signals(self, market_data: Dict) -> List:
        """Generate trading signals from market data"""
        signals = []
        for pool_id, data in market_data.items():
            try:
                if self._check_entry_conditions(data):
                    signals.append({
                        'pool_id': pool_id,
                        'type': 'entry',
                        'price': data['price'],
                        'size': self._calculate_position_size(data)
                    })
            except Exception as e:
                logger.error(f"Error generating signals: {e}")
        return signals

    def _check_entry_conditions(self, data: Dict) -> bool:
        """Basic entry conditions check"""
        try:
            price = float(data['price'])
            volume = float(data.get('volume', 0))
            volatility = self._calculate_volatility(data)
            
            # Basic conditions
            return (
                volume > 100000 and  # Min volume
                volatility > 0.01 and  # Min volatility
                volatility < 0.05  # Max volatility
            )
        except Exception as e:
            logger.error(f"Error checking entry conditions: {e}")
            return False

    def _calculate_position_size(self, data: Dict) -> float:
        """Calculate position size based on risk parameters"""
        try:
            volatility = self._calculate_volatility(data)
            base_size = self.capital * 0.02  # 2% base position size
            return base_size * (1 / volatility)  # Adjust for volatility
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0

    def _calculate_volatility(self, data: Dict) -> float:
        """Calculate price volatility"""
        try:
            prices = pd.Series(data['prices'])
            return prices.pct_change().std()
        except Exception as e:
            logger.error(f"Error calculating volatility: {e}")
            return float('inf')

    async def run_backtest(self):
        """Run the backtest simulation"""
        current_date = self.start_date
        while current_date <= self.end_date:
            try:
                # Get market data
                market_data = await self._get_historical_data(current_date)
                
                # Generate and process signals
                signals = self._generate_signals(market_data)
                for signal in signals:
                    if self.risk_manager.check_trade(signal, market_data[signal['pool_id']]['price']):
                        trade_result = await self._execute_backtest_trade(signal)
                        if trade_result:
                            self.trades.append(trade_result)
                
                # Update positions and metrics
                self._update_positions(market_data)
                self._calculate_daily_metrics(current_date)
                
                current_date += timedelta(minutes=1)  # 1-minute intervals
                
            except Exception as e:
                logger.error(f"Error in backtest loop: {e}")
                
            await asyncio.sleep(0)  # Allow other tasks to run

    def generate_report(self) -> Dict:
        """Generate backtest report"""
        try:
            return {
                'total_return': self._calculate_total_return(),
                'sharpe_ratio': self._calculate_sharpe_ratio(),
                'max_drawdown': self._calculate_max_drawdown(),
                'win_rate': self._calculate_win_rate(),
                'trades': self.trades
            }
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return {}

    def _calculate_total_return(self) -> float:
        """Calculate total return percentage"""
        if not self.equity_curve:
            return 0
        return ((self.equity_curve[-1] - self.equity_curve[0]) / self.equity_curve[0]) * 100

    def _calculate_sharpe_ratio(self) -> float:
        """Calculate Sharpe ratio"""
        if not self.daily_returns:
            return 0
        returns = np.array(self.daily_returns)
        if returns.std() == 0:
            return 0
        return (returns.mean() / returns.std()) * np.sqrt(252)

    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown percentage"""
        if not self.equity_curve:
            return 0
        peak = self.equity_curve[0]
        max_dd = 0
        for value in self.equity_curve:
            if value > peak:
                peak = value
            dd = (peak - value) / peak * 100
            max_dd = max(max_dd, dd)
        return max_dd

    def _calculate_win_rate(self) -> float:
        """Calculate win rate percentage"""
        if not self.trades:
            return 0
        winning_trades = sum(1 for trade in self.trades if trade.get('profit', 0) > 0)
        return (winning_trades / len(self.trades)) * 100

    async def _execute_backtest_trade(self, signal: Dict) -> Dict:
        """Execute trade in backtest environment"""
        try:
            price = signal['price']
            size = signal['size']
            pool_id = signal['pool_id']
            
            # Simulate execution with slippage
            executed_price = self._apply_slippage(price, size)
            
            trade_result = {
                'timestamp': datetime.now(),
                'pool_id': pool_id,
                'type': signal['type'],
                'size': size,
                'price': executed_price,
                'value': size * executed_price,
                'slippage': (executed_price - price) / price * 100
            }
            
            # Calculate profit/loss if closing position
            if pool_id in self.positions:
                entry_price = self.positions[pool_id]['price']
                trade_result['profit'] = (executed_price - entry_price) / entry_price * 100
                
            return trade_result
            
        except Exception as e:
            logger.error(f"Error executing backtest trade: {e}")
            return None

    def _apply_slippage(self, price: float, size: float) -> float:
        """Simulate price slippage based on order size"""
        try:
            # Basic slippage model: larger orders = more slippage
            base_slippage = 0.001  # 0.1% base slippage
            size_factor = size / 10000  # Adjust based on your typical order size
            total_slippage = base_slippage * (1 + size_factor)
            
            # Random component to simulate market conditions
            random_factor = np.random.normal(1, 0.1)  # Mean=1, STD=0.1
            total_slippage *= random_factor
            
            return price * (1 + total_slippage)
            
        except Exception as e:
            logger.error(f"Error applying slippage: {e}")
            return price

    def _update_positions(self, market_data: Dict):
        """Update positions with current market data"""
        try:
            for pool_id, position in self.positions.items():
                if pool_id in market_data:
                    current_price = market_data[pool_id]['price']
                    
                    # Update position value
                    position['current_price'] = current_price
                    position['current_value'] = position['size'] * current_price
                    position['profit_loss'] = (current_price - position['price']) / position['price'] * 100
                    
                    # Check stop loss
                    if position['profit_loss'] < -self.risk_manager.stop_loss:
                        self._close_position(pool_id, current_price)
                        
        except Exception as e:
            logger.error(f"Error updating positions: {e}")

    def _calculate_daily_metrics(self, date: datetime):
        """Calculate daily performance metrics"""
        try:
            # Calculate total portfolio value
            portfolio_value = self.capital
            for position in self.positions.values():
                portfolio_value += position['current_value']
                
            # Calculate daily return
            if self.equity_curve:
                daily_return = (portfolio_value - self.equity_curve[-1]) / self.equity_curve[-1]
                self.daily_returns.append(daily_return)
                
            self.equity_curve.append(portfolio_value)
            
        except Exception as e:
            logger.error(f"Error calculating daily metrics: {e}")

    def _close_position(self, pool_id: str, price: float):
        """Close a position and record the trade"""
        try:
            position = self.positions[pool_id]
            trade_result = {
                'timestamp': datetime.now(),
                'pool_id': pool_id,
                'type': 'exit',
                'size': position['size'],
                'price': price,
                'value': position['size'] * price,
                'profit': (price - position['price']) / position['price'] * 100
            }
            
            self.trades.append(trade_result)
            del self.positions[pool_id]
            
        except Exception as e:
            logger.error(f"Error closing position: {e}")