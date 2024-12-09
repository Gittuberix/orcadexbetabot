from solana.rpc.api import Client
from solana.rpc.commitment import Confirmed
from typing import Optional, Dict, List
import logging
import asyncio
from datetime import datetime
import base58

class SolanaRPC:
    def __init__(self, network: str = "mainnet"):
        # RPC Endpoints
        self.endpoints = {
            "mainnet": [
                "https://api.mainnet-beta.solana.com",
                "https://solana-api.projectserum.com",
                "https://rpc.ankr.com/solana"
            ],
            "devnet": [
                "https://api.devnet.solana.com"
            ]
        }
        
        self.network = network
        self.current_endpoint = 0
        self.client = Client(self.endpoints[network][0])
        self.last_request_time = {}
        self.request_interval = 0.1  # 100ms zwischen Anfragen
        
        # Performance Tracking
        self.response_times = []
        self.error_counts = {}
        
    async def get_token_accounts(self, wallet_address: str) -> List[Dict]:
        """Holt alle Token Accounts einer Wallet"""
        try:
            response = await self.client.get_token_accounts_by_owner(
                wallet_address,
                {'programId': 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'}
            )
            
            if response['result']['value']:
                return [
                    {
                        'mint': acc['account']['data']['parsed']['info']['mint'],
                        'amount': float(acc['account']['data']['parsed']['info']['tokenAmount']['uiAmount']),
                        'address': acc['pubkey']
                    }
                    for acc in response['result']['value']
                ]
            return []
            
        except Exception as e:
            await self._handle_error("get_token_accounts", e)
            return []
            
    async def get_token_balance(self, token_account: str) -> float:
        """Holt den Balance eines Token Accounts"""
        try:
            response = await self.client.get_token_account_balance(token_account)
            if response['result']['value']:
                return float(response['result']['value']['uiAmount'])
            return 0.0
        except Exception as e:
            await self._handle_error("get_token_balance", e)
            return 0.0
            
    async def get_sol_balance(self, wallet_address: str) -> float:
        """Holt den SOL Balance einer Wallet"""
        try:
            response = await self.client.get_balance(wallet_address)
            if response['result']['value']:
                return response['result']['value'] / 1e9  # Lamports zu SOL
            return 0.0
        except Exception as e:
            await self._handle_error("get_sol_balance", e)
            return 0.0
            
    async def get_token_info(self, token_mint: str) -> Optional[Dict]:
        """Holt Token Metadaten"""
        try:
            response = await self.client.get_account_info(token_mint)
            if response['result']['value']:
                data = base58.b58decode(response['result']['value']['data'][0])
                return {
                    'mint': token_mint,
                    'decimals': data[4],
                    'supply': int.from_bytes(data[4:12], 'little') / (10 ** data[4]),
                    'is_initialized': bool(data[12])
                }
            return None
        except Exception as e:
            await self._handle_error("get_token_info", e)
            return None
            
    async def get_recent_performance(self) -> Dict:
        """Gibt Performance-Metriken zurück"""
        if not self.response_times:
            return {
                'avg_response_time': 0,
                'error_rate': 0,
                'total_requests': 0
            }
            
        total_requests = len(self.response_times)
        total_errors = sum(self.error_counts.values())
        
        return {
            'avg_response_time': sum(self.response_times) / len(self.response_times),
            'error_rate': total_errors / total_requests if total_requests > 0 else 0,
            'total_requests': total_requests,
            'errors_by_method': dict(self.error_counts)
        }
        
    async def _handle_error(self, method: str, error: Exception):
        """Behandelt RPC Fehler"""
        self.error_counts[method] = self.error_counts.get(method, 0) + 1
        
        if "429" in str(error):  # Rate Limit
            await asyncio.sleep(1)
            return
            
        if "502" in str(error) or "503" in str(error):  # Server Fehler
            await self._switch_endpoint()
            return
            
        logging.error(f"RPC Fehler in {method}: {str(error)}")
        
    async def _switch_endpoint(self):
        """Wechselt zu einem anderen RPC Endpoint"""
        self.current_endpoint = (self.current_endpoint + 1) % len(self.endpoints[self.network])
        new_endpoint = self.endpoints[self.network][self.current_endpoint]
        
        self.client = Client(new_endpoint)
        logging.warning(f"Gewechselt zu RPC Endpoint: {new_endpoint}")
        
    async def _measure_performance(self, method: str, start_time: float):
        """Misst die Performance eines RPC Calls"""
        duration = time.time() - start_time
        self.response_times.append(duration)
        
        # Nur die letzten 1000 Messungen behalten
        if len(self.response_times) > 1000:
            self.response_times.pop(0)
            
        # Warnung bei langsamen Anfragen
        if duration > 1.0:  # Mehr als 1 Sekunde
            logging.warning(f"Langsame RPC Anfrage: {method} ({duration:.2f}s)")

    async def get_pool_info(self, pool_address: str) -> Optional[Dict]:
        """Holt detaillierte Pool-Informationen"""
        try:
            response = await self.client.get_account_info(
                pool_address,
                encoding="jsonParsed",
                commitment=Confirmed
            )
            
            if response['result']['value']:
                data = response['result']['value']['data']
                return {
                    'address': pool_address,
                    'liquidity': float(data['parsed']['info']['liquidity']),
                    'token_a_amount': float(data['parsed']['info']['tokenAAmount']),
                    'token_b_amount': float(data['parsed']['info']['tokenBAmount']),
                    'fee_rate': float(data['parsed']['info']['feeRate']) / 10000,
                    'last_update': datetime.fromtimestamp(data['parsed']['info']['lastUpdateTime'])
                }
            return None
        except Exception as e:
            await self._handle_error("get_pool_info", e)
            return None

    async def get_phantom_transaction(self, tx_data: Dict) -> Dict:
        """Erstellt eine Phantom-kompatible Transaktion"""
        try:
            # Transaktion vorbereiten
            tx = {
                'network': self.network,
                'instructions': tx_data['instructions'],
                'signers': [tx_data.get('signer')],
                'feePayer': tx_data.get('fee_payer'),
                'recentBlockhash': await self._get_recent_blockhash()
            }
            
            return {
                'transaction': base58.b58encode(tx).decode('ascii'),
                'message': tx_data.get('message', 'Orca DEX Swap')
            }
            
        except Exception as e:
            await self._handle_error("get_phantom_transaction", e)
            return None

    async def _get_recent_blockhash(self) -> str:
        """Holt den aktuellen Blockhash"""
        try:
            response = await self.client.get_recent_blockhash()
            return response['result']['value']['blockhash']
        except Exception as e:
            await self._handle_error("get_recent_blockhash", e)
            return None

# Beispiel Nutzung:
async def main():
    rpc = SolanaRPC()
    
    # Wallet Balance abrufen
    wallet_address = "YOUR_WALLET_ADDRESS"
    sol_balance = await rpc.get_sol_balance(wallet_address)
    print(f"SOL Balance: {sol_balance}")
    
    # Token Accounts abrufen
    token_accounts = await rpc.get_token_accounts(wallet_address)
    for acc in token_accounts:
        print(f"Token: {acc['mint']}, Amount: {acc['amount']}")
        
    # Performance Metriken
    perf = await rpc.get_recent_performance()
    print(f"RPC Performance: {perf}")

if __name__ == "__main__":
    asyncio.run(main()) 