from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

@dataclass
class WhirlpoolData:
    pool_name: str
    price: float
    liquidity: int
    volume_24h: float
    fee_rate: float
    timestamp: datetime

@dataclass
class TradeData:
    pool_name: str
    price: float
    amount: float
    side: str  # 'buy' oder 'sell'
    timestamp: datetime

@dataclass
class BacktestResult:
    total_trades: int
    winning_trades: int
    losing_trades: int
    roi: Decimal
    max_drawdown: Decimal
    sharpe_ratio: float
    trades: List[TradeData]

@dataclass
class PoolState:
    address: str
    token_a: str
    token_b: str
    price: Decimal
    liquidity: int
    volume_24h: Decimal
    fee_rate: int
    tick_spacing: int
    tick_current: int
    timestamp: datetime

@dataclass
class Trade:
    timestamp: datetime
    pool_address: str
    side: str  # 'buy' oder 'sell'
    amount_in: int
    amount_out: int
    price: Decimal
    fee: int
    slippage: Decimal
    success: bool
    gas_cost: Optional[int] = None
    tx_signature: Optional[str] = None
    error_message: Optional[str] = None 