import json
from pathlib import Path

def create_config():
    config = {
        "public_key": "Bh3xV3ctC45DSy92JK7MKbC2fYe1tZMmoyi3XyTGcV3b",
        "network": "mainnet-beta",
        "rpc_url": "https://api.mainnet-beta.solana.com"
    }
    
    # Config-Verzeichnis erstellen
    config_dir = Path("src/config")
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # Config-Datei schreiben
    config_file = config_dir / "wallet_config.json"
    with open(config_file, "w") as f:
        json.dump(config, f, indent=4)
        
    print(f"Created config file at: {config_file}")

if __name__ == "__main__":
    create_config() 