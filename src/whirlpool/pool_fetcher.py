import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from orca_whirlpool.context import WhirlpoolContext
from orca_whirlpool.constants import ORCA_WHIRLPOOL_PROGRAM_ID
from orca_whirlpool.utils import PriceMath, DecimalUtil, SwapUtil
from rich.console import Console

console = Console()
logger = logging.getLogger(__name__)

class WhirlpoolFetcher:
    def __init__(self):
        self.connection = AsyncClient("https://api.mainnet-beta.solana.com")
        self.ctx = WhirlpoolContext(ORCA_WHIRLPOOL_PROGRAM_ID, self.connection, Keypair())
        
    async def get_pool_data(self, pool_address: str) -> Optional[Dict]:
        """Holt detaillierte Pool-Daten"""
        try:
            whirlpool = await self.ctx.fetcher.get_whirlpool(
                Pubkey.from_string(pool_address)
            )
            
            token_a = await self.ctx.fetcher.get_token_mint(whirlpool.token_mint_a)
            token_b = await self.ctx.fetcher.get_token_mint(whirlpool.token_mint_b)
            
            price = PriceMath.sqrt_price_x64_to_price(
                whirlpool.sqrt_price,
                token_a.decimals,
                token_b.decimals
            )
            
            return {
                'address': pool_address,
                'token_a': {
                    'address': str(whirlpool.token_mint_a),
                    'decimals': token_a.decimals
                },
                'token_b': {
                    'address': str(whirlpool.token_mint_b),
                    'decimals': token_b.decimals
                },
                'price': float(DecimalUtil.to_fixed(price, token_b.decimals)),
                'liquidity': whirlpool.liquidity,
                'fee_rate': whirlpool.fee_rate,
                'tick_spacing': whirlpool.tick_spacing,
                'tick_current': whirlpool.tick_current_index
            }
            
        except Exception as e:
            logger.error(f"Fehler beim Abrufen von Pool {pool_address}: {e}")
            return None
            
    async def simulate_swap(self, pool_address: str, amount_in: int, is_a_to_b: bool) -> Optional[Dict]:
        """Simuliert einen Swap"""
        try:
            whirlpool = await self.ctx.fetcher.get_whirlpool(
                Pubkey.from_string(pool_address)
            )
            
            quote = SwapUtil.get_swap_quote(
                whirlpool,
                amount_in,
                is_a_to_b,
                slippage=0.01,  # 1% slippage
                with_price_impact=True
            )
            
            return {
                'amount_in': amount_in,
                'amount_out': quote.amount_out,
                'price_impact': quote.price_impact,
                'fee': quote.fee_amount
            }
            
        except Exception as e:
            logger.error(f"Fehler bei Swap-Simulation: {e}")
            return None