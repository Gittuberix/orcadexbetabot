import asyncio
from rich.console import Console
from data.token_fetcher import OrcaTokenFetcher
from debug_orca_connection import debug_orca_connections

console = Console()

async def test_orca_integration():
    """Testet vollständige Orca Integration"""
    console.print("\n[bold cyan]Testing Orca DEX Integration[/bold cyan]")
    
    # 1. Verbindungen testen
    console.print("\n[yellow]Step 1: Testing Connections...[/yellow]")
    await debug_orca_connections()
    
    # 2. Token Fetching testen
    console.print("\n[yellow]Step 2: Testing Token Fetching...[/yellow]")
    fetcher = OrcaTokenFetcher()
    tokens = await fetcher.fetch_all_tokens()
    
    if tokens:
        console.print(f"[green]✓ Successfully fetched {len(tokens)} tokens[/green]")
        
        # Top 10 Token Details
        console.print("\n[cyan]Top 10 Tokens:[/cyan]")
        for i, token in enumerate(tokens[:10], 1):
            console.print(f"{i}. {token['symbol']} ({token['address'][:8]}...)")
            
            # Pool Details für jeden Token
            pools = await fetcher.get_token_pools(token['address'])
            if pools:
                console.print(f"   Found {len(pools)} pools")
                # Details des liquidesten Pools
                top_pool = max(pools, key=lambda x: float(x.get('liquidity', 0)))
                console.print(f"   Top Pool: {top_pool['address'][:8]}...")
                console.print(f"   Liquidity: ${float(top_pool.get('liquidity', 0)):,.2f}")
                console.print(f"   Volume 24h: ${float(top_pool.get('volume24h', 0)):,.2f}")
    else:
        console.print("[red]× Failed to fetch tokens[/red]")
        
    # 3. Preisdaten testen
    if tokens:
        console.print("\n[yellow]Step 3: Testing Price Data...[/yellow]")
        top_token = tokens[0]
        top_pools = await fetcher.get_token_pools(top_token['address'])
        
        if top_pools:
            top_pool = top_pools[0]
            console.print(f"\nTesting price data for {top_token['symbol']}")
            
            # Historische Daten
            async with aiohttp.ClientSession() as session:
                url = f"{fetcher.base_url}/v1/pool/{top_pool['address']}/candles"
                params = {
                    'resolution': '1m',
                    'limit': 60  # Letzte Stunde
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        console.print(f"[green]✓ Got {len(data)} price points[/green]")
                        
                        # Beispiel-Daten zeigen
                        if data:
                            latest = data[-1]
                            console.print(f"Latest price: ${float(latest['close']):,.4f}")
                            console.print(f"Volume: ${float(latest['volume']):,.2f}")
                    else:
                        console.print("[red]× Failed to get price data[/red]")

if __name__ == "__main__":
    asyncio.run(test_orca_integration()) 