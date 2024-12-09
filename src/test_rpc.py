import asyncio
from solana.rpc.async_api import AsyncClient
from rich.console import Console
from rich.table import Table
from datetime import datetime

async def test_solana_connection():
    console = Console()
    console.print("\n[cyan]🚀 Testing Solana RPC Connection...[/cyan]")
    
    try:
        # RPC Client initialisieren
        rpc = AsyncClient("https://api.mainnet-beta.solana.com")
        
        # Tests durchführen
        tests = Table(title="Solana RPC Tests")
        tests.add_column("Test", style="cyan")
        tests.add_column("Result", justify="center")
        tests.add_column("Details", style="green")
        
        # 1. Health Check
        health = await rpc.get_health()
        tests.add_row(
            "Health Check",
            "✅" if health.value == "ok" else "❌",
            f"Status: {health.value}"
        )
        
        # 2. Version Check
        version = await rpc.get_version()
        tests.add_row(
            "Version",
            "✅",
            f"Solana {version.solana_core}"
        )
        
        # 3. Slot Check
        slot = await rpc.get_slot()
        tests.add_row(
            "Current Slot",
            "✅",
            str(slot.value)
        )
        
        # 4. Block Time
        block_time = await rpc.get_block_time(slot.value)
        timestamp = datetime.fromtimestamp(block_time.value)
        tests.add_row(
            "Block Time",
            "✅",
            timestamp.strftime('%H:%M:%S')
        )
        
        # 5. Recent Performance
        performance = await rpc.get_recent_performance_samples()
        avg_tps = sum(p.num_transactions for p in performance.value) / len(performance.value)
        tests.add_row(
            "Avg TPS",
            "✅",
            f"{avg_tps:.0f} tx/s"
        )
        
        # Ergebnisse anzeigen
        console.print(tests)
        
        # Verbindung schließen
        await rpc.close()
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        
if __name__ == "__main__":
    asyncio.run(test_solana_connection()) 