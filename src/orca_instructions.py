from solana.transaction import Transaction, TransactionInstruction
from solders.pubkey import Pubkey
from solders.system_program import SYS_PROGRAM_ID
from solana.spl.token.constants import TOKEN_PROGRAM_ID
import struct

class OrcaInstructions:
    WHIRLPOOL_PROGRAM = Pubkey.from_string("whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc")
    
    @staticmethod
    def create_swap_instruction(
        pool_address: str,
        user_token_account: str,
        amount: int,
        is_buy: bool,
        min_out: int
    ) -> TransactionInstruction:
        """Erstellt eine Orca Swap Instruction"""
        
        # Account Metas
        keys = [
            # Pool
            {"pubkey": Pubkey.from_string(pool_address), "is_signer": False, "is_writable": True},
            # User Token Account
            {"pubkey": Pubkey.from_string(user_token_account), "is_signer": False, "is_writable": True},
            # Token Program
            {"pubkey": TOKEN_PROGRAM_ID, "is_signer": False, "is_writable": False},
        ]
        
        # Instruction Data
        data = struct.pack(
            "<BQQB",  # Format: u8, u64, u64, u8
            0,        # Instruction index (swap = 0)
            amount,   # Amount in
            min_out,  # Minimum amount out
            1 if is_buy else 0  # Direction
        )
        
        return TransactionInstruction(
            program_id=OrcaInstructions.WHIRLPOOL_PROGRAM,
            data=data,
            keys=keys
        ) 