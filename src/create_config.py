import yaml

default_config = {
    'network_config': {
        'rpc_endpoint': 'https://api.mainnet-beta.solana.com',
        'orca_api': 'https://api.orca.so',
        'jupiter_api': 'https://price.jup.ag/v4',
        'whirlpool_program': 'whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc',
        'max_retries': 3,
        'retry_delay': 1
    },
    'trading_params': {
        'candle_interval': '1m',
        'min_liquidity': 10000,
        'min_volume_24h': 5000,
        'position_size': 0.1,
        'take_profit': 0.05,
        'stop_loss': 0.02
    },
    'risk_management': {
        'max_position_size': 1.0,
        'max_daily_loss': 5.0,
        'max_drawdown': 10.0,
        'max_open_positions': 3,
        'min_liquidity': 10000,
        'max_slippage': 0.01
    }
}

def create_default_config():
    with open('config/config.yaml', 'w') as f:
        yaml.dump(default_config, f, default_flow_style=False) 