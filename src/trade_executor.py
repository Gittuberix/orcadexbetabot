import logging
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solana.transaction import Transaction
import struct
from typing import Dict, Optional
from models import Trade
from wallet_manager import WalletManager

logger = logging.getLogger(__name__)

class TradeExecutor:
    def __init__(self, rpc_client: AsyncClient, wallet_manager: WalletManager, config: Dict):
        self.rpc = rpc_client
        self.wallet = wallet_manager
        self.config = config
        self.whirlpool_program = Pubkey.from_string("whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc")
        
    async def execute_trade(self, trade: Trade) -> bool:
        """Führt einen Trade aus"""
        try:
            logger.info(f"Executing {trade.type} trade for {trade.amount} tokens")
            
            # 1. Build transaction
            tx = await self._build_swap_transaction(trade)
            
            # 2. Sign transaction
            tx.sign(self.wallet.wallet)
            
            # 3. Send transaction
            signature = await self.rpc.send_transaction(tx)
            
            # 4. Confirm transaction
            await self._confirm_transaction(signature)
            
            logger.info(f"Trade executed successfully: {signature}")
            return True
            
        except Exception as e:
            logger.error(f"Trade execution failed: {e}")
            return False
            
    async def _build_swap_transaction(self, trade: Trade) -> Transaction:
        """Erstellt Swap Transaction"""
        try:
            tx = Transaction()
            
            # Swap instruction
            swap_ix = await self._create_swap_instruction(trade)
            tx.add(swap_ix)
            
            # Recent blockhash
            blockhash = await self.rpc.get_recent_blockhash()
            tx.recent_blockhash = blockhash['result']['value']['blockhash']
            
            return tx
            
        except Exception as e:
            logger.error(f"Error building transaction: {e}")
            raise