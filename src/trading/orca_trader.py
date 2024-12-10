import logging
from typing import Optional, Dict, Tuple
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solana.rpc.async_api import AsyncClient
from orca_whirlpool.context import WhirlpoolContext
from orca_whirlpool.constants import ORCA_WHIRLPOOL_PROGRAM_ID
from orca_whirlpool.utils import PriceMath, DecimalUtil, SwapUtil, PoolUtil
from orca_whirlpool.types import Percentage, SwapQuote
from .whirlpool_errors import WhirlpoolError

logger = logging.getLogger(__name__)

class OrcaTrader:
    def __init__(self, wallet_keypair: Keypair):
        self.connection = AsyncClient("https://api.mainnet-beta.solana.com")
        self.ctx = WhirlpoolContext(ORCA_WHIRLPOOL_PROGRAM_ID, self.connection, wallet_keypair)
        self.slippage = Percentage.from_fraction(1, 100)  # 1% Slippage
        self.max_price_impact = Percentage.from_fraction(5, 100)  # 5% max Impact
        
    async def check_pool_health(self, pool_address: str) -> Tuple[bool, str]:
        """Prüft die Gesundheit eines Pools"""
        try:
            whirlpool = await self.ctx.fetcher.get_whirlpool(
                Pubkey.from_string(pool_address)
            )
            
            if whirlpool.liquidity == 0:
                return False, "Keine Liquidität"
                
            if whirlpool.fee_rate > 10000:  # > 1%
                return False, "Zu hohe Gebühren"
                
            return True, "Pool OK"
            
        except Exception as e:
            return False, f"Pool-Fehler: {e}"
            
    async def simulate_swap(self,
        pool_address: str,
        amount_in: int,
        is_a_to_b: bool
    ) -> Optional[Dict]:
        """Simuliert einen Swap mit Fehlerprüfung"""
        try:
            # Prüfe Pool-Gesundheit
            is_healthy, message = await self.check_pool_health(pool_address)
            if not is_healthy:
                raise ValueError(message)
            
            whirlpool = await self.ctx.fetcher.get_whirlpool(
                Pubkey.from_string(pool_address)
            )
            
            # Prüfe Token-Balancen
            if is_a_to_b:
                token_account = await self.ctx.fetcher.get_token_account(
                    whirlpool.token_mint_a,
                    self.ctx.wallet.pubkey
                )
                if not token_account or token_account.amount < amount_in:
                    raise ValueError(WhirlpoolError.get_error_message(
                        WhirlpoolError.INSUFFICIENT_TOKEN_BALANCE
                    ))
            
            # Berechne Quote
            quote = SwapUtil.get_swap_quote(
                whirlpool,
                amount_in,
                is_a_to_b,
                self.slippage,
                True
            )
            
            # Prüfe Preis-Impact
            if quote.price_impact > self.max_price_impact:
                raise ValueError(WhirlpoolError.get_error_message(
                    WhirlpoolError.PRICE_IMPACT_EXCEEDED
                ))
            
            return {
                'amount_in': amount_in,
                'amount_out': quote.amount_out,
                'price_impact': quote.price_impact,
                'fee': quote.fee_amount,
                'other_fee': quote.other_fee_amount,
                'slippage': float(self.slippage)
            }
            
        except Exception as e:
            logger.error(f"Swap-Simulation fehlgeschlagen: {e}")
            return None
            
    async def execute_swap(self,
        pool_address: str,
        amount_in: int,
        is_a_to_b: bool,
        dry_run: bool = True
    ) -> Dict:
        """Führt einen Swap aus mit vollständiger Validierung"""
        try:
            # Simuliere zuerst
            quote = await self.simulate_swap(pool_address, amount_in, is_a_to_b)
            if not quote:
                raise ValueError("Simulation fehlgeschlagen")
                
            if dry_run:
                return {
                    'success': True,
                    'dry_run': True,
                    'quote': quote
                }
            
            # Baue und sende Transaktion
            whirlpool = await self.ctx.fetcher.get_whirlpool(
                Pubkey.from_string(pool_address)
            )
            
            tx = await SwapUtil.get_swap_transaction(
                self.ctx,
                whirlpool,
                SwapQuote(**quote),
                self.ctx.wallet.pubkey
            )
            
            signature = await self.ctx.send_transaction(tx)
            await self.connection.confirm_transaction(signature)
            
            return {
                'success': True,
                'signature': str(signature),
                'quote': quote
            }
            
        except Exception as e:
            logger.error(f"Swap-Ausführung fehlgeschlagen: {e}")
            return {
                'success': False,
                'error': str(e),
                'quote': None
            }
            
    async def get_pool_info(self, pool_address: str) -> Dict:
        """Holt detaillierte Pool-Informationen"""
        whirlpool = await self.ctx.fetcher.get_whirlpool(
            Pubkey.from_string(pool_address)
        )
        
        decimals_a = (await self.ctx.fetcher.get_token_mint(whirlpool.token_mint_a)).decimals
        decimals_b = (await self.ctx.fetcher.get_token_mint(whirlpool.token_mint_b)).decimals
        
        price = PriceMath.sqrt_price_x64_to_price(
            whirlpool.sqrt_price,
            decimals_a,
            decimals_b
        )
        
        return {
            'token_a': str(whirlpool.token_mint_a),
            'token_b': str(whirlpool.token_mint_b),
            'price': float(DecimalUtil.to_fixed(price, decimals_b)),
            'liquidity': whirlpool.liquidity,
            'fee_rate': whirlpool.fee_rate,
            'tick_spacing': whirlpool.tick_spacing,
            'tick_current': whirlpool.tick_current_index
        } 