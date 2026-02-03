"""Performance optimization utilities for the supply chain intelligence platform."""

import asyncio
import functools
import time
import threading
import pickle
import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Union, Tuple
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import logging

# Setup logging for performance monitoring
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Monitor and track performance metrics for various operations."""
    
    def __init__(self, data_dir: Path):
        """Initialize performance monitor.
        
        Args:
            data_dir: Directory for storing performance data
        """
        self.data_dir = data_dir
        self.metrics_dir = data_dir / 'performance'
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        
        self.metrics = {}
        self.start_times = {}
    
    def start_timer(self, operation: str) -> None:
        """Start timing an operation.
        
        Args:
            operation: Name of the operation to time
        """
        self.start_times[operation] = time.time()
    
    def end_timer(self, operation: str) -> float:
        """End timing an operation and record the duration.
        
        Args:
            operation: Name of the operation to stop timing
            
        Returns:
            Duration in seconds
        """
        if operation not in self.start_times:
            logger.warning(f"Timer for operation '{operation}' was not started")
            return 0.0
        
        duration = time.time() - self.start_times[operation]
        
        # Record metric
        if operation not in self.metrics:
            self.metrics[operation] = []
        
        self.metrics[operation].append({
            'timestamp': datetime.now().isoformat(),
            'duration': duration
        })
        
        # Keep only last 1000 measurements per operation
        if len(self.metrics[operation]) > 1000:
            self.metrics[operation] = self.metrics[operation][-1000:]
        
        del self.start_times[operation]
        return duration
    
    def get_performance_stats(self, operation: str = None) -> Dict:
        """Get performance statistics for operations.
        
        Args:
            operation: Specific operation to get stats for, or None for all
            
        Returns:
            Dictionary containing performance statistics
        """
        if operation:
            if operation not in self.metrics:
                return {'error': f'No metrics found for operation: {operation}'}
            
            durations = [m['duration'] for m in self.metrics[operation]]
            return self._calculate_stats(operation, durations)
        else:
            stats = {}
            for op in self.metrics:
                durations = [m['duration'] for m in self.metrics[op]]
                stats[op] = self._calculate_stats(op, durations)
            return stats
    
    def _calculate_stats(self, operation: str, durations: List[float]) -> Dict:
        """Calculate statistics for duration measurements."""
        if not durations:
            return {'count': 0}
        
        durations.sort()
        count = len(durations)
        
        return {
            'operation': operation,
            'count': count,
            'avg_duration': sum(durations) / count,
            'min_duration': durations[0],
            'max_duration': durations[-1],
            'median_duration': durations[count // 2],
            'p95_duration': durations[int(count * 0.95)] if count > 20 else durations[-1],
            'p99_duration': durations[int(count * 0.99)] if count > 100 else durations[-1],
            'recent_avg': sum(durations[-10:]) / min(10, count)
        }
    
    def export_metrics(self, filename: str = None) -> Path:
        """Export performance metrics to JSON file.
        
        Args:
            filename: Output filename, auto-generated if None
            
        Returns:
            Path to exported file
        """
        if not filename:
            filename = f"performance_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        output_path = self.metrics_dir / filename
        
        with open(output_path, 'w') as f:
            json.dump({
                'exported_at': datetime.now().isoformat(),
                'metrics': self.metrics
            }, f, indent=2)
        
        return output_path


# Global performance monitor instance
_performance_monitor = None


def get_performance_monitor(data_dir: Path = None) -> PerformanceMonitor:
    """Get or create the global performance monitor instance."""
    global _performance_monitor
    if _performance_monitor is None and data_dir:
        _performance_monitor = PerformanceMonitor(data_dir)
    return _performance_monitor


def timed(operation_name: str = None):
    """Decorator to automatically time function execution.
    
    Args:
        operation_name: Name for the operation, uses function name if None
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            if not monitor:
                return func(*args, **kwargs)
            
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            monitor.start_timer(op_name)
            try:
                result = func(*args, **kwargs)
                duration = monitor.end_timer(op_name)
                logger.debug(f"Operation '{op_name}' took {duration:.3f} seconds")
                return result
            except Exception as e:
                monitor.end_timer(op_name)
                raise
        
        return wrapper
    return decorator


