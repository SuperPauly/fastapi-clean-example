"""Load logger configuration use case."""

from typing import Optional
from pydantic import BaseModel, Field

from src.application.ports.logger_configuration import LoggerConfigurationPort
from src.domain.entities.logger_config import LoggerConfig


class LoadLoggerConfigRequest(BaseModel):
    """Request to load logger configuration."""
    
    name: Optional[str] = Field(
        default=None,
        description="Configuration name to load. If None, loads default."
    )


class LoadLoggerConfigResponse(BaseModel):
    """Response from loading logger configuration."""
    
    config: Optional[LoggerConfig] = Field(
        default=None,
        description="Loaded configuration"
    )
    success: bool = Field(
        ...,
        description="Whether the operation was successful"
    )
    message: str = Field(
        ...,
        description="Result message"
    )
    
    model_config = {
        "arbitrary_types_allowed": True,
    }


class LoadLoggerConfigUseCase:
    """Use case for loading logger configuration."""
    
    def __init__(self, config_port: LoggerConfigurationPort):
        """
        Initialize the use case.
        
        Args:
            config_port: Logger configuration port implementation.
        """
        self._config_port = config_port
    
    async def execute(self, request: LoadLoggerConfigRequest) -> LoadLoggerConfigResponse:
        """
        Execute the load configuration use case.
        
        Args:
            request: Load configuration request.
            
        Returns:
            Load configuration response.
        """
        try:
            config = await self._config_port.load_configuration(request.name)
            
            if config is None:
                config_name = request.name or "default"
                return LoadLoggerConfigResponse(
                    config=None,
                    success=False,
                    message=f"Configuration '{config_name}' not found"
                )
            
            # Validate the loaded configuration
            warnings = await self._config_port.validate_configuration(config)
            
            message = f"Configuration '{config.name}' loaded successfully"
            if warnings:
                message += f" (with {len(warnings)} warnings)"
            
            return LoadLoggerConfigResponse(
                config=config,
                success=True,
                message=message
            )
            
        except Exception as e:
            return LoadLoggerConfigResponse(
                config=None,
                success=False,
                message=f"Failed to load configuration: {str(e)}"
            )
