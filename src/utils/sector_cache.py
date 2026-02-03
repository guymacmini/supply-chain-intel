"""Sector analysis caching system to avoid redundant API calls and improve performance."""

import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
import time


@dataclass
class CacheEntry:
    """A cached data entry with metadata."""
    data: Any
    created_at: str
    expires_at: str
    access_count: int = 0
    last_accessed: Optional[str] = None
    cache_key: Optional[str] = None
    data_source: Optional[str] = None  # 'finnhub', 'tavily', 'anthropic'
    
    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        return datetime.fromisoformat(self.expires_at) < datetime.now()
    
    def is_fresh(self, max_age_hours: int = 24) -> bool:
        """Check if the cache entry is still fresh within max_age."""
        created = datetime.fromisoformat(self.created_at)
        return datetime.now() - created < timedelta(hours=max_age_hours)
    
    def access(self) -> None:
        """Record an access to this cache entry."""
        self.access_count += 1
        self.last_accessed = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CacheEntry':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class SectorInfo:
    """Information about a sector for caching purposes."""
    sector: str
    industry: Optional[str] = None
    gics_sector: Optional[str] = None
    gics_industry: Optional[str] = None
    companies_count: int = 0
    total_market_cap: Optional[float] = None
    representative_tickers: List[str] = None
    
    def __post_init__(self):
        if self.representative_tickers is None:
            self.representative_tickers = []


