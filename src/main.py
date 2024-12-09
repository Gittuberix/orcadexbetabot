import asyncio
import logging
from datetime import datetime
from live_trader import LiveTrader
from token_tracker import TokenTracker
from security_verifier import SecurityVerifier
from config import BotConfig
import yaml

async def main():
    print("\n" + "="*80)
    print("🚀 ORCA DEX TRADING BOT 🚀".center(80))
    print("="*80 + "\n")
    
    # Load configurations
    backtest_config = BotConfig.load_from_file("config_backtest.yaml")
    live_config = BotConfig.load_from_file("config.yaml")
    
    # Verify parameter consistency
    security_verifier = SecurityVerifier()
    try:
        security_verifier.ensure_parameter_consistency(backtest_config, live_config)
        print("✅ Security check passed: All parameters match between backtest and live environments")
    except ValueError as e:
        print("❌ Security check failed!")
        print(str(e))
        return
    
    # Initialize trading components
    trader = LiveTrader(initial_capital=1.0)
    tracker = TokenTracker()
    
    try:
        # Start token tracking
        tracker_task = asyncio.create_task(tracker.start_tracking())
        
        # Start trading
        await trader.start_trading()
        
    except KeyboardInterrupt:
        print("\n⚠️ Bot manually stopped")
    except Exception as e:
        print(f"\n❌ Bot error: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 