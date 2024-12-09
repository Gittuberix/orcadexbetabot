import logging
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
from anchorpy import Wallet, Provider
from solana.transaction import Transaction
import base58

class PhantomConnector:
    def __init__(self):
        self.wallet = None
        self.provider = None
        self.rpc_client = AsyncClient("https://api.mainnet-beta.solana.com")
        
    async def connect(self, private_key: str):
        """Verbindet mit Phantom Wallet"""
        try:
            keypair = Keypair.from_bytes(bytes.fromhex(private_key))
            self.wallet = Wallet(keypair)
            self.provider = Provider(self.rpc_client, self.wallet)
            return True
        except Exception as e:
            logging.error(f"Wallet Connection Error: {e}")
            return False
            
    async def execute_swap(self, pool_address: str, amount: float, is_buy: bool):
        """Führt einen Swap auf Orca aus"""
        try:
            # Swap Instruction erstellen
            ix = await self._create_swap_instruction(pool_address, amount, is_buy)
            
            # Transaktion bauen und senden
            tx = Transaction().add(ix)
            signature = await self.provider.send_and_confirm_transaction(tx)
            
            return {
                "success": True,
                "signature": str(signature),
                "amount": amount
            }
        except Exception as e:
            logging.error(f"Swap Error: {e}")
            return {"success": False, "error": str(e)} 