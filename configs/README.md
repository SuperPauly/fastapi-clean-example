# Configs Directory (`configs/`)

The **Configs Directory** contains configuration files and settings management for different environments and application components. This directory handles environment-specific configurations, logging setup, and system settings that control application behavior.

## 🎯 Purpose & Role in Hexagon Architecture

Configuration management serves as **environment adaptation support** that:
- **Manages environment-specific settings** (development, testing, production)
- **Configures external service connections** (databases, Redis, APIs)
- **Sets up logging and monitoring** configurations
- **Handles feature flags** and application behavior toggles
- **Provides secure credential management** patterns

## 🏗️ Key Responsibilities

### 1. **Environment Management**
- Development, testing, staging, and production configurations
- Environment variable handling and validation
- Configuration inheritance and overrides

### 2. **Service Configuration**
- Database connection settings
- External API configurations
- Caching and message queue setup

### 3. **Application Behavior**
- Feature flags and toggles
- Performance tuning parameters
- Security and authentication settings

## 📁 Config Structure

```
configs/
├── logging/               # Logging configuration files
│   ├── development.yaml   # Development logging config
│   ├── production.yaml    # Production logging config
│   └── testing.yaml       # Testing logging config
├── app_config.py         # Main application configuration
├── database_config.py    # Database configuration
└── README.md             # This file
```

## 🔧 Implementation Examples

### Main Application Configuration

```python
# configs/app_config.py
from pydantic import BaseSettings, Field, validator
from typing import Optional, List, Dict, Any
from pathlib import Path
import os

class AppConfig(BaseSettings):
    """
    Main application configuration using Pydantic BaseSettings.
    
    Automatically loads configuration from environment variables,
    .env files, and provides validation and type conversion.
    """
    
    # Application Basic Settings
    app_name: str = Field(default="FastAPI Clean Architecture", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=False, description="Enable debug mode")
    environment: str = Field(default="development", description="Environment name")
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, ge=1, le=65535, description="Server port")
    reload: bool = Field(default=False, description="Enable auto-reload")
    workers: int = Field(default=1, ge=1, description="Number of worker processes")
    
    # Database Configuration
    database_url: str = Field(
        default="postgresql://user:password@localhost:5432/fastapi_clean",
        description="Database connection URL"
    )
    database_echo: bool = Field(default=False, description="Enable SQL query logging")
    database_pool_size: int = Field(default=5, ge=1, description="Database connection pool size")
    database_max_overflow: int = Field(default=10, ge=0, description="Database max overflow connections")
    
    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")
    redis_password: Optional[str] = Field(default=None, description="Redis password")
    redis_max_connections: int = Field(default=20, ge=1, description="Redis max connections")
    
    # Task Queue Configuration
    taskiq_broker_url: str = Field(default="redis://localhost:6379/0", description="Taskiq broker URL")
    taskiq_result_backend_url: str = Field(default="redis://localhost:6379/1", description="Taskiq result backend URL")
    taskiq_workers: int = Field(default=2, ge=1, description="Number of task workers")
    
    # Security Settings
    secret_key: str = Field(default="your-secret-key-change-in-production", description="Secret key for signing")
    allowed_hosts: List[str] = Field(default=["*"], description="Allowed hosts for CORS")
    cors_origins: List[str] = Field(default=["*"], description="CORS allowed origins")
    
    # API Configuration
    api_prefix: str = Field(default="/api/v1", description="API URL prefix")
    docs_url: Optional[str] = Field(default="/docs", description="Swagger UI URL")
    redoc_url: Optional[str] = Field(default="/redoc", description="ReDoc URL")
    openapi_url: Optional[str] = Field(default="/openapi.json", description="OpenAPI schema URL")
    
    # Pagination Settings
    default_page_size: int = Field(default=20, ge=1, le=100, description="Default pagination size")
    max_page_size: int = Field(default=100, ge=1, description="Maximum pagination size")
    
    # Cache Settings
    cache_ttl: int = Field(default=3600, ge=0, description="Default cache TTL in seconds")
    enable_caching: bool = Field(default=True, description="Enable application caching")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log message format"
    )
    log_file: Optional[str] = Field(default=None, description="Log file path")
    
    # Feature Flags
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")
    enable_tracing: bool = Field(default=False, description="Enable distributed tracing")
    enable_rate_limiting: bool = Field(default=True, description="Enable API rate limiting")
    
    # External Services
    email_service_url: Optional[str] = Field(default=None, description="Email service URL")
    email_service_api_key: Optional[str] = Field(default=None, description="Email service API key")
    
    # File Upload Settings
    max_file_size_mb: int = Field(default=10, ge=1, description="Maximum file upload size in MB")
    upload_directory: str = Field(default="uploads", description="File upload directory")
    
    @validator('environment')
    def validate_environment(cls, v):
        """Validate environment value."""
        allowed_environments = ['development', 'testing', 'staging', 'production']
        if v not in allowed_environments:
            raise ValueError(f'Environment must be one of: {allowed_environments}')
        return v
    
    @validator('log_level')
    def validate_log_level(cls, v):
        """Validate log level."""
        allowed_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in allowed_levels:
            raise ValueError(f'Log level must be one of: {allowed_levels}')
        return v.upper()
    
    @validator('secret_key')
    def validate_secret_key(cls, v, values):
        """Validate secret key in production."""
        if values.get('environment') == 'production' and v == 'your-secret-key-change-in-production':
            raise ValueError('Secret key must be changed in production environment')
        return v
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == 'development'
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == 'production'
    
    @property
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.environment == 'testing'
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration dictionary."""
        return {
            'url': self.database_url,
            'echo': self.database_echo,
            'pool_size': self.database_pool_size,
            'max_overflow': self.database_max_overflow
        }
    
    def get_redis_config(self) -> Dict[str, Any]:
        """Get Redis configuration dictionary."""
        return {
            'url': self.redis_url,
            'password': self.redis_password,
            'max_connections': self.redis_max_connections
        }
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
        # Example environment variables
        schema_extra = {
            "example": {
                "APP_NAME": "My FastAPI App",
                "ENVIRONMENT": "production",
                "DATABASE_URL": "postgresql://user:pass@localhost/db",
                "REDIS_URL": "redis://localhost:6379/0",
                "SECRET_KEY": "your-production-secret-key",
                "LOG_LEVEL": "INFO"
            }
        }

# Global configuration instance
config = AppConfig()
```

