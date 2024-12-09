import requests
from colorama import init, Fore, Style
import json

init()

def test_connection():
    print(f"{Fore.CYAN}Testing Basic Connection...{Style.RESET_ALL}")
    
    # Test URLs
    urls = [
        "https://price.jup.ag/v4/price?ids=So11111111111111111111111111111111111111112",
        "https://api.orca.so/v1/pools",
        "https://api.mainnet.orca.so/v1/pools"
    ]
    
    for url in urls:
        try:
            print(f"\n{Fore.YELLOW}Testing URL: {url}{Style.RESET_ALL}")
            response = requests.get(url)
            print(f"{Fore.GREEN}Response: {response.status_code}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error: {str(e)}{Style.RESET_ALL}") 