from config.connections import ENVIRONMENTS, API_HEADERS
from colorama import init, Fore, Style
import requests
import time
import asyncio
import aiohttp

init()

class ConnectionManager:
    def __init__(self, env='mainnet'):
        print(f"{Fore.CYAN}Initializing Connection Manager...{Style.RESET_ALL}")
        self.config = ENVIRONMENTS[env]
        self.endpoints = self.config['endpoints']
        self.rpcs = self.config['rpcs']
        self.headers = API_HEADERS
        self.active_rpc = self.get_best_rpc()
        self.rpc_endpoints = [
            "https://api.mainnet-beta.solana.com",
            "https://solana-api.projectserum.com"
        ]

    def get_best_rpc(self):
        """Find fastest RPC endpoint"""
        print(f"\n{Fore.YELLOW}Testing RPC endpoints...{Style.RESET_ALL}")
        
        best_rpc = None
        best_time = float('inf')
        
        for rpc in self.rpcs:
            try:
                start = time.time()
                response = requests.post(
                    rpc,
                    json={"jsonrpc": "2.0", "id": 1, "method": "getHealth"},
                    headers=self.headers,
                    timeout=5
                )
                elapsed = time.time() - start
                
                if response.status_code == 200:
                    print(f"{Fore.GREEN}✓ {rpc}: {elapsed:.2f}s{Style.RESET_ALL}")
                    if elapsed < best_time:
                        best_time = elapsed
                        best_rpc = rpc
            except Exception as e:
                print(f"{Fore.RED}✗ {rpc}: {str(e)}{Style.RESET_ALL}")
        
        return best_rpc

    def get_pool_data(self, pool_id):
        """Get Whirlpool data"""
        try:
            url = f"{self.endpoints['whirlpool']}/{pool_id}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                return response.json()
                
        except Exception as e:
            print(f"{Fore.RED}Pool data error: {str(e)}{Style.RESET_ALL}")
            
        return None

    async def smart_rpc_routing(self):
        while True:
            # Latenz-Monitoring
            latencies = {}
            for endpoint in self.rpc_endpoints:
                latency = await self._measure_latency(endpoint)
                latencies[endpoint] = latency
                
            # Automatisches Failover
            sorted_endpoints = sorted(latencies.items(), key=lambda x: x[1])
            self.active_rpc = sorted_endpoints[0][0]
            
            # Load Balancing
            self.endpoint_weights = self._calculate_weights(latencies)
            
            await asyncio.sleep(60)

    async def optimize_batch_requests(self):
        # Request Batching
        self.request_queue = asyncio.Queue()
        self.batch_size = 20
        self.batch_timeout = 0.1  # 100ms
        
        while True:
            batch = []
            try:
                while len(batch) < self.batch_size:
                    request = await asyncio.wait_for(
                        self.request_queue.get(),
                        timeout=self.batch_timeout
                    )
                    batch.append(request)
            except asyncio.TimeoutError:
                pass
                
            if batch:
                await self._execute_batch(batch)

    async def _measure_latency(self, endpoint):
        start = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(endpoint) as response:
                    await response.text()
                    return time.time() - start
        except:
            return float('inf')

    def _calculate_weights(self, latencies):
        total = sum(1/l for l in latencies.values())
        return {ep: (1/lat)/total for ep, lat in latencies.items()}

    async def _execute_batch(self, batch):
        async with aiohttp.ClientSession() as session:
            tasks = [self._execute_request(session, req) for req in batch]
            return await asyncio.gather(*tasks)