from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional, List

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
class BacktestResult:
    pool_address: str
    start_time: datetime
    end_time: datetime
    total_trades: int
    winning_trades: int
    total_volume: Decimal
    total_fees_paid: Decimal
    total_gas_cost: Decimal
    net_profit: Decimal
    roi: Decimal
    max_drawdown: Decimal
    trades: List[Trade]

@dataclass
class TokenBalance:
    mint: str
    amount: Decimal
    decimals: int
    symbol: Optional[str] = None

@dataclass
class WhirlpoolConfig:
    address: str
    token_a: str
    token_b: str
    tick_spacing: int
    fee_rate: int
    decimals_a: int
    decimals_b: int

@dataclass
class TradingStrategy:
    name: str
    min_profit: Decimal
    max_loss: Decimal
    position_size: Decimal
    slippage_tolerance: Decimal
    min_liquidity: int
    max_price_impact: Decimal