### Database Configuration

```python
# configs/database_config.py
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator
from .app_config import config

class DatabaseConfig:
    """Database configuration and session management."""
    
    def __init__(self):
        self.database_url = config.database_url
        self.async_database_url = self._convert_to_async_url(config.database_url)
        
        # Create engines
        self.engine = create_engine(
            self.database_url,
            echo=config.database_echo,
            pool_size=config.database_pool_size,
            max_overflow=config.database_max_overflow
        )
        
        self.async_engine = create_async_engine(
            self.async_database_url,
            echo=config.database_echo,
            pool_size=config.database_pool_size,
            max_overflow=config.database_max_overflow
        )
        
        # Create session factories
        self.SessionLocal = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False
        )
        
        self.AsyncSessionLocal = sessionmaker(
            bind=self.async_engine,
            class_=AsyncSession,
            autocommit=False,
            autoflush=False
        )
    
    def _convert_to_async_url(self, url: str) -> str:
        """Convert synchronous database URL to async version."""
        if url.startswith('postgresql://'):
            return url.replace('postgresql://', 'postgresql+asyncpg://', 1)
        elif url.startswith('sqlite://'):
            return url.replace('sqlite://', 'sqlite+aiosqlite://', 1)
        return url
    
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get async database session."""
        async with self.AsyncSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    def get_session(self):
        """Get synchronous database session."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

# Global database configuration
db_config = DatabaseConfig()
```

### Logging Configuration Files

```yaml
# configs/logging/development.yaml
version: 1
disable_existing_loggers: false

formatters:
  default:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    datefmt: '%Y-%m-%d %H:%M:%S'
  
  detailed:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(lineno)d - %(message)s'
    datefmt: '%Y-%m-%d %H:%M:%S'

handlers:
  console:
    class: logging.StreamHandler
    level: DEBUG
    formatter: detailed
    stream: ext://sys.stdout
  
  file:
    class: logging.handlers.RotatingFileHandler
    level: DEBUG
    formatter: default
    filename: logs/development.log
    maxBytes: 10485760  # 10MB
    backupCount: 5

loggers:
  '':  # Root logger
    level: DEBUG
    handlers: [console, file]
    propagate: false
  
  uvicorn:
    level: INFO
    handlers: [console]
    propagate: false
  
  sqlalchemy.engine:
    level: INFO
    handlers: [console]
    propagate: false
  
  fastapi:
    level: DEBUG
    handlers: [console, file]
    propagate: false

root:
  level: DEBUG
  handlers: [console, file]
```

