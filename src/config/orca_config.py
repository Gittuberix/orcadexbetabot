from dataclasses import dataclass
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

@dataclass
class WhirlpoolConfig:
    program_id: str
    pool_address: str
    token_a_mint: str
    token_b_mint: str
    fee_rate: float
    tick_spacing: int

# Orca Programm IDs
ORCA_WHIRLPOOL_PROGRAM_ID = "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc"

# Wichtige Whirlpools mit Konfiguration
WHIRLPOOL_CONFIGS = {
    'SOL/USDC': WhirlpoolConfig(
        program_id=ORCA_WHIRLPOOL_PROGRAM_ID,
        pool_address="HJPjoWUrhoZzkNfRpHuieeFk9WcZWjwy6PBjZ81ngndJ",
        token_a_mint="So11111111111111111111111111111111111111112",  # SOL
        token_b_mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
        fee_rate=0.0001,  # 0.01%
        tick_spacing=64
    ),
    # Weitere Pools hier hinzufügen
}

# Token Decimals
TOKEN_DECIMALS = {
    'SOL': 9,
    'USDC': 6,
    'ORCA': 6
} 