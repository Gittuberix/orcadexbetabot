import logging
import asyncio
from typing import Dict, Optional
from ..core.solana_client import SolanaClient
from ..core.orca_client import OrcaClient
from ..config.settings import TRADE_SETTINGS, ORCA_POOLS

logger = logging.getLogger(__name__)

class TradingEngine:
    def __init__(self):
        self.solana = SolanaClient()
        self.orca = OrcaClient()
        self.running = False
        self.positions = {}
        self.settings = TRADE_SETTINGS
        
    async def start(self) -> bool:
        """Start trading engine"""
        try:
            # Connect to clients
            if not await self.solana.connect():
                logger.error("Failed to connect Solana client")
                return False
                
            if not await self.orca.connect():
                logger.error("Failed to connect Orca client")
                return False
                
            # Initial balance check
            sol_balance = await self.solana.get_sol_balance()
            logger.info(f"Initial SOL balance: {sol_balance:.4f}")
            
            self.running = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to start trading engine: {e}")
            return False
            
    async def execute_trade(self, pool_id: str, side: str, amount: float) -> bool:
        """Execute trade on Orca"""
        try:
            # Validate trade
            if not await self._validate_trade(pool_id, side, amount):
                return False
                
            # Get pool data
            pool_data = await self.orca.get_pool_data(pool_id)
            if not pool_data:
                logger.error("Failed to get pool data")
                return False
                
            # Log trade
            price = float(pool_data['price'])
            logger.info(f"Executing {side} trade: {amount} SOL at {price} USDC")
            
            # TODO: Implement actual trade execution
            # For now, just simulate success
            return True
            
        except Exception as e:
            logger.error(f"Trade execution failed: {e}")
            return False
            
    async def _validate_trade(self, pool_id: str, side: str, amount: float) -> bool:
        """Validate trade parameters"""
        try:
            # Check amount limits
            if amount < self.settings['min_size']:
                logger.warning(f"Trade amount {amount} below minimum {self.settings['min_size']}")
                return False
                
            if amount > self.settings['max_size']:
                logger.warning(f"Trade amount {amount} above maximum {self.settings['max_size']}")
                return False
                
            # Check balance
            sol_balance = await self.solana.get_sol_balance()
            if sol_balance is None:
                logger.error("Failed to get SOL balance")
                return False
                
            # Ensure enough SOL for trade + gas
            required = amount + self.settings['gas_buffer']
            if side == 'buy' and sol_balance < required:
                logger.warning(f"Insufficient SOL balance: {sol_balance} < {required}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Trade validation failed: {e}")
            return False
            
    async def update_positions(self):
        """Update open positions"""
        try:
            for pool_id, position in self.positions.items():
                current_price = await self.orca.get_pool_price(pool_id)
                if current_price:
                    # Update unrealized PnL
                    entry_price = position['entry_price']
                    side = position['side']
                    size = position['size']
                    
                    if side == 'buy':
                        pnl = (current_price - entry_price) / entry_price * 100
                    else:
                        pnl = (entry_price - current_price) / entry_price * 100
                        
                    position['unrealized_pnl'] = pnl
                    logger.debug(f"Position {pool_id} PnL: {pnl:.2f}%")
                    
        except Exception as e:
            logger.error(f"Failed to update positions: {e}")
            
    async def shutdown(self):
        """Cleanup and shutdown"""
        self.running = False
        await self.solana.close()
        await self.orca.close() 