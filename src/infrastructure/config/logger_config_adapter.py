"""Dynaconf adapter for logger configuration persistence."""

import json
import asyncio
from typing import Optional, List, Dict, Any
from pathlib import Path

from src.application.ports.logger_configuration import LoggerConfigurationPort
from src.domain.entities.logger_config import LoggerConfig


class DynaconfLoggerConfigAdapter(LoggerConfigurationPort):
    """Dynaconf implementation of logger configuration port."""
    
    def __init__(self, config_dir: str = "configs/logging"):
        """
        Initialize the Dynaconf adapter.
        
        Args:
            config_dir: Directory to store configuration files.
        """
        self._config_dir = Path(config_dir)
        self._config_dir.mkdir(parents=True, exist_ok=True)
        
        # Default configuration
        self._default_config = LoggerConfig(
            name="default",
            description="Default Loguru configuration"
        )
    
    async def load_configuration(self, name: Optional[str] = None) -> Optional[LoggerConfig]:
        """Load logger configuration by name."""
        config_name = name or "default"
        config_file = self._config_dir / f"{config_name}.json"
        
        try:
            if not config_file.exists():
                # Return default configuration if no file exists
                if config_name == "default":
                    return self._default_config
                return None
            
            # Load configuration from file
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            
            # Create LoggerConfig from loaded data
            return LoggerConfig(**config_data)
            
        except Exception as e:
            print(f"Error loading configuration '{config_name}': {e}")
            return None
    
    async def save_configuration(self, config: LoggerConfig) -> bool:
        """Save logger configuration."""
        try:
            config_file = self._config_dir / f"{config.name}.json"
            
            # Convert configuration to dict
            config_data = config.model_dump()
            
            # Save to file
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2, default=str)
            
            return True
            
        except Exception as e:
            print(f"Error saving configuration '{config.name}': {e}")
            return False
    
    async def delete_configuration(self, name: str) -> bool:
        """Delete logger configuration by name."""
        try:
            config_file = self._config_dir / f"{name}.json"
            
            if config_file.exists():
                config_file.unlink()
                return True
            
            return False
            
        except Exception as e:
            print(f"Error deleting configuration '{name}': {e}")
            return False
    
    async def list_configurations(self) -> List[str]:
        """List all available configuration names."""
        try:
            config_files = list(self._config_dir.glob("*.json"))
            return [f.stem for f in config_files]
            
        except Exception as e:
            print(f"Error listing configurations: {e}")
            return []
    
    async def get_configuration_summary(self, name: str) -> Optional[Dict[str, Any]]:
        """Get summary information about a configuration."""
        config = await self.load_configuration(name)
        if config:
            return config.get_summary()
        return None
    
    async def validate_configuration(self, config: LoggerConfig) -> List[str]:
        """Validate a logger configuration."""
        return config.validate_configuration()
    
    async def export_configuration(self, name: str, format: str = "toml") -> Optional[str]:
        """Export configuration to string format."""
        config = await self.load_configuration(name)
        if not config:
            return None
        
        try:
            config_data = config.model_dump()
            
            if format.lower() == "json":
                return json.dumps(config_data, indent=2, default=str)
            elif format.lower() == "yaml":
                try:
                    import yaml
                    return yaml.dump(config_data, default_flow_style=False)
                except ImportError:
                    print("PyYAML not installed. Install with: pip install pyyaml")
                    return None
            elif format.lower() == "toml":
                try:
                    import tomli_w
                    return tomli_w.dumps(config_data)
                except ImportError:
                    print("tomli-w not installed. Install with: pip install tomli-w")
                    return None
            else:
                print(f"Unsupported export format: {format}")
                return None
                
        except Exception as e:
            print(f"Error exporting configuration: {e}")
            return None
    
    async def import_configuration(
        self, 
        config_data: str, 
        format: str = "toml", 
        name: Optional[str] = None
    ) -> Optional[LoggerConfig]:
        """Import configuration from string format."""
        try:
            # Parse configuration data based on format
            if format.lower() == "json":
                data = json.loads(config_data)
            elif format.lower() == "yaml":
                try:
                    import yaml
                    data = yaml.safe_load(config_data)
                except ImportError:
                    print("PyYAML not installed. Install with: pip install pyyaml")
                    return None
            elif format.lower() == "toml":
                try:
                    import tomllib
                    data = tomllib.loads(config_data)
                except ImportError:
                    try:
                        import tomli
                        data = tomli.loads(config_data)
                    except ImportError:
                        print("tomllib/tomli not installed. Install with: pip install tomli")
                        return None
            else:
                print(f"Unsupported import format: {format}")
                return None
            
            # Override name if provided
            if name:
                data['name'] = name
            
            # Create LoggerConfig from imported data
            return LoggerConfig(**data)
            
        except Exception as e:
            print(f"Error importing configuration: {e}")
            return None
