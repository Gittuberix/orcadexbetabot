import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from rich.console import Console
from rich.table import Table

console = Console()
logger = logging.getLogger(__name__)

@dataclass
class Position:
    token: str
    amount: float
    entry_price: float
    timestamp: datetime
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

@dataclass
class Trade:
    pool_address: str
    token: str
    type: str  # 'buy' oder 'sell'
    amount: float
    price: float
    timestamp: datetime
    pnl: Optional[float] = None

class OrcaTradeSimulator:
    def __init__(self, initial_capital: float = 10.0):
        self.initial_capital = initial_capital  # In SOL
        self.current_capital = initial_capital
        self.positions: Dict[str, Position] = {}  # token -> Position
        self.trades: List[Trade] = []
        self.max_position_size = 0.2  # 20% des Kapitals
        self.max_slippage = 0.01  # 1% max slippage
        
    def simulate_trade(self, pool_data: Dict, amount: float, is_buy: bool) -> Optional[Trade]:
        """Simuliert einen Trade mit Slippage und Fees"""
        try:
            token = pool_data['tokenA']['symbol']
            price = float(pool_data['price'])
            liquidity = float(pool_data.get('liquidity', 0))
            
            # 1. Position Size Check
            max_amount = self.current_capital * self.max_position_size
            if amount > max_amount:
                logger.warning(f"Amount {amount} exceeds max position size {max_amount}")
                return None
                
            # 2. Liquidität Check
            required_liquidity = amount * price
            if required_liquidity > liquidity * 0.01:  # Max 1% of pool liquidity
                logger.warning("Insufficient pool liquidity")
                return None
                
            # 3. Slippage Simulation
            impact = self._calculate_price_impact(amount, liquidity)
            actual_price = price * (1 + impact if is_buy else 1 - impact)
            
            if abs(actual_price - price) / price > self.max_slippage:
                logger.warning("Slippage too high")
                return None
                
            # 4. Trade ausführen
            total_cost = amount * actual_price
            if is_buy:
                if total_cost > self.current_capital:
                    logger.warning("Insufficient capital")
                    return None
                    
                # Position eröffnen
                self.positions[token] = Position(
                    token=token,
                    amount=amount,
                    entry_price=actual_price,
                    timestamp=datetime.now(),
                    stop_loss=actual_price * 0.95,  # 5% Stop Loss
                    take_profit=actual_price * 1.15  # 15% Take Profit
                )
                self.current_capital -= total_cost
                
            else:
                if token not in self.positions:
                    logger.warning("No position to sell")
                    return None
                    
                # Position schließen
                position = self.positions[token]
                pnl = (actual_price - position.entry_price) * amount
                self.current_capital += total_cost
                del self.positions[token]
                
            # 5. Trade aufzeichnen
            trade = Trade(
                pool_address=pool_data['address'],
                token=token,
                type='buy' if is_buy else 'sell',
                amount=amount,
                price=actual_price,
                timestamp=datetime.now(),
                pnl=pnl if not is_buy else None
            )
            self.trades.append(trade)
            
            self._log_trade(trade)
            return trade
            
        except Exception as e:
            logger.error(f"Trade simulation failed: {e}")
            return None
            
    def _calculate_price_impact(self, amount: float, liquidity: float) -> float:
        """Berechnet simulierten Price Impact"""
        return (amount / liquidity) ** 0.5 * 0.01  # Vereinfachte Formel
        
    def check_positions(self, current_prices: Dict[str, float]):
        """Prüft Stop Loss und Take Profit"""
        for token, position in list(self.positions.items()):
            if token not in current_prices:
                continue
                
            current_price = current_prices[token]
            
            # Stop Loss
            if position.stop_loss and current_price <= position.stop_loss:
                logger.info(f"Stop Loss triggered for {token}")
                self.simulate_trade(
                    {'address': '', 'tokenA': {'symbol': token}, 'price': current_price},
                    position.amount,
                    False
                )
                
            # Take Profit
            elif position.take_profit and current_price >= position.take_profit:
                logger.info(f"Take Profit triggered for {token}")
                self.simulate_trade(
                    {'address': '', 'tokenA': {'symbol': token}, 'price': current_price},
                    position.amount,
                    False
                )
                
    def get_stats(self) -> Table:
        """Generiert Statistiken"""
        table = Table(title="Trading Stats")
        
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right")
        
        # Performance
        pnl = self.current_capital - self.initial_capital
        pnl_pct = (pnl / self.initial_capital) * 100
        
        # Trades
        profitable_trades = len([t for t in self.trades if t.pnl and t.pnl > 0])
        total_trades = len(self.trades)
        win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Stats hinzufügen
        table.add_row("Initial Capital", f"{self.initial_capital:.4f} SOL")
        table.add_row("Current Capital", f"{self.current_capital:.4f} SOL")
        table.add_row("P/L", f"{pnl:+.4f} SOL ({pnl_pct:+.2f}%)")
        table.add_row("Total Trades", str(total_trades))
        table.add_row("Win Rate", f"{win_rate:.1f}%")
        
        return table
        
    def _log_trade(self, trade: Trade):
        """Loggt Trade-Details"""
        color = "green" if trade.type == 'buy' else "red"
        console.print(f"[{color}]Trade: {trade.type.upper()} {trade.amount:.4f} {trade.token} @ {trade.price:.4f}[/{color}]")
        if trade.pnl:
            pnl_color = "green" if trade.pnl > 0 else "red"
            console.print(f"P/L: [{pnl_color}]{trade.pnl:+.4f}[/{pnl_color}]") 