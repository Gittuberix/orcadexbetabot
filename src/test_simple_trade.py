from trade_executor import TradeExecutor
from colorama import init, Fore, Style

init()

def test_trade():
    print(f"{Fore.CYAN}=== Testing Simple Trade ==={Style.RESET_ALL}")
    
    # Initialize executor
    executor = TradeExecutor()
    
    # Check balance
    executor.check_balance()
    
    # Test parameters
    pool_id = "HJPjoWUrhoZzkNfRpHuieeFk9WcZWjwy6PBjZ81ngndJ"  # SOL-USDC pool
    amount = 0.1  # SOL amount
    side = "buy"
    
    # Execute test trade
    result = executor.execute_trade(pool_id, amount, side)
    
    if result:
        print(f"{Fore.GREEN}Test successful!{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Test failed!{Style.RESET_ALL}")

if __name__ == "__main__":
    test_trade() 