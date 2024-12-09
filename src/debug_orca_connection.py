import asyncio
import aiohttp
from rich.console import Console
from solana.rpc.async_api import AsyncClient
from datetime import datetime
from config.config import load_config

console = Console()

async def debug_orca_connections():
    """Debug Orca API und RPC Verbindungen"""
    try:
        config = load_config()
        console.print("\n[cyan]Debugging Orca Connections...[/cyan]")
        
        # Korrekte Orca Endpoints
        endpoints = {
            "Orca API": f"{config['network']['orca_api']}",
            "Whirlpool List": f"{config['network']['orca_api']}/whirlpool/list",
            "SOL-USDC Pool": f"{config['network']['orca_api']}/whirlpool/7qbRF6YsyGuLUVs6Y1q64bdVrfe4ZcUUz1JRdoVNUJpi"
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                # 1. Test Base API
                console.print("\n[yellow]Testing Base API...[/yellow]")
                async with session.get(endpoints["Orca API"]) as response:
                    console.print(f"Status: {response.status}")
                    if response.status == 200:
                        console.print("[green]✓ Base API working[/green]")
                    else:
                        console.print("[red]× Base API failed[/red]")
                
                # 2. Test Whirlpool List
                console.print("\n[yellow]Testing Whirlpool List...[/yellow]")
                async with session.get(endpoints["Whirlpool List"]) as response:
                    console.print(f"Status: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        pools = data.get('whirlpools', [])
                        console.print(f"[green]✓ Found {len(pools)} whirlpools[/green]")
                        if pools:
                            pool = pools[0]
                            console.print("\nSample Pool Data:")
                            console.print(f"Address: {pool.get('address')}")
                            console.print(f"Token A: {pool.get('tokenA', {}).get('symbol')}")
                            console.print(f"Token B: {pool.get('tokenB', {}).get('symbol')}")
                    else:
                        console.print("[red]× Whirlpool List failed[/red]")
                
                # 3. Test SOL-USDC Pool
                console.print("\n[yellow]Testing SOL-USDC Pool...[/yellow]")
                async with session.get(endpoints["SOL-USDC Pool"]) as response:
                    console.print(f"Status: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        console.print("[green]✓ Pool data retrieved[/green]")
                        console.print(f"Price: ${float(data.get('price', 0)):,.4f}")
                        console.print(f"Volume: ${float(data.get('volume24h', 0)):,.2f}")
                    else:
                        console.print("[red]× Pool data failed[/red]")
                
                # 4. Test RPC Connection
                console.print("\n[yellow]Testing RPC Connections...[/yellow]")
                
                # Main RPC
                rpc = AsyncClient(config['network']['rpc_url'])
                try:
                    response = await rpc.get_health()
                    if response.value == "ok":
                        console.print("[green]✓ Main RPC working[/green]")
                    else:
                        console.print("[red]× Main RPC failed[/red]")
                except Exception as e:
                    console.print(f"[red]Main RPC error: {e}[/red]")
                
                # Backup RPC
                backup_rpc = AsyncClient(config['network']['backup_rpc'])
                try:
                    response = await backup_rpc.get_health()
                    if response.value == "ok":
                        console.print("[green]✓ Backup RPC working[/green]")
                    else:
                        console.print("[red]× Backup RPC failed[/red]")
                except Exception as e:
                    console.print(f"[red]Backup RPC error: {e}[/red]")
                    
            except Exception as e:
                console.print(f"[red]Session error: {e}[/red]")
                
    except Exception as e:
        console.print(f"[red]Connection error: {e}[/red]")
        
    finally:
        console.print("\n[cyan]Debug complete[/cyan]")

if __name__ == "__main__":
    try:
        asyncio.run(debug_orca_connections())
    except KeyboardInterrupt:
        console.print("\n[yellow]Debug stopped by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]") 