import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.data.orca_pipeline import OrcaWhirlpoolPipeline as BasePipeline

class OrcaWhirlpoolPipeline(BasePipeline):
    """Erweiterte Pipeline für Backtest-Funktionalität"""
    
    async def get_historical_prices(self, pool_address: str, start_time, end_time):
        """Holt historische Preise für einen Pool"""
        pool_data = await self.get_pool_data(pool_address)
        if not pool_data:
            return None
            
        return {
            'address': pool_address,
            'token_a_symbol': pool_data['token_a_symbol'],
            'token_b_symbol': pool_data['token_b_symbol'],
            'initial_price': pool_data['price'],
            'initial_liquidity': pool_data['liquidity']
        } 