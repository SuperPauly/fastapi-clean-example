"""Configuration management using Dynaconf."""

from dynaconf import Dynaconf

# Initialize Dynaconf settings
settings = Dynaconf(
    envvar_prefix="FASTAPI",
    settings_files=["settings.toml", ".secrets.toml"],
    environments=True,
    load_dotenv=True,
    env_switcher="FASTAPI_ENV",
    merge_enabled=True,
)

# Configuration classes for type safety
class DatabaseConfig:
    """Database configuration."""
    
    @property
    def url(self) -> str:
        """Get database URL."""
        return settings.DATABASE.URL
    
    @property
    def host(self) -> str:
        """Get database host."""
        return settings.DATABASE.HOST
    
    @property
    def port(self) -> int:
        """Get database port."""
        return settings.DATABASE.PORT
    
    @property
    def name(self) -> str:
        """Get database name."""
        return settings.DATABASE.NAME
    
    @property
    def user(self) -> str:
        """Get database user."""
        return settings.DATABASE.USER
    
    @property
    def password(self) -> str:
        """Get database password."""
        return settings.DATABASE.PASSWORD


class AppConfig:
    """Application configuration."""
    
    @property
    def name(self) -> str:
        """Get application name."""
        return settings.APP.NAME
    
    @property
    def version(self) -> str:
        """Get application version."""
        return settings.APP.VERSION
    
    @property
    def debug(self) -> bool:
        """Get debug mode."""
        return settings.APP.DEBUG
    
    @property
    def host(self) -> str:
        """Get application host."""
        return settings.APP.HOST
    
    @property
    def port(self) -> int:
        """Get application port."""
        return settings.APP.PORT


class RedisConfig:
    """Redis configuration for task queue."""
    
    @property
    def url(self) -> str:
        """Get Redis URL."""
        return settings.REDIS.URL
    
    @property
    def host(self) -> str:
        """Get Redis host."""
        return settings.REDIS.HOST
    
    @property
    def port(self) -> int:
        """Get Redis port."""
        return settings.REDIS.PORT
    
    @property
    def db(self) -> int:
        """Get Redis database number."""
        return settings.REDIS.DB


class TaskiqConfig:
    """Taskiq task queue configuration."""
    
    @property
    def broker_url(self) -> str:
        """Get Taskiq broker URL."""
        return settings.TASKIQ.BROKER_URL
    
    @property
    def result_backend_url(self) -> str:
        """Get Taskiq result backend URL."""
        return settings.TASKIQ.RESULT_BACKEND_URL
    
    @property
    def max_workers(self) -> int:
        """Get maximum number of workers."""
        return settings.TASKIQ.get("MAX_WORKERS", 4)
    
    @property
    def prefetch_count(self) -> int:
        """Get prefetch count for workers."""
        return settings.TASKIQ.get("PREFETCH_COUNT", 10)


class LoggingConfig:
    """Logging configuration."""
    
    @property
    def level(self) -> str:
        """Get logging level."""
        return settings.LOGGING.LEVEL
    
    @property
    def format(self) -> str:
        """Get logging format."""
        return settings.LOGGING.FORMAT
    
    @property
    def file_path(self) -> str:
        """Get log file path."""
        return settings.LOGGING.FILE_PATH


# Configuration instances
database_config = DatabaseConfig()
app_config = AppConfig()
redis_config = RedisConfig()
taskiq_config = TaskiqConfig()
logging_config = LoggingConfig()
