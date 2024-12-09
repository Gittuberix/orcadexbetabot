import asyncio
from typing import Optional
from datetime import datetime
import logging
from .config import BotConfig
from .interface import TradingInterface

class BotController:
    """Zentrale Steuerungsklasse für den Trading Bot"""
    def __init__(self, config: BotConfig, interface: TradingInterface):
        self.config = config
        self.interface = interface
        self.running = False
        self.paused = False
        self.last_trade_time: Optional[datetime] = None
        self.trades_today = 0
        
    def start(self):
        """Startet den Bot"""
        self.running = True
        self.paused = False
        logging.info("Bot gestartet")
        
    def stop(self):
        """Stoppt den Bot"""
        self.running = False
        logging.info("Bot gestoppt")
        
    def pause(self):
        """Pausiert den Bot"""
        self.paused = True
        logging.info("Bot pausiert")
        
    def resume(self):
        """Setzt den Bot fort"""
        self.paused = False
        logging.info("Bot fortgesetzt")
        
    def can_trade(self) -> bool:
        """Prüft, ob der Bot handeln darf"""
        if not self.running or self.paused:
            return False
            
        if self.trades_today >= self.config.max_trades_per_day:
            logging.warning("Maximale Anzahl Trades für heute erreicht")
            return False
            
        return True
        
    async def process_keyboard_input(self):
        """Verarbeitet Tastatureingaben zur Steuerung des Bots"""
        import keyboard
        
        # Tastenkombinationen registrieren
        keyboard.add_hotkey('ctrl+s', self.stop)
        keyboard.add_hotkey('ctrl+p', self.pause)
        keyboard.add_hotkey('ctrl+r', self.resume)
        keyboard.add_hotkey('ctrl+q', self.emergency_stop)
        
        while True:
            try:
                if keyboard.is_pressed('h'):
                    self.show_help()
                elif keyboard.is_pressed('i'):
                    self.show_info()
                    
                await asyncio.sleep(0.1)
            except Exception as e:
                logging.error(f"Fehler bei der Tastaturverarbeitung: {e}")
                
    def show_help(self):
        """Zeigt Hilfe-Informationen an"""
        help_text = """
        Tastenkombinationen:
        CTRL+S: Bot stoppen
        CTRL+P: Bot pausieren
        CTRL+R: Bot fortsetzen
        CTRL+Q: Notfall-Stop
        H: Diese Hilfe anzeigen
        I: Bot-Informationen anzeigen
        """
        self.interface.show_message(help_text)
        
    def show_info(self):
        """Zeigt Bot-Informationen an"""
        info = {
            'Status': 'Aktiv' if self.running else 'Gestoppt',
            'Pausiert': 'Ja' if self.paused else 'Nein',
            'Trades heute': self.trades_today,
            'Max Trades': self.config.max_trades_per_day,
            'Letzter Trade': self.last_trade_time.strftime('%H:%M:%S') if self.last_trade_time else 'Noch keine Trades'
        }
        self.interface.show_info(info)
        
    def emergency_stop(self):
        """Notfall-Stop des Bots"""
        self.stop()
        logging.warning("NOTFALL-STOP AUSGEFÜHRT!")
        self.interface.show_message("⚠️ NOTFALL-STOP AUSGEFÜHRT!", style="bold red")