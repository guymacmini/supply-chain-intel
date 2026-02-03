"""API authentication and authorization system."""

import hashlib
import secrets
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
from functools import wraps
from flask import request, jsonify, current_app


class APIKeyManager:
    """Manages API keys for REST API access."""
    
    def __init__(self, data_dir: Path):
        """Initialize API key manager.
        
        Args:
            data_dir: Directory to store API key data
        """
        self.data_dir = data_dir
        self.keys_dir = data_dir / 'api_keys'
        self.keys_dir.mkdir(parents=True, exist_ok=True)
        
        self.keys_file = self.keys_dir / 'api_keys.json'
        self.usage_file = self.keys_dir / 'api_usage.json'
        
        # Load existing keys
        self.api_keys = self._load_api_keys()
        self.usage_stats = self._load_usage_stats()
    
    def _load_api_keys(self) -> Dict[str, Dict]:
        """Load API keys from file."""
        if not self.keys_file.exists():
            return {}
        
        try:
            with open(self.keys_file, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    
    def _save_api_keys(self) -> None:
        """Save API keys to file."""
        try:
            with open(self.keys_file, 'w') as f:
                json.dump(self.api_keys, f, indent=2)
        except Exception as e:
            print(f"Error saving API keys: {e}")
    
    def _load_usage_stats(self) -> Dict[str, Dict]:
        """Load usage statistics from file."""
        if not self.usage_file.exists():
            return {}
        
        try:
            with open(self.usage_file, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    
    def _save_usage_stats(self) -> None:
        """Save usage statistics to file."""
        try:
            with open(self.usage_file, 'w') as f:
                json.dump(self.usage_stats, f, indent=2)
        except Exception as e:
            print(f"Error saving usage stats: {e}")
    
    def create_api_key(self, name: str, description: str = "", 
                      rate_limit: int = 1000) -> Dict[str, str]:
        """Create a new API key.
        
        Args:
            name: Name for the API key
            description: Optional description
            rate_limit: Requests per hour limit
            
        Returns:
            Dictionary with key information
        """
        # Generate a secure API key
        api_key = f"sci_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        key_data = {
            'name': name,
            'description': description,
            'key_hash': key_hash,
            'created_at': datetime.now().isoformat(),
            'rate_limit': rate_limit,
            'active': True,
            'last_used': None,
            'total_requests': 0
        }
        
        self.api_keys[api_key] = key_data
        self.usage_stats[api_key] = {
            'requests_today': 0,
            'last_request_date': None,
            'hourly_requests': {}
        }
        
        self._save_api_keys()
        self._save_usage_stats()
        
        return {
            'api_key': api_key,
            'name': name,
            'created_at': key_data['created_at'],
            'rate_limit': rate_limit
        }
    
    def validate_api_key(self, api_key: str) -> Optional[Dict]:
        """Validate an API key and return key data if valid.
        
        Args:
            api_key: API key to validate
            
        Returns:
            Key data if valid, None otherwise
        """
        if not api_key or api_key not in self.api_keys:
            return None
        
        key_data = self.api_keys[api_key]
        
        # Check if key is active
        if not key_data.get('active', True):
            return None
        
        # Check rate limiting
        if not self._check_rate_limit(api_key):
            return None
        
        # Update usage statistics
        self._record_usage(api_key)
        
        return key_data
    
    def _check_rate_limit(self, api_key: str) -> bool:
        """Check if API key is within rate limits.
        
        Args:
            api_key: API key to check
            
        Returns:
            True if within limits, False otherwise
        """
        key_data = self.api_keys.get(api_key)
        if not key_data:
            return False
        
        rate_limit = key_data.get('rate_limit', 1000)
        usage_data = self.usage_stats.get(api_key, {})
        
        # Check hourly limit
        current_hour = datetime.now().strftime('%Y-%m-%d-%H')
        hourly_requests = usage_data.get('hourly_requests', {})
        
        if hourly_requests.get(current_hour, 0) >= rate_limit:
            return False
        
        return True
    
    def _record_usage(self, api_key: str) -> None:
        """Record API usage for an API key.
        
        Args:
            api_key: API key that was used
        """
        now = datetime.now()
        current_date = now.strftime('%Y-%m-%d')
        current_hour = now.strftime('%Y-%m-%d-%H')
        
        # Update key data
        if api_key in self.api_keys:
            self.api_keys[api_key]['last_used'] = now.isoformat()
            self.api_keys[api_key]['total_requests'] += 1
        
        # Update usage stats
        if api_key not in self.usage_stats:
            self.usage_stats[api_key] = {
                'requests_today': 0,
                'last_request_date': None,
                'hourly_requests': {}
            }
        
        usage_data = self.usage_stats[api_key]
        
        # Reset daily count if it's a new day
        if usage_data.get('last_request_date') != current_date:
            usage_data['requests_today'] = 0
            usage_data['last_request_date'] = current_date
        
        usage_data['requests_today'] += 1
        
        # Update hourly count
        if 'hourly_requests' not in usage_data:
            usage_data['hourly_requests'] = {}
        
        usage_data['hourly_requests'][current_hour] = usage_data['hourly_requests'].get(current_hour, 0) + 1
        
        # Clean up old hourly data (keep last 24 hours)
        cutoff_time = now - timedelta(hours=24)
        cutoff_hour = cutoff_time.strftime('%Y-%m-%d-%H')
        
        old_hours = [h for h in usage_data['hourly_requests'].keys() if h < cutoff_hour]
        for old_hour in old_hours:
            del usage_data['hourly_requests'][old_hour]
        
        # Save periodically (every 10 requests)
        if usage_data['requests_today'] % 10 == 0:
            self._save_api_keys()
            self._save_usage_stats()
    
    def deactivate_key(self, api_key: str) -> bool:
        """Deactivate an API key.
        
        Args:
            api_key: API key to deactivate
            
        Returns:
            True if successful, False otherwise
        """
        if api_key in self.api_keys:
            self.api_keys[api_key]['active'] = False
            self._save_api_keys()
            return True
        return False
    
    def list_keys(self) -> list:
        """List all API keys with usage statistics.
        
        Returns:
            List of API key information
        """
        keys_info = []
        
        for api_key, key_data in self.api_keys.items():
            usage_data = self.usage_stats.get(api_key, {})
            
            # Mask the actual key for security
            masked_key = f"{api_key[:8]}...{api_key[-4:]}"
            
            keys_info.append({
                'masked_key': masked_key,
                'name': key_data.get('name'),
                'description': key_data.get('description'),
                'created_at': key_data.get('created_at'),
                'active': key_data.get('active', True),
                'rate_limit': key_data.get('rate_limit'),
                'total_requests': key_data.get('total_requests', 0),
                'requests_today': usage_data.get('requests_today', 0),
                'last_used': key_data.get('last_used')
            })
        
        return sorted(keys_info, key=lambda x: x['created_at'], reverse=True)
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get overall usage statistics.
        
        Returns:
            Dictionary with usage statistics
        """
        total_keys = len(self.api_keys)
        active_keys = sum(1 for k in self.api_keys.values() if k.get('active', True))
        total_requests = sum(k.get('total_requests', 0) for k in self.api_keys.values())
        
        today = datetime.now().strftime('%Y-%m-%d')
        requests_today = sum(
            u.get('requests_today', 0) 
            for u in self.usage_stats.values() 
            if u.get('last_request_date') == today
        )
        
        return {
            'total_keys': total_keys,
            'active_keys': active_keys,
            'total_requests': total_requests,
            'requests_today': requests_today,
            'last_updated': datetime.now().isoformat()
        }


def require_api_key(api_key_manager: APIKeyManager):
    """Decorator to require valid API key for endpoint access.
    
    Args:
        api_key_manager: APIKeyManager instance
        
    Returns:
        Decorator function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get API key from header or query parameter
            api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
            
            if not api_key:
                return jsonify({
                    'error': 'API key required',
                    'message': 'Provide API key via X-API-Key header or api_key parameter'
                }), 401
            
            # Validate API key
            key_data = api_key_manager.validate_api_key(api_key)
            if not key_data:
                return jsonify({
                    'error': 'Invalid or rate-limited API key',
                    'message': 'Check your API key and rate limits'
                }), 403
            
            # Add key data to request context
            request.api_key_data = key_data
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def create_default_api_key(api_key_manager: APIKeyManager) -> Optional[str]:
    """Create a default API key if none exist.
    
    Args:
        api_key_manager: APIKeyManager instance
        
    Returns:
        Default API key if created, None otherwise
    """
    if not api_key_manager.api_keys:
        key_info = api_key_manager.create_api_key(
            name="Default Development Key",
            description="Auto-generated development API key",
            rate_limit=5000
        )
        print(f"Created default API key: {key_info['api_key']}")
        return key_info['api_key']
    
    return None