class MemoryCache:
    """In-memory cache with TTL support for performance optimization."""
    
    def __init__(self, default_ttl_seconds: int = 3600, max_size: int = 1000):
        """Initialize memory cache.
        
        Args:
            default_ttl_seconds: Default time-to-live for cache entries
            max_size: Maximum number of cache entries
        """
        self.default_ttl = default_ttl_seconds
        self.max_size = max_size
        self.cache = {}
        self.expiry_times = {}
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            if key not in self.cache:
                return None
            
            # Check expiry
            if key in self.expiry_times:
                if datetime.now() > self.expiry_times[key]:
                    self._remove(key)
                    return None
            
            return self.cache[key]
    
    def set(self, key: str, value: Any, ttl_seconds: int = None) -> None:
        """Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time-to-live override
        """
        with self._lock:
            # Cleanup if cache is full
            if len(self.cache) >= self.max_size:
                self._cleanup_expired()
                
                # If still full, remove oldest entries
                if len(self.cache) >= self.max_size:
                    keys_to_remove = list(self.cache.keys())[:self.max_size // 4]
                    for old_key in keys_to_remove:
                        self._remove(old_key)
            
            self.cache[key] = value
            
            ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
            if ttl > 0:
                self.expiry_times[key] = datetime.now() + timedelta(seconds=ttl)
    
    def remove(self, key: str) -> bool:
        """Remove key from cache.
        
        Args:
            key: Cache key to remove
            
        Returns:
            True if key was found and removed
        """
        with self._lock:
            return self._remove(key)
    
    def _remove(self, key: str) -> bool:
        """Internal remove method (not thread-safe)."""
        found = key in self.cache
        self.cache.pop(key, None)
        self.expiry_times.pop(key, None)
        return found
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self.cache.clear()
            self.expiry_times.clear()
    
    def _cleanup_expired(self) -> int:
        """Remove expired entries from cache."""
        now = datetime.now()
        expired_keys = [
            key for key, expiry in self.expiry_times.items() 
            if expiry <= now
        ]
        
        for key in expired_keys:
            self._remove(key)
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict:
        """Get cache statistics."""
        with self._lock:
            expired_count = self._cleanup_expired()
            
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'expired_cleaned': expired_count,
                'utilization_pct': (len(self.cache) / self.max_size) * 100
            }


class DiskCache:
    """Disk-based cache with pickle serialization for large objects."""
    
    def __init__(self, cache_dir: Path, default_ttl_seconds: int = 7200):
        """Initialize disk cache.
        
        Args:
            cache_dir: Directory for cache files
            default_ttl_seconds: Default TTL for cache entries
        """
        self.cache_dir = cache_dir
        self.default_ttl = default_ttl_seconds
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = cache_dir / '.cache_index.json'
        self.index = self._load_index()
    
    def _load_index(self) -> Dict:
        """Load cache index from disk."""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save_index(self) -> None:
        """Save cache index to disk."""
        with open(self.index_file, 'w') as f:
            json.dump(self.index, f, indent=2)
    
    def _get_cache_path(self, key: str) -> Path:
        """Get file path for cache key."""
        # Create a safe filename from the key
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.pkl"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from disk cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        if key not in self.index:
            return None
        
        entry = self.index[key]
        
        # Check expiry
        if 'expires_at' in entry:
            expiry_time = datetime.fromisoformat(entry['expires_at'])
            if datetime.now() > expiry_time:
                self.remove(key)
                return None
        
        # Load from disk
        cache_path = self._get_cache_path(key)
        if not cache_path.exists():
            self.remove(key)
            return None
        
        try:
            with open(cache_path, 'rb') as f:
                return pickle.load(f)
        except:
            self.remove(key)
            return None
    
    def set(self, key: str, value: Any, ttl_seconds: int = None) -> bool:
        """Set value in disk cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time-to-live override
            
        Returns:
            True if successfully cached
        """
        try:
            cache_path = self._get_cache_path(key)
            
            # Serialize to disk
            with open(cache_path, 'wb') as f:
                pickle.dump(value, f)
            
            # Update index
            entry = {
                'key': key,
                'file': cache_path.name,
                'created_at': datetime.now().isoformat(),
                'size_bytes': cache_path.stat().st_size
            }
            
            ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
            if ttl > 0:
                entry['expires_at'] = (datetime.now() + timedelta(seconds=ttl)).isoformat()
            
            self.index[key] = entry
            self._save_index()
            
            return True
        except Exception as e:
            logger.error(f"Failed to cache key '{key}': {e}")
            return False
    
    def remove(self, key: str) -> bool:
        """Remove key from cache.
        
        Args:
            key: Cache key to remove
            
        Returns:
            True if key was found and removed
        """
        if key not in self.index:
            return False
        
        try:
            cache_path = self._get_cache_path(key)
            if cache_path.exists():
                cache_path.unlink()
            
            del self.index[key]
            self._save_index()
            return True
        except Exception as e:
            logger.error(f"Failed to remove cache key '{key}': {e}")
            return False
    
    def clear(self) -> int:
        """Clear all cache entries.
        
        Returns:
            Number of entries removed
        """
        count = len(self.index)
        
        # Remove all cache files
        for key in list(self.index.keys()):
            self.remove(key)
        
        return count
    
    def cleanup_expired(self) -> int:
        """Remove expired cache entries.
        
        Returns:
            Number of expired entries removed
        """
        now = datetime.now()
        expired_keys = []
        
        for key, entry in self.index.items():
            if 'expires_at' in entry:
                expiry_time = datetime.fromisoformat(entry['expires_at'])
                if now > expiry_time:
                    expired_keys.append(key)
        
        for key in expired_keys:
            self.remove(key)
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict:
        """Get cache statistics."""
        cleanup_count = self.cleanup_expired()
        
        total_size = sum(
            entry.get('size_bytes', 0) 
            for entry in self.index.values()
        )
        
        return {
            'entry_count': len(self.index),
            'total_size_mb': total_size / (1024 * 1024),
            'expired_cleaned': cleanup_count,
            'cache_dir': str(self.cache_dir)
        }


