import os
import logging
from pathlib import Path
import shutil
import sys

class BotSetup:
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.structure = {
            'src': {
                'strategies': ['__init__.py', 'meme_sniper.py'],
                'utils': ['__init__.py'],
                'files': [
                    '__init__.py',
                    'backtest.py',
                    'monitor.py',
                    'orca_data.py',
                    'performance.py',
                    'risk_manager.py',
                    'test_wallet.py',
                    'fee_calculator.py',
                    'transaction_handler.py'
                ]
            },
            'logs': {
                'trades': [],
                'errors': [],
                'performance': []
            },
            'data': {
                'historical': [],
                'cache': []
            },
            'config': ['config.yaml']
        }
        
    def setup(self):
        """Führt das komplette Setup durch"""
        try:
            print("🚀 Starting Solana Orca Bot Setup...")
            
            # Virtuelle Umgebung prüfen
            if not self._check_venv():
                print("❌ Bitte starten Sie das Setup in einer virtuellen Umgebung!")
                return False
                
            # Ordnerstruktur erstellen
            if not self._create_directories():
                return False
                
            # Logging einrichten
            if not self._setup_logging():
                return False
                
            # Konfiguration prüfen/erstellen
            if not self._setup_config():
                return False
                
            print("✅ Setup erfolgreich abgeschlossen!")
            return True
            
        except Exception as e:
            print(f"❌ Fehler beim Setup: {e}")
            return False
            
    def _check_venv(self) -> bool:
        """Prüft, ob das Skript in einer virtuellen Umgebung läuft"""
        return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
        
    def _create_directories(self) -> bool:
        """Erstellt die Projektstruktur"""
        try:
            print("\n📁 Erstelle Ordnerstruktur...")
            
            for main_dir, content in self.structure.items():
                main_path = self.root_dir / main_dir
                main_path.mkdir(exist_ok=True)
                
                if isinstance(content, dict):
                    # Verarbeite Unterordner und Dateien
                    for sub_dir, files in content.items():
                        if sub_dir == 'files':
                            # Hauptverzeichnis-Dateien
                            for file in files:
                                file_path = main_path / file
                                if not file_path.exists():
                                    file_path.touch()
                        else:
                            # Unterordner
                            sub_path = main_path / sub_dir
                            sub_path.mkdir(exist_ok=True)
                            
                            for file in files:
                                file_path = sub_path / file
                                if not file_path.exists():
                                    file_path.touch()
                else:
                    # Verarbeite Dateien im Hauptverzeichnis
                    for file in content:
                        file_path = main_path / file
                        if not file_path.exists():
                            file_path.touch()
                            
            print("✅ Ordnerstruktur erstellt")
            return True
            
        except Exception as e:
            print(f"❌ Fehler beim Erstellen der Ordnerstruktur: {e}")
            return False
            
    def _setup_logging(self) -> bool:
        """Richtet das Logging-System ein"""
        try:
            print("\n📝 Konfiguriere Logging...")
            
            log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            
            # Hauptlogger
            logging.basicConfig(
                level=logging.INFO,
                format=log_format,
                handlers=[
                    logging.FileHandler(self.root_dir / 'logs/bot.log'),
                    logging.StreamHandler()
                ]
            )
            
            # Spezifische Logger
            for log_type in ['trades', 'errors', 'performance']:
                logger = logging.getLogger(log_type)
                handler = logging.FileHandler(
                    self.root_dir / f'logs/{log_type}/{log_type}.log'
                )
                handler.setFormatter(logging.Formatter(log_format))
                logger.addHandler(handler)
                logger.setLevel(logging.INFO)
                
            print("✅ Logging konfiguriert")
            return True
            
        except Exception as e:
            print(f"❌ Fehler beim Setup des Logging-Systems: {e}")
            return False
            
    def _setup_config(self) -> bool:
        """Erstellt/Prüft die Konfigurationsdatei"""
        try:
            print("\n⚙️ Prüfe Konfiguration...")
            
            config_path = self.root_dir / 'config/config.yaml'
            if not config_path.exists():
                # Kopiere Standard-Config
                default_config = self.root_dir / 'src/config_template.yaml'
                if default_config.exists():
                    shutil.copy(default_config, config_path)
                    print("✅ Standard-Konfiguration kopiert")
                else:
                    print("⚠️ Keine Standard-Konfiguration gefunden")
                    config_path.touch()
            else:
                print("✅ Konfigurationsdatei existiert bereits")
                
            return True
            
        except Exception as e:
            print(f"❌ Fehler beim Setup der Konfiguration: {e}")
            return False
            
    def verify(self) -> dict:
        """Überprüft die Installation"""
        status = {
            'venv': self._check_venv(),
            'directories': {},
            'files': {},
            'logging': {},
            'missing': []
        }
        
        # Detaillierte Prüfung hier implementieren...
        return status

def main():
    setup = BotSetup()
    if setup.setup():
        print("\n🎉 Bot ist bereit für den Start!")
        print("\nFühren Sie als nächstes aus:")
        print("1. pip install -e .")
        print("2. python src/backtest.py")
    else:
        print("\n❌ Setup fehlgeschlagen. Bitte Fehler beheben und erneut versuchen.")

if __name__ == "__main__":
    main() 