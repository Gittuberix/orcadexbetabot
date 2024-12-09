import logging
import traceback
import psutil
import time
from datetime import datetime, timedelta
import json
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass, asdict

@dataclass
class ErrorRecord:
    timestamp: str
    error_type: str
    message: str
    context: str
    traceback: str
    severity: str

class SystemMonitor:
    def __init__(self, name: str):
        self.name = name
        self.start_time = datetime.now()
        self.errors: List[ErrorRecord] = []
        self.metrics: Dict[str, List[float]] = {
            'cpu_usage': [],
            'memory_usage': [],
            'response_times': [],
            'cycle_times': []
        }
        self.logger = logging.getLogger(name)
        
    def log_error(self, error: Exception, context: str, severity: str = "ERROR") -> None:
        """Log detailed error information"""
        error_record = ErrorRecord(
            timestamp=datetime.now().isoformat(),
            error_type=type(error).__name__,
            message=str(error),
            context=context,
            traceback=traceback.format_exc(),
            severity=severity
        )
        self.errors.append(error_record)
        
        # Keep last 100 errors
        if len(self.errors) > 100:
            self.errors.pop(0)
            
        # Log based on severity
        if severity == "CRITICAL":
            self.logger.critical(f"{context}: {str(error)}", exc_info=True)
        else:
            self.logger.error(f"{context}: {str(error)}", exc_info=True)
            
        # Save error to file
        self._save_error(error_record)

    def _save_error(self, error: ErrorRecord) -> None:
        """Save error to JSON file"""
        error_dir = Path("logs/errors")
        error_dir.mkdir(parents=True, exist_ok=True)
        
        error_file = error_dir / f"error_{datetime.now().strftime('%Y%m%d')}.json"
        
        try:
            if error_file.exists():
                with open(error_file, 'r') as f:
                    errors = json.load(f)
            else:
                errors = []
                
            errors.append(asdict(error))
            
            with open(error_file, 'w') as f:
                json.dump(errors, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save error record: {e}")

    def update_metrics(self) -> None:
        """Update system performance metrics"""
        try:
            self.metrics['cpu_usage'].append(psutil.cpu_percent())
            self.metrics['memory_usage'].append(psutil.Process().memory_info().rss / 1024 / 1024)
            
            # Keep last 1000 measurements
            for key in self.metrics:
                if len(self.metrics[key]) > 1000:
                    self.metrics[key] = self.metrics[key][-1000:]
                    
        except Exception as e:
            self.logger.error(f"Failed to update metrics: {e}")

    def get_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive health report"""
        try:
            uptime = (datetime.now() - self.start_time).total_seconds()
            recent_errors = len([e for e in self.errors if 
                               (datetime.now() - datetime.fromisoformat(e.timestamp)).total_seconds() < 3600])
            
            return {
                'status': 'healthy' if recent_errors < 5 else 'degraded',
                'uptime_seconds': uptime,
                'recent_errors': recent_errors,
                'metrics': {
                    'cpu_usage_avg': sum(self.metrics['cpu_usage'][-60:]) / len(self.metrics['cpu_usage'][-60:]) if self.metrics['cpu_usage'] else 0,
                    'memory_mb_avg': sum(self.metrics['memory_usage'][-60:]) / len(self.metrics['memory_usage'][-60:]) if self.metrics['memory_usage'] else 0,
                }
            }
        except Exception as e:
            self.logger.error(f"Failed to generate health report: {e}")
            return {'status': 'unknown', 'error': str(e)} 