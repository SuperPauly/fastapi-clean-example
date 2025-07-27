"""Save logger configuration use case."""

from pydantic import BaseModel, Field

from src.application.ports.logger_configuration import LoggerConfigurationPort
from src.domain.entities.logger_config import LoggerConfig


class SaveLoggerConfigRequest(BaseModel):
    """Request to save logger configuration."""
    
    config: LoggerConfig = Field(
        ...,
        description="Configuration to save"
    )
    
    model_config = {
        "arbitrary_types_allowed": True,
    }


class SaveLoggerConfigResponse(BaseModel):
    """Response from saving logger configuration."""
    
    success: bool = Field(
        ...,
        description="Whether the operation was successful"
    )
    message: str = Field(
        ...,
        description="Result message"
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Configuration warnings"
    )


class SaveLoggerConfigUseCase:
    """Use case for saving logger configuration."""
    
    def __init__(self, config_port: LoggerConfigurationPort):
        """
        Initialize the use case.
        
        Args:
            config_port: Logger configuration port implementation.
        """
        self._config_port = config_port
    
    async def execute(self, request: SaveLoggerConfigRequest) -> SaveLoggerConfigResponse:
        """
        Execute the save configuration use case.
        
        Args:
            request: Save configuration request.
            
        Returns:
            Save configuration response.
        """
        try:
            # Validate configuration before saving
            warnings = await self._config_port.validate_configuration(request.config)
            
            # Save the configuration
            success = await self._config_port.save_configuration(request.config)
            
            if not success:
                return SaveLoggerConfigResponse(
                    success=False,
                    message=f"Failed to save configuration '{request.config.name}'",
                    warnings=warnings
                )
            
            message = f"Configuration '{request.config.name}' saved successfully"
            if warnings:
                message += f" (with {len(warnings)} warnings)"
            
            return SaveLoggerConfigResponse(
                success=True,
                message=message,
                warnings=warnings
            )
            
        except Exception as e:
            return SaveLoggerConfigResponse(
                success=False,
                message=f"Failed to save configuration: {str(e)}",
                warnings=[]
            )
