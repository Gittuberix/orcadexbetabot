import asyncio
import logging
from rich.console import Console
from pathlib import Path
import os

# Erstelle notwendige Verzeichnisse
os.makedirs('logs/errors', exist_ok=True)

console = Console()

async def start_bot():
    try:
        from data.orca_pipeline import OrcaPipeline
        from trading_manager import TradingManager
        from risk_manager import RiskManager
        
        console.print("\n[bold cyan]🚀 Starting Orca DEX Bot[/bold cyan]")
        
        # Initialisiere Komponenten
        pipeline = OrcaPipeline()
        trading_manager = TradingManager()
        risk_manager = RiskManager()
        
        # Starte Pipeline
        pipeline_task = asyncio.create_task(pipeline.start_pipeline())
        
        # Starte Trading
        trading_task = asyncio.create_task(trading_manager.optimize_execution({}))
        
        # Starte Risk Management
        risk_task = asyncio.create_task(risk_manager.dynamic_risk_adjustment())
        
        # Warte auf alle Tasks
        await asyncio.gather(
            pipeline_task,
            trading_task,
            risk_task
        )
        
    except Exception as e:
        console.print(f"\n[red]Fatal error: {str(e)}[/red]")
        logging.exception("Fatal error occurred")

if __name__ == "__main__":
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        console.print("\n[yellow]Bot stopped by user[/yellow]") 