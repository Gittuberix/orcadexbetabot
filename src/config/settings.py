from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

# RPC Endpoints
RPC_ENDPOINTS = {
    'quicknode': os.getenv('QUICKNODE_RPC_URL'),
    'orca': "https://api.mainnet.orca.so/rpc",
    'serum': "https://solana-api.projectserum.com",
    'ankr': "https://rpc.ankr.com/solana",
    'backup': [
        "https://api.mainnet-beta.solana.com",
        "https://solana-mainnet.rpc.extrnode.com",
        "https://rpc.helius.xyz/?api-key=" + os.getenv('HELIUS_API_KEY', '')
    ]
}

# DEX APIs
DEX_ENDPOINTS = {
    'orca': {
        'rest': "https://api.orca.so",
        'ws': "wss://api.orca.so/ws",
        'whirlpool': "https://api.orca.so/v1/whirlpool",
        'whirlpool_list': "https://api.orca.so/v1/whirlpool/list"
    },
    'jupiter': {
        'rest': "https://price.jup.ag/v4",
        'ws': "wss://price.jup.ag/v4/ws"
    },
    'serum': {
        'rest': "https://api.projectserum.com",
        'ws': "wss://api.projectserum.com/ws"
    }
}

# Wichtige Pools
POOLS = {
    'orca': {
        'SOL/USDC': 'HJPjoWUrhoZzkNfRpHuieeFk9WcZWjwy6PBjZ81ngndJ',
        'ORCA/USDC': '2p7nYbtPBgtmY69NsE8DAW6szpRJn7tQvDnqvoEWQvjY',
        'BONK/SOL': '9vqYJjDUFecLL2xPUC4Rc7hyCtZ6iJ4mDiVZX7aFXoAe'
    },
    'jupiter': {
        'SOL/USDC': 'GUNS2Q1ZXVi3qzwqHMtUdmwwZNW3whtjQXs1A8wUQq1',
        'BONK/USDC': '8QaXeHBrShJTdtN1rWCccBxpSVvKksQ2PCu5mZaQgGwZ'
    }
}

# Token Addresses
TOKENS = {
    'SOL': 'So11111111111111111111111111111111111111112',
    'USDC': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',
    'ORCA': 'orcaEKTdK7LKz57vaAYr9QeNsVEPfiu6QeMU1kektZE',
    'BONK': 'DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263'
}

# API Headers
API_HEADERS = {
    'User-Agent': 'SolanaBot/1.0',
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

# Rate Limits (requests per second)
RATE_LIMITS = {
    'quicknode': 100,
    'orca': 10,
    'jupiter': 10,
    'serum': 10,
    'public': 2
}

# Logging
LOG_DIR = Path('logs')
LOG_DIR.mkdir(exist_ok=True) 