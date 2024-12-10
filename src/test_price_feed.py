import asyncio
import logging
from solana.rpc.async_api import AsyncClient
from solana.publickey import PublicKey
from datetime import datetime

logger = logging.getLogger(__name__)

class OrcaPriceFeed:
    def __init__(self):
        self.client = AsyncClient("https://api.mainnet-beta.solana.com")
        # Bekannte Whirlpool-Adressen
        self.known_pools = {
            "SOL/USDC": "HJPjoWUrhoZzkNfRpHuieeFk9WcZWjwy6PBjZ81ngndJ",
            "SOL/USDT": "4GpUivZ2jvZqQ3vJRsoq5PwnYv6gdV9fJ9BzHT2JcRr7",
            "BONK/SOL": "8QaXeHBrShJTdtN1rWHbp3pPJGCuYKxqZn8M5YBV1HSF",
            "JTO/SOL": "2QdhepnKRTLjjSqPL1PtKNwqrUkoLee5Gqs8bvZhRdMv"
        }

    async def fetch_all_pool_prices(self):
        """Holt die Preise aller bekannten Pools"""
        prices = {}
        for pair, address in self.known_pools.items():
            try:
                price = await self.fetch_pool_price(address)
                prices[pair] = price
                print(f"{pair}: ${price:.4f}")
            except Exception as e:
                logger.error(f"Fehler beim Abrufen des Preises für {pair}: {e}")
        return prices

    async def fetch_pool_price(self, pool_address: str) -> float:
        """Holt den Preis eines spezifischen Pools"""
        try:
            # Hole Pool-Account-Daten
            response = await self.client.get_account_info(
                PublicKey(pool_address),
                commitment="confirmed",
                encoding="jsonParsed"
            )
            
            if response['result']['value']:
                data = response['result']['value']['data']
                # Decodiere die Pool-Daten
                sqrt_price = int.from_bytes(bytes.fromhex(data[0:16]), 'little')
                # Berechne den aktuellen Preis
                price = (sqrt_price / (2 ** 64)) ** 2
                return price
            return 0.0
        except Exception as e:
            logger.error(f"Fehler beim Abrufen des Pool-Preises: {e}")
            return 0.0

    async def monitor_prices(self, interval_seconds: int = 5):
        """Überwacht die Preise kontinuierlich"""
        while True:
            print(f"\n=== Preisupdate {datetime.now().strftime('%H:%M:%S')} ===")
            await self.fetch_all_pool_prices()
            await asyncio.sleep(interval_seconds)

async def main():
    price_feed = OrcaPriceFeed()
    try:
        # Einmalige Preisabfrage
        print("\n=== Aktuelle Preise ===")
        await price_feed.fetch_all_pool_prices()
        
        # Kontinuierliche Überwachung
        print("\n=== Starte Preisüberwachung ===")
        await price_feed.monitor_prices()
    except KeyboardInterrupt:
        print("\nPreisüberwachung beendet.")
    finally:
        await price_feed.client.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main()) 