class AsyncExecutor:
    """Asynchronous execution utilities for performance optimization."""
    
    def __init__(self, max_workers: int = 4):
        """Initialize async executor.
        
        Args:
            max_workers: Maximum number of worker threads
        """
        self.max_workers = max_workers
        self.thread_executor = ThreadPoolExecutor(max_workers=max_workers)
        self.process_executor = ProcessPoolExecutor(max_workers=min(max_workers, 2))
    
    async def run_in_thread(self, func: Callable, *args, **kwargs) -> Any:
        """Run function in thread pool.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.thread_executor, 
            functools.partial(func, **kwargs), 
            *args
        )
    
    async def run_in_process(self, func: Callable, *args, **kwargs) -> Any:
        """Run function in process pool.
        
        Args:
            func: Function to execute (must be picklable)
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.process_executor,
            functools.partial(func, **kwargs),
            *args
        )
    
    async def gather_with_limit(self, tasks: List[Callable], limit: int = None) -> List[Any]:
        """Execute multiple tasks with concurrency limit.
        
        Args:
            tasks: List of async tasks or functions
            limit: Maximum concurrent tasks (defaults to max_workers)
            
        Returns:
            List of task results
        """
        if limit is None:
            limit = self.max_workers
        
        semaphore = asyncio.Semaphore(limit)
        
        async def limited_task(task):
            async with semaphore:
                if asyncio.iscoroutine(task):
                    return await task
                else:
                    return await self.run_in_thread(task)
        
        return await asyncio.gather(*[limited_task(task) for task in tasks])
    
    def close(self) -> None:
        """Close executor pools."""
        self.thread_executor.shutdown(wait=True)
        self.process_executor.shutdown(wait=True)


