import logging
from rich.logging import RichHandler
import sys

def setup_logger():
    # Root Logger
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            RichHandler(rich_tracebacks=True),
            logging.FileHandler("logs/debug.log")
        ]
    )
    return logging.getLogger("orca_bot") 