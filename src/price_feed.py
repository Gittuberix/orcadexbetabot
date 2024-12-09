import asyncio
import logging
from typing import Dict, Optional, List
from datetime import datetime
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
import aiohttp
from dataclasses import dataclass
from rich.console import Console
from rich.live import Live
from rich.table import Table

@dataclass
class MemePool:
    address: str
    name: str
    price: float
    price_change_24h: float
    volume_24h: float
    liquidity: float
    holders: int
    age_hours: int
    momentum_score: float

class OrcaMemeScanner:
    def __init__(self):
        self.console = Console()
        self.rpc = AsyncClient("https://api.mainnet-beta.solana.com")
        self.orca_api = "https://api.orca.so"
        
        # Tracking
        self.pools: Dict[str, MemePool] = {}
        self.hot_pools: List[str] = []
        self.last_update = None
        
        # Schwellenwerte
        self.MIN_LIQUIDITY = 10000  # $10k
        self.MIN_VOLUME = 5000      # $5k
        self.MIN_HOLDERS = 50
        self.MAX_AGE_HOURS = 48     # 2 Tage
        
    async def start(self):
        """Startet den Memecoin Scanner"""
        self.console.print("\n[bold cyan]🔍 Orca Memecoin Scanner Starting...[/bold cyan]")
        
        try:
            with Live(self._generate_table(), refresh_per_second=1) as live:
                while True:
                    await self._scan_pools()
                    self._identify_opportunities()
                    live.update(self._generate_table())
                    await asyncio.sleep(1)
                    
        except Exception as e:
            self.console.print(f"[bold red]Error: {str(e)}[/bold red]")
            
    async def _scan_pools(self):
        """Scannt alle Orca Pools"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.orca_api}/v1/whirlpool/list") as response:
                    if response.status == 200:
                        pools = await response.json()
                        
                        for pool in pools:
                            # Nur USDC Pairs
                            if pool['tokenB']['symbol'] == 'USDC':
                                await self._process_pool(pool)
                                
            self.last_update = datetime.now()
            
        except Exception as e:
            logging.error(f"Scan error: {e}")
            
    async def _process_pool(self, pool_data: Dict):
        """Verarbeitet einen einzelnen Pool"""
        try:
            # Prüfen ob alle notwendigen Felder vorhanden sind
            if not all(key in pool_data for key in ['address', 'tokenA', 'tokenB', 'price', 'tvl']):
                return
                
            address = pool_data['address']
            token_a = pool_data['tokenA']
            token_b = pool_data['tokenB']
            
            # Nur USDC Pairs berücksichtigen
            if token_b.get('symbol') != 'USDC':
                return
                
            # Token Details
            token_name = token_a.get('symbol', 'Unknown')
            token_mint = token_a.get('mint', '')
            
            # Nur neue oder unbekannte Token
            if not token_a.get('verified', False):
                try:
                    # Pool Details
                    price = float(pool_data.get('price', 0))
                    volume = float(pool_data.get('volume', {}).get('day', 0))
                    liquidity = float(pool_data.get('tvl', 0))
                    price_change = float(pool_data.get('priceChange', {}).get('day', 0))
                    
                    # Alter berechnen
                    created_timestamp = pool_data.get('createdAt', datetime.now().timestamp())
                    created_at = datetime.fromtimestamp(created_timestamp)
                    age_hours = (datetime.now() - created_at).total_seconds() / 3600
                    
                    # Momentum Score
                    momentum = self._calculate_momentum(price_change, volume, liquidity, age_hours)
                    
                    # Pool speichern
                    self.pools[address] = MemePool(
                        address=address,
                        name=token_name,
                        price=price,
                        price_change_24h=price_change,
                        volume_24h=volume,
                        liquidity=liquidity,
                        holders=len(token_a.get('holders', [])),
                        age_hours=int(age_hours),
                        momentum_score=momentum
                    )
                    
                except (ValueError, TypeError, KeyError) as e:
                    logging.debug(f"Fehler bei Pool {address}: {e}")
                    
        except Exception as e:
            logging.error(f"Pool processing error: {e}")
            logging.debug(f"Pool data: {pool_data}")
            
    def _calculate_momentum(self, price_change: float, volume: float, liquidity: float, age_hours: float) -> float:
        """Berechnet einen Momentum Score"""
        score = 0.0
        
        # Preis-Momentum (40%)
        if price_change > 0:
            score += min(40, price_change)
            
        # Volumen/Liquidität Ratio (30%)
        if liquidity > 0:
            vol_liq_ratio = (volume / liquidity) * 100
            score += min(30, vol_liq_ratio)
            
        # Alter Bonus (30%)
        if age_hours <= self.MAX_AGE_HOURS:
            age_bonus = 30 * (1 - (age_hours / self.MAX_AGE_HOURS))
            score += age_bonus
            
        return min(100, score)
        
    def _identify_opportunities(self):
        """Identifiziert Trading Opportunities"""
        self.hot_pools = []
        
        for address, pool in self.pools.items():
            # Basis-Kriterien
            if (pool.liquidity >= self.MIN_LIQUIDITY and 
                pool.volume_24h >= self.MIN_VOLUME and
                pool.holders >= self.MIN_HOLDERS and
                pool.age_hours <= self.MAX_AGE_HOURS):
                
                # Momentum Check
                if pool.momentum_score >= 70:  # Hoher Score
                    self.hot_pools.append(address)
                    
    def _generate_table(self) -> Table:
        """Generiert die Übersichtstabelle"""
        table = Table(title="🚀 Hot Memecoin Opportunities")
        
        table.add_column("Token", style="cyan")
        table.add_column("Price", justify="right", style="green")
        table.add_column("24h %", justify="right")
        table.add_column("Volume", justify="right", style="blue")
        table.add_column("Liquidity", justify="right", style="magenta")
        table.add_column("Age", justify="right")
        table.add_column("Score", justify="right", style="yellow")
        table.add_column("Status", justify="center")
        
        # Nach Momentum sortieren
        sorted_pools = sorted(
            [p for p in self.pools.values() if p.address in self.hot_pools],
            key=lambda x: x.momentum_score,
            reverse=True
        )
        
        for pool in sorted_pools:
            # Formatierung
            price_color = "green" if pool.price_change_24h > 0 else "red"
            price_text = f"[{price_color}]{pool.price_change_24h:+.1f}%[/{price_color}]"
            
            table.add_row(
                pool.name,
                f"${pool.price:.6f}",
                price_text,
                f"${pool.volume_24h:,.0f}",
                f"${pool.liquidity:,.0f}",
                f"{pool.age_hours}h",
                f"{pool.momentum_score:.0f}",
                "🔥 HOT" if pool.momentum_score >= 80 else "⚡ Active"
            )
            
        return table

async def main():
    scanner = OrcaMemeScanner()
    await scanner.start()

if __name__ == "__main__":
    asyncio.run(main()) 