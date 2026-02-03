"""Advanced configuration management system."""

import json
import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass, asdict, field
from datetime import datetime
import logging


@dataclass
class DatabaseConfig:
    """Database configuration."""
    host: str = "localhost"
    port: int = 5432
    database: str = "supply_chain_intel"
    username: str = "user"
    password: str = ""
    ssl_mode: str = "prefer"


@dataclass
class APIConfig:
    """API service configuration."""
    finnhub_key: str = ""
    tavily_key: str = ""
    openai_key: str = ""
    anthropic_key: str = ""
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    timeout_seconds: int = 30


@dataclass 
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    enable_console: bool = True
    enable_file: bool = True


@dataclass
class WebhookConfig:
    """Webhook configuration."""
    default_timeout: int = 30
    retry_attempts: int = 3
    retry_delay: int = 5
    enabled_platforms: List[str] = field(default_factory=lambda: ["slack", "discord", "teams"])


@dataclass
class PerformanceConfig:
    """Performance and caching configuration."""
    cache_enabled: bool = True
    cache_ttl: int = 3600  # 1 hour
    max_cache_size: int = 1000
    background_workers: int = 4
    request_batch_size: int = 10


@dataclass
class AlertConfig:
    """Alert system configuration."""
    enabled: bool = True
    check_interval: int = 300  # 5 minutes
    max_alerts_per_hour: int = 20
    email_enabled: bool = False
    webhook_enabled: bool = True


@dataclass
class SecurityConfig:
    """Security configuration."""
    api_key_length: int = 32
    session_timeout: int = 86400  # 24 hours
    max_failed_attempts: int = 5
    lockout_duration: int = 900  # 15 minutes
    encryption_enabled: bool = True


