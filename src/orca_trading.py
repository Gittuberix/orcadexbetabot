from typing import Dict, Optional
import logging
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from anchorpy import Program, Provider, Wallet
import base58
from solana.transaction import Transaction
import json
from solders.keypair import Keypair
from solders.system_program import CreateAccountParams, initialize_account
from solana.keypair import Keypair
from solana.system_program import create_account, CreateAccountParams
from solana.spl.token.instructions import initialize_account, InitializeAccountParams

class OrcaTrading:
    def __init__(self, config: Dict, provider: Provider):
        self.config = config
        self.provider = provider
        self.orca_program_id = Pubkey.from_string("9W959DqEETiGZocYWCQPaJ6sBmUzgfxXfqGeTEdp3aQP")
        
    async def execute_swap(self, 
                         pool_address: str,
                         amount_in: float,
                         min_amount_out: float,
                         is_buy: bool) -> Dict:
        """Führt einen Swap auf Orca aus"""
        try:
            # Pool Account laden
            pool_account = await self.provider.connection.get_account_info(
                Pubkey.from_string(pool_address)
            )
            
            # Swap Instruction erstellen
            ix = await self._create_swap_instruction(
                pool_address=pool_address,
                amount_in=amount_in,
                min_amount_out=min_amount_out,
                is_buy=is_buy
            )
            
            # Transaktion erstellen und senden
            tx = Transaction()
            tx.add(ix)
            
            # Transaktion signieren und senden
            signature = await self.provider.send_and_confirm_transaction(tx)
            
            logging.info(f"Swap ausgeführt: {signature}")
            return {
                'success': True,
                'signature': str(signature),
                'amount': amount_in,
                'type': 'buy' if is_buy else 'sell'
            }
            
        except Exception as e:
            logging.error(f"Fehler bei Swap-Ausführung: {e}")
            return {'success': False, 'error': str(e)}
            
    async def _create_swap_instruction(self, pool_address: str, 
                                     amount_in: float,
                                     min_amount_out: float,
                                     is_buy: bool):
        """Erstellt die Swap-Instruction"""
        pool_pubkey = Pubkey.from_string(pool_address)
        
        # Token-Konten des Pools abrufen
        pool_data = await self._get_pool_token_accounts(pool_pubkey)
        
        # Benutzer Token-Konten
        user_source_token = await self._get_or_create_token_account(
            pool_data['source_mint'] if is_buy else pool_data['dest_mint']
        )
        user_dest_token = await self._get_or_create_token_account(
            pool_data['dest_mint'] if is_buy else pool_data['source_mint']
        )
        
        # Instruction Data
        data = self._encode_swap_data(amount_in, min_amount_out, is_buy)
        
        # Account Metas
        accounts = [
            {"pubkey": pool_pubkey, "is_signer": False, "is_writable": True},
            {"pubkey": pool_data['authority'], "is_signer": False, "is_writable": False},
            {"pubkey": user_source_token, "is_signer": False, "is_writable": True},
            {"pubkey": user_dest_token, "is_signer": False, "is_writable": True},
            {"pubkey": pool_data['source_token'], "is_signer": False, "is_writable": True},
            {"pubkey": pool_data['dest_token'], "is_signer": False, "is_writable": True},
            {"pubkey": self.provider.wallet.public_key, "is_signer": True, "is_writable": False},
        ]
        
        return Program.instruction(
            program_id=self.orca_program_id,
            data=data,
            accounts=accounts
        )
        
    async def _get_pool_token_accounts(self, pool_pubkey: Pubkey) -> Dict:
        """Holt die Token-Konten eines Pools"""
        try:
            account_info = await self.provider.connection.get_account_info(pool_pubkey)
            if not account_info or not account_info.data:
                raise ValueError("Pool nicht gefunden")
                
            # Orca Pool Layout parsen
            data = account_info.data
            
            # Token A und B Konten aus den ersten 128 Bytes extrahieren
            token_a = Pubkey(data[0:32])
            token_b = Pubkey(data[32:64])
            authority = Pubkey(data[64:96])
            
            # Token Mints aus den nächsten 64 Bytes
            mint_a = Pubkey(data[96:128])
            mint_b = Pubkey(data[128:160])
            
            return {
                'authority': authority,
                'source_token': token_a if is_buy else token_b,
                'dest_token': token_b if is_buy else token_a,
                'source_mint': mint_a if is_buy else mint_b,
                'dest_mint': mint_b if is_buy else mint_a
            }
            
        except Exception as e:
            logging.error(f"Fehler beim Laden der Pool-Konten: {e}")
            raise
            
    async def _get_or_create_token_account(self, mint: Pubkey) -> Pubkey:
        """Findet oder erstellt ein Token-Konto"""
        try:
            # Prüfe ob Konto existiert
            accounts = await self.provider.connection.get_token_accounts_by_owner(
                self.provider.wallet.public_key,
                {"mint": mint}
            )
            
            if accounts.value:
                return accounts.value[0].pubkey
                
            # Wenn nicht, erstelle neues Konto
            return await self._create_token_account(mint)
            
        except Exception as e:
            logging.error(f"Fehler bei Token-Konto: {e}")
            raise
            
    async def _create_token_account(self, mint: Pubkey) -> Pubkey:
        """Erstellt ein neues Token-Konto"""
        try:
            # System Program für Konto-Erstellung
            system_program = Pubkey.from_string("11111111111111111111111111111111")
            # Token Program
            token_program = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
            # Rent Sysvar
            rent = Pubkey.from_string("SysvarRent111111111111111111111111111111111")
            
            # Neues Konto generieren
            new_account = Keypair.generate()
            
            # Minimale Rent-Exemption berechnen
            rent_exemption = await self.provider.connection.get_minimum_balance_for_rent_exemption(165)
            
            # Create Account Instruction
            create_account_ix = create_account(
                CreateAccountParams(
                    from_pubkey=self.provider.wallet.public_key,
                    new_account_pubkey=new_account.public_key,
                    lamports=rent_exemption,
                    space=165,
                    program_id=token_program
                )
            )
            
            # Initialize Account Instruction
            init_account_ix = initialize_account(
                InitializeAccountParams(
                    account=new_account.public_key,
                    mint=mint,
                    owner=self.provider.wallet.public_key,
                    program_id=token_program
                )
            )
            
            # Transaktion erstellen und senden
            tx = Transaction()
            tx.add(create_account_ix)
            tx.add(init_account_ix)
            
            # Transaktion signieren (beide Signaturen notwendig)
            await self.provider.send_and_confirm_transaction(
                tx, 
                [new_account, self.provider.wallet.payer]
            )
            
            logging.info(f"Neues Token-Konto erstellt: {new_account.public_key}")
            return new_account.public_key
            
        except Exception as e:
            logging.error(f"Fehler bei Token-Konto-Erstellung: {e}")
            raise
            
    def _encode_swap_data(self, amount_in: float, min_amount_out: float, is_buy: bool) -> bytes:
        """Encodiert die Swap-Instruction-Daten"""
        # Instruction Index für Swap
        instruction_index = 1
        
        # Beträge in Lamports umrechnen
        amount_in_lamports = int(amount_in * 1e9)
        min_amount_out_lamports = int(min_amount_out * 1e9)
        
        # Daten packen
        import struct
        return struct.pack("<BQQ", instruction_index, amount_in_lamports, min_amount_out_lamports) 