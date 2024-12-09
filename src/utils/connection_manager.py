from typing import Dict, Optional
import aiohttp
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ConnectionType(Enum):
    ORCA_API = "orca_api"
    ORCA_RPC = "orca_rpc"
    SERUM_RPC = "serum_rpc"
    JUPITER_API = "jupiter_api"

@dataclass
class ConnectionConfig:
    url: str
    timeout: int = 30
    max_retries: int = 3
    retry_delay: int = 1

class ConnectionFactory:
    """Factory für verschiedene API/RPC Verbindungen"""
    
    @staticmethod
    def create_connection(conn_type: ConnectionType, config: ConnectionConfig) -> 'BaseConnection':
        if conn_type == ConnectionType.ORCA_API:
            return OrcaApiConnection(config)
        elif conn_type == ConnectionType.ORCA_RPC:
            return OrcaRpcConnection(config)
        elif conn_type == ConnectionType.SERUM_RPC:
            return SerumRpcConnection(config)
        else:
            raise ValueError(f"Unknown connection type: {conn_type}")

class BaseConnection(ABC):
    """Basis-Klasse für alle Verbindungen"""
    
    def __init__(self, config: ConnectionConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.healthy = False
        
    async def connect(self) -> bool:
        """Verbindung aufbauen"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout)
                )
            self.healthy = await self.health_check()
            return self.healthy
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False
            
    @abstractmethod
    async def health_check(self) -> bool:
        """Health Check implementieren"""
        pass
        
    async def close(self):
        """Verbindung sauber schließen"""
        if self.session:
            await self.session.close()
            self.session = None
            self.healthy = False

class ConnectionPool:
    """Verwaltet mehrere Verbindungen"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
        
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.connections: Dict[str, BaseConnection] = {}
            self.initialized = True
            
    async def get_connection(self, conn_type: ConnectionType) -> BaseConnection:
        """Holt oder erstellt Verbindung"""
        if conn_type.value not in self.connections:
            config = self._get_config(conn_type)
            connection = ConnectionFactory.create_connection(conn_type, config)
            await connection.connect()
            self.connections[conn_type.value] = connection
        return self.connections[conn_type.value]
        
    def _get_config(self, conn_type: ConnectionType) -> ConnectionConfig:
        """Lädt Konfiguration für Verbindungstyp"""
        configs = {
            ConnectionType.ORCA_API: ConnectionConfig(
                url="https://api.orca.so",
                timeout=30,
                max_retries=3
            ),
            ConnectionType.ORCA_RPC: ConnectionConfig(
                url="https://api.mainnet.orca.so/v1/rpc",
                timeout=60,
                max_retries=5
            ),
            ConnectionType.SERUM_RPC: ConnectionConfig(
                url="https://solana-api.projectserum.com",
                timeout=30,
                max_retries=3
            )
        }
        return configs[conn_type]

class OrcaApiConnection(BaseConnection):
    """Orca API Verbindung"""
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1))
    async def health_check(self) -> bool:
        try:
            async with self.session.get(f"{self.config.url}/v1/health") as response:
                return response.status == 200
        except Exception:
            return False
            
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1))
    async def get_pools(self) -> list:
        """Holt Pools mit Retry"""
        if not self.healthy:
            await self.connect()
            
        async with self.session.get(f"{self.config.url}/v1/whirlpools") as response:
            if response.status == 200:
                return await response.json()
            raise Exception(f"Failed to get pools: {response.status}") 