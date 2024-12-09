from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

# Wallet
WALLET_PUBLIC_KEY = "Bh3xV3ctC45DSy92JK7MKbC2fYe1tZMmoyi3XyTGcV3b"
WALLET_PRIVATE_KEY = os.getenv('WALLET_PRIVATE_KEY')

# RPC
RPC_ENDPOINTS = {
    'quicknode': os.getenv('QUICKNODE_RPC_URL'),
    'backup': "https://api.mainnet-beta.solana.com"
}

# Orca
ORCA_POOLS = {
    'SOL/USDC': 'HJPjoWUrhoZzkNfRpHuieeFk9WcZWjwy6PBjZ81ngndJ'
}

# Trading
TRADE_SETTINGS = {
    'min_size': 0.1,      # SOL
    'max_size': 10.0,     # SOL
    'slippage': 0.01,     # 1%
    'gas_buffer': 0.01    # SOL
}

# Logging
LOG_DIR = Path('logs')
LOG_DIR.mkdir(exist_ok=True) 