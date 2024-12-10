import asyncio
from rich.console import Console
from .core.orca_client import OrcaClient
from .config.settings import POOLS, TOKENS, DEX_ENDPOINTS
import aiohttp

console = Console()

async def verify_token_addresses():
    """Verify all token addresses and pool pairs"""
    console.print("\n[cyan]Verifying Token Addresses and Pool Pairs...[/cyan]")
    
    async with aiohttp.ClientSession() as session:
        # 1. Verify Token Addresses
        for token, address in TOKENS.items():
            try:
                # Check token info via Solana API
                url = f"https://api.mainnet-beta.solana.com"
                response = await session.post(url, json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getAccountInfo",
                    "params": [address]
                })
                data = await response.json()
                
                if data.get('result'):
                    console.print(f"✅ {token}: {address} verified")
                else:
                    console.print(f"❌ {token}: {address} not found!")
                    
            except Exception as e:
                console.print(f"❌ Error verifying {token}: {e}")
                
        # 2. Verify Orca Pools
        orca = OrcaClient()
        if await orca.connect():
            for pair, pool_address in POOLS['orca'].items():
                try:
                    pool_data = await orca.get_pool_data(pool_address)
                    if pool_data:
                        console.print(f"✅ Orca {pair}: {pool_address}")
                        console.print(f"   Price: ${float(pool_data['price']):.4f}")
                        console.print(f"   Volume: ${float(pool_data['volume24h']):,.2f}")
                    else:
                        console.print(f"❌ Orca {pair}: Pool not found!")
                except Exception as e:
                    console.print(f"❌ Error verifying Orca {pair}: {e}")

async def main():
    await verify_token_addresses()

if __name__ == "__main__":
    asyncio.run(main()) 