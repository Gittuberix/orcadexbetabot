from solana.rpc.api import Client
from solana.transaction import Transaction
from solana.keypair import Keypair
from solders.pubkey import Pubkey
import logging
from typing import Optional, Dict
import base58
from dataclasses import dataclass
import asyncio

@dataclass
class TradeResult:
    success: bool
    transaction_id: Optional[str] = None
    error: Optional[str] = None
    price: Optional[float] = None
    amount: Optional[float] = None
    fee: Optional[float] = None

class TestWallet:
    def __init__(self, private_key: str, rpc_url: str = "https://api.mainnet-beta.solana.com"):
        self.client = Client(rpc_url)
        self.keypair = Keypair.from_secret_key(base58.b58decode(private_key))
        self.balance = 0
        self.transactions = []
        
    async def initialize(self) -> bool:
        """Initialisiert das Wallet und lädt den aktuellen Balance"""
        try:
            response = await self.client.get_balance(self.keypair.public_key)
            self.balance = response['result']['value'] / 1e9  # Convert lamports to SOL
            logging.info(f"Wallet initialisiert. Balance: {self.balance} SOL")
            return True
        except Exception as e:
            logging.error(f"Fehler bei Wallet-Initialisierung: {e}")
            return False
            
    async def simulate_trade(self, pool_address: str, amount: float, is_buy: bool) -> TradeResult:
        """Simuliert einen Trade für Backtesting"""
        try:
            # Prüfe Balance
            if is_buy and amount > self.balance:
                return TradeResult(
                    success=False,
                    error="Insufficient funds"
                )
                
            # Simuliere Transaktion
            simulated_tx = {
                'from': str(self.keypair.public_key),
                'to': pool_address,
                'amount': amount,
                'type': 'buy' if is_buy else 'sell',
                'fee': 0.000005  # Typische Solana Transaktionsgebühr
            }
            
            # Update Balance
            if is_buy:
                self.balance -= (amount + simulated_tx['fee'])
            else:
                self.balance += (amount - simulated_tx['fee'])
                
            self.transactions.append(simulated_tx)
            
            return TradeResult(
                success=True,
                transaction_id=f"simulated_tx_{len(self.transactions)}",
                price=0,  # Wird im echten Trading gesetzt
                amount=amount,
                fee=simulated_tx['fee']
            )
            
        except Exception as e:
            logging.error(f"Fehler bei Trade-Simulation: {e}")
            return TradeResult(success=False, error=str(e))
            
    async def get_transaction_history(self) -> list:
        """Gibt die simulierte Transaktionshistorie zurück"""
        return self.transactions
        
    def get_balance(self) -> float:
        """Gibt den aktuellen Wallet-Balance zurück"""
        return self.balance

class BacktestWallet(TestWallet):
    """Spezielle Wallet-Klasse für Backtesting"""
    def __init__(self, initial_balance: float = 1000.0):
        self.balance = initial_balance
        self.transactions = []
        self.open_positions = {}
        
    async def initialize(self) -> bool:
        """Keine echte Initialisierung nötig für Backtest"""
        logging.info(f"Backtest Wallet initialisiert mit {self.balance} SOL")
        return True
        
    async def execute_trade(self, market_data: Dict, amount: float, is_buy: bool) -> TradeResult:
        """Führt einen simulierten Trade aus"""
        try:
            price = market_data['price']
            cost = amount * price
            fee = cost * 0.003  # 0.3% Handelsgebühr
            
            if is_buy:
                if cost + fee > self.balance:
                    return TradeResult(success=False, error="Insufficient funds")
                    
                self.balance -= (cost + fee)
                self.open_positions[market_data['token_address']] = {
                    'amount': amount,
                    'price': price
                }
            else:
                if market_data['token_address'] not in self.open_positions:
                    return TradeResult(success=False, error="No position to sell")
                    
                position = self.open_positions[market_data['token_address']]
                profit = (price - position['price']) * position['amount']
                self.balance += cost - fee
                del self.open_positions[market_data['token_address']]
                
            self.transactions.append({
                'timestamp': market_data['timestamp'],
                'type': 'buy' if is_buy else 'sell',
                'amount': amount,
                'price': price,
                'fee': fee,
                'balance_after': self.balance
            })
            
            return TradeResult(
                success=True,
                transaction_id=f"backtest_tx_{len(self.transactions)}",
                price=price,
                amount=amount,
                fee=fee
            )
            
        except Exception as e:
            logging.error(f"Fehler bei Backtest-Trade: {e}")
            return TradeResult(success=False, error=str(e)) 