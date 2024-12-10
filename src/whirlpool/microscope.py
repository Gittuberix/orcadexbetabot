import asyncio
import logging
import json
import base64
from typing import Dict, List, Optional
from pathlib import Path
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient
from orca_whirlpool.context import WhirlpoolContext
from orca_whirlpool.constants import ORCA_WHIRLPOOL_PROGRAM_ID
from orca_whirlpool.utils import PriceMath, DecimalUtil, PoolUtil
from rich.console import Console
from datetime import datetime
from src.config.network_config import WHIRLPOOL_CONFIGS

logger = logging.getLogger(__name__)
console = Console()

class WhirlpoolMicroscope:
    """Account Microscope für Orca Whirlpools"""
    
    def __init__(self):
        self.connection = AsyncClient("https://api.mainnet-beta.solana.com")
        self.ctx = WhirlpoolContext(ORCA_WHIRLPOOL_PROGRAM_ID, self.connection, None)
        
        # Alle wichtigen Orca Whirlpools
        self.pools = WHIRLPOOL_CONFIGS
        self.historical_data = {}
        
    async def dump_account(self, pubkey: str, filename: Optional[str] = None) -> Dict:
        """Speichert Account-Daten als JSON"""
        try:
            account = await self.connection.get_account_info(
                Pubkey.from_string(pubkey),
                encoding="base64"
            )
            
            if not account or not account.value:
                raise ValueError(f"Account {pubkey} nicht gefunden")
                
            # Parse Account-Daten
            data = {
                'pubkey': pubkey,
                'lamports': account.value.lamports,
                'owner': str(account.value.owner),
                'executable': account.value.executable,
                'rent_epoch': account.value.rent_epoch,
                'data': account.value.data[0],  # base64 encoded data
                'data_hex': base64.b64decode(account.value.data[0]).hex()
            }
            
            # Speichere als JSON
            if filename:
                output_path = self.data_dir / filename
                with open(output_path, 'w') as f:
                    json.dump(data, f, indent=2)
                console.print(f"[green]Account-Daten gespeichert in {output_path}[/green]")
                
            return data
            
        except Exception as e:
            logger.error(f"Fehler beim Dumpen von Account {pubkey}: {e}")
            return {}
            
    async def clone_whirlpool(self, pool_address: str, output_dir: Optional[str] = None) -> bool:
        """Klont einen Whirlpool für LocalValidator"""
        try:
            # Erstelle Output-Verzeichnis
            output_path = Path(output_dir) if output_dir else self.data_dir / "cloned_pools"
            output_path.mkdir(parents=True, exist_ok=True)
            
            # 1. Hole Whirlpool Account
            whirlpool = await self.ctx.fetcher.get_whirlpool(
                Pubkey.from_string(pool_address)
            )
            
            # 2. Hole Token Accounts
            token_a = await self.ctx.fetcher.get_token_mint(whirlpool.token_mint_a)
            token_b = await self.ctx.fetcher.get_token_mint(whirlpool.token_mint_b)
            
            # 3. Hole Tick Arrays
            tick_arrays = await self.ctx.fetcher.find_tick_arrays_by_whirlpool(
                ORCA_WHIRLPOOL_PROGRAM_ID,
                Pubkey.from_string(pool_address)
            )
            
            # 4. Hole Positionen
            positions = await self.get_all_positions(pool_address)
            
            # 5. Speichere alle Accounts
            accounts_data = {
                'whirlpool': await self.dump_account(pool_address),
                'token_a': await self.dump_account(str(whirlpool.token_mint_a)),
                'token_b': await self.dump_account(str(whirlpool.token_mint_b)),
                'tick_arrays': [
                    await self.dump_account(str(ta.pubkey))
                    for ta in tick_arrays
                ],
                'positions': [
                    await self.dump_account(pos['address'])
                    for pos in positions
                ]
            }
            
            # Speichere Konfiguration
            config = {
                'address': pool_address,
                'token_a': str(whirlpool.token_mint_a),
                'token_b': str(whirlpool.token_mint_b),
                'tick_spacing': whirlpool.tick_spacing,
                'fee_rate': whirlpool.fee_rate
            }
            
            # Speichere alles
            with open(output_path / f"whirlpool_{pool_address}.json", 'w') as f:
                json.dump({
                    'config': config,
                    'accounts': accounts_data
                }, f, indent=2)
                
            console.print(f"[green]Whirlpool {pool_address} erfolgreich geklont![/green]")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Klonen von Whirlpool {pool_address}: {e}")
            return False
            
    async def get_whirlpool_data(self, pool_address: str) -> Optional[Dict]:
        """Holt detaillierte Pool-Daten"""
        try:
            whirlpool = await self.ctx.fetcher.get_whirlpool(
                Pubkey.from_string(pool_address)
            )
            
            token_a = await self.ctx.fetcher.get_token_mint(whirlpool.token_mint_a)
            token_b = await self.ctx.fetcher.get_token_mint(whirlpool.token_mint_b)
            
            price = PriceMath.sqrt_price_x64_to_price(
                whirlpool.sqrt_price,
                token_a.decimals,
                token_b.decimals
            )
            
            return {
                'address': pool_address,
                'token_a': str(whirlpool.token_mint_a),
                'token_b': str(whirlpool.token_mint_b),
                'price': float(DecimalUtil.to_fixed(price, token_b.decimals)),
                'liquidity': whirlpool.liquidity,
                'fee_rate': whirlpool.fee_rate,
                'tick_spacing': whirlpool.tick_spacing,
                'tick_current': whirlpool.tick_current_index,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Fehler beim Microscoping von Pool {pool_address}: {e}")
            return None
            
    async def get_historical_pool_data(self, 
        pool_address: str, 
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict]:
        """Holt historische Pool-Daten"""
        try:
            # Hole historische Daten von Orca API
            historical_data = await self.ctx.fetcher.get_historical_pool_data(
                Pubkey.from_string(pool_address),
                start_time,
                end_time
            )
            
            return historical_data
            
        except Exception as e:
            logger.error(f"Fehler beim Abrufen historischer Daten: {e}")
            return []
            
    async def get_historical_gas_price(self, timestamp: datetime) -> Optional[int]:
        """Holt historische Gas-Preise"""
        try:
            # Typische Gas-Kosten für Orca Swaps: ~0.000005 SOL
            return 5000  # 0.000005 SOL in Lamports
            
        except Exception as e:
            logger.error(f"Fehler beim Abrufen historischer Gas-Preise: {e}")
            return None
            
    async def get_position_data(self, position_address: str) -> Optional[Dict]:
        """Holt Position Details"""
        try:
            position = await self.ctx.fetcher.get_position(
                Pubkey.from_string(position_address)
            )
            
            return {
                'address': position_address,
                'whirlpool': str(position.whirlpool),
                'liquidity': position.liquidity,
                'tick_lower_index': position.tick_lower_index,
                'tick_upper_index': position.tick_upper_index,
                'fee_growth_checkpoint_a': position.fee_growth_checkpoint_a,
                'fee_growth_checkpoint_b': position.fee_growth_checkpoint_b,
                'fee_owed_a': position.fee_owed_a,
                'fee_owed_b': position.fee_owed_b
            }
            
        except Exception as e:
            logger.error(f"Fehler beim Microscoping von Position {position_address}: {e}")
            return None
            
    async def get_all_positions(self, pool_address: str) -> List[Dict]:
        """Holt alle Positionen eines Pools mit Details"""
        try:
            positions = await self.ctx.fetcher.find_positions_by_whirlpool(
                ORCA_WHIRLPOOL_PROGRAM_ID,
                Pubkey.from_string(pool_address)
            )
            
            position_data = []
            for pos in positions:
                data = await self.get_position_data(str(pos.pubkey))
                if data:
                    # Hole zusätzliche Token Account Infos
                    token_a_account = await self.ctx.fetcher.get_token_account(
                        Pubkey.from_string(data['token_a']),
                        Pubkey.from_string(data['owner'])
                    )
                    token_b_account = await self.ctx.fetcher.get_token_account(
                        Pubkey.from_string(data['token_b']),
                        Pubkey.from_string(data['owner'])
                    )
                    
                    data.update({
                        'token_a_balance': token_a_account.amount if token_a_account else 0,
                        'token_b_balance': token_b_account.amount if token_b_account else 0
                    })
                    
                    position_data.append(data)
                    
            return position_data
            
        except Exception as e:
            logger.error(f"Fehler beim Laden der Positionen für Pool {pool_address}: {e}")
            return []
            
    async def create_test_tokens(self, mint_address: str, amount: int) -> bool:
        """Erstellt Test-Token für LocalValidator"""
        try:
            # Hole Token Mint Account
            mint_data = await self.dump_account(
                mint_address,
                f"token_mint_{mint_address}.json"
            )
            
            # Erstelle Token Account mit Guthaben
            token_account = {
                'mint': mint_address,
                'owner': str(self.ctx.wallet.pubkey),
                'amount': amount,
                'delegate': None,
                'delegated_amount': 0,
                'close_authority': None
            }
            
            # Speichere für LocalValidator
            with open(self.data_dir / f"token_account_{mint_address}.json", 'w') as f:
                json.dump(token_account, f, indent=2)
                
            console.print(f"[green]Test-Token {mint_address} erstellt![/green]")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Erstellen von Test-Token {mint_address}: {e}")
            return False
