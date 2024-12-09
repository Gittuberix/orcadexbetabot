import websockets
import json
import asyncio
import logging
from typing import Optional, Dict, Callable
from ..config.connections import QUICKNODE_WS_URL, QUICKNODE_API_KEY
from ..config.wallet_config import WalletConfig

logger = logging.getLogger(__name__)

class QuickNodeWebSocket:
    def __init__(self, wallet_config: WalletConfig):
        self.wallet_config = wallet_config
        self.ws = None
        self.subscriptions = {}
        self.connected = False
        self.reconnect_delay = 1
        self.max_reconnect_attempts = 5
        self.message_handlers = {}
        
    async def connect(self) -> bool:
        """Establish WebSocket connection to QuickNode"""
        try:
            self.ws = await websockets.connect(
                QUICKNODE_WS_URL,
                extra_headers={
                    "Authorization": f"Bearer {QUICKNODE_API_KEY}",
                    "Content-Type": "application/json"
                }
            )
            self.connected = True
            
            # Start message handler
            asyncio.create_task(self._handle_messages())
            # Start heartbeat
            asyncio.create_task(self._heartbeat())
            
            logger.info("QuickNode WebSocket connected")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to QuickNode WebSocket: {e}")
            return False
            
    async def _heartbeat(self):
        """Keep connection alive"""
        while self.connected:
            try:
                if self.ws:
                    await self.ws.ping()
                await asyncio.sleep(30)
            except Exception:
                await self.reconnect()
                
    async def reconnect(self) -> bool:
        """Attempt to reconnect"""
        for attempt in range(self.max_reconnect_attempts):
            try:
                logger.info(f"Reconnection attempt {attempt + 1}")
                await self.connect()
                
                # Resubscribe to all active subscriptions
                for sub_id, sub_info in self.subscriptions.items():
                    await self.subscribe(
                        method=sub_info['method'],
                        params=sub_info['params'],
                        callback=sub_info['callback']
                    )
                return True
                
            except Exception as e:
                logger.error(f"Reconnection attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(self.reconnect_delay * (2 ** attempt))
                
        return False
        
    async def subscribe(self, method: str, params: list, callback: Callable) -> Optional[int]:
        """Subscribe to updates"""
        try:
            message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": method,
                "params": params
            }
            
            await self.ws.send(json.dumps(message))
            response = await self.ws.recv()
            result = json.loads(response)
            
            if 'result' in result:
                sub_id = result['result']
                self.subscriptions[sub_id] = {
                    'method': method,
                    'params': params,
                    'callback': callback
                }
                logger.info(f"Subscribed to {method} with id {sub_id}")
                return sub_id
                
        except Exception as e:
            logger.error(f"Failed to subscribe: {e}")
            
        return None
        
    async def _handle_messages(self):
        """Handle incoming WebSocket messages"""
        while self.connected:
            try:
                message = await self.ws.recv()
                data = json.loads(message)
                
                # Handle subscription notifications
                if 'method' in data and data['method'].endswith('Notification'):
                    sub_id = data['params']['subscription']
                    if sub_id in self.subscriptions:
                        callback = self.subscriptions[sub_id]['callback']
                        await callback(data['params']['result'])
                        
            except websockets.ConnectionClosed:
                logger.warning("WebSocket connection closed")
                self.connected = False
                await self.reconnect()
                break
            except Exception as e:
                logger.error(f"Error handling message: {e}")
                
    async def subscribe_to_program(self, program_id: str, callback: Callable):
        """Subscribe to Solana program updates"""
        return await self.subscribe(
            "programSubscribe",
            [program_id, {"encoding": "jsonParsed", "commitment": "confirmed"}],
            callback
        )
        
    async def subscribe_to_logs(self, address: str, callback: Callable):
        """Subscribe to account logs"""
        return await self.subscribe(
            "logsSubscribe",
            [{"mentions": [address]}, {"commitment": "confirmed"}],
            callback
        )
        
    async def close(self):
        """Close WebSocket connection"""
        self.connected = False
        if self.ws:
            await self.ws.close() 
        
    async def subscribe_to_transactions(self, callback: Callable):
        """Subscribe to all transactions"""
        return await self.subscribe(
            "logsSubscribe",
            [{"mentions": ["*"]}, {"commitment": "confirmed"}],  # * subscribes to all transactions
            callback
        )
        
    async def get_transaction_details(self, signature: str) -> Optional[Dict]:
        """Get detailed transaction information"""
        try:
            message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getTransaction",
                "params": [
                    signature,
                    {
                        "encoding": "jsonParsed",
                        "maxSupportedTransactionVersion": 0
                    }
                ]
            }
            
            await self.ws.send(json.dumps(message))
            response = await self.ws.recv()
            result = json.loads(response)
            
            if 'result' in result:
                return result['result']
                
        except Exception as e:
            logger.error(f"Failed to get transaction details: {e}")
            
        return None
        
    async def monitor_orca_transactions(self, callback: Callable):
        """Monitor Orca DEX transactions specifically"""
        return await self.subscribe(
            "logsSubscribe",
            [{
                "mentions": ["whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc"]  # Orca program ID
            }, {
                "commitment": "confirmed"
            }],
            self._handle_orca_transaction(callback)
        )
        
    async def _handle_orca_transaction(self, callback: Callable):
        """Process Orca transaction data"""
        async def handler(data: Dict):
            try:
                # Check if transaction involves our wallet
                if self.wallet_config.public_key in data.get('accountKeys', []):
                    # Extract transaction signature
                    signature = data.get('signature')
                    if signature:
                        tx_details = await self.get_transaction_details(signature)
                        if tx_details and self._is_orca_swap(tx_details):
                            swap_info = self._extract_swap_info(tx_details)
                            await callback(swap_info)
                            
            except Exception as e:
                logger.error(f"Error handling Orca transaction: {e}")
                
        return handler
        
    def _is_orca_swap(self, tx_details: Dict) -> bool:
        """Check if transaction is an Orca swap"""
        try:
            program_id = tx_details.get('transaction', {}).get('message', {}).get('accountKeys', [])[0]
            return program_id == "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc"
        except Exception:
            return False
            
    def _extract_swap_info(self, tx_details: Dict) -> Dict:
        """Extract relevant swap information"""
        try:
            return {
                'signature': tx_details.get('transaction', {}).get('signatures', [])[0],
                'timestamp': tx_details.get('blockTime'),
                'success': not bool(tx_details.get('meta', {}).get('err')),
                'pool': tx_details.get('meta', {}).get('logMessages', [])[0],  # Usually contains pool address
                'amount_in': self._parse_amount(tx_details, 'in'),
                'amount_out': self._parse_amount(tx_details, 'out')
            }
        except Exception as e:
            logger.error(f"Error extracting swap info: {e}")
            return {}
            
    def _parse_amount(self, tx_details: Dict, direction: str) -> float:
        """Parse token amounts from transaction"""
        try:
            # Implementation depends on exact Orca transaction structure
            # This is a placeholder
            return 0.0
        except Exception:
            return 0.0