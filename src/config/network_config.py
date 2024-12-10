import os
from dotenv import load_dotenv
import aiohttp
import logging
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed

load_dotenv()
logger = logging.getLogger(__name__)

# RPC Setup
QUICKNODE_RPC_URL = os.getenv("QUICKNODE_RPC_URL")
if not QUICKNODE_RPC_URL:
    logger.warning("Kein QuickNode RPC URL gefunden, nutze Fallback")
    QUICKNODE_RPC_URL = "https://api.mainnet-beta.solana.com"

async def get_rpc_client() -> AsyncClient:
    """Erstellt einen RPC Client mit optimalen Einstellungen"""
    return AsyncClient(
        QUICKNODE_RPC_URL,
        commitment=Confirmed,
        timeout=30,
        blockhash_cache=True
    )

# Standard Whirlpools für Fallback
DEFAULT_WHIRLPOOLS = {
    "SOL/USDC": {
        "address": "HJPjoWUrhoZzkNfRpHuieeFk9WcZWjwy6PBjZ81ngndJ",
        "token_a": "So11111111111111111111111111111111111111112",
        "token_b": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        "decimals_a": 9,
        "decimals_b": 6,
        "fee_rate": 0.0001
    },
    "SOL/USDT": {
        "address": "4GpUivZ2jvZqQ3vJRsoq5PwnYv6gdV9fJ9BzHT2JcRr7",
        "token_a": "So11111111111111111111111111111111111111112",
        "token_b": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
        "decimals_a": 9,
        "decimals_b": 6,
        "fee_rate": 0.0001
    }
}

async def fetch_whirlpool_configs():
    """Holt aktuelle Whirlpool Konfigurationen"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.mainnet.orca.so/v1/whirlpool/list") as resp:
                data = await resp.json()
                
                configs = {}
                for pool in data["whirlpools"]:
                    if pool["whitelisted"]:  # Nur verifizierte Pools
                        symbol = f"{pool['tokenA']['symbol']}/{pool['tokenB']['symbol']}"
                        configs[symbol] = {
                            "address": pool["address"],
                            "token_a": pool["tokenA"]["mint"],
                            "token_b": pool["tokenB"]["mint"],
                            "decimals_a": pool["tokenA"]["decimals"],
                            "decimals_b": pool["tokenB"]["decimals"],
                            "fee_rate": pool["lpFeeRate"]
                        }
                        
                return configs
                
    except Exception as e:
        logger.error(f"Fehler beim Laden der Whirlpool Konfigurationen: {e}")
        return DEFAULT_WHIRLPOOLS

# Initialisiere Whirlpool Konfigurationen
WHIRLPOOL_CONFIGS = {} 