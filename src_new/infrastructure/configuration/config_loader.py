"""Configuration loader and management system.

This module provides centralized configuration management for the QuantumFlux trading platform,
supporting multiple environments and configuration sources.
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from functools import lru_cache


@dataclass
class DatabaseConfig:
    """Database configuration."""
    type: str
    url: str
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10
    ssl_require: bool = False


@dataclass
class TradingConfig:
    """Trading configuration."""
    platform: str
    demo_mode: bool = True
    default_stake_amount: float = 10.0
    max_concurrent_trades: int = 3
    max_daily_trades: int = 50
    risk_management: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MarketDataConfig:
    """Market data configuration."""
    providers: Dict[str, str] = field(default_factory=dict)
    cache: Dict[str, Any] = field(default_factory=dict)
    real_time: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategyConfig:
    """Strategy configuration."""
    default_timeframe: str = "1m"
    signal_strength_threshold: str = "MODERATE"
    backtest: Dict[str, Any] = field(default_factory=dict)
    validation: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WebDriverConfig:
    """WebDriver configuration."""
    browser: str = "chrome"
    headless: bool = False
    implicit_wait: int = 10
    page_load_timeout: int = 30
    window_size: Dict[str, int] = field(default_factory=lambda: {"width": 1920, "height": 1080})
    options: list = field(default_factory=list)


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    handlers: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SecurityConfig:
    """Security configuration."""
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    session_timeout_minutes: int = 60
    rate_limiting: Dict[str, Any] = field(default_factory=dict)
    encryption: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AppConfig:
    """Main application configuration."""
    name: str
    version: str
    environment: str
    debug: bool = False
    log_level: str = "INFO"


@dataclass
class APIConfig:
    """API configuration."""
    host: str = "localhost"
    port: int = 8000
    reload: bool = False
    workers: int = 1
    cors_origins: list = field(default_factory=list)
    rate_limiting: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Config:
    """Main configuration container."""
    app: AppConfig
    api: APIConfig
    database: DatabaseConfig
    trading: TradingConfig
    market_data: MarketDataConfig
    strategy: StrategyConfig
    webdriver: WebDriverConfig
    logging: LoggingConfig
    security: SecurityConfig
    monitoring: Dict[str, Any] = field(default_factory=dict)
    external_services: Dict[str, Any] = field(default_factory=dict)
    testing: Dict[str, Any] = field(default_factory=dict)
    deployment: Dict[str, Any] = field(default_factory=dict)


class ConfigLoader:
    """Configuration loader with environment support."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize configuration loader.
        
        Args:
            config_dir: Path to configuration directory. Defaults to project config_new directory.
        """
        if config_dir is None:
            # Default to config_new directory relative to project root
            project_root = Path(__file__).parent.parent.parent.parent
            config_dir = project_root / "config_new"
        
        self.config_dir = Path(config_dir)
        self.environment = os.getenv("ENVIRONMENT", "development")
        self._config_cache: Optional[Config] = None
    
    def load_config(self, environment: Optional[str] = None) -> Config:
        """Load configuration for specified environment.
        
        Args:
            environment: Environment name. Defaults to ENVIRONMENT env var or 'development'.
            
        Returns:
            Loaded configuration object.
            
        Raises:
            FileNotFoundError: If configuration file doesn't exist.
            yaml.YAMLError: If configuration file is invalid YAML.
        """
        env = environment or self.environment
        config_file = self.config_dir / "environments" / env / "settings.yaml"
        
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        # Substitute environment variables
        config_data = self._substitute_env_vars(config_data)
        
        # Create configuration objects
        return self._create_config_objects(config_data)
    
    def _substitute_env_vars(self, data: Any) -> Any:
        """Recursively substitute environment variables in configuration data.
        
        Args:
            data: Configuration data (dict, list, or primitive).
            
        Returns:
            Data with environment variables substituted.
        """
        if isinstance(data, dict):
            return {key: self._substitute_env_vars(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._substitute_env_vars(item) for item in data]
        elif isinstance(data, str) and data.startswith("${") and data.endswith("}"):
            env_var = data[2:-1]
            return os.getenv(env_var, data)  # Return original if env var not found
        else:
            return data
    
    def _create_config_objects(self, config_data: Dict[str, Any]) -> Config:
        """Create configuration objects from loaded data.
        
        Args:
            config_data: Raw configuration data.
            
        Returns:
            Structured configuration object.
        """
        return Config(
            app=AppConfig(**config_data.get("app", {})),
            api=APIConfig(**config_data.get("api", {})),
            database=DatabaseConfig(**config_data.get("database", {})),
            trading=TradingConfig(**config_data.get("trading", {})),
            market_data=MarketDataConfig(**config_data.get("market_data", {})),
            strategy=StrategyConfig(**config_data.get("strategy", {})),
            webdriver=WebDriverConfig(**config_data.get("webdriver", {})),
            logging=LoggingConfig(**config_data.get("logging", {})),
            security=SecurityConfig(**config_data.get("security", {})),
            monitoring=config_data.get("monitoring", {}),
            external_services=config_data.get("external_services", {}),
            testing=config_data.get("testing", {}),
            deployment=config_data.get("deployment", {})
        )
    
    @lru_cache(maxsize=1)
    def get_config(self) -> Config:
        """Get cached configuration.
        
        Returns:
            Cached configuration object.
        """
        if self._config_cache is None:
            self._config_cache = self.load_config()
        return self._config_cache
    
    def reload_config(self) -> Config:
        """Reload configuration from file.
        
        Returns:
            Reloaded configuration object.
        """
        self._config_cache = None
        self.get_config.cache_clear()
        return self.get_config()


# Global configuration loader instance
_config_loader = ConfigLoader()


def get_config() -> Config:
    """Get global configuration instance.
    
    Returns:
        Global configuration object.
    """
    return _config_loader.get_config()


def reload_config() -> Config:
    """Reload global configuration.
    
    Returns:
        Reloaded configuration object.
    """
    return _config_loader.reload_config()


def set_environment(environment: str) -> None:
    """Set configuration environment.
    
    Args:
        environment: Environment name (development, staging, production).
    """
    global _config_loader
    _config_loader.environment = environment
    _config_loader._config_cache = None
    _config_loader.get_config.cache_clear()