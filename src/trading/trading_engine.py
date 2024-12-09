from ..config.connections import ENVIRONMENTS, WHIRLPOOL_IDS, API_HEADERS
from ..connection.connection_manager import ConnectionManager
from colorama import init, Fore, Style
import time
from ..config.trading_config import TradingConfig
from ..whirlpool import WhirlpoolClient
import logging
from ..connection.solana_client import SolanaClient
from ..config.wallet_config import WalletConfig
from dataclasses import dataclass
from typing import Optional
from .balance_tracker import BalanceTracker, Balance
import asyncio

init()
logger = logging.getLogger(__name__)

@dataclass
class PriceAlert:
    target_price: float
    alert_type: str
    triggered: bool = False

class TradingEngine:
    def __init__(self, config: TradingConfig):
        self.config = config
        self.wallet_config = WalletConfig()
        self.parameters = config.parameters
        logger.info("Initializing Trading Engine...")
        
        self.env_config = ENVIRONMENTS['mainnet']
        self.whirlpool_ids = WHIRLPOOL_IDS
        self.headers = API_HEADERS
        
        # Initialize state
        self.active_pools = set()
        self.price_alerts = {}
        self.positions = {}
        self.wallet = None
        self.connection_manager = None
        self.balance_tracker = None
        
    async def initialize(self, pipeline):
        """Initialize trading engine"""
        try:
            self.pipeline = pipeline
            
            # Initialize connections
            self.connection_manager = ConnectionManager()
            await self.connection_manager.initialize()
            
            # Initialize balance tracker
            self.balance_tracker = BalanceTracker(
                self.wallet_config,
                self.connection_manager.solana
            )
            
            # Start balance tracking in background
            asyncio.create_task(self.balance_tracker.start())
            
            # Wait for initial balance update
            await asyncio.sleep(2)
            
            # Log initial balances
            logger.info(f"Initial SOL balance: {self.balance_tracker.get_available_sol():.4f}")
            logger.info(f"Initial USDC balance: {self.balance_tracker.get_available_usdc():.2f}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize trading engine: {e}")
            return False

    async def _check_balances(self, side: str, amount: float) -> bool:
        """Check if wallet has sufficient balance for trade"""
        try:
            if side == 'buy':
                # Check USDC balance
                available_usdc = self.balance_tracker.get_available_usdc()
                if available_usdc < amount:
                    logger.warning(f"Insufficient USDC balance: {available_usdc} < {amount}")
                    return False
            else:
                # Check SOL balance
                available_sol = self.balance_tracker.get_available_sol()
                if available_sol < amount:
                    logger.warning(f"Insufficient SOL balance: {available_sol} < {amount}")
                    return False
                    
            return True
            
        except Exception as e:
            logger.error(f"Error checking balances: {e}")
            return False
            
    async def _create_swap_transaction(self, pool_id: str, side: str, amount: float):
        """Create Orca swap transaction"""
        try:
            pool_data = await self.get_pool_data(pool_id)
            if not pool_data:
                return None
                
            # Calculate amounts and slippage
            price_impact = self.whirlpool.calculate_price_impact(pool_data, amount)
            slippage = self.whirlpool.calculate_slippage(pool_data, amount)
            
            # Create transaction
            transaction = await self.whirlpool.create_swap_transaction(
                pool_id=pool_id,
                side=side,
                amount=amount,
                slippage=slippage,
                wallet=self.wallet.pubkey()
            )
            
            return transaction
            
        except Exception as e:
            logger.error(f"Error creating swap transaction: {e}")
            return None
            
    async def _handle_price_trigger(self, pool_id: str, alert: PriceAlert, price: float):
        """Handle triggered price alert"""
        try:
            if alert.triggered:
                return
                
            alert.triggered = True
            logger.info(f"Price alert triggered for {pool_id} at {price}")
            
            # Execute trade based on alert type
            if alert.alert_type == 'above':
                await self.execute_trade(pool_id, 'sell', self.config.trade_size)
            else:
                await self.execute_trade(pool_id, 'buy', self.config.trade_size)
                
        except Exception as e:
            logger.error(f"Error handling price trigger: {e}")
            
    async def _update_trading_metrics(self, pool_id: str, price_data: dict):
        """Update trading metrics for monitoring"""
        try:
            # Update position P&L if exists
            if pool_id in self.positions:
                position = self.positions[pool_id]
                current_price = float(price_data['price'])
                
                # Calculate unrealized P&L
                if position['side'] == 'buy':
                    pnl = (current_price - position['entry_price']) / position['entry_price'] * 100
                else:
                    pnl = (position['entry_price'] - current_price) / position['entry_price'] * 100
                    
                position['unrealized_pnl'] = pnl
                logger.debug(f"Updated P&L for {pool_id}: {pnl:.2f}%")
                
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")

    async def shutdown(self):
        """Cleanup resources"""
        try:
            if self.balance_tracker:
                self.balance_tracker.stop()
            if self.connection_manager:
                await self.connection_manager.close()
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")