from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Pool(Base):
    __tablename__ = 'pools'
    
    id = Column(Integer, primary_key=True)
    address = Column(String, unique=True)
    token_a = Column(String)
    token_b = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    prices = relationship("PoolPrice", back_populates="pool")
    
class PoolPrice(Base):
    __tablename__ = 'pool_prices'
    
    id = Column(Integer, primary_key=True)
    pool_id = Column(Integer, ForeignKey('pools.id'))
    price = Column(Float)
    liquidity = Column(Float)
    volume_24h = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    pool = relationship("Pool", back_populates="prices")

class Token(Base):
    __tablename__ = 'tokens'
    
    id = Column(Integer, primary_key=True)
    address = Column(String, unique=True)
    symbol = Column(String)
    decimals = Column(Integer)
    is_verified = Column(Integer, default=0) 