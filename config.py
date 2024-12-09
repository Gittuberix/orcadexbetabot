from dataclasses import dataclass, field
from typing import Dict, Optional
from datetime import timedelta

@dataclass
class NetworkConfig:
    rpc_url: str = "https://api.mainnet-beta.solana.com"
    orca_api: str = "https://api.mainnet.orca.so"
    priority_fee: float = 0.000001
    max_retries: int = 3
    retry_delay: int = 1

@dataclass
class TradingParams:
    initial_balance: float = 1000.0
    position_size: float = 0.1
    max_slippage: float = 0.01
    min_profit: float = 0.02
    min_liquidity: float = 10000.0
    min_volume_24h: float = 5000.0
    max_price_impact: float = 0.02
    update_interval: int = 1
    cache_duration: int = 30
    candle_interval: int = 60
    stop_loss: float = 0.05
    take_profit: float = 0.1
    max_open_positions: int = 3
    backtest_days: int = 7
    backtest_initial_balance: float = 10000.0

@dataclass
class BotConfig:
    network_config: NetworkConfig = field(default_factory=NetworkConfig)
    trading_params: TradingParams = field(default_factory=TradingParams)
    token_whitelist: Optional[Dict[str, str]] = None
    token_blacklist: Optional[Dict[str, str]] = None