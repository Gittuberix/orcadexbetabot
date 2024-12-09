import sys
import os

# Füge src zum Python-Path hinzu
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import logging
from test_data import test_data_fetching
import asyncio

# Logging Setup
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/test.log'),
        logging.StreamHandler()
    ]
)

# Tests ausführen
if __name__ == "__main__":
    print("🧪 Starting Orca API Tests...")
    try:
        asyncio.run(test_data_fetching())
    except KeyboardInterrupt:
        print("\n⚠️ Tests manually stopped")
    except Exception as e:
        print(f"\n❌ Tests failed: {str(e)}") 