import os
import sys
import subprocess
import shutil
from pathlib import Path

def setup_bot():
    print("🚀 Starting Solana Orca Bot Setup...")
    
    # 1. Basis-Pakete installieren
    print("\n📦 Installiere Basis-Pakete...")
    packages = [
        "pip install --upgrade pip",
        "pip install wheel setuptools",
        "pip install solana-sdk anchorpy base58",
        "pip install pandas numpy aiohttp",
        "pip install python-dotenv pyyaml rich"
    ]
    
    for cmd in packages:
        try:
            subprocess.run(cmd.split(), check=True)
            print(f"✅ {cmd}")
        except Exception as e:
            print(f"❌ Fehler bei {cmd}: {e}")
            
    # 2. Ordnerstruktur erstellen
    folders = [
        "src/strategies",
        "src/utils",
        "logs/trades",
        "logs/errors",
        "logs/performance",
        "data/historical",
        "data/cache",
        "config"
    ]
    
    print("\n📁 Erstelle Ordnerstruktur...")
    for folder in folders:
        Path(folder).mkdir(parents=True, exist_ok=True)
        print(f"✅ {folder}")
        
    # 3. __init__.py Dateien erstellen
    init_files = [
        "src/__init__.py",
        "src/strategies/__init__.py",
        "src/utils/__init__.py"
    ]
    
    print("\n📝 Erstelle Python-Module...")
    for file in init_files:
        Path(file).touch(exist_ok=True)
        print(f"✅ {file}")
        
    # 4. Config erstellen
    config = """# Network Configuration
network_config:
  rpc_endpoint: "https://api.mainnet-beta.solana.com"
  orca_api: "https://api.orca.so"
  max_retries: 3
  retry_delay: 1

# Trading Parameters
trading_params:
  candle_interval: 60
  update_interval: 3
  cache_duration: 10
  min_liquidity: 10000
  min_volume_24h: 1000
  position_size: 0.1
  take_profit: 0.05
  stop_loss: 0.02

# Risk Management
risk_management:
  max_position_size: 1.0
  max_daily_loss: 5.0
  max_drawdown: 10.0
  max_open_positions: 3
  min_liquidity: 10000
  max_slippage: 0.01

# Backtest Settings
backtest:
  start_balance: 1000
  fee_rate: 0.003
  slippage_model: "fixed"
  fixed_slippage: 0.001

# Meme Strategy Settings
meme_strategy:
  min_momentum_score: 50
  entry_momentum_threshold: 70
  exit_momentum_threshold: 30
  min_liquidity_score: 60
  min_volume_score: 50
  base_position_size: 0.1
  max_position_size: 1.0
  stop_loss_percentage: 0.02
  take_profit_percentage: 0.05
  target_liquidity: 100000
  target_volume_24h: 50000"""
    
    config_path = Path("config/config.yaml")
    config_path.write_text(config)
    print("\n✅ Konfigurationsdatei erstellt")
    
    print("\n🎉 Setup abgeschlossen!")
    print("\nNächste Schritte:")
    print("1. Überprüfen Sie die Konfiguration in config/config.yaml")
    print("2. Starten Sie den Backtest mit: python src/backtest.py")

if __name__ == "__main__":
    setup_bot() 