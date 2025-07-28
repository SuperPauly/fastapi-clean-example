"""Test logger configuration use case."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from src.application.ports.logger_configuration import LoggerApplicationPort
from src.domain.entities.logger_config import LoggerConfig


class TestLoggerConfigRequest(BaseModel):
    """Request to test logger configuration."""
    
    config: LoggerConfig = Field(
        ...,
        description="Configuration to test"
    )
    test_messages: Optional[List[str]] = Field(
        default=None,
        description="Custom test messages. If None, uses default test messages."
    )
    preview_only: bool = Field(
        default=False,
        description="If True, only preview output without actually logging"
    )
    
    model_config = {
        "arbitrary_types_allowed": True,
    }


class TestLoggerConfigResponse(BaseModel):
    """Response from testing logger configuration."""
    
    success: bool = Field(
        ...,
        description="Whether the test was successful"
    )
    message: str = Field(
        ...,
        description="Result message"
    )
    test_results: Dict[str, Any] = Field(
        default_factory=dict,
        description="Detailed test results"
    )
    preview_output: List[str] = Field(
        default_factory=list,
        description="Preview of log output"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Configuration warnings"
    )


class TestLoggerConfigUseCase:
    """Use case for testing logger configuration."""
    
    def __init__(self, logger_port: LoggerApplicationPort):
        """
        Initialize the use case.
        
        Args:
            logger_port: Logger application port implementation.
        """
        self._logger_port = logger_port
    
    def _get_default_test_messages(self) -> List[str]:
        """Get default test messages for different log levels."""
        return [
            "TRACE: This is a trace message for debugging",
            "DEBUG: Debug information about application state",
            "INFO: Application started successfully",
            "SUCCESS: Operation completed successfully",
            "WARNING: This is a warning message",
            "ERROR: An error occurred during processing",
            "CRITICAL: Critical system failure detected"
        ]
    
    async def execute(self, request: TestLoggerConfigRequest) -> TestLoggerConfigResponse:
        """
        Execute the test configuration use case.
        
        Args:
            request: Test configuration request.
            
        Returns:
            Test configuration response.
        """
        try:
            # Get test messages
            test_messages = request.test_messages or self._get_default_test_messages()
            
            # Generate preview output
            preview_output = await self._logger_port.preview_log_output(
                request.config, 
                test_messages
            )
            
            if request.preview_only:
                return TestLoggerConfigResponse(
                    success=True,
                    message="Configuration preview generated successfully",
                    test_results={"preview_only": True},
                    preview_output=preview_output,
                    warnings=request.config.validate_configuration()
                )
            
            # Perform actual test
            test_results = await self._logger_port.test_configuration(
                request.config,
                test_messages
            )
            
            if not test_results.get("success", False):
                return TestLoggerConfigResponse(
                    success=False,
                    message=f"Configuration test failed: {test_results.get('error', 'Unknown error')}",
                    test_results=test_results,
                    preview_output=preview_output,
                    warnings=request.config.validate_configuration()
                )
            
            # Analyze test results
            handlers_tested = test_results.get("handlers_tested", 0)
            messages_logged = test_results.get("messages_logged", 0)
            
            message = f"Configuration test successful: {handlers_tested} handlers tested, {messages_logged} messages logged"
            
            return TestLoggerConfigResponse(
                success=True,
                message=message,
                test_results=test_results,
                preview_output=preview_output,
                warnings=request.config.validate_configuration()
            )
            
        except Exception as e:
            return TestLoggerConfigResponse(
                success=False,
                message=f"Failed to test configuration: {str(e)}",
                test_results={"error": str(e)},
                preview_output=[],
                warnings=[]
            )