@dataclass
class SystemConfig:
    """Complete system configuration."""
    version: str = "1.0.0"
    environment: str = "development"
    debug: bool = False
    data_dir: str = "./data"
    temp_dir: str = "./tmp"
    backup_enabled: bool = True
    backup_retention_days: int = 30
    
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    api: APIConfig = field(default_factory=APIConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    webhooks: WebhookConfig = field(default_factory=WebhookConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    alerts: AlertConfig = field(default_factory=AlertConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    
    # Runtime tracking
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


class ConfigurationManager:
    """Advanced configuration manager with environment support."""
    
    def __init__(self, config_dir: Optional[Path] = None, environment: str = None):
        """Initialize configuration manager.
        
        Args:
            config_dir: Configuration directory path
            environment: Environment name (dev, staging, prod)
        """
        if config_dir is None:
            config_dir = Path(__file__).parent.parent.parent / 'config'
        
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        # Determine environment
        self.environment = environment or os.getenv('SUPPLY_CHAIN_ENV', 'development')
        
        # Configuration files
        self.base_config_file = self.config_dir / 'config.yml'
        self.env_config_file = self.config_dir / f'config.{self.environment}.yml'
        self.local_config_file = self.config_dir / 'config.local.yml'
        self.secrets_file = self.config_dir / '.secrets.yml'
        
        # Load configuration
        self._config = self._load_config()
        
        # Setup logging if configured
        self._setup_logging()
    
    def _load_config(self) -> SystemConfig:
        """Load configuration from multiple sources with precedence."""
        # Start with default configuration
        config_dict = asdict(SystemConfig())
        
        # Layer on configurations in order of precedence
        configs_to_load = [
            self.base_config_file,
            self.env_config_file,
            self.local_config_file
        ]
        
        for config_file in configs_to_load:
            if config_file.exists():
                try:
                    file_config = self._load_yaml_file(config_file)
                    config_dict = self._deep_merge(config_dict, file_config)
                except Exception as e:
                    logging.warning(f"Failed to load config file {config_file}: {e}")
        
        # Load secrets separately (not merged, just API keys)
        if self.secrets_file.exists():
            try:
                secrets = self._load_yaml_file(self.secrets_file)
                if 'api' in secrets:
                    config_dict.setdefault('api', {}).update(secrets['api'])
            except Exception as e:
                logging.warning(f"Failed to load secrets file: {e}")
        
        # Override with environment variables
        config_dict = self._apply_environment_overrides(config_dict)
        
        # Convert back to dataclass
        return self._dict_to_config(config_dict)
    
    def _load_yaml_file(self, file_path: Path) -> Dict[str, Any]:
        """Load YAML configuration file."""
        try:
            with open(file_path, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logging.error(f"Error loading YAML file {file_path}: {e}")
            return {}
    
    def _deep_merge(self, base: Dict, overlay: Dict) -> Dict:
        """Deep merge two dictionaries."""
        result = base.copy()
        
        for key, value in overlay.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _apply_environment_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides."""
        env_mappings = {
            'SCI_DEBUG': ('debug', bool),
            'SCI_DATA_DIR': ('data_dir', str),
            'SCI_LOG_LEVEL': ('logging.level', str),
            'SCI_API_TIMEOUT': ('api.timeout_seconds', int),
            'SCI_CACHE_ENABLED': ('performance.cache_enabled', bool),
            'SCI_WEBHOOK_TIMEOUT': ('webhooks.default_timeout', int),
            'SCI_ALERT_INTERVAL': ('alerts.check_interval', int),
            'FINNHUB_API_KEY': ('api.finnhub_key', str),
            'TAVILY_API_KEY': ('api.tavily_key', str),
            'OPENAI_API_KEY': ('api.openai_key', str),
            'ANTHROPIC_API_KEY': ('api.anthropic_key', str),
        }
        
        for env_var, (config_path, data_type) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    # Convert value to appropriate type
                    if data_type == bool:
                        value = value.lower() in ('true', '1', 'yes', 'on')
                    elif data_type == int:
                        value = int(value)
                    
                    # Set nested config value
                    self._set_nested_value(config, config_path, value)
                    
                except (ValueError, TypeError) as e:
                    logging.warning(f"Invalid environment variable {env_var}={value}: {e}")
        
        return config
    
    def _set_nested_value(self, config: Dict, path: str, value: Any):
        """Set a nested dictionary value using dot notation."""
        keys = path.split('.')
        current = config
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def _dict_to_config(self, config_dict: Dict[str, Any]) -> SystemConfig:
        """Convert dictionary to SystemConfig dataclass."""
        try:
            # Handle nested dataclasses
            if 'database' in config_dict:
                config_dict['database'] = DatabaseConfig(**config_dict['database'])
            if 'api' in config_dict:
                config_dict['api'] = APIConfig(**config_dict['api'])
            if 'logging' in config_dict:
                config_dict['logging'] = LoggingConfig(**config_dict['logging'])
            if 'webhooks' in config_dict:
                config_dict['webhooks'] = WebhookConfig(**config_dict['webhooks'])
            if 'performance' in config_dict:
                config_dict['performance'] = PerformanceConfig(**config_dict['performance'])
            if 'alerts' in config_dict:
                config_dict['alerts'] = AlertConfig(**config_dict['alerts'])
            if 'security' in config_dict:
                config_dict['security'] = SecurityConfig(**config_dict['security'])
            
            return SystemConfig(**config_dict)
            
        except Exception as e:
            logging.error(f"Error converting config dict to dataclass: {e}")
            return SystemConfig()
    
    def _setup_logging(self):
        """Setup logging based on configuration."""
        log_config = self._config.logging
        
        # Configure root logger
        logger = logging.getLogger()
        logger.setLevel(getattr(logging, log_config.level.upper()))
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Create formatter
        formatter = logging.Formatter(log_config.format)
        
        # Console handler
        if log_config.enable_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        # File handler
        if log_config.enable_file and log_config.file_path:
            from logging.handlers import RotatingFileHandler
            
            log_dir = Path(log_config.file_path).parent
            log_dir.mkdir(parents=True, exist_ok=True)
            
            file_handler = RotatingFileHandler(
                log_config.file_path,
                maxBytes=log_config.max_file_size,
                backupCount=log_config.backup_count
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
    
    @property
    def config(self) -> SystemConfig:
        """Get current configuration."""
        return self._config
    
    def get(self, path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation.
        
        Args:
            path: Dot-separated path (e.g., 'api.timeout_seconds')
            default: Default value if path not found
            
        Returns:
            Configuration value or default
        """
        try:
            current = asdict(self._config)
            for key in path.split('.'):
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default
    
    def set(self, path: str, value: Any):
        """Set configuration value using dot notation.
        
        Args:
            path: Dot-separated path
            value: Value to set
        """
        config_dict = asdict(self._config)
        self._set_nested_value(config_dict, path, value)
        config_dict['updated_at'] = datetime.now().isoformat()
        self._config = self._dict_to_config(config_dict)
    
    def save_config(self, include_secrets: bool = False):
        """Save current configuration to file.
        
        Args:
            include_secrets: Whether to save API keys to secrets file
        """
        try:
            config_dict = asdict(self._config)
            
            # Remove sensitive data for main config
            safe_config = config_dict.copy()
            if 'api' in safe_config and not include_secrets:
                api_keys = ['finnhub_key', 'tavily_key', 'openai_key', 'anthropic_key']
                for key in api_keys:
                    if key in safe_config['api']:
                        safe_config['api'][key] = '[REDACTED]'
            
            # Save main config
            with open(self.env_config_file, 'w') as f:
                yaml.dump(safe_config, f, default_flow_style=False, indent=2)
            
            # Save secrets separately if requested
            if include_secrets and 'api' in config_dict:
                secrets = {'api': {}}
                api_keys = ['finnhub_key', 'tavily_key', 'openai_key', 'anthropic_key']
                for key in api_keys:
                    if key in config_dict['api'] and config_dict['api'][key]:
                        secrets['api'][key] = config_dict['api'][key]
                
                if secrets['api']:
                    with open(self.secrets_file, 'w') as f:
                        yaml.dump(secrets, f, default_flow_style=False, indent=2)
                    
                    # Secure the secrets file
                    os.chmod(self.secrets_file, 0o600)
            
            logging.info(f"Configuration saved to {self.env_config_file}")
            
        except Exception as e:
            logging.error(f"Failed to save configuration: {e}")
    
    def validate_config(self) -> Dict[str, List[str]]:
        """Validate current configuration.
        
        Returns:
            Dictionary of validation errors by section
        """
        errors = {}
        
        # Validate API keys
        api_errors = []
        if not self._config.api.finnhub_key:
            api_errors.append("Finnhub API key is missing")
        if not self._config.api.tavily_key:
            api_errors.append("Tavily API key is missing")
        
        if api_errors:
            errors['api'] = api_errors
        
        # Validate data directories
        data_errors = []
        data_dir = Path(self._config.data_dir)
        if not data_dir.exists():
            try:
                data_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                data_errors.append(f"Cannot create data directory: {e}")
        
        if data_errors:
            errors['data'] = data_errors
        
        # Validate logging configuration
        log_errors = []
        if self._config.logging.level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            log_errors.append(f"Invalid log level: {self._config.logging.level}")
        
        if log_errors:
            errors['logging'] = log_errors
        
        return errors
    
    def create_sample_config(self):
        """Create sample configuration files."""
        # Base config
        sample_config = {
            'version': '1.0.0',
            'environment': 'development',
            'debug': False,
            'data_dir': './data',
            'logging': {
                'level': 'INFO',
                'enable_console': True,
                'enable_file': True,
                'file_path': './logs/supply_chain_intel.log'
            },
            'api': {
                'rate_limit_requests': 100,
                'timeout_seconds': 30
            },
            'performance': {
                'cache_enabled': True,
                'cache_ttl': 3600
            },
            'alerts': {
                'enabled': True,
                'check_interval': 300
            },
            'webhooks': {
                'default_timeout': 30,
                'enabled_platforms': ['slack', 'discord']
            }
        }
        
        # Sample secrets
        sample_secrets = {
            'api': {
                'finnhub_key': 'your_finnhub_api_key_here',
                'tavily_key': 'your_tavily_api_key_here',
                'openai_key': 'your_openai_api_key_here',
                'anthropic_key': 'your_anthropic_api_key_here'
            }
        }
        
        # Write sample files
        sample_config_file = self.config_dir / 'config.sample.yml'
        sample_secrets_file = self.config_dir / '.secrets.sample.yml'
        
        with open(sample_config_file, 'w') as f:
            yaml.dump(sample_config, f, default_flow_style=False, indent=2)
        
        with open(sample_secrets_file, 'w') as f:
            yaml.dump(sample_secrets, f, default_flow_style=False, indent=2)
        
        print(f"Sample configuration files created:")
        print(f"  Config: {sample_config_file}")
        print(f"  Secrets: {sample_secrets_file}")
        print(f"\nCopy these files and customize for your environment:")
        print(f"  cp {sample_config_file} {self.base_config_file}")
        print(f"  cp {sample_secrets_file} {self.secrets_file}")


# Global configuration manager instance
_config_manager = None

def get_config_manager(config_dir: Optional[Path] = None, environment: str = None) -> ConfigurationManager:
    """Get global configuration manager instance."""
    global _config_manager
    
    if _config_manager is None:
        _config_manager = ConfigurationManager(config_dir, environment)
    
    return _config_manager

def get_config() -> SystemConfig:
    """Get current system configuration."""
    return get_config_manager().config