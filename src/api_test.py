import asyncio
import aiohttp
import logging
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.progress import Progress

console = Console()

class OrcaAPITester:
    def __init__(self):
        # API Endpoints
        self.endpoints = {
            'mainnet': {
                'base': 'https://api.orca.so',
                'pools': '/v1/whirlpools',
                'price': '/v1/price'
            },
            'devnet': {
                'base': 'https://api.devnet.orca.so',
                'pools': '/v1/whirlpools',
                'price': '/v1/price'
            }
        }
        
    async def test_endpoints(self):
        """Testet alle API Endpoints"""
        console.print("\n[cyan]🌊 Testing Orca API Endpoints...[/cyan]")
        
        results = []
        async with aiohttp.ClientSession() as session:
            with Progress() as progress:
                task = progress.add_task("[cyan]Testing endpoints...", total=len(self.endpoints))
                
                for network, urls in self.endpoints.items():
                    progress.update(task, advance=1)
                    
                    # Base URL Test
                    base_result = await self._test_url(session, urls['base'])
                    results.append(('Base URL', network, base_result))
                    
                    # Pools Endpoint
                    pools_url = f"{urls['base']}{urls['pools']}"
                    pools_result = await self._test_url(session, pools_url)
                    results.append(('Pools', network, pools_result))
                    
                    # Price Endpoint
                    price_url = f"{urls['base']}{urls['price']}"
                    price_result = await self._test_url(session, price_url)
                    results.append(('Price', network, price_result))
                    
        self._print_results(results)
        
    async def _test_url(self, session: aiohttp.ClientSession, url: str) -> dict:
        """Testet einen einzelnen Endpoint"""
        try:
            start_time = datetime.now()
            async with session.get(url) as response:
                elapsed = (datetime.now() - start_time).total_seconds()
                
                return {
                    'status': response.status,
                    'latency': elapsed,
                    'success': response.status == 200,
                    'error': None if response.status == 200 else await response.text()
                }
        except Exception as e:
            return {
                'status': 0,
                'latency': 0,
                'success': False,
                'error': str(e)
            }
            
    def _print_results(self, results: list):
        """Gibt die Testergebnisse aus"""
        table = Table(title="🔍 API Test Results")
        
        table.add_column("Endpoint", style="cyan")
        table.add_column("Network", style="blue")
        table.add_column("Status", justify="center")
        table.add_column("Latency", justify="right")
        table.add_column("Error", style="red")
        
        for endpoint, network, result in results:
            status = "✅" if result['success'] else "❌"
            latency = f"{result['latency']:.3f}s" if result['success'] else "-"
            error = result['error'] if not result['success'] else ""
            
            table.add_row(
                endpoint,
                network,
                status,
                latency,
                str(error)[:50] + "..." if error and len(str(error)) > 50 else str(error)
            )
            
        console.print(table)

async def main():
    tester = OrcaAPITester()
    await tester.test_endpoints()

if __name__ == "__main__":
    asyncio.run(main()) 