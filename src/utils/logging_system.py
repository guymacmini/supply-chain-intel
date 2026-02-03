"""Enhanced logging and monitoring system."""

import json
import logging
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field, asdict
from contextlib import contextmanager
from functools import wraps
from collections import defaultdict, deque
import threading


@dataclass
class LogMetrics:
    """Log metrics tracking."""
    total_logs: int = 0
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    debug_count: int = 0
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def increment(self, level: str):
        """Increment counter for log level."""
        self.total_logs += 1
        level_lower = level.lower()
        if level_lower == 'error':
            self.error_count += 1
        elif level_lower == 'warning':
            self.warning_count += 1
        elif level_lower == 'info':
            self.info_count += 1
        elif level_lower == 'debug':
            self.debug_count += 1


@dataclass
class PerformanceMetric:
    """Performance metric record."""
    operation: str
    duration: float
    timestamp: str
    success: bool
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PerformanceMonitor:
    """Performance monitoring and metrics collection."""
    
    def __init__(self, max_metrics: int = 10000):
        """Initialize performance monitor.
        
        Args:
            max_metrics: Maximum number of metrics to keep in memory
        """
        self.max_metrics = max_metrics
        self.metrics = deque(maxlen=max_metrics)
        self.operation_stats = defaultdict(list)
        self._lock = threading.RLock()
    
    def record_metric(self, operation: str, duration: float, success: bool = True, 
                     metadata: Optional[Dict[str, Any]] = None):
        """Record a performance metric.
        
        Args:
            operation: Name of the operation
            duration: Duration in seconds
            success: Whether the operation was successful
            metadata: Additional metadata
        """
        metric = PerformanceMetric(
            operation=operation,
            duration=duration,
            timestamp=datetime.now().isoformat(),
            success=success,
            metadata=metadata or {}
        )
        
        with self._lock:
            self.metrics.append(metric)
            self.operation_stats[operation].append(duration)
            
            # Keep only recent stats for each operation
            if len(self.operation_stats[operation]) > 1000:
                self.operation_stats[operation] = self.operation_stats[operation][-500:]
    
    @contextmanager
    def measure(self, operation: str, metadata: Optional[Dict[str, Any]] = None):
        """Context manager for measuring operation duration.
        
        Args:
            operation: Name of the operation
            metadata: Additional metadata
        """
        start_time = time.time()
        success = True
        exception = None
        
        try:
            yield
        except Exception as e:
            success = False
            exception = e
            raise
        finally:
            duration = time.time() - start_time
            final_metadata = metadata or {}
            if exception:
                final_metadata['error'] = str(exception)
            
            self.record_metric(operation, duration, success, final_metadata)
    
    def get_stats(self, operation: Optional[str] = None, 
                 time_window: Optional[timedelta] = None) -> Dict[str, Any]:
        """Get performance statistics.
        
        Args:
            operation: Specific operation to get stats for
            time_window: Time window for metrics (default: all)
            
        Returns:
            Performance statistics
        """
        with self._lock:
            # Filter metrics by time window
            now = datetime.now()
            filtered_metrics = self.metrics
            
            if time_window:
                cutoff = now - time_window
                filtered_metrics = [
                    m for m in self.metrics 
                    if datetime.fromisoformat(m.timestamp) >= cutoff
                ]
            
            # Filter by operation
            if operation:
                filtered_metrics = [m for m in filtered_metrics if m.operation == operation]
            
            if not filtered_metrics:
                return {}
            
            # Calculate statistics
            durations = [m.duration for m in filtered_metrics]
            successful = [m for m in filtered_metrics if m.success]
            failed = [m for m in filtered_metrics if not m.success]
            
            stats = {
                'total_operations': len(filtered_metrics),
                'successful_operations': len(successful),
                'failed_operations': len(failed),
                'success_rate': len(successful) / len(filtered_metrics) if filtered_metrics else 0,
                'avg_duration': sum(durations) / len(durations) if durations else 0,
                'min_duration': min(durations) if durations else 0,
                'max_duration': max(durations) if durations else 0,
                'total_duration': sum(durations)
            }
            
            # Operation breakdown
            if not operation:
                operation_counts = defaultdict(int)
                for metric in filtered_metrics:
                    operation_counts[metric.operation] += 1
                stats['operations'] = dict(operation_counts)
            
            return stats


