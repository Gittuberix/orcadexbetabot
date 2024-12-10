import logging
from rich.logging import RichHandler
from pathlib import Path

def setup_logging():
    # Erstelle logs Verzeichnis
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Konfiguriere Logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            RichHandler(rich_tracebacks=True),
            logging.FileHandler(log_dir / "data_processing.log")
        ]
    )
    return logging.getLogger("orca_bot") 