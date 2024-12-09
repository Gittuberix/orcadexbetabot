from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict

@dataclass
class Trade:
    pool_address: str
    token_address: str
    type: str  # 'buy' oder 'sell'
    amount: float
    price: float
    timestamp: datetime
    tx_id: Optional[str] = None
    slippage: Optional[float] = None
    profit: Optional[float] = None
    status: str = 'pending'  # 'pending', 'completed', 'failed'
    source: str = 'mainnet'  # 'mainnet' oder 'backtest'

@dataclass
class Pool:
    name: str
    token_a: str
    token_b: str
    fee_tier: float

@dataclass
class Signal:
    type: str
    pool_address: str
    price: float
    amount: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None 