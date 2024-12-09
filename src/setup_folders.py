import os

def create_folder_structure():
    folders = [
        'logs',
        'config',
        'src/utils',
        'src/strategies',
        'data/historical'
    ]
    
    for folder in folders:
        os.makedirs(folder, exist_ok=True) 