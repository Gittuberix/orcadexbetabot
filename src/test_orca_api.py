import asyncio
import aiohttp
from rich.console import Console

console = Console()

async def test_api_versions():
    """Testet verschiedene Orca API Versionen"""
    console.print("\n[cyan]Testing Orca API Versions...[/cyan]")
    
    # Test URLs
    urls = {
        "Base API": "https://api.orca.so",
        "Whirlpool v1": "https://api.orca.so/v1/whirlpool/list",
        "Whirlpool v2": "https://api.orca.so/v2/whirlpool/list",
        "Direct Pool v1": "https://api.orca.so/v1/whirlpool/7qbRF6YsyGuLUVs6Y1q64bdVrfe4ZcUUz1JRdoVNUJpi",
        "Direct Pool v2": "https://api.orca.so/v2/whirlpool/7qbRF6YsyGuLUVs6Y1q64bdVrfe4ZcUUz1JRdoVNUJpi"
    }
    
    async with aiohttp.ClientSession() as session:
        for name, url in urls.items():
            try:
                console.print(f"\nTesting {name}")
                console.print(f"URL: {url}")
                
                async with session.get(url) as response:
                    console.print(f"Status: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        console.print("[green]✓ Success[/green]")
                        console.print(f"Response sample: {str(data)[:200]}...")
                    else:
                        console.print(f"[red]× Failed: {response.status}[/red]")
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

if __name__ == "__main__":
    asyncio.run(test_api_versions()) 