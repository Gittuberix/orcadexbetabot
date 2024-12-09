import logging
import asyncio
from typing import Dict
from datetime import datetime
from orca_data import OrcaDataProvider

class TokenTracker:
    def __init__(self):
        self.top_tokens = {}
        self.orca_pools = {}
        self.last_update = None
        
    async def start_tracking(self):
        """Startet das Token Tracking"""
        logging.info("Starting token tracking...")
        
        while True:
            try:
                await self._update_token_data()
                await asyncio.sleep(60)  # Update alle 60 Sekunden
                
            except Exception as e:
                logging.error(f"Tracking error: {e}")
                await asyncio.sleep(5)
                
    async def _update_token_data(self):
        """Aktualisiert Token Daten"""
        self.last_update = datetime.now()
        # Implementierung folgt