def cached(cache_key_func: Callable = None, ttl_seconds: int = 3600, 
          use_disk_cache: bool = False):
    """Decorator for caching function results.
    
    Args:
        cache_key_func: Function to generate cache key from args
        ttl_seconds: Cache time-to-live
        use_disk_cache: Whether to use disk cache instead of memory
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if cache_key_func:
                cache_key = cache_key_func(*args, **kwargs)
            else:
                # Default key generation
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = hashlib.md5('|'.join(key_parts).encode()).hexdigest()
            
            # Try to get from cache
            monitor = get_performance_monitor()
            if monitor:
                if use_disk_cache:
                    cache = getattr(wrapper, '_disk_cache', None)
                else:
                    cache = getattr(wrapper, '_memory_cache', None)
                
                if cache:
                    cached_result = cache.get(cache_key)
                    if cached_result is not None:
                        logger.debug(f"Cache hit for {func.__name__}")
                        return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            
            if monitor and hasattr(wrapper, '_memory_cache' if not use_disk_cache else '_disk_cache'):
                cache = getattr(wrapper, '_memory_cache' if not use_disk_cache else '_disk_cache')
                cache.set(cache_key, result, ttl_seconds)
                logger.debug(f"Cached result for {func.__name__}")
            
            return result
        
        # Attach cache instance to wrapper
        if use_disk_cache:
            wrapper._disk_cache = DiskCache(
                Path.cwd() / '.cache' / 'function_cache', 
                ttl_seconds
            )
        else:
            wrapper._memory_cache = MemoryCache(ttl_seconds)
        
        return wrapper
    return decorator


class BatchProcessor:
    """Process items in batches for improved performance."""
    
    def __init__(self, batch_size: int = 100, max_workers: int = 4):
        """Initialize batch processor.
        
        Args:
            batch_size: Number of items per batch
            max_workers: Maximum concurrent workers
        """
        self.batch_size = batch_size
        self.executor = AsyncExecutor(max_workers)
    
    async def process_batches(self, items: List[Any], 
                            processor_func: Callable[[List[Any]], Any]) -> List[Any]:
        """Process items in batches.
        
        Args:
            items: Items to process
            processor_func: Function that processes a batch of items
            
        Returns:
            List of processing results
        """
        # Create batches
        batches = [
            items[i:i + self.batch_size] 
            for i in range(0, len(items), self.batch_size)
        ]
        
        # Process batches concurrently
        batch_tasks = [
            self.executor.run_in_thread(processor_func, batch)
            for batch in batches
        ]
        
        return await self.executor.gather_with_limit(batch_tasks)
    
    def process_batches_sync(self, items: List[Any],
                           processor_func: Callable[[List[Any]], Any]) -> List[Any]:
        """Synchronous batch processing.
        
        Args:
            items: Items to process
            processor_func: Function that processes a batch of items
            
        Returns:
            List of processing results
        """
        return asyncio.run(self.process_batches(items, processor_func))


class PerformanceOptimizer:
    """Main performance optimization coordinator."""
    
    def __init__(self, data_dir: Path):
        """Initialize performance optimizer.
        
        Args:
            data_dir: Data directory for caching and metrics
        """
        self.data_dir = data_dir
        self.performance_dir = data_dir / 'performance'
        self.cache_dir = data_dir / 'cache'
        
        # Create directories
        self.performance_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.monitor = PerformanceMonitor(data_dir)
        self.memory_cache = MemoryCache(default_ttl_seconds=3600)
        self.disk_cache = DiskCache(self.cache_dir)
        self.async_executor = AsyncExecutor()
        self.batch_processor = BatchProcessor()
        
        # Set global monitor
        global _performance_monitor
        _performance_monitor = self.monitor
    
    def get_system_stats(self) -> Dict:
        """Get comprehensive system performance statistics."""
        return {
            'performance_metrics': self.monitor.get_performance_stats(),
            'memory_cache': self.memory_cache.get_stats(),
            'disk_cache': self.disk_cache.get_stats(),
            'cache_dir': str(self.cache_dir),
            'performance_dir': str(self.performance_dir)
        }
    
    def cleanup_caches(self) -> Dict:
        """Clean up expired cache entries.
        
        Returns:
            Cleanup statistics
        """
        memory_cleaned = len(self.memory_cache.cache)
        self.memory_cache._cleanup_expired()
        memory_cleaned = memory_cleaned - len(self.memory_cache.cache)
        
        disk_cleaned = self.disk_cache.cleanup_expired()
        
        return {
            'memory_cache_cleaned': memory_cleaned,
            'disk_cache_cleaned': disk_cleaned
        }
    
    def optimize_for_research_analysis(self, enable_caching: bool = True,
                                     enable_async: bool = True) -> Dict:
        """Apply optimizations for research analysis workloads.
        
        Args:
            enable_caching: Whether to enable aggressive caching
            enable_async: Whether to enable async processing
            
        Returns:
            Optimization configuration applied
        """
        config = {
            'caching_enabled': enable_caching,
            'async_enabled': enable_async,
            'optimizations_applied': []
        }
        
        if enable_caching:
            # Increase cache sizes for research data
            self.memory_cache.max_size = 2000
            self.memory_cache.default_ttl = 7200  # 2 hours
            config['optimizations_applied'].append('increased_cache_sizes')
        
        if enable_async:
            # Increase worker count for research operations
            self.async_executor.max_workers = 8
            config['optimizations_applied'].append('increased_worker_count')
        
        return config
    
    def export_performance_report(self) -> Path:
        """Export comprehensive performance report.
        
        Returns:
            Path to exported report
        """
        report = {
            'generated_at': datetime.now().isoformat(),
            'system_stats': self.get_system_stats(),
            'optimization_recommendations': self._generate_recommendations()
        }
        
        output_path = self.performance_dir / f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return output_path
    
    def _generate_recommendations(self) -> List[str]:
        """Generate performance optimization recommendations."""
        recommendations = []
        
        # Analyze cache performance
        memory_stats = self.memory_cache.get_stats()
        if memory_stats['utilization_pct'] > 90:
            recommendations.append("Consider increasing memory cache size")
        
        disk_stats = self.disk_cache.get_stats()
        if disk_stats['total_size_mb'] > 1000:  # 1GB
            recommendations.append("Consider disk cache cleanup or size limits")
        
        # Analyze operation performance
        perf_stats = self.monitor.get_performance_stats()
        for operation, stats in perf_stats.items():
            if 'avg_duration' in stats and stats['avg_duration'] > 10:  # 10 seconds
                recommendations.append(f"Operation '{operation}' is slow - consider optimization")
        
        if not recommendations:
            recommendations.append("System performance appears optimal")
        
        return recommendations
    
    def close(self) -> None:
        """Clean up optimizer resources."""
        self.async_executor.close()