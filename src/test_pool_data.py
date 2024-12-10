import asyncio
import logging
import aiohttp
from solana.rpc.async_api import AsyncClient
from solana.publickey import PublicKey
from datetime import datetime
import os
from dotenv import load_dotenv

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class WhirlpoolTester:
    def __init__(self):
        load_dotenv()
        self.client = AsyncClient("https://api.mainnet-beta.solana.com")
        self.solscan_base_url = "https://pro-api.solscan.io"
        self.solscan_api_key = os.getenv("SOLSCAN_API_KEY")
        self.headers = {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0",
            "token": self.solscan_api_key  # Solscan Pro API Key
        }
        self.test_pools = {
            "SOL/USDC": {
                "address": "HJPjoWUrhoZzkNfRpHuieeFk9WcZWjwy6PBjZ81ngndJ",
                "tokens": {
                    "SOL": "So11111111111111111111111111111111111111112",
                    "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
                }
            }
        }

    async def get_token_market_volume(self):
        """Holt Token Market Volume von Solscan Pro API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.solscan_base_url}/v2.0/token/market/volume",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Token Market Volume Data: {data}")
                        return data
                    else:
                        logger.error(f"Token Market Volume API Fehler: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Fehler beim Token Market Volume Abruf: {e}")
            return None

    async def get_token_holders(self, token_address: str):
        """Holt Token Holder Informationen"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.solscan_base_url}/v2.0/token/{token_address}/holders",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Token Holders: {data}")
                        return data
                    else:
                        logger.error(f"Token Holders API Fehler: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Fehler beim Token Holders Abruf: {e}")
            return None

    async def get_market_depth(self, pool_address: str):
        """Holt Market Depth für einen Pool"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.solscan_base_url}/v2.0/market/depth/{pool_address}",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Market Depth: {data}")
                        return data
                    else:
                        logger.error(f"Market Depth API Fehler: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Fehler beim Market Depth Abruf: {e}")
            return None

async def main():
    tester = WhirlpoolTester()
    
    print("\n=== Token Market Volume ===")
    volume_data = await tester.get_token_market_volume()
    if volume_data:
        print("Top Token nach Volumen:")
        for token in volume_data.get('data', [])[:5]:
            print(f"Symbol: {token.get('symbol')} - Volume: ${float(token.get('volume', 0)):,.2f}")
    
    print("\n=== SOL Token Holders ===")
    sol_holders = await tester.get_token_holders(tester.test_pools["SOL/USDC"]["tokens"]["SOL"])
    if sol_holders:
        print(f"Anzahl SOL Holder: {sol_holders.get('total', 0)}")
    
    print("\n=== Market Depth SOL/USDC ===")
    depth_data = await tester.get_market_depth(tester.test_pools["SOL/USDC"]["address"])
    if depth_data:
        print("Orderbook Tiefe:")
        print(f"Bids: {len(depth_data.get('bids', []))} Orders")
        print(f"Asks: {len(depth_data.get('asks', []))} Orders")
    
    await tester.client.close()

if __name__ == "__main__":
    asyncio.run(main()) 