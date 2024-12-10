import logging
import time
from datetime import datetime
from rich.console import Console
from rich.table import Table
from typing import Dict, List
import asyncio
import traceback

console = Console()

class OrcaDebugManager:
    def __init__(self):
        self.pipeline_health = {}
        self.error_counts = {}
        self.latency_metrics = {}
        self.warning_thresholds = {
            'data_delay': 2.0,  # seconds
            'price_deviation': 0.05,  # 5%
            'error_rate': 5,  # errors per minute
            'memory_usage': 0.8  # 80% threshold
        }
        self.setup_logging()

    def setup_logging(self):
        """Konfiguriert spezielles Logging für Orca DEX"""
        self.logger = logging.getLogger('orca_dex')
        self.logger.setLevel(logging.DEBUG)
        
        # File Handler für detaillierte Logs
        fh = logging.FileHandler('logs/orca_dex_debug.log')
        fh.setLevel(logging.DEBUG)
        
        # Console Handler für wichtige Meldungen
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Formatter mit zusätzlichen Orca-spezifischen Informationen
        formatter = logging.Formatter(
            '%(asctime)s - [%(levelname)s] - %(name)s - Pool: %(pool_id)s - %(message)s'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)

    async def monitor_pipeline(self, pipeline):
        """Überwacht die Orca Datenpipeline in Echtzeit"""
        while True:
            try:
                # Prüfe WebSocket-Verbindung
                ws_status = await self._check_websocket(pipeline)
                
                # Prüfe Daten-Latenz
                data_latency = self._check_data_latency(pipeline)
                
                # Prüfe Preisabweichungen
                price_anomalies = self._detect_price_anomalies(pipeline)
                
                # Aktualisiere Pipeline-Gesundheit
                self.pipeline_health.update({
                    'websocket': ws_status,
                    'latency': data_latency,
                    'price_quality': len(price_anomalies) == 0
                })
                
                # Zeige Status
                self._display_health_status()
                
                # Warnungen bei Problemen
                if not all(self.pipeline_health.values()):
                    await self._handle_pipeline_issues()
                
            except Exception as e:
                self.log_error('pipeline_monitor', e)
            
            await asyncio.sleep(1)

    def _check_data_latency(self, pipeline) -> float:
        """Misst und analysiert Daten-Latenz"""
        current_time = time.time()
        latencies = []
        
        for pool_id, last_update in pipeline.last_updates.items():
            latency = current_time - last_update
            latencies.append(latency)
            
            if latency > self.warning_thresholds['data_delay']:
                self.log_warning(
                    f"High latency detected for pool {pool_id}: {latency:.2f}s",
                    pool_id=pool_id
                )
                
        return sum(latencies) / len(latencies) if latencies else float('inf')

    def _detect_price_anomalies(self, pipeline) -> List[Dict]:
        """Erkennt verdächtige Preisbewegungen"""
        anomalies = []
        
        for pool_id, price_history in pipeline.price_history.items():
            if len(price_history) < 2:
                continue
                
            price_change = (price_history[-1] - price_history[-2]) / price_history[-2]
            
            if abs(price_change) > self.warning_thresholds['price_deviation']:
                anomaly = {
                    'pool_id': pool_id,
                    'change': price_change,
                    'timestamp': datetime.now()
                }
                anomalies.append(anomaly)
                self.log_warning(
                    f"Large price movement detected: {price_change:.2%}",
                    pool_id=pool_id
                )
                
        return anomalies

    async def _handle_pipeline_issues(self):
        """Behandelt erkannte Pipeline-Probleme"""
        if not self.pipeline_health['websocket']:
            self.log_error(
                'websocket',
                Exception("WebSocket connection lost"),
                critical=True
            )
            # Versuche Reconnect
            await self._attempt_reconnect()
            
        if self.pipeline_health['latency'] > self.warning_thresholds['data_delay']:
            self.log_warning(
                f"High pipeline latency: {self.pipeline_health['latency']:.2f}s"
            )
            # Implementiere Latency-Optimierung

    def _display_health_status(self):
        """Zeigt detaillierten Gesundheitsstatus"""
        table = Table(title="Orca DEX Pipeline Status")
        
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details", style="yellow")
        
        for component, status in self.pipeline_health.items():
            status_symbol = "✅" if status else "❌"
            details = self._get_component_details(component)
            table.add_row(component, status_symbol, details)
            
        console.clear()
        console.print(table)

    def log_error(self, component: str, error: Exception, critical: bool = False):
        """Erweiterte Fehlerprotokollierung"""
        error_id = int(time.time())
        
        # Fehler zählen
        self.error_counts[component] = self.error_counts.get(component, 0) + 1
        
        # Detaillierte Fehlerinformationen
        error_info = {
            'id': error_id,
            'timestamp': datetime.now(),
            'component': component,
            'error_type': type(error).__name__,
            'message': str(error),
            'traceback': traceback.format_exc(),
            'critical': critical
        }
        
        # Log entsprechend der Schwere
        log_method = self.logger.critical if critical else self.logger.error
        log_method(
            f"Error {error_id} in {component}: {str(error)}",
            extra={'pool_id': 'SYSTEM'}
        )
        
        # Speichere detaillierte Fehlerinformation
        self._save_error_details(error_info)
        
        return error_id

    def log_warning(self, message: str, pool_id: str = 'SYSTEM'):
        """Protokolliert Warnungen mit Kontext"""
        self.logger.warning(
            message,
            extra={'pool_id': pool_id}
        )

    def _save_error_details(self, error_info: Dict):
        """Speichert detaillierte Fehlerinformationen"""
        try:
            with open(f"logs/errors/error_{error_info['id']}.log", 'w') as f:
                for key, value in error_info.items():
                    f.write(f"{key}: {value}\n")
        except Exception as e:
            self.logger.error(f"Failed to save error details: {e}") 

    async def _check_websocket(self, pipeline) -> bool:
        """Überprüft WebSocket-Verbindung"""
        try:
            if not pipeline.ws or not pipeline.ws.connected:
                return False
            
            # Ping test
            await pipeline.ws._ws.ping()
            return True
        except Exception as e:
            self.log_error('websocket_check', e)
            return False

    async def _attempt_reconnect(self):
        """Versucht WebSocket-Reconnect"""
        try:
            if hasattr(self.pipeline, 'ws'):
                await self.pipeline.ws.close()
                await self.pipeline.ws.connect()
                
                # Erneuere Subscriptions
                await self.pipeline.ws.subscribe_to_program(
                    "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc",
                    self.pipeline._handle_program_update
                )
                
                for pool in self.pipeline.watchlist_pools.values():
                    await self.pipeline.ws.subscribe_to_logs(
                        pool,
                        self.pipeline._handle_pool_update
                    )
        except Exception as e:
            self.log_error('reconnect', e)

    def _get_component_details(self, component: str) -> str:
        """Liefert detaillierte Komponenteninformationen"""
        if component == 'websocket':
            return f"Errors: {self.error_counts.get('websocket', 0)}"
        elif component == 'latency':
            return f"{self.pipeline_health['latency']:.2f}s"
        elif component == 'price_quality':
            return f"Anomalies: {len(self._detect_price_anomalies(self.pipeline))}"
        return ""