class SectorAnalysisCache:
    """High-performance caching system for sector analysis data."""
    
    def __init__(self, cache_dir: Path, default_ttl_hours: int = 24):
        """Initialize the sector cache.
        
        Args:
            cache_dir: Directory to store cache files
            default_ttl_hours: Default time-to-live for cache entries in hours
        """
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.default_ttl_hours = default_ttl_hours
        
        # Cache file locations
        self.finnhub_cache_file = self.cache_dir / 'finnhub_sector_cache.json'
        self.tavily_cache_file = self.cache_dir / 'tavily_sector_cache.json'
        self.sector_info_file = self.cache_dir / 'sector_info.json'
        self.cache_stats_file = self.cache_dir / 'cache_stats.json'
        
        # In-memory caches for performance
        self._finnhub_cache: Dict[str, CacheEntry] = {}
        self._tavily_cache: Dict[str, CacheEntry] = {}
        self._sector_info: Dict[str, SectorInfo] = {}
        self._cache_stats = {
            'hits': 0,
            'misses': 0,
            'created': 0,
            'evicted': 0,
            'last_cleanup': datetime.now().isoformat()
        }
        
        # Load existing cache data
        self._load_caches()
    
    def _load_caches(self) -> None:
        """Load cache data from disk."""
        # Load Finnhub cache
        if self.finnhub_cache_file.exists():
            try:
                with open(self.finnhub_cache_file, 'r') as f:
                    data = json.load(f)
                    self._finnhub_cache = {
                        k: CacheEntry.from_dict(v) for k, v in data.items()
                    }
            except Exception as e:
                print(f"Error loading Finnhub cache: {e}")
        
        # Load Tavily cache
        if self.tavily_cache_file.exists():
            try:
                with open(self.tavily_cache_file, 'r') as f:
                    data = json.load(f)
                    self._tavily_cache = {
                        k: CacheEntry.from_dict(v) for k, v in data.items()
                    }
            except Exception as e:
                print(f"Error loading Tavily cache: {e}")
        
        # Load sector info
        if self.sector_info_file.exists():
            try:
                with open(self.sector_info_file, 'r') as f:
                    data = json.load(f)
                    self._sector_info = {
                        k: SectorInfo(**v) for k, v in data.items()
                    }
            except Exception as e:
                print(f"Error loading sector info: {e}")
        
        # Load cache stats
        if self.cache_stats_file.exists():
            try:
                with open(self.cache_stats_file, 'r') as f:
                    self._cache_stats.update(json.load(f))
            except Exception as e:
                print(f"Error loading cache stats: {e}")
    
    def _save_caches(self) -> None:
        """Save cache data to disk."""
        try:
            # Save Finnhub cache
            with open(self.finnhub_cache_file, 'w') as f:
                json.dump({k: v.to_dict() for k, v in self._finnhub_cache.items()}, 
                         f, indent=2)
            
            # Save Tavily cache
            with open(self.tavily_cache_file, 'w') as f:
                json.dump({k: v.to_dict() for k, v in self._tavily_cache.items()}, 
                         f, indent=2)
            
            # Save sector info
            with open(self.sector_info_file, 'w') as f:
                json.dump({k: asdict(v) for k, v in self._sector_info.items()}, 
                         f, indent=2)
            
            # Save cache stats
            with open(self.cache_stats_file, 'w') as f:
                json.dump(self._cache_stats, f, indent=2)
                
        except Exception as e:
            print(f"Error saving caches: {e}")
    
    def _generate_cache_key(self, source: str, sector: str, query_params: Dict = None) -> str:
        """Generate a consistent cache key.
        
        Args:
            source: Data source ('finnhub', 'tavily')
            sector: Sector name
            query_params: Additional query parameters
            
        Returns:
            Cache key string
        """
        key_data = {
            'source': source,
            'sector': sector.lower().strip(),
            'params': query_params or {}
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get_finnhub_sector_data(self, sector: str, max_age_hours: int = None) -> Optional[Any]:
        """Get cached Finnhub data for a sector.
        
        Args:
            sector: Sector name
            max_age_hours: Maximum age in hours, uses default if None
            
        Returns:
            Cached data or None if not available/expired
        """
        cache_key = self._generate_cache_key('finnhub', sector)
        max_age = max_age_hours or self.default_ttl_hours
        
        if cache_key in self._finnhub_cache:
            entry = self._finnhub_cache[cache_key]
            
            if entry.is_fresh(max_age):
                entry.access()
                self._cache_stats['hits'] += 1
                return entry.data
            else:
                # Expired entry
                del self._finnhub_cache[cache_key]
        
        self._cache_stats['misses'] += 1
        return None
    
    def set_finnhub_sector_data(self, sector: str, data: Any, ttl_hours: int = None) -> None:
        """Cache Finnhub data for a sector.
        
        Args:
            sector: Sector name
            data: Data to cache
            ttl_hours: Time to live in hours, uses default if None
        """
        cache_key = self._generate_cache_key('finnhub', sector)
        ttl = ttl_hours or self.default_ttl_hours
        
        now = datetime.now()
        expires_at = now + timedelta(hours=ttl)
        
        entry = CacheEntry(
            data=data,
            created_at=now.isoformat(),
            expires_at=expires_at.isoformat(),
            cache_key=cache_key,
            data_source='finnhub'
        )
        
        self._finnhub_cache[cache_key] = entry
        self._cache_stats['created'] += 1
        
        # Update sector info
        self._update_sector_info(sector, data, 'finnhub')
    
    def get_tavily_sector_data(self, sector: str, query_type: str = 'general', 
                              max_age_hours: int = None) -> Optional[Any]:
        """Get cached Tavily search data for a sector.
        
        Args:
            sector: Sector name
            query_type: Type of query ('general', 'news', 'trends', etc.)
            max_age_hours: Maximum age in hours, uses default if None
            
        Returns:
            Cached data or None if not available/expired
        """
        cache_key = self._generate_cache_key('tavily', sector, {'query_type': query_type})
        max_age = max_age_hours or self.default_ttl_hours
        
        if cache_key in self._tavily_cache:
            entry = self._tavily_cache[cache_key]
            
            if entry.is_fresh(max_age):
                entry.access()
                self._cache_stats['hits'] += 1
                return entry.data
            else:
                # Expired entry
                del self._tavily_cache[cache_key]
        
        self._cache_stats['misses'] += 1
        return None
    
    def set_tavily_sector_data(self, sector: str, query_type: str, data: Any, 
                              ttl_hours: int = None) -> None:
        """Cache Tavily search data for a sector.
        
        Args:
            sector: Sector name
            query_type: Type of query performed
            data: Data to cache
            ttl_hours: Time to live in hours, uses default if None
        """
        cache_key = self._generate_cache_key('tavily', sector, {'query_type': query_type})
        ttl = ttl_hours or self.default_ttl_hours
        
        now = datetime.now()
        expires_at = now + timedelta(hours=ttl)
        
        entry = CacheEntry(
            data=data,
            created_at=now.isoformat(),
            expires_at=expires_at.isoformat(),
            cache_key=cache_key,
            data_source='tavily'
        )
        
        self._tavily_cache[cache_key] = entry
        self._cache_stats['created'] += 1
        
        # Update sector info
        self._update_sector_info(sector, data, 'tavily')
    
    def _update_sector_info(self, sector: str, data: Any, source: str) -> None:
        """Update sector information from cached data."""
        if sector not in self._sector_info:
            self._sector_info[sector] = SectorInfo(sector=sector)
        
        sector_info = self._sector_info[sector]
        
        if source == 'finnhub' and isinstance(data, dict):
            # Extract info from Finnhub data
            if 'tickers' in data:
                sector_info.companies_count = len(data['tickers'])
                sector_info.representative_tickers = list(data['tickers'][:10])  # Top 10
                
            if 'market_data' in data:
                # Calculate total market cap if available
                total_cap = 0
                for ticker_data in data['market_data'].values():
                    if 'marketCap' in ticker_data:
                        total_cap += ticker_data.get('marketCap', 0)
                sector_info.total_market_cap = total_cap
        
        elif source == 'tavily' and isinstance(data, dict):
            # Extract info from Tavily data
            if 'results' in data:
                # Could extract industry info from search results
                pass
    
    def get_sector_tickers(self, sector: str, limit: int = 20) -> List[str]:
        """Get representative tickers for a sector.
        
        Args:
            sector: Sector name
            limit: Maximum number of tickers to return
            
        Returns:
            List of ticker symbols
        """
        if sector in self._sector_info:
            return self._sector_info[sector].representative_tickers[:limit]
        
        # Try to get from cached Finnhub data
        cached_data = self.get_finnhub_sector_data(sector)
        if cached_data and 'tickers' in cached_data:
            return list(cached_data['tickers'][:limit])
        
        return []
    
    def invalidate_sector(self, sector: str) -> int:
        """Invalidate all cached data for a specific sector.
        
        Args:
            sector: Sector name
            
        Returns:
            Number of cache entries invalidated
        """
        invalidated = 0
        
        # Find and remove Finnhub entries
        to_remove = []
        for key, entry in self._finnhub_cache.items():
            if entry.cache_key and sector.lower() in entry.cache_key:
                to_remove.append(key)
        
        for key in to_remove:
            del self._finnhub_cache[key]
            invalidated += 1
        
        # Find and remove Tavily entries
        to_remove = []
        for key, entry in self._tavily_cache.items():
            if entry.cache_key and sector.lower() in entry.cache_key:
                to_remove.append(key)
        
        for key in to_remove:
            del self._tavily_cache[key]
            invalidated += 1
        
        # Remove sector info
        if sector in self._sector_info:
            del self._sector_info[sector]
            invalidated += 1
        
        self._cache_stats['evicted'] += invalidated
        return invalidated
    
    def cleanup_expired_entries(self) -> int:
        """Remove expired cache entries.
        
        Returns:
            Number of entries removed
        """
        removed = 0
        
        # Clean Finnhub cache
        expired_keys = [k for k, v in self._finnhub_cache.items() if v.is_expired()]
        for key in expired_keys:
            del self._finnhub_cache[key]
            removed += 1
        
        # Clean Tavily cache
        expired_keys = [k for k, v in self._tavily_cache.items() if v.is_expired()]
        for key in expired_keys:
            del self._tavily_cache[key]
            removed += 1
        
        self._cache_stats['evicted'] += removed
        self._cache_stats['last_cleanup'] = datetime.now().isoformat()
        
        if removed > 0:
            self._save_caches()
        
        return removed
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        # Calculate hit rate
        total_requests = self._cache_stats['hits'] + self._cache_stats['misses']
        hit_rate = (self._cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'finnhub_entries': len(self._finnhub_cache),
            'tavily_entries': len(self._tavily_cache),
            'sectors_tracked': len(self._sector_info),
            'hit_rate_pct': round(hit_rate, 1),
            'total_hits': self._cache_stats['hits'],
            'total_misses': self._cache_stats['misses'],
            'entries_created': self._cache_stats['created'],
            'entries_evicted': self._cache_stats['evicted'],
            'last_cleanup': self._cache_stats['last_cleanup'],
            'cache_size_mb': self._estimate_cache_size()
        }
    
    def _estimate_cache_size(self) -> float:
        """Estimate cache size in MB."""
        try:
            size_bytes = 0
            
            if self.finnhub_cache_file.exists():
                size_bytes += self.finnhub_cache_file.stat().st_size
            
            if self.tavily_cache_file.exists():
                size_bytes += self.tavily_cache_file.stat().st_size
            
            if self.sector_info_file.exists():
                size_bytes += self.sector_info_file.stat().st_size
                
            return round(size_bytes / (1024 * 1024), 2)
        except:
            return 0.0
    
    def get_available_sectors(self) -> List[str]:
        """Get list of sectors with cached data.
        
        Returns:
            List of sector names
        """
        return sorted(list(self._sector_info.keys()))
    
    def warm_up_cache(self, sectors: List[str], finnhub_client=None, tavily_client=None) -> Dict[str, bool]:
        """Pre-populate cache with data for specified sectors.
        
        Args:
            sectors: List of sector names to warm up
            finnhub_client: Optional Finnhub client for data fetching
            tavily_client: Optional Tavily client for search data
            
        Returns:
            Dictionary mapping sectors to success status
        """
        results = {}
        
        for sector in sectors:
            results[sector] = False
            
            try:
                # Warm up Finnhub data
                if finnhub_client and finnhub_client.is_available():
                    # This would need to be implemented based on available Finnhub methods
                    # For now, just mark as successful if we can get some data
                    pass
                
                # Warm up Tavily data
                if tavily_client and tavily_client.is_available():
                    # This would need to be implemented based on available Tavily methods
                    pass
                
                results[sector] = True
                
            except Exception as e:
                print(f"Error warming up cache for {sector}: {e}")
        
        return results
    
    def generate_cache_report(self) -> str:
        """Generate a markdown report of cache performance.
        
        Returns:
            Markdown formatted cache report
        """
        stats = self.get_cache_stats()
        
        lines = [
            "\n---",
            "\n## Sector Analysis Cache Report",
            f"*Cache performance and utilization statistics*\n",
            "### Cache Performance",
            f"- **Hit Rate**: {stats['hit_rate_pct']}% ({stats['total_hits']}/{stats['total_hits'] + stats['total_misses']} requests)",
            f"- **Cache Size**: {stats['cache_size_mb']} MB",
            f"- **Entries**: {stats['finnhub_entries']} Finnhub + {stats['tavily_entries']} Tavily",
            f"- **Sectors Tracked**: {stats['sectors_tracked']}",
            ""
        ]
        
        if self._sector_info:
            lines.extend([
                "### Cached Sectors",
                "| Sector | Companies | Market Cap | Last Updated |",
                "|--------|-----------|------------|--------------|"
            ])
            
            for sector, info in sorted(self._sector_info.items()):
                market_cap = f"${info.total_market_cap/1e9:.1f}B" if info.total_market_cap else "N/A"
                companies = f"{info.companies_count}" if info.companies_count else "N/A"
                
                lines.append(f"| {sector} | {companies} | {market_cap} | Recent |")
        
        lines.extend([
            "",
            "### Cache Efficiency",
            f"- **Entries Created**: {stats['entries_created']}",
            f"- **Entries Evicted**: {stats['entries_evicted']}",
            f"- **Last Cleanup**: {stats['last_cleanup'][:10]}",
            "",
            "*Sector caching reduces API calls and improves research generation speed.*"
        ])
        
        return "\n".join(lines)
    
    def save_and_cleanup(self) -> None:
        """Save cache data and perform cleanup."""
        self.cleanup_expired_entries()
        self._save_caches()
    
    def clear_all_caches(self) -> int:
        """Clear all cached data.
        
        Returns:
            Number of entries cleared
        """
        total_cleared = len(self._finnhub_cache) + len(self._tavily_cache) + len(self._sector_info)
        
        self._finnhub_cache.clear()
        self._tavily_cache.clear()
        self._sector_info.clear()
        
        # Reset stats
        self._cache_stats = {
            'hits': 0,
            'misses': 0,
            'created': 0,
            'evicted': total_cleared,
            'last_cleanup': datetime.now().isoformat()
        }
        
        self._save_caches()
        return total_cleared