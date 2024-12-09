import os
from pathlib import Path

def create_project_structure():
    """Erstellt Projektstruktur"""
    folders = [
        'src/backtest',
        'src/strategies',
        'src/utils',
        'src/data',
        'logs',
        'results'
    ]
    
    for folder in folders:
        Path(folder).mkdir(parents=True, exist_ok=True)
        
    # __init__.py Files erstellen
    init_files = [
        'src/__init__.py',
        'src/backtest/__init__.py',
        'src/strategies/__init__.py',
        'src/utils/__init__.py',
        'src/data/__init__.py'
    ]
    
    for init_file in init_files:
        Path(init_file).touch(exist_ok=True)

if __name__ == "__main__":
    create_project_structure() 