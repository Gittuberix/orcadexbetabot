from dataclasses import dataclass
from typing import Dict, Optional
import logging
from solana.rpc.api import Client
import aiohttp

@dataclass
class TransactionFees:
    base_fee: float  # Basis Solana Tx Fee
    priority_fee: float  # Priority Fee für schnellere Ausführung
    orca_fee: float  # Orca DEX Fee
    total_fee: float  # Gesamtgebühren

class FeeCalculator:
    def __init__(self, rpc_client: Client):
        self.client = rpc_client
        self.orca_api = "https://api.orca.so"
        
        # Standard Gebühren (werden dynamisch aktualisiert)
        self.default_fees = {
            'base_fee': 0.000005,  # 5000 Lamports
            'priority_fee': 0.000001,  # 1000 Lamports
            'orca_fees': {
                'stable_pools': 0.0001,  # 0.01%
                'volatile_pools': 0.0025,  # 0.25%
                'protocol_fee': 0.0001,  # 0.01%
            }
        }
        
    async def get_current_fees(self, pool_address: str, amount: float) -> TransactionFees:
        """Berechnet aktuelle Gebühren für eine Transaktion"""
        try:
            # Aktuelle Solana Netzwerk-Gebühren
            base_fee = await self._get_network_fee()
            priority_fee = await self._get_priority_fee()
            
            # Orca Pool-spezifische Gebühren
            pool_fee = await self._get_pool_fee(pool_address)
            
            # Berechne Orca Gebühren basierend auf Handelsvolumen
            orca_fee = amount * pool_fee
            
            # Gesamtgebühren
            total_fee = base_fee + priority_fee + orca_fee
            
            return TransactionFees(
                base_fee=base_fee,
                priority_fee=priority_fee,
                orca_fee=orca_fee,
                total_fee=total_fee
            )
            
        except Exception as e:
            logging.error(f"Fehler bei Fee-Berechnung: {e}")
            return self._get_default_fees(amount)
            
    async def _get_network_fee(self) -> float:
        """Holt aktuelle Solana Netzwerk-Gebühr"""
        try:
            response = await self.client.get_recent_blockhash()
            if response['result']:
                return float(response['result']['value']['feeCalculator']['lamportsPerSignature']) / 1e9
            return self.default_fees['base_fee']
        except Exception as e:
            logging.error(f"Fehler beim Abrufen der Netzwerk-Gebühr: {e}")
            return self.default_fees['base_fee']
            
    async def _get_priority_fee(self) -> float:
        """Berechnet optimale Priority Fee basierend auf Netzwerkauslastung"""
        try:
            # Recent Block Performance abrufen
            response = await self.client.get_recent_performance_samples()
            if not response['result']:
                return self.default_fees['priority_fee']
                
            # Durchschnittliche Auslastung berechnen
            recent_blocks = response['result'][:10]  # Letzte 10 Blöcke
            avg_utilization = sum(block['numTransactions'] for block in recent_blocks) / len(recent_blocks)
            
            # Priority Fee basierend auf Auslastung anpassen
            if avg_utilization > 1000:  # Hohe Auslastung
                return self.default_fees['priority_fee'] * 2
            elif avg_utilization > 500:  # Mittlere Auslastung
                return self.default_fees['priority_fee'] * 1.5
                
            return self.default_fees['priority_fee']
            
        except Exception as e:
            logging.error(f"Fehler beim Berechnen der Priority Fee: {e}")
            return self.default_fees['priority_fee']
            
    async def _get_pool_fee(self, pool_address: str) -> float:
        """Holt aktuelle Pool-Gebühren von Orca"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.orca_api}/v1/pool/{pool_address}") as response:
                    if response.status == 200:
                        data = await response.json()
                        return float(data['fee_rate'])
                        
            # Fallback auf Standard-Gebühr
            return self.default_fees['orca_fees']['volatile_pools']
            
        except Exception as e:
            logging.error(f"Fehler beim Abrufen der Pool-Gebühr: {e}")
            return self.default_fees['orca_fees']['volatile_pools']
            
    def _get_default_fees(self, amount: float) -> TransactionFees:
        """Gibt Standard-Gebühren zurück"""
        orca_fee = amount * self.default_fees['orca_fees']['volatile_pools']
        total = (
            self.default_fees['base_fee'] +
            self.default_fees['priority_fee'] +
            orca_fee
        )
        
        return TransactionFees(
            base_fee=self.default_fees['base_fee'],
            priority_fee=self.default_fees['priority_fee'],
            orca_fee=orca_fee,
            total_fee=total
        )
        
    def estimate_price_impact(self, pool_data: Dict, amount: float) -> float:
        """Schätzt den Preiseinfluss eines Trades"""
        try:
            liquidity = float(pool_data['liquidity'])
            if liquidity <= 0:
                return 1.0  # 100% Preiseinfluss
                
            # Vereinfachte Preiseinfluss-Berechnung
            impact = (amount / liquidity) ** 0.5
            return min(impact, 1.0)  # Maximal 100% Preiseinfluss
            
        except Exception as e:
            logging.error(f"Fehler bei Preiseinfluss-Berechnung: {e}")
            return 1.0

# Beispiel Nutzung:
async def main():
    from solana.rpc.api import Client
    
    rpc_client = Client("https://api.mainnet-beta.solana.com")
    calculator = FeeCalculator(rpc_client)
    
    # Beispiel Trade
    pool_address = "YOUR_POOL_ADDRESS"
    amount = 1.0  # 1 SOL
    
    fees = await calculator.get_current_fees(pool_address, amount)
    print(f"""
    Gebühren Übersicht:
    Basis Fee: {fees.base_fee:.6f} SOL
    Priority Fee: {fees.priority_fee:.6f} SOL
    Orca Fee: {fees.orca_fee:.6f} SOL
    ───────────────────
    Gesamt: {fees.total_fee:.6f} SOL
    """)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 