import asyncio
import logging
from datetime import datetime, timedelta
from token_tracker import TokenTracker
from live_trader import LiveTrader
from backtest_data import BacktestDataProvider
from strategies.meme_sniper import MemeSniper
import yaml

async def run_test():
    # Logging einrichten
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/test.log'),
            logging.StreamHandler()
        ]
    )
    
    # Config laden
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    print("\n" + "="*80)
    print("🧪 ORCA BOT TEST & BACKTEST 🧪".center(80))
    print("="*80 + "\n")
    
    # 1. Backtest Daten laden
    print("1️⃣ Lade historische Daten...")
    start_time = datetime.now() - timedelta(hours=24)
    end_time = datetime.now()
    
    data_provider = BacktestDataProvider()
    await data_provider.load_historical_data(start_time, end_time)
    
    # 2. Live Token Tracking starten
    print("\n2️⃣ Starte Token Tracking...")
    tracker = TokenTracker()
    tracking_task = asyncio.create_task(tracker.start_tracking())
    
    # 3. Trading Bot starten
    print("\n3️⃣ Starte Trading Bot...")
    trader = LiveTrader(initial_capital=1.0)
    trader.strategy = MemeSniper(config['meme_strategy'])
    
    try:
        await trader.start_trading()
    except KeyboardInterrupt:
        print("\n⚠️ Test manuell beendet")
    finally:
        # Tracking Task beenden
        tracking_task.cancel()
        try:
            await tracking_task
        except asyncio.CancelledError:
            pass
            
        print("\n📊 TEST ERGEBNISSE:")
        print(f"• Token getrackt: {len(tracker.top_tokens)}")
        print(f"• Pools überwacht: {len(tracker.orca_pools)}")
        print(f"• Trades simuliert: {len(trader.trade_history)}")

if __name__ == "__main__":
    try:
        asyncio.run(run_test())
    except KeyboardInterrupt:
        print("\n⚠️ Bot manuell beendet")
    except Exception as e:
        logging.error(f"Unerwarteter Fehler: {e}") 