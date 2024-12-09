from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Trade:
    pool_address: str
    token_address: str
    type: str  # 'buy' oder 'sell'
    amount: float
    price: float
    timestamp: datetime
    source: str = 'bot'
    profit: Optional[float] = None

@dataclass
class Pool:
    address: str
    token_a: str
    token_b: str
    liquidity: float
    volume_24h: float
    fee: float 