class StructuredLogger:
    """Enhanced structured logging system."""
    
    def __init__(self, name: str, log_dir: Optional[Path] = None):
        """Initialize structured logger.
        
        Args:
            name: Logger name
            log_dir: Directory for log files
        """
        self.name = name
        self.log_dir = Path(log_dir) if log_dir else Path('./logs')
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logger
        self.logger = logging.getLogger(name)
        self.metrics = LogMetrics()
        self.performance_monitor = PerformanceMonitor()
        
        # Custom handler for structured logging
        self._setup_structured_handler()
    
    def _setup_structured_handler(self):
        """Setup structured logging handler."""
        # JSON formatter for structured logs
        json_formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
            '"logger": "%(name)s", "message": "%(message)s"}'
        )
        
        # File handler for structured logs
        structured_log_file = self.log_dir / f'{self.name}_structured.json'
        structured_handler = logging.FileHandler(structured_log_file)
        structured_handler.setFormatter(json_formatter)
        structured_handler.setLevel(logging.DEBUG)
        
        # Metrics handler
        class MetricsHandler(logging.Handler):
            def __init__(self, metrics):
                super().__init__()
                self.metrics = metrics
            
            def emit(self, record):
                self.metrics.increment(record.levelname)
        
        metrics_handler = MetricsHandler(self.metrics)
        
        # Add handlers
        self.logger.addHandler(structured_handler)
        self.logger.addHandler(metrics_handler)
    
    def log_structured(self, log_level: str, message: str, **kwargs):
        """Log with structured data.
        
        Args:
            log_level: Log level
            message: Log message
            **kwargs: Additional structured data
        """
        # Add structured data as extra fields
        extra_data = json.dumps(kwargs) if kwargs else ''
        full_message = f"{message} | {extra_data}" if extra_data else message
        
        log_method = getattr(self.logger, log_level.lower())
        log_method(full_message)
    
    def info(self, message: str, **kwargs):
        """Log info message with structured data."""
        self.log_structured('info', message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with structured data."""
        self.log_structured('warning', message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with structured data."""
        self.log_structured('error', message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with structured data.""" 
        self.log_structured('debug', message, **kwargs)
    
    def log_api_request(self, endpoint: str, method: str, status_code: int, 
                       duration: float, **kwargs):
        """Log API request with standard fields.
        
        Args:
            endpoint: API endpoint
            method: HTTP method
            status_code: Response status code
            duration: Request duration
            **kwargs: Additional fields
        """
        self.info(
            f"API Request: {method} {endpoint}",
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            duration=duration,
            **kwargs
        )
        
        # Record performance metric
        self.performance_monitor.record_metric(
            f"api_{method.lower()}_{endpoint.replace('/', '_')}",
            duration,
            200 <= status_code < 400,
            {'endpoint': endpoint, 'method': method, 'status_code': status_code}
        )
    
    def log_research_operation(self, operation: str, ticker: Optional[str] = None,
                             duration: Optional[float] = None, success: bool = True,
                             **kwargs):
        """Log research operation with standard fields.
        
        Args:
            operation: Research operation name
            ticker: Stock ticker (if applicable)
            duration: Operation duration
            success: Whether operation was successful
            **kwargs: Additional fields
        """
        log_level = 'info' if success else 'error'
        self.log_structured(
            log_level,
            f"Research Operation: {operation}",
            operation=operation,
            ticker=ticker,
            duration=duration,
            success=success,
            **kwargs
        )
        
        if duration is not None:
            self.performance_monitor.record_metric(
                f"research_{operation.lower().replace(' ', '_')}",
                duration,
                success,
                {'operation': operation, 'ticker': ticker}
            )
    
    def log_alert_event(self, alert_type: str, ticker: Optional[str] = None,
                       threshold: Optional[float] = None, current_value: Optional[float] = None,
                       **kwargs):
        """Log alert event with standard fields.
        
        Args:
            alert_type: Type of alert
            ticker: Stock ticker
            threshold: Alert threshold value
            current_value: Current value that triggered alert
            **kwargs: Additional fields
        """
        self.info(
            f"Alert Triggered: {alert_type}",
            alert_type=alert_type,
            ticker=ticker,
            threshold=threshold,
            current_value=current_value,
            **kwargs
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get logging metrics."""
        return {
            'log_counts': asdict(self.metrics),
            'performance_stats': self.performance_monitor.get_stats(),
            'recent_performance': self.performance_monitor.get_stats(
                time_window=timedelta(hours=1)
            )
        }
    
    def export_logs(self, output_file: Path, time_window: Optional[timedelta] = None):
        """Export logs to file.
        
        Args:
            output_file: Output file path
            time_window: Time window for export (default: all)
        """
        # Read structured logs
        structured_log_file = self.log_dir / f'{self.name}_structured.json'
        
        if not structured_log_file.exists():
            return
        
        logs = []
        cutoff = datetime.now() - time_window if time_window else None
        
        with open(structured_log_file, 'r') as f:
            for line in f:
                try:
                    log_entry = json.loads(line.strip())
                    if cutoff:
                        log_time = datetime.fromisoformat(log_entry.get('timestamp', ''))
                        if log_time < cutoff:
                            continue
                    logs.append(log_entry)
                except (json.JSONDecodeError, ValueError):
                    continue
        
        # Export logs
        with open(output_file, 'w') as f:
            json.dump({
                'export_timestamp': datetime.now().isoformat(),
                'log_count': len(logs),
                'metrics': self.get_metrics(),
                'logs': logs
            }, f, indent=2)


def performance_monitor(operation: str, metadata: Optional[Dict[str, Any]] = None):
    """Decorator for monitoring function performance.
    
    Args:
        operation: Operation name
        metadata: Additional metadata
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger_name = getattr(func, '__module__', 'default')
            logger = get_logger(logger_name)
            
            with logger.performance_monitor.measure(operation, metadata):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def log_function_calls(logger_name: Optional[str] = None):
    """Decorator for logging function calls.
    
    Args:
        logger_name: Logger name (defaults to function module)
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            effective_logger_name = logger_name or func.__module__
            logger = get_logger(effective_logger_name)
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                logger.debug(
                    f"Function called: {func.__name__}",
                    function=func.__name__,
                    duration=duration,
                    success=True,
                    args_count=len(args),
                    kwargs_count=len(kwargs)
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                logger.error(
                    f"Function failed: {func.__name__}",
                    function=func.__name__,
                    duration=duration,
                    success=False,
                    error=str(e),
                    error_type=type(e).__name__
                )
                raise
        
        return wrapper
    return decorator


# Global logger registry
_loggers: Dict[str, StructuredLogger] = {}
_lock = threading.RLock()

def get_logger(name: str, log_dir: Optional[Path] = None) -> StructuredLogger:
    """Get or create a structured logger.
    
    Args:
        name: Logger name
        log_dir: Log directory
        
    Returns:
        Structured logger instance
    """
    global _loggers
    
    with _lock:
        if name not in _loggers:
            _loggers[name] = StructuredLogger(name, log_dir)
        return _loggers[name]

def get_system_metrics() -> Dict[str, Any]:
    """Get system-wide logging metrics.
    
    Returns:
        Combined metrics from all loggers
    """
    with _lock:
        system_metrics = {
            'total_loggers': len(_loggers),
            'loggers': {}
        }
        
        total_logs = 0
        total_errors = 0
        
        for name, logger in _loggers.items():
            logger_metrics = logger.get_metrics()
            system_metrics['loggers'][name] = logger_metrics
            
            log_counts = logger_metrics.get('log_counts', {})
            total_logs += log_counts.get('total_logs', 0)
            total_errors += log_counts.get('error_count', 0)
        
        system_metrics['totals'] = {
            'total_logs': total_logs,
            'total_errors': total_errors,
            'error_rate': total_errors / total_logs if total_logs > 0 else 0
        }
        
        return system_metrics