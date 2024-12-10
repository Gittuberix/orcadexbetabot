import aiosqlite
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_url: str = "sqlite+aiosqlite:///data/orca_pools.db"):
        self.engine = create_async_engine(db_url, echo=True)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        
    async def init_db(self):
        """Initialisiert die Datenbank"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
    async def save_pool(self, pool_data: Dict):
        """Speichert Pool-Daten"""
        async with self.async_session() as session:
            try:
                pool = Pool(
                    address=pool_data['address'],
                    token_a=pool_data['tokenA'],
                    token_b=pool_data['tokenB']
                )
                session.add(pool)
                await session.commit()
                
                # Speichere aktuellen Preis
                price = PoolPrice(
                    pool_id=pool.id,
                    price=float(pool_data.get('price', 0)),
                    liquidity=float(pool_data.get('liquidity', 0)),
                    volume_24h=float(pool_data.get('volume24h', 0))
                )
                session.add(price)
                await session.commit()
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Fehler beim Speichern des Pools: {e}")
                
    async def get_active_pools(self) -> List[Dict]:
        """Holt aktive Pools mit den neuesten Preisen"""
        async with self.async_session() as session:
            result = await session.execute(
                select(Pool, PoolPrice)
                .join(PoolPrice)
                .order_by(PoolPrice.timestamp.desc())
            )
            return [
                {
                    'address': pool.address,
                    'token_a': pool.token_a,
                    'token_b': pool.token_b,
                    'price': price.price,
                    'liquidity': price.liquidity,
                    'volume_24h': price.volume_24h,
                    'timestamp': price.timestamp
                }
                for pool, price in result
            ] 