```yaml
# configs/logging/production.yaml
version: 1
disable_existing_loggers: false

formatters:
  json:
    class: pythonjsonlogger.jsonlogger.JsonFormatter
    format: '%(asctime)s %(name)s %(levelname)s %(message)s'
  
  standard:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    datefmt: '%Y-%m-%d %H:%M:%S'

handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: json
    stream: ext://sys.stdout
  
  file:
    class: logging.handlers.RotatingFileHandler
    level: WARNING
    formatter: json
    filename: logs/production.log
    maxBytes: 52428800  # 50MB
    backupCount: 10
  
  error_file:
    class: logging.handlers.RotatingFileHandler
    level: ERROR
    formatter: json
    filename: logs/errors.log
    maxBytes: 52428800  # 50MB
    backupCount: 10

loggers:
  '':  # Root logger
    level: INFO
    handlers: [console, file]
    propagate: false
  
  uvicorn:
    level: WARNING
    handlers: [console]
    propagate: false
  
  sqlalchemy.engine:
    level: WARNING
    handlers: [file]
    propagate: false

root:
  level: INFO
  handlers: [console, file, error_file]
```

## 🧪 Testing Configuration

```python
# tests/unit/configs/test_app_config.py
import pytest
import os
from configs.app_config import AppConfig

class TestAppConfig:
    def test_default_configuration(self):
        """Test default configuration values."""
        config = AppConfig()
        
        assert config.app_name == "FastAPI Clean Architecture"
        assert config.port == 8000
        assert config.environment == "development"
        assert config.debug is False
    
    def test_environment_validation(self):
        """Test environment validation."""
        with pytest.raises(ValueError):
            AppConfig(environment="invalid")
    
    def test_production_secret_key_validation(self):
        """Test that default secret key is rejected in production."""
        with pytest.raises(ValueError):
            AppConfig(
                environment="production",
                secret_key="your-secret-key-change-in-production"
            )
    
    def test_environment_properties(self):
        """Test environment check properties."""
        dev_config = AppConfig(environment="development")
        prod_config = AppConfig(environment="production", secret_key="secure-key")
        
        assert dev_config.is_development is True
        assert dev_config.is_production is False
        
        assert prod_config.is_development is False
        assert prod_config.is_production is True
    
    def test_database_config_dict(self):
        """Test database configuration dictionary."""
        config = AppConfig()
        db_config = config.get_database_config()
        
        assert 'url' in db_config
        assert 'echo' in db_config
        assert 'pool_size' in db_config
        assert 'max_overflow' in db_config
```

## ✅ Best Practices

### Configuration Management
- **Use environment variables** for sensitive data
- **Validate configuration** at startup
- **Provide sensible defaults** for development
- **Document all configuration options** clearly
- **Use type hints** for configuration values

### Security
- **Never commit secrets** to version control
- **Use different configurations** for each environment
- **Validate security settings** in production
- **Rotate secrets regularly** in production environments

### Organization
- **Group related settings** logically
- **Use consistent naming** conventions
- **Provide configuration examples** and documentation
- **Keep environment-specific files** separate

## ❌ Common Pitfalls

- **Hardcoding configuration** values in code
- **Not validating configuration** at startup
- **Using the same configuration** across all environments
- **Committing sensitive data** to version control
- **Not documenting configuration** options

## 🔄 Integration Points

Configuration integrates with:
- **Application Startup** - Loads and validates settings
- **Infrastructure Layer** - Provides connection parameters
- **Logging System** - Configures log levels and formats
- **External Services** - Supplies API keys and endpoints
- **Testing Framework** - Provides test-specific configurations

The configs directory is essential for managing application behavior across different environments while maintaining security and flexibility in your hexagon architecture.

