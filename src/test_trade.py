from trade_executor import TradeExecutor
from colorama import init, Fore, Style

init()

def run_tests():
    print(f"{Fore.CYAN}=== Running Trade Tests ==={Style.RESET_ALL}")
    
    executor = TradeExecutor()
    
    # Test 1: Check balances
    print(f"\n{Fore.YELLOW}Test 1: Balance Check{Style.RESET_ALL}")
    executor.check_balances()
    
    # Test 2: Small buy order
    print(f"\n{Fore.YELLOW}Test 2: Buy Order{Style.RESET_ALL}")
    executor.execute_trade('buy', 0.1, 0.01)
    
    # Test 3: Small sell order
    print(f"\n{Fore.YELLOW}Test 3: Sell Order{Style.RESET_ALL}")
    executor.execute_trade('sell', 0.1, 0.01)

if __name__ == "__main__":
    run_tests() 