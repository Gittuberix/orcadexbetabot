# Installation Script
Write-Host "🚀 Installiere Orca Trading Bot..." -ForegroundColor Cyan

# 1. Virtuelle Umgebung aktivieren
.\venv\Scripts\activate

# 2. Pakete installieren
Write-Host "`n📦 Installiere Pakete..." -ForegroundColor Green
pip install -r requirements.txt

# 3. Test starten
Write-Host "`n🧪 Starte Test..." -ForegroundColor Yellow
python src/test_orca_data.py