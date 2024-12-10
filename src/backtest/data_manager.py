import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

import asyncio
import logging
from datetime import datetime, timedelta
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from colorama import init, Fore, Style
from .historical_replayer import WhirlpoolReplayer
from .orca_whirlpool_pipeline import OrcaWhirlpoolPipeline
from decimal import Decimal
from src.data.orca_pipeline import OrcaDataPipeline
from src.models import PoolState, Trade
from rich.console import Console
from src.models import TradeData, BacktestResult
from src.data.orca_pipeline import OrcaPipeline

init()
logger = logging.getLogger(__name__)
console = Console()

class OrcaDataManager:
    def __init__(self):
        self.client = AsyncClient("https://api.mainnet-beta.solana.com")
        self.data_dir = Path("data/historical")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Wichtige Pool-Adressen
        self.pools = {
            "SOL/USDC": "HJPjoWUrhoZzkNfRpHuieeFk9WcZWjwy6PBjZ81ngndJ",
            "SOL/USDT": "4GpUivZ2jvZqQ3vJRsoq5PwnYv6gdV9fJ9BzHT2JcRr7",
            "BONK/SOL": "8QaXeHBrShJTdtN1rWHbp3pPJGCuYKxqZn8M5YBV1HSF"
        }
        
    async def fetch_pool_data(self, pool_address: str) -> Dict:
        """Holt aktuelle Pool-Daten"""
        try:
            account = await self.client.get_account_info(
                Pubkey.from_string(pool_address),
                commitment=Confirmed,
                encoding="base64"
            )
            
            if account and account.value:
                data = account.value.data
                # Decodiere Whirlpool-Daten
                sqrt_price = int.from_bytes(data[:8], 'little')
                price = (sqrt_price / (2 ** 64)) ** 2
                liquidity = int.from_bytes(data[16:24], 'little')
                
                return {
                    'timestamp': datetime.now().isoformat(),
                    'price': price,
                    'liquidity': liquidity,
                    'sqrt_price': sqrt_price
                }
            return None
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Pool-Daten: {e}")
            return None
            
    async def collect_historical_data(self, 
        pool_address: str, 
        duration_hours: int = 24,
        interval_seconds: int = 60
    ):
        """Sammelt historische Daten für einen Pool"""
        data_points = []
        start_time = datetime.now()
        
        print(f"{Fore.CYAN}Sammle Daten für Pool {pool_address}{Style.RESET_ALL}")
        print(f"Start: {start_time}")
        
        while (datetime.now() - start_time).total_seconds() < duration_hours * 3600:
            pool_data = await self.fetch_pool_data(pool_address)
            if pool_data:
                data_points.append(pool_data)
                if len(data_points) % 10 == 0:  # Status alle 10 Datenpunkte
                    print(f"Gesammelte Datenpunkte: {len(data_points)}", end='\r')
                    
            await asyncio.sleep(interval_seconds)
            
        # Speichere Daten
        df = pd.DataFrame(data_points)
        filename = f"pool_{pool_address}_{start_time:%Y%m%d_%H%M}.parquet"
        df.to_parquet(self.data_dir / filename)
        print(f"\n{Fore.GREEN}Datensammlung abgeschlossen. {len(data_points)} Datenpunkte gespeichert.{Style.RESET_ALL}")
        return df
        
    def load_historical_data(self, pool_address: str) -> pd.DataFrame:
        """Lädt historische Daten für einen Pool"""
        files = list(self.data_dir.glob(f"pool_{pool_address}_*.parquet"))
        if not files:
            raise FileNotFoundError(f"Keine historischen Daten für Pool {pool_address}")
            
        # Lade und kombiniere alle Dateien
        dfs = []
        for file in files:
            df = pd.read_parquet(file)
            dfs.append(df)
            
        combined_df = pd.concat(dfs).sort_values('timestamp')
        print(f"{Fore.GREEN}Geladen: {len(combined_df)} Datenpunkte von {len(files)} Dateien{Style.RESET_ALL}")
        return combined_df

class HistoricalDataManager:
    def __init__(self):
        self.pipeline = OrcaWhirlpoolPipeline()
        self.replayer = WhirlpoolReplayer()
        self.data_dir = Path("data/historical")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    async def prepare_backtest_data(self,
        start_time: datetime,
        end_time: datetime,
        min_volume: float = 100000
    ) -> Dict[str, pd.DataFrame]:
        """Bereitet Backtest-Daten mit dem Replayer vor"""
        
        # Setup Replayer
        await self.replayer.setup_replayer()
        
        # Hole aktive Pools
        active_pools = await self.pipeline.fetch_all_whirlpools()
        active_pools = [p for p in active_pools if p.get('volume24h', 0) >= min_volume]
        
        print(f"\nSammle Daten für {len(active_pools)} Pools...")
        
        pool_data = {}
        for pool in active_pools:
            try:
                # Hole historische Daten via Replayer
                df = await self.replayer.fetch_historical_data(
                    pool['address'],
                    start_time,
                    end_time
                )
                
                if not df.empty:
                    # Verarbeite Replay-Daten
                    processed_df = self.replayer.process_replay_data(df)
                    pool_data[pool['address']] = processed_df
                    
                    print(f"✓ {pool.get('token_a_symbol')}/{pool.get('token_b_symbol')}: "
                          f"{len(processed_df)} Datenpunkte")
                    
            except Exception as e:
                logger.error(f"Fehler bei Pool {pool['address']}: {e}")
                
        return pool_data

