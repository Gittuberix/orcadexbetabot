import asyncio
import logging
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from orca_whirlpool.context import WhirlpoolContext
from orca_whirlpool.constants import ORCA_WHIRLPOOL_PROGRAM_ID
from orca_whirlpool.utils import PriceMath, DecimalUtil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SOL/USDC Pool
SOL_USDC_POOL = "HJPjoWUrhoZzkNfRpHuieeFk9WcZWjwy6PBjZ81ngndJ"

async def test_whirlpool():
    try:
        # Setup
        connection = AsyncClient("https://api.mainnet-beta.solana.com")
        ctx = WhirlpoolContext(ORCA_WHIRLPOOL_PROGRAM_ID, connection, Keypair())
        
        print("\n=== Teste Whirlpool Connection ===")
        
        # Hole Pool-Daten
        whirlpool = await ctx.fetcher.get_whirlpool(
            Pubkey.from_string(SOL_USDC_POOL)
        )
        
        # Hole Token Decimals
        decimals_a = (await ctx.fetcher.get_token_mint(whirlpool.token_mint_a)).decimals
        decimals_b = (await ctx.fetcher.get_token_mint(whirlpool.token_mint_b)).decimals
        
        # Berechne Preis
        price = PriceMath.sqrt_price_x64_to_price(
            whirlpool.sqrt_price,
            decimals_a,
            decimals_b
        )
        
        print("\nSOL/USDC Pool Details:")
        print(f"Token A: {whirlpool.token_mint_a}")
        print(f"Token B: {whirlpool.token_mint_b}")
        print(f"Tick Spacing: {whirlpool.tick_spacing}")
        print(f"Current Tick: {whirlpool.tick_current_index}")
        print(f"Sqrt Price: {whirlpool.sqrt_price}")
        print(f"Price: ${float(DecimalUtil.to_fixed(price, decimals_b)):.4f}")
        print(f"Liquidity: {whirlpool.liquidity}")
        
    except Exception as e:
        logger.error(f"Fehler: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await connection.close()

if __name__ == "__main__":
    asyncio.run(test_whirlpool()) 