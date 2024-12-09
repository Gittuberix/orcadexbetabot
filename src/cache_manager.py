from pathlib import Path
from colorama import init, Fore, Style
import shutil
import json
import time

init()

class CacheManager:
    def __init__(self):
        print(f"{Fore.CYAN}Initializing Cache Manager...{Style.RESET_ALL}")
        
        # Cache Struktur definieren
        self.cache_structure = {
            'backtest_data': {
                'whirlpool': {},
                'market': {},
                'trades': {}
            },
            'live_data': {
                'whirlpool': {},
                'market': {},
                'trades': {}
            },
            'temp': {}
        }
        
        # Cache Pfade
        self.cache_dir = Path('cache')
        self.backtest_dir = self.cache_dir / 'backtest_data'
        self.live_dir = self.cache_dir / 'live_data'
        self.temp_dir = self.cache_dir / 'temp'

    def clean_cache(self):
        """Clean and restructure cache"""
        print(f"\n{Fore.YELLOW}Cleaning cache...{Style.RESET_ALL}")
        
        try:
            # Remove old cache if exists
            if self.cache_dir.exists():
                print(f"Removing old cache...")
                shutil.rmtree(self.cache_dir)
            
            # Create new structure
            print(f"Creating new cache structure...")
            self.create_cache_structure()
            
            print(f"{Fore.GREEN}Cache cleaned successfully!{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"{Fore.RED}Error cleaning cache: {str(e)}{Style.RESET_ALL}")

    def create_cache_structure(self):
        """Create new cache directory structure"""
        # Create main directories
        self.cache_dir.mkdir(exist_ok=True)
        self.backtest_dir.mkdir(exist_ok=True)
        self.live_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        for data_type in ['whirlpool', 'market', 'trades']:
            (self.backtest_dir / data_type).mkdir(exist_ok=True)
            (self.live_dir / data_type).mkdir(exist_ok=True)

    def verify_cache(self):
        """Verify cache structure"""
        print(f"\n{Fore.YELLOW}Verifying cache structure...{Style.RESET_ALL}")
        
        all_valid = True
        
        # Check all required directories
        required_dirs = [
            self.cache_dir,
            self.backtest_dir,
            self.live_dir,
            self.temp_dir
        ]
        
        for dir_path in required_dirs:
            if not dir_path.exists():
                print(f"{Fore.RED}Missing directory: {dir_path}{Style.RESET_ALL}")
                all_valid = False
        
        if all_valid:
            print(f"{Fore.GREEN}Cache structure verified!{Style.RESET_ALL}")
        return all_valid

def clean_and_test():
    """Clean cache and test structure"""
    print(f"{Fore.CYAN}=== Cache Cleanup and Test ==={Style.RESET_ALL}")
    
    manager = CacheManager()
    
    # Clean cache
    manager.clean_cache()
    
    # Verify structure
    if manager.verify_cache():
        print(f"\n{Fore.GREEN}Cache ready for use!{Style.RESET_ALL}")
        print("\nCache structure:")
        print("└── cache/")
        print("    ├── backtest_data/")
        print("    │   ├── whirlpool/")
        print("    │   ├── market/")
        print("    │   └── trades/")
        print("    ├── live_data/")
        print("    │   ├── whirlpool/")
        print("    │   ├── market/")
        print("    │   └── trades/")
        print("    └── temp/")

if __name__ == "__main__":
    clean_and_test() 