import asyncio
from pathlib import Path
from config.config import save_config
from rich.console import Console

console = Console()

def setup_project():
    """Initialisiert Projektstruktur"""
    try:
        # Verzeichnisse erstellen
        directories = [
            'src/config',
            'src/strategies',
            'src/data',
            'src/wallet',
            'src/trading',
            'src/ui'
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            Path(f"{directory}/__init__.py").touch(exist_ok=True)
            
        # Konfiguration speichern
        save_config()
        
        console.print("[green]✓ Project setup complete[/green]")
        return True
        
    except Exception as e:
        console.print(f"[red]Setup failed: {e}[/red]")
        return False

async def test_connections():
    """Testet alle Verbindungen"""
    from debug_orca_connection import debug_orca_connections
    await debug_orca_connections()

if __name__ == "__main__":
    if setup_project():
        asyncio.run(test_connections()) 