import os
from pathlib import Path

def create_bot_files():
    print("🤖 Erstelle Bot-Dateien...")
    
    # Definiere die Dateien und deren Inhalte
    files = {
        "src/strategies/meme_sniper.py": meme_sniper_content,
        "src/monitor.py": monitor_content,
        "src/orca_data.py": orca_data_content,
        "src/performance.py": performance_content,
        "src/risk_manager.py": risk_manager_content
    }
    
    # Erstelle die Dateien
    for file_path, content in files.items():
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        print(f"✅ {file_path}")

if __name__ == "__main__":
    create_bot_files() 