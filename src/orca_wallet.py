from solana.rpc.api import Client
from solana.transaction import Transaction
from solana.keypair import Keypair
from solders.pubkey import Pubkey
from anchorpy import Provider, Wallet
import logging
from typing import Optional, Dict
import base58
from dataclasses import dataclass
import asyncio
import json
from spl.token.instructions import get_associated_token_address
from spl.token.constants import TOKEN_PROGRAM_ID
import aiohttp
from datetime import datetime
from pathlib import Path
import traceback
from spl.token.instructions import create_associated_token_account
from solana.transaction import TransactionInstruction
from solana.rpc.types import TxOpts

@dataclass
class OrcaTradeResult:
    success: bool
    transaction_id: Optional[str] = None
    error: Optional[str] = None
    price: Optional[float] = None
    amount: Optional[float] = None
    fee: Optional[float] = None
    slippage: Optional[float] = None

class OrcaWalletError(Exception):
    """Basis-Klasse für Wallet-spezifische Fehler"""
    pass

class InsufficientFundsError(OrcaWalletError):
    """Fehler bei unzureichendem Guthaben"""
    pass

class PoolLiquidityError(OrcaWalletError):
    """Fehler bei unzureichender Pool-Liquidität"""
    pass

class TransactionError(OrcaWalletError):
    """Fehler bei Transaktionsausführung"""
    pass

class OrcaWallet:
    def __init__(self, private_key: str, rpc_url: str = "https://api.mainnet-beta.solana.com"):
        self.client = Client(rpc_url)
        self.keypair = Keypair.from_secret_key(base58.b58decode(private_key))
        self.provider = Provider(self.client, Wallet(self.keypair))
        self.balance = 0
        self.transactions = []
        self.token_accounts = {}
        
        # Logging Setup
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        
        self.trade_log = self.log_dir / "trades.log"
        self.error_log = self.log_dir / "errors.log"
        
        # Retry Konfiguration
        self.max_retries = 3
        self.retry_delay = 1
        
    async def initialize(self) -> bool:
        """Initialisiert das Wallet und lädt Token-Accounts"""
        try:
            # SOL Balance laden
            response = await self.client.get_balance(self.keypair.public_key)
            self.balance = response['result']['value'] / 1e9
            
            # Token Accounts laden
            accounts = await self.client.get_token_accounts_by_owner(
                self.keypair.public_key,
                {'programId': TOKEN_PROGRAM_ID}
            )
            
            for account in accounts['result']['value']:
                mint = account['account']['data']['parsed']['info']['mint']
                self.token_accounts[mint] = account['pubkey']
                
            logging.info(f"Wallet initialisiert. SOL Balance: {self.balance}")
            return True
            
        except Exception as e:
            logging.error(f"Fehler bei Wallet-Initialisierung: {e}")
            return False
            
    def _log_trade(self, trade_data: Dict):
        """Protokolliert Trade-Informationen"""
        timestamp = datetime.now().isoformat()
        log_entry = f"{timestamp} | {json.dumps(trade_data)}\n"
        
        with open(self.trade_log, "a") as f:
            f.write(log_entry)
            
    def _log_error(self, error: Exception, context: str):
        """Protokolliert detaillierte Fehlerinformationen"""
        timestamp = datetime.now().isoformat()
        stack_trace = traceback.format_exc()
        
        log_entry = f"""
        {timestamp} | {context}
        Error Type: {type(error).__name__}
        Error Message: {str(error)}
        Stack Trace:
        {stack_trace}
        {"="*50}
        """
        
        with open(self.error_log, "a") as f:
            f.write(log_entry)
            
    async def execute_orca_swap(
        self,
        pool_address: str,
        token_mint: str,
        amount: float,
        is_buy: bool,
        slippage: float = 0.01
    ) -> OrcaTradeResult:
        """Führt einen Swap auf Orca DEX aus mit verbesserter Fehlerbehandlung"""
        try:
            # Balance Check
            if is_buy:
                required_balance = amount * (1 + slippage)  # Plus Slippage
                if self.balance < required_balance:
                    raise InsufficientFundsError(
                        f"Benötigt: {required_balance} SOL, Verfügbar: {self.balance} SOL"
                    )
            
            # Pool-Daten mit Retry
            pool_data = await self._retry_operation(
                self._get_pool_data,
                pool_address
            )
            
            if not pool_data:
                raise PoolLiquidityError(f"Pool {pool_address} nicht gefunden")
                
            # Liquiditäts-Check
            if float(pool_data['liquidity']) < amount * 10:  # Mindestens 10x Liquidität
                raise PoolLiquidityError(
                    f"Unzureichende Liquidität: {pool_data['liquidity']}"
                )
                
            # Quote mit Retry
            quote = await self._retry_operation(
                self._get_orca_quote,
                pool_address,
                amount,
                is_buy,
                slippage
            )
            
            if not quote['success']:
                raise TransactionError(f"Quote Fehler: {quote.get('error')}")
                
            # Slippage-Check
            if float(quote['price_impact']) > slippage:
                raise TransactionError(
                    f"Slippage zu hoch: {quote['price_impact']} > {slippage}"
                )
                
            # Token Account
            token_account = await self._get_or_create_token_account(token_mint)
            
            # Transaktion mit Prioritätsgebühr
            tx = Transaction()
            tx.add(await self._create_swap_instruction(
                pool_address,
                token_account,
                amount,
                quote,
                is_buy
            ))
            
            # Transaktion mit Retry senden
            opts = TxOpts(
                skip_preflight=True,
                priority_fee=1000  # 0.000001 SOL Prioritätsgebühr
            )
            
            result = await self._retry_operation(
                self.provider.send,
                tx,
                opts=opts
            )
            
            if result['result']:
                trade_data = {
                    'success': True,
                    'transaction_id': result['result'],
                    'type': 'buy' if is_buy else 'sell',
                    'amount': amount,
                    'price': quote['price'],
                    'fee': quote['fee'],
                    'slippage': quote['price_impact'],
                    'pool': pool_address,
                    'token': token_mint
                }
                
                self._log_trade(trade_data)
                
                return OrcaTradeResult(
                    success=True,
                    transaction_id=result['result'],
                    price=quote['price'],
                    amount=amount,
                    fee=quote['fee'],
                    slippage=quote['price_impact']
                )
            else:
                raise TransactionError(f"Transaction failed: {result.get('error')}")
                
        except OrcaWalletError as e:
            self._log_error(e, "Wallet Operation Error")
            return OrcaTradeResult(success=False, error=str(e))
            
        except Exception as e:
            self._log_error(e, "Unexpected Error")
            return OrcaTradeResult(success=False, error=f"Unexpected error: {str(e)}")
            
    async def _retry_operation(self, operation, *args, **kwargs):
        """Führt eine Operation mit Retry-Logik aus"""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                return await operation(*args, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    
        self._log_error(last_error, f"Retry failed for {operation.__name__}")
        raise last_error
        
    async def _get_pool_data(self, pool_address: str) -> Optional[Dict]:
        """Holt Pool-Daten von Orca"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://api.orca.so/v1/pool/{pool_address}"
                ) as response:
                    if response.status == 200:
                        return await response.json()
            return None
        except Exception as e:
            logging.error(f"Pool Daten Fehler: {e}")
            return None
            
    async def _get_orca_quote(
        self,
        pool_address: str,
        amount: float,
        is_buy: bool,
        slippage: float
    ) -> Dict:
        """Holt ein Quote von Orca"""
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    'amount': str(amount),
                    'inputMint': 'SOL' if is_buy else pool_address,
                    'outputMint': pool_address if is_buy else 'SOL',
                    'slippage': slippage
                }
                
                async with session.get(
                    f"https://api.orca.so/v1/quote",
                    params=params
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    return {'success': False, 'error': f"Quote Status: {response.status}"}
                    
        except Exception as e:
            logging.error(f"Quote Fehler: {e}")
            return {'success': False, 'error': str(e)}
            
    async def _get_or_create_token_account(self, token_mint: str) -> Pubkey:
        """Findet oder erstellt einen Token Account"""
        if token_mint in self.token_accounts:
            return self.token_accounts[token_mint]
            
        # Associated Token Account erstellen
        ata = get_associated_token_address(
            self.keypair.public_key,
            Pubkey.from_string(token_mint)
        )
        
        # Prüfen ob Account existiert
        info = await self.client.get_account_info(ata)
        if not info['result']['value']:
            # Account erstellen
            create_ix = create_associated_token_account(
                self.keypair.public_key,
                self.keypair.public_key,
                Pubkey.from_string(token_mint)
            )
            tx = Transaction().add(create_ix)
            await self.provider.send(tx)
            
        self.token_accounts[token_mint] = ata
        return ata
        
    async def _create_swap_instruction(
        self,
        pool_address: str,
        token_account: Pubkey,
        amount: float,
        quote: Dict,
        is_buy: bool
    ) -> TransactionInstruction:
        """Erstellt die Swap Instruction für Orca Whirlpool"""
        try:
            # Implementieren Sie hier die spezifische Orca Whirlpool Swap Instruction
            # Dies erfordert die Verwendung des Orca SDK oder direktes Aufrufen des Programms
            
            # Beispiel (muss an Ihre spezifischen Anforderungen angepasst werden):
            from orca_sdk import WhirlpoolContext, SwapParams
            
            ctx = WhirlpoolContext(
                self.provider,
                Pubkey.from_string(pool_address)
            )
            
            swap_params = SwapParams(
                amount=amount,
                other_amount_threshold=int(quote['minimum_received']),
                sqrt_price_limit=0,
                is_a_to_b=is_buy
            )
            
            return ctx.swap(swap_params)
            
        except Exception as e:
            self._log_error(e, "Swap Instruction Error")
            raise TransactionError(f"Failed to create swap instruction: {str(e)}")
        
    async def get_token_balance(self, token_mint: str) -> float:
        """Gibt den Balance eines Tokens zurück"""
        try:
            if token_mint not in self.token_accounts:
                return 0.0
                
            response = await self.client.get_token_account_balance(
                self.token_accounts[token_mint]
            )
            
            if response['result']['value']:
                return float(response['result']['value']['uiAmount'])
            return 0.0
            
        except Exception as e:
            logging.error(f"Token Balance Fehler: {e}")
            return 0.0 