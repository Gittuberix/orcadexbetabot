from solana.rpc.api import Client
from solana.transaction import Transaction
from solders.pubkey import Pubkey
import base58
import json
import logging
from typing import Optional, Dict

class PhantomWalletIntegration:
    def __init__(self, network: str = "mainnet"):
        self.network = network
        self.rpc_url = "https://api.mainnet-beta.solana.com" if network == "mainnet" else "https://api.devnet.solana.com"
        self.client = Client(self.rpc_url)
        
    def create_transaction(self, swap_data: Dict) -> str:
        """Erstellt eine Transaktion für Phantom Wallet"""
        try:
            # Transaktion erstellen
            tx = Transaction()
            
            # Orca Swap Instructions hinzufügen
            # (Implementierung abhängig von Orca SDK)
            
            # Transaktion serialisieren
            serialized_tx = base58.b58encode(tx.serialize()).decode('ascii')
            
            # Daten für Phantom Wallet
            wallet_data = {
                'network': self.network,
                'transaction': serialized_tx,
                'message': f"Swap {swap_data['amount']} {swap_data['from_token']} to {swap_data['to_token']}"
            }
            
            return json.dumps(wallet_data)
            
        except Exception as e:
            logging.error(f"Fehler bei Transaktion: {e}")
            return None
            
    def verify_transaction(self, signature: str) -> bool:
        """Überprüft eine Transaktion"""
        try:
            result = self.client.get_transaction(signature)
            return result['result']['meta']['status']['Ok'] is not None
        except Exception as e:
            logging.error(f"Verifikations-Fehler: {e}")
            return False 