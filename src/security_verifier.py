from dataclasses import asdict
from typing import Dict, List, Optional
import logging
from config import BotConfig, NetworkConfig, TradingParams

class SecurityVerifier:
    """Ensures parameter consistency between backtest and live environments"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def verify_parameters(self, backtest_config: BotConfig, live_config: BotConfig) -> Dict[str, List[str]]:
        """
        Verifies that backtest and live parameters match exactly.
        Returns a dictionary of mismatches if any are found.
        """
        mismatches = {
            'trading_params': [],
            'risk_management': [],
            'network_config': []
        }
        
        # Compare TradingParams
        backtest_params = asdict(backtest_config.trading_params)
        live_params = asdict(live_config.trading_params)
        
        for key in backtest_params:
            if backtest_params[key] != live_params[key]:
                mismatches['trading_params'].append(
                    f"{key}: backtest={backtest_params[key]} != live={live_params[key]}"
                )
        
        # Compare Risk Management Parameters
        risk_params = [
            'max_position_size',
            'stop_loss_percentage',
            'take_profit_percentage',
            'min_profit_threshold'
        ]
        
        for param in risk_params:
            backtest_value = getattr(backtest_config, param)
            live_value = getattr(live_config, param)
            if backtest_value != live_value:
                mismatches['risk_management'].append(
                    f"{param}: backtest={backtest_value} != live={live_value}"
                )
        
        # Compare Network Config (excluding environment-specific settings)
        network_params = ['priority_fee']
        for param in network_params:
            backtest_value = getattr(backtest_config.network_config, param)
            live_value = getattr(live_config.network_config, param)
            if backtest_value != live_value:
                mismatches['network_config'].append(
                    f"{param}: backtest={backtest_value} != live={live_value}"
                )
        
        return {k: v for k, v in mismatches.items() if v}
    
    def ensure_parameter_consistency(self, backtest_config: BotConfig, live_config: BotConfig) -> bool:
        """
        Ensures that all critical parameters match between backtest and live environments.
        Raises ValueError if mismatches are found.
        """
        mismatches = self.verify_parameters(backtest_config, live_config)
        
        if mismatches:
            error_msg = "Critical parameter mismatches found:\n"
            for category, issues in mismatches.items():
                error_msg += f"\n{category.upper()}:\n"
                for issue in issues:
                    error_msg += f"- {issue}\n"
            raise ValueError(error_msg)
        
        self.logger.info("✅ All parameters verified - backtest and live settings match 100%")
        return True 