class BacktestDataManager:
    def __init__(self):
        self.pipeline = OrcaDataPipeline()
        
    async def collect_backtest_data(self,
        pool_address: str,
        duration_hours: int = 24,
        interval_seconds: int = 1
    ) -> List[PoolState]:
        """Sammelt Daten für den Backtest"""
        try:
            # Starte Datensammlung
            collection_task = asyncio.create_task(
                self.pipeline.start_data_collection(interval_seconds)
            )
            
            # Warte auf Datensammlung
            console.print(f"\nSammle {duration_hours} Stunden Daten...")
            await asyncio.sleep(duration_hours * 3600)
            
            # Stoppe Sammlung
            await self.pipeline.stop()
            collection_task.cancel()
            
            # Hole gesammelte Daten
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=duration_hours)
            
            historical_data = await self.pipeline.get_historical_data(
                pool_address,
                start_time,
                end_time
            )
            
            # Konvertiere zu PoolState
            pool_states = []
            for data in historical_data:
                pool_data = await self.pipeline.microscope.get_whirlpool_data(pool_address)
                if pool_data:
                    state = PoolState(
                        address=pool_address,
                        token_a=pool_data['token_a']['address'],
                        token_b=pool_data['token_b']['address'],
                        price=Decimal(str(data['price'])),
                        liquidity=data['liquidity'],
                        volume_24h=Decimal("0"),
                        fee_rate=pool_data['fee_rate'],
                        tick_spacing=pool_data['tick_spacing'],
                        tick_current=data['tick_current'],
                        timestamp=data['timestamp']
                    )
                    pool_states.append(state)
                    
            return pool_states
            
        except Exception as e:
            logger.error(f"Fehler bei Datensammlung: {e}")
            return []
        
    async def simulate_trades(self,
        pool_states: List[PoolState],
        trade_size: Decimal,
        slippage: Decimal = Decimal("0.01")
    ) -> List[Trade]:
        """Simuliert Trades basierend auf historischen Daten"""
        trades = []
        
        for i, state in enumerate(pool_states[:-1]):
            next_state = pool_states[i + 1]
            price_change = (next_state.price - state.price) / state.price
            
            # Simple Strategie: Kaufe bei Preisanstieg, Verkaufe bei Preisfall
            if abs(price_change) > float(slippage):
                side = 'buy' if price_change > 0 else 'sell'
                amount_in = int(trade_size * 1e9)  # Convert to lamports
                
                trade = Trade(
                    timestamp=next_state.timestamp,
                    pool_address=state.address,
                    side=side,
                    amount_in=amount_in,
                    amount_out=int(amount_in * float(next_state.price)),
                    price=next_state.price,
                    fee=int(amount_in * state.fee_rate / 10000),
                    slippage=slippage,
                    success=True
                )
                trades.append(trade)
                
        return trades

class BacktestManager:
    def __init__(self):
        self.pipeline = OrcaPipeline()
        self.historical_data = {}
        
    async def initialize(self):
        """Initialisiert den Manager"""
        await self.pipeline.initialize()
        
    async def load_historical_data(
        self,
        pool_name: str,
        start_time: datetime,
        end_time: datetime = None
    ) -> List[TradeData]:
        """Lädt historische Daten"""
        if not end_time:
            end_time = datetime.now()
            
        key = f"{pool_name}_{start_time.timestamp()}_{end_time.timestamp()}"
        
        if key not in self.historical_data:
            trades = await self.pipeline.fetch_historical_data(
                pool_name, start_time, end_time
            )
            self.historical_data[key] = trades
            
        return self.historical_data[key]
        
    async def run_backtest(
        self,
        pool_name: str,
        start_time: datetime,
        end_time: datetime,
        strategy,
        initial_capital: Decimal,
        trade_size: Decimal
    ) -> Optional[BacktestResult]:
        """Führt Backtest durch"""
        try:
            # Lade Daten
            trades = await self.load_historical_data(
                pool_name, start_time, end_time
            )
            
            if not trades:
                logger.error("Keine historischen Daten verfügbar")
                return None
                
            # Initialisiere Tracking
            capital = initial_capital
            positions = []
            max_capital = initial_capital
            min_capital = initial_capital
            
            # Simuliere Trading
            for trade in trades:
                signal = strategy.generate_signal(trade)
                
                if signal:
                    # Simuliere Trade
                    fee = trade_size * Decimal(str(trade.fee_rate))
                    if signal == "buy":
                        capital -= trade_size + fee
                        positions.append(trade)
                    else:
                        capital += trade_size - fee
                        positions.append(trade)
                        
                    # Update Tracking
                    max_capital = max(max_capital, capital)
                    min_capital = min(min_capital, capital)
                    
            # Berechne Metriken
            roi = (capital - initial_capital) / initial_capital * 100
            max_drawdown = (max_capital - min_capital) / max_capital * 100
            
            winning_trades = sum(1 for p in positions if p.price > 0)
            
            return BacktestResult(
                total_trades=len(positions),
                winning_trades=winning_trades,
                losing_trades=len(positions) - winning_trades,
                roi=roi,
                max_drawdown=max_drawdown,
                sharpe_ratio=self._calculate_sharpe_ratio(positions),
                trades=positions
            )
            
        except Exception as e:
            logger.error(f"Fehler beim Backtest: {e}")
            return None
            
    def _calculate_sharpe_ratio(self, trades: List[TradeData]) -> float:
        """Berechnet Sharpe Ratio"""
        if not trades:
            return 0.0
            
        returns = []
        for i in range(1, len(trades)):
            ret = (trades[i].price - trades[i-1].price) / trades[i-1].price
            returns.append(ret)
            
        if not returns:
            return 0.0
            
        import numpy as np
        return float(np.mean(returns) / np.std(returns) * np.sqrt(252))
        
    async def close(self):
        """Schließt den Manager"""
        await self.pipeline.close()