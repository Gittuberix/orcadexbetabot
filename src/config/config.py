import json
from pathlib import Path

CONFIG = {
    "network": {
        "rpc_url": "https://api.mainnet-beta.solana.com",
        "orca_api": "https://api.orca.so/v1",
        "backup_rpc": "https://solana-api.projectserum.com"
    },
    "wallet": {
        "public_key": "Bh3xV3ctC45DSy92JK7MKbC2fYe1tZMmoyi3XyTGcV3b",
        "network": "mainnet-beta"
    },
    "trading": {
        "initial_capital": 1.0,
        "max_trade_size": 0.01,
        "min_volume": 10000,
        "min_liquidity": 50000,
        "max_slippage": 0.01
    }
}

def load_config():
    config_file = Path("src/config/config.json")
    if config_file.exists():
        with open(config_file) as f:
            return json.load(f)
    return CONFIG

def save_config():
    config_file = Path("src/config/config.json")
    with open(config_file, "w") as f:
        json.dump(CONFIG, f, indent=4) 