import os
from dotenv import load_dotenv
from solders.keypair import Keypair
from solders.pubkey import Pubkey
import base58

load_dotenv()

class WalletConfig:
    def __init__(self):
        self.public_key = "Bh3xV3ctC45DSy92JK7MKbC2fYe1tZMmoyi3XyTGcV3b"
        self.private_key = os.getenv('WALLET_PRIVATE_KEY')
        self.usdc_token_account = os.getenv('USDC_TOKEN_ACCOUNT')
        self.sol_token_account = os.getenv('SOL_TOKEN_ACCOUNT')
        
        if not all([self.public_key, self.private_key, 
                   self.usdc_token_account, self.sol_token_account]):
            raise ValueError("Missing wallet configuration")
            
    def get_keypair(self) -> Keypair:
        """Get wallet keypair"""
        return Keypair.from_bytes(base58.b58decode(self.private_key))
        
    def get_pubkey(self) -> Pubkey:
        """Get wallet public key"""
        return Pubkey.from_string(self.public_key)
        
    def get_token_account(self, token: str) -> str:
        """Get specific token account"""
        if token.upper() == 'USDC':
            return self.usdc_token_account
        elif token.upper() == 'SOL':
            return self.sol_token_account
        raise ValueError(f"Unknown token: {token}") 