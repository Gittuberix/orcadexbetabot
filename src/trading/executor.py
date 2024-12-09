from typing import Dict, Optional
import logging
from models import Trade
from wallet.phantom_wallet import PhantomWallet
from whirlpool import WhirlpoolClient

logger = logging.getLogger(__name__)

class TradeExecutor:
    def __init__(self, wallet: PhantomWallet, whirlpool: WhirlpoolClient):
        self.wallet = wallet
        self.whirlpool = whirlpool
        
    async def execute_trade(self, trade: Trade) -> bool:
        """Führt Trade aus"""
        try:
            # 1. Pool validieren
            pool_info = await self.whirlpool.get_pool_info(trade.pool_address)
            if not pool_info:
                raise Exception("Invalid pool")
                
            # 2. Balance prüfen
            balance = await self.wallet.get_sol_balance()
            if balance < trade.amount:
                raise Exception("Insufficient balance")
                
            # 3. Swap Transaction erstellen
            tx = await self._build_swap_transaction(trade, pool_info)
            
            # 4. Transaktion senden
            signature = await self.wallet.sign_and_send_transaction(tx)
            if not signature:
                raise Exception("Transaction failed")
                
            logger.info(f"Trade executed: {signature}")
            return True
            
        except Exception as e:
            logger.error(f"Trade failed: {e}")
            return False