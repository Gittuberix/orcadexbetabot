import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from solders.keypair import Keypair
from solana.rpc.async_api import AsyncClient
from rich.console import Console
from src.whirlpool.microscope import WhirlpoolMicroscope
from src.trading.orca_trader import OrcaTrader
from src.data_fetcher import DataFetcher
from src.risk_manager import RiskManager, RiskParameters
from src.config.orca_config import WHIRLPOOL_CONFIGS
from src.models import Trade, PoolState

console = Console()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_backtest():
    try:
        print(f"\n=== Starte Backtest System ===")
        
        # Setup
        connection = AsyncClient("https://api.mainnet-beta.solana.com")
        microscope = WhirlpoolMicroscope(connection)
        
        # Zeitraum definieren
        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)  # 1 Woche Backtest
        print(f"\nZeitraum: {start_time} bis {end_time}")
        
        # Hole Pool-Daten
        test_pools = {
            name: config["address"]
            for name, config in WHIRLPOOL_CONFIGS.items()
        }
        
        # Initialisiere Komponenten
        risk_manager = RiskManager(RiskParameters(
            max_position_size=0.1,    # 10% des Portfolios
            max_slippage=0.01,        # 1% max Slippage
            max_price_impact=0.05,    # 5% max Impact
            min_liquidity=10000,      # $10k min Liquidität
            stop_loss=0.05,           # 5% Stop Loss
            take_profit=0.1           # 10% Take Profit
        ))
        
        # Sammle historische Daten
        print("\n=== Sammle historische Daten ===")
        pool_histories = {}
        for name, address in test_pools.items():
            print(f"\nAnalysiere {name} Pool...")
            
            # 1. Hole Pool-Zustand
            pool_data = await microscope.get_whirlpool_data(address)
            if not pool_data:
                print(f"Keine Daten für {name}")
                continue
                
            # 2. Hole Positionen
            positions = await microscope.get_all_positions(address)
            print(f"Aktive Positionen: {len(positions)}")
            
            # 3. Klone Pool für Backtest
            success = await microscope.clone_whirlpool(address)
            if not success:
                print(f"Fehler beim Klonen von {name}")
                continue
                
            # 4. Erstelle Pool State
            pool_state = PoolState(
                address=address,
                token_a=pool_data['token_a']['mint'],
                token_b=pool_data['token_b']['mint'],
                price=pool_data['price'],
                liquidity=pool_data['liquidity'],
                volume_24h=0,  # Wird später aktualisiert
                fee_rate=pool_data['fee_rate'],
                tick_spacing=pool_data['tick_spacing'],
                tick_current=pool_data['tick_current'],
                timestamp=datetime.now()
            )
            
            # 5. Simuliere Trades
            print("\nSimuliere Trades...")
            trades = []
            
            # Beispiel Trade (0.1 SOL)
            amount_in = int(0.1 * 1e9)  # 0.1 SOL in Lamports
            
            # Prüfe Risiko
            is_safe, message = risk_manager.check_trade(
                price=pool_state.price,
                amount=0.1,
                liquidity=pool_state.liquidity,
                price_impact=0.01  # Beispiel
            )
            
            if is_safe:
                print(f"Trade möglich: {message}")
                # Simuliere Trade
                trade = Trade(
                    timestamp=datetime.now(),
                    pool_address=address,
                    side='buy',
                    amount_in=amount_in,
                    amount_out=0,  # Wird durch Simulation bestimmt
                    price=pool_state.price,
                    fee=pool_state.fee_rate,
                    slippage=0.01,
                    success=True
                )
                trades.append(trade)
            else:
                print(f"Trade nicht möglich: {message}")
            
            pool_histories[name] = {
                'state': pool_state,
                'trades': trades,
                'positions': positions
            }
            
        # Zeige Ergebnisse
        print("\n=== Backtest Ergebnisse ===")
        for name, history in pool_histories.items():
            print(f"\n{name}:")
            print(f"Trades: {len(history['trades'])}")
            print(f"Positionen: {len(history['positions'])}")
            print(f"Letzter Preis: ${history['state'].price:.4f}")
            
    except Exception as e:
        logger.error(f"Fehler im Backtest: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await connection.close()

if __name__ == "__main__":
    asyncio.run(run_backtest()) 