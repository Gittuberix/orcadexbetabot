from dataclasses import dataclass
from typing import Dict, Optional
import yaml
import os
from pathlib import Path

@dataclass
class NetworkConfig:
    """Network-specific configuration"""
    rpc_endpoint: str = "https://api.mainnet-beta.solana.com"
    orca_api: str = "https://api.orca.so"
    priority_fee: float = 0.000001
    
    @classmethod
    def get_config(cls, network: str = 'mainnet') -> "NetworkConfig":
        configs = {
            'mainnet': {
                'rpc_endpoint': 'https://api.mainnet-beta.solana.com',
                'orca_api': 'https://api.orca.so',
                'priority_fee': 0.000001,
            },
            'devnet': {
                'rpc_endpoint': 'https://api.devnet.solana.com',
                'orca_api': 'https://api.devnet.orca.so',
                'priority_fee': 0.000001,
            }
        }
        return cls(**configs[network])

@dataclass
class TradingParams:
    """Trading parameters consistent across networks"""
    update_interval: int = 3  # seconds
    candle_interval: int = 60  # seconds
    cache_duration: int = 10  # seconds
    min_liquidity: float = 10000  # USD
    min_volume_24h: float = 1000  # USD
    slippage_tolerance: float = 0.005  # 0.5%
    maker_fee: float = 0.0020  # 0.20%
    taker_fee: float = 0.0035  # 0.35%
    protocol_fee: float = 0.0001  # 0.01%

@dataclass
class MemeSnipingConfig:
    """Meme token sniping strategy configuration"""
    enabled: bool = True
    max_token_price: float = 0.001
    min_liquidity: float = 10000.0
    min_holders: int = 100
    max_position_size: float = 0.5
    max_liquidity_percentage: float = 0.01
    min_liquidity_growth: float = 0.5
    min_price_growth: float = 0.2
    max_price_growth: float = 5.0
    breakout_threshold: float = 1.2
    stop_loss: float = 0.3
    take_profit: float = 2.0
    max_entry_time: int = 300
    min_hold_time: int = 60

@dataclass
class BotConfig:
    """Main bot configuration"""
    # Network settings
    network: str = 'mainnet'
    network_config: NetworkConfig = None
    trading_params: TradingParams = None
    
    # Trading settings
    trading_enabled: bool = True
    backtesting_mode: bool = False
    max_trades_per_day: int = 100
    min_profit_threshold: float = 0.005  # 0.5%
    
    # Risk management
    max_position_size: float = 1000.0  # USD
    stop_loss_percentage: float = 0.02  # 2%
    take_profit_percentage: float = 0.05  # 5%
    
    # Strategy settings
    meme_sniping: MemeSnipingConfig = None
    
    def __post_init__(self):
        if self.network_config is None:
            self.network_config = NetworkConfig.get_config(self.network)
        if self.trading_params is None:
            self.trading_params = TradingParams()
        if self.meme_sniping is None:
            self.meme_sniping = MemeSnipingConfig()
    
    def validate_backtest_consistency(self, live_config: "BotConfig") -> bool:
        """
        Validates that backtest configuration matches live trading configuration
        for all relevant parameters that affect profitability calculations.
        
        Args:
            live_config: The live trading configuration to compare against
            
        Returns:
            bool: True if configurations match, raises ValueError if not
        """
        critical_params = [
            ('trading_params.maker_fee', self.trading_params.maker_fee, live_config.trading_params.maker_fee),
            ('trading_params.taker_fee', self.trading_params.taker_fee, live_config.trading_params.taker_fee),
            ('trading_params.protocol_fee', self.trading_params.protocol_fee, live_config.trading_params.protocol_fee),
            ('trading_params.slippage_tolerance', self.trading_params.slippage_tolerance, live_config.trading_params.slippage_tolerance),
            ('min_profit_threshold', self.min_profit_threshold, live_config.min_profit_threshold),
            ('max_position_size', self.max_position_size, live_config.max_position_size),
            ('stop_loss_percentage', self.stop_loss_percentage, live_config.stop_loss_percentage),
            ('take_profit_percentage', self.take_profit_percentage, live_config.take_profit_percentage),
            ('trading_params.min_liquidity', self.trading_params.min_liquidity, live_config.trading_params.min_liquidity),
            ('trading_params.min_volume_24h', self.trading_params.min_volume_24h, live_config.trading_params.min_volume_24h),
        ]
        
        mismatches = []
        for param_name, backtest_value, live_value in critical_params:
            if abs(backtest_value - live_value) > 1e-10:  # Using small epsilon for float comparison
                mismatches.append(f"{param_name}: backtest={backtest_value} != live={live_value}")
                
        if mismatches:
            raise ValueError(
                "Backtest configuration does not match live configuration:\n" +
                "\n".join(mismatches)
            )
            
        return True
    
    @classmethod
    def load_from_file(cls, config_path: str = "config.yaml") -> "BotConfig":
        """Loads configuration from YAML file"""
        if not os.path.exists(config_path):
            return cls()
            
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
            # Convert nested dicts to dataclasses
            if 'network_config' in config_data:
                config_data['network_config'] = NetworkConfig(**config_data['network_config'])
            if 'trading_params' in config_data:
                config_data['trading_params'] = TradingParams(**config_data['trading_params'])
            if 'meme_sniping' in config_data:
                config_data['meme_sniping'] = MemeSnipingConfig(**config_data['meme_sniping'])
            return cls(**config_data)
            
    def save_to_file(self, config_path: str = "config.yaml"):
        """Saves current configuration to YAML file"""
        config_dict = {
            k: (v.__dict__ if isinstance(v, (NetworkConfig, TradingParams, MemeSnipingConfig)) else v)
            for k, v in self.__dict__.items()
            if not k.startswith('_')
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(config_dict, f) 