"""Logger configuration port interface for hexagonal architecture."""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from uuid import UUID

from src.domain.entities.logger_config import LoggerConfig


class LoggerConfigurationPort(ABC):
    """Port interface for logger configuration management."""
    
    @abstractmethod
    async def load_configuration(self, name: Optional[str] = None) -> Optional[LoggerConfig]:
        """
        Load logger configuration by name.
        
        Args:
            name: Configuration name. If None, loads default configuration.
            
        Returns:
            LoggerConfig if found, None otherwise.
        """
        pass
    
    @abstractmethod
    async def save_configuration(self, config: LoggerConfig) -> bool:
        """
        Save logger configuration.
        
        Args:
            config: Logger configuration to save.
            
        Returns:
            True if saved successfully, False otherwise.
        """
        pass
    
    @abstractmethod
    async def delete_configuration(self, name: str) -> bool:
        """
        Delete logger configuration by name.
        
        Args:
            name: Configuration name to delete.
            
        Returns:
            True if deleted successfully, False otherwise.
        """
        pass
    
    @abstractmethod
    async def list_configurations(self) -> List[str]:
        """
        List all available configuration names.
        
        Returns:
            List of configuration names.
        """
        pass
    
    @abstractmethod
    async def get_configuration_summary(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get summary information about a configuration.
        
        Args:
            name: Configuration name.
            
        Returns:
            Summary dict if configuration exists, None otherwise.
        """
        pass
    
    @abstractmethod
    async def validate_configuration(self, config: LoggerConfig) -> List[str]:
        """
        Validate a logger configuration.
        
        Args:
            config: Configuration to validate.
            
        Returns:
            List of validation warnings/errors.
        """
        pass
    
    @abstractmethod
    async def export_configuration(self, name: str, format: str = "toml") -> Optional[str]:
        """
        Export configuration to string format.
        
        Args:
            name: Configuration name to export.
            format: Export format (toml, json, yaml).
            
        Returns:
            Exported configuration string if successful, None otherwise.
        """
        pass
    
    @abstractmethod
    async def import_configuration(self, config_data: str, format: str = "toml", name: Optional[str] = None) -> Optional[LoggerConfig]:
        """
        Import configuration from string format.
        
        Args:
            config_data: Configuration data as string.
            format: Import format (toml, json, yaml).
            name: Optional name for the imported configuration.
            
        Returns:
            Imported LoggerConfig if successful, None otherwise.
        """
        pass


class LoggerApplicationPort(ABC):
    """Port interface for applying logger configuration to actual logger."""
    
    @abstractmethod
    async def apply_configuration(self, config: LoggerConfig) -> bool:
        """
        Apply configuration to the actual logger.
        
        Args:
            config: Logger configuration to apply.
            
        Returns:
            True if applied successfully, False otherwise.
        """
        pass
    
    @abstractmethod
    async def test_configuration(self, config: LoggerConfig, test_messages: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Test a configuration by applying it temporarily and generating test logs.
        
        Args:
            config: Configuration to test.
            test_messages: Optional custom test messages.
            
        Returns:
            Test results including success status and any captured output.
        """
        pass
    
    @abstractmethod
    async def get_current_configuration(self) -> Optional[LoggerConfig]:
        """
        Get the currently active logger configuration.
        
        Returns:
            Current LoggerConfig if available, None otherwise.
        """
        pass
    
    @abstractmethod
    async def reset_logger(self) -> bool:
        """
        Reset logger to default state.
        
        Returns:
            True if reset successfully, False otherwise.
        """
        pass
    
    @abstractmethod
    async def preview_log_output(self, config: LoggerConfig, sample_messages: List[str]) -> List[str]:
        """
        Preview what log output would look like with given configuration.
        
        Args:
            config: Configuration to preview.
            sample_messages: Sample log messages to format.
            
        Returns:
            List of formatted log output strings.
        """
        pass
