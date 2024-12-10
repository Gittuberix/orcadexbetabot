import json
from pathlib import Path
from dataclasses import dataclass
from typing import Dict

@dataclass
class OrcaConfig:
    RPC_URL: str = "https://api.mainnet-beta.solana.com"
    WHIRLPOOL_PROGRAM: str = "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc"
    UPDATE_INTERVAL: int = 1  # Sekunden
    
    # Wichtige Pool-Adressen
    POOLS: Dict[str, str] = {
        "SOL/USDC": "HJPjoWUrhoZzkNfRpHuieeFk9WcZWjwy6PBjZ81ngndJ",
        "SOL/USDT": "4GpUivZ2jvZqQ3vJRsoq5PwnYv6gdV9fJ9BzHT2JcRr7",
        # Weitere Pools hier hinzufügen
    }
    
    @classmethod
    def load(cls, config_path: str = "config/orca_config.json"):
        if Path(config_path).exists():
            with open(config_path, 'r') as f:
                config_data = json.load(f)
                return cls(**config_data)
        return cls()

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