from wallet_manager import WalletManager
from colorama import init, Fore, Style

init()

def check_wallet_setup():
    print(f"{Fore.CYAN}=== Wallet Setup Check ==={Style.RESET_ALL}")
    
    wallet = WalletManager()
    
    # Check if wallet exists
    if wallet.keypair:
        print(f"{Fore.GREEN}✓ Wallet loaded successfully{Style.RESET_ALL}")
        print(f"Public Key: {wallet.keypair.public_key}")
        
        # Check balances
        sol_balance = wallet.check_balance()
        if sol_balance is not None:
            print(f"SOL Balance: {sol_balance:.4f}")
            
        usdc_address = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
        usdc_balance = wallet.get_token_balance(usdc_address)
        if usdc_balance is not None:
            print(f"USDC Balance: ${usdc_balance:.2f}")
    else:
        print(f"{Fore.RED}✗ No wallet found{Style.RESET_ALL}")

if __name__ == "__main__":
    check_wallet_setup() 