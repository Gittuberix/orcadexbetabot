import logging
from typing import Dict, Optional
from decimal import Decimal
from rich.console import Console

console = Console()
logger = logging.getLogger(__name__)

class DataValidator:
    @staticmethod
    def validate_pool_data(data: Dict) -> bool:
        """Validiert Pool-Daten"""
        required_fields = [
            'price', 'liquidity', 'fee_rate', 'tick_spacing', 
            'tick_current', 'token_a', 'token_b'
        ]
        
        try:
            # Prüfe ob alle Felder existieren
            for field in required_fields:
                if field not in data:
                    logger.error(f"Fehlendes Feld: {field}")
                    return False
                    
            # Validiere Werte
            if data['price'] <= 0:
                logger.error(f"Ungültiger Preis: {data['price']}")
                return False
                
            if data['liquidity'] <= 0:
                logger.error(f"Ungültige Liquidität: {data['liquidity']}")
                return False
                
            if data['fee_rate'] < 0 or data['fee_rate'] > 1000000:  # Max 100%
                logger.error(f"Ungültige Fee Rate: {data['fee_rate']}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Fehler bei Pool-Daten Validierung: {e}")
            return False
            
    @staticmethod
    def validate_trade_data(data: Dict) -> bool:
        """Validiert Trade-Daten"""
        required_fields = [
            'timestamp', 'side', 'amount_in', 'amount_out',
            'price', 'fee', 'slippage'
        ]
        
        try:
            # Prüfe ob alle Felder existieren
            for field in required_fields:
                if field not in data:
                    logger.error(f"Fehlendes Feld: {field}")
                    return False
                    
            # Validiere Werte
            if data['amount_in'] <= 0:
                logger.error(f"Ungültiger Input Amount: {data['amount_in']}")
                return False
                
            if data['amount_out'] <= 0:
                logger.error(f"Ungültiger Output Amount: {data['amount_out']}")
                return False
                
            if data['price'] <= 0:
                logger.error(f"Ungültiger Preis: {data['price']}")
                return False
                
            if data['fee'] < 0:
                logger.error(f"Ungültige Fee: {data['fee']}")
                return False
                
            if not 0 <= float(data['slippage']) <= 1:
                logger.error(f"Ungültiger Slippage: {data['slippage']}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Fehler bei Trade-Daten Validierung: {e}")
            return False 