import asyncio
import sys
from pathlib import Path
from rich.console import Console
from src.trading.trading_engine import TradingEngine
from src.config.trading_config import TradingConfig
from src.data.orca_pipeline import OrcaPipeline
from src.strategies.meme_strategy import MemeStrategy

console = Console()

async def main():
    try:
        # Initialize components
        config = TradingConfig()
        pipeline = OrcaPipeline()
        strategy = MemeStrategy()
        engine = TradingEngine(config)
        
        # Start pipeline
        console.print("[cyan]Starting Orca pipeline...[/cyan]")
        await pipeline.start_pipeline()
        
        # Initialize trading engine
        console.print("[cyan]Initializing trading engine...[/cyan]")
        await engine.initialize(pipeline)
        
        # Start strategy
        console.print("[cyan]Starting trading strategy...[/cyan]")
        await strategy.start(engine)
        
        # Keep running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down...[/yellow]")
        await engine.shutdown()
        await pipeline.shutdown()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 