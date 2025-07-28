"""Integration tests for TUI workflows across layers."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
import tempfile
import json
import asyncio

# Import test utilities
from tests.fixtures.tui_fixtures import (
    sample_logger_config,
    temp_config_dir,
    sample_config_file,
    async_test_timeout
)
from tests.fixtures.mock_repositories import MockLoggerConfigurationRepository, MockLoggerApplicationAdapter
from tests.utils.tui_test_helpers import AsyncTestHelper, ConfigurationTestHelper

# Import components under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.presentation.tui.app import LoguruConfigApp
from src.application.use_cases.load_logger_config import LoadLoggerConfigUseCase, LoadLoggerConfigRequest
from src.application.use_cases.save_logger_config import SaveLoggerConfigUseCase, SaveLoggerConfigRequest
from src.application.use_cases.test_logger_config import TestLoggerConfigUseCase, TestLoggerConfigRequest
from src.domain.entities.logger_config import LoggerConfig
from src.domain.value_objects.log_level import LogLevel


class TestLoguruTUIWorkflowIntegration:
    """Test complete workflows for Loguru TUI integration."""
    
    @pytest.fixture
    def mock_config_repository(self):
        """Create a mock configuration repository."""
        return MockLoggerConfigurationRepository()
    
    @pytest.fixture
    def mock_logger_adapter(self):
        """Create a mock logger adapter."""
        return MockLoggerApplicationAdapter()
    
    @pytest.fixture
    def integrated_tui_app(self, mock_config_repository, mock_logger_adapter):
        """Create a TUI app with integrated mock dependencies."""
        return LoguruConfigApp(mock_config_repository, mock_logger_adapter)
    
    @pytest.mark.asyncio
    async def test_complete_configuration_creation_workflow(self, integrated_tui_app, sample_logger_config):
        """Test complete workflow from TUI to domain layer for configuration creation."""
        # Step 1: Save configuration through TUI
        integrated_tui_app.current_config = sample_logger_config
        save_result = await integrated_tui_app.save_current_configuration()
        assert save_result is True
        
        # Step 2: Verify configuration was saved in repository
        saved_config = await integrated_tui_app.config_port.load_configuration(sample_logger_config.name)
        assert saved_config is not None
        assert saved_config.name == sample_logger_config.name
        assert saved_config.enabled == sample_logger_config.enabled
        
        # Step 3: Apply configuration through logger adapter
        apply_result = await integrated_tui_app.logger_port.apply_configuration(saved_config)
        assert apply_result is True
        
        # Step 4: Verify configuration is active
        current_config = await integrated_tui_app.logger_port.get_current_configuration()
        assert current_config == saved_config
    
    @pytest.mark.asyncio
    async def test_configuration_loading_and_testing_workflow(self, integrated_tui_app, sample_logger_config):
        """Test workflow for loading and testing configurations."""
        # Step 1: Save a configuration first
        await integrated_tui_app.config_port.save_configuration(sample_logger_config)
        
        # Step 2: Load configuration through TUI
        load_result = await integrated_tui_app.load_configuration(sample_logger_config.name)
        assert load_result is True
        
        # Step 3: Test the loaded configuration
        test_result = await integrated_tui_app.test_configuration(sample_logger_config)
        assert test_result["success"] is True
        assert len(test_result["output"]) > 0
        
        # Step 4: Preview log output
        sample_messages = ["Test message 1", "Test message 2"]
        preview_result = await integrated_tui_app.preview_log_output(sample_logger_config, sample_messages)
        assert len(preview_result) == len(sample_messages)
    
    @pytest.mark.asyncio
    async def test_configuration_validation_workflow(self, integrated_tui_app, sample_logger_config):
        """Test configuration validation across layers."""
        # Step 1: Validate configuration through repository
        warnings = await integrated_tui_app.config_port.validate_configuration(sample_logger_config)
        assert isinstance(warnings, list)
        
        # Step 2: Test configuration with invalid setup
        invalid_config = LoggerConfig(
            name="invalid_config",
            description="Invalid configuration",
            enabled=True,
            global_level=LogLevel.DEBUG,
            handlers=[],  # No handlers - should generate warnings
            activation=[],
            patcher=None,
            extra={}
        )
        
        invalid_warnings = await integrated_tui_app.config_port.validate_configuration(invalid_config)
        assert len(invalid_warnings) > 0
        assert any("No handlers configured" in warning for warning in invalid_warnings)
    
    @pytest.mark.asyncio
    async def test_configuration_export_import_workflow(self, integrated_tui_app, sample_logger_config):
        """Test complete export/import workflow."""
        # Step 1: Save original configuration
        await integrated_tui_app.config_port.save_configuration(sample_logger_config)
        
        # Step 2: Export configuration
        exported_data = await integrated_tui_app.config_port.export_configuration(
            sample_logger_config.name, "json"
        )
        assert exported_data is not None
        assert sample_logger_config.name in exported_data
        
        # Step 3: Import configuration with new name
        imported_config = await integrated_tui_app.config_port.import_configuration(
            exported_data, "json", "imported_test_config"
        )
        assert imported_config is not None
        assert imported_config.name == "imported_test_config"
        
        # Step 4: Save imported configuration
        save_result = await integrated_tui_app.config_port.save_configuration(imported_config)
        assert save_result is True
        
        # Step 5: Verify both configurations exist
        config_list = await integrated_tui_app.config_port.list_configurations()
        assert sample_logger_config.name in config_list
        assert "imported_test_config" in config_list


class TestDynaconfTUIWorkflowIntegration:
    """Test complete workflows for Dynaconf TUI integration."""
    
    @pytest.fixture
    def mock_dynaconf_repository(self):
        """Create a mock repository for Dynaconf testing."""
        mock = Mock()
        mock.save_configuration = AsyncMock(return_value=True)
        mock.load_configuration = AsyncMock(return_value=None)
        mock.backup_configuration = AsyncMock(return_value=True)
        return mock
    
    @pytest.fixture
    def sample_dynaconf_config_set(self):
        """Create a sample configuration set for testing."""
        from manage_config import ConfigurationSet, ConfigurationItem, ConfigurationKey, ConfigurationValue, ConfigurationFormat, Environment
        
        config_set = ConfigurationSet("IntegrationTest", ConfigurationFormat.TOML)
        
        items = [
            ConfigurationItem(
                key=ConfigurationKey("PROJECT_NAME"),
                value=ConfigurationValue("IntegrationTest"),
                description="Project name"
            ),
            ConfigurationItem(
                key=ConfigurationKey("DEBUG"),
                value=ConfigurationValue(True),
                description="Debug mode",
                environment=Environment.DEVELOPMENT
            ),
            ConfigurationItem(
                key=ConfigurationKey("SECRET_KEY"),
                value=ConfigurationValue("super_secret_key"),
                description="Application secret key"
            )
        ]
        
        for item in items:
            config_set.add_item(item)
        
        return config_set
    
    @pytest.mark.asyncio
    async def test_dynaconf_configuration_crud_workflow(self, mock_dynaconf_repository, sample_dynaconf_config_set):
        """Test complete CRUD workflow for Dynaconf configurations."""
        # Import use cases
        from manage_config import CreateConfigurationUseCase, UpdateConfigurationUseCase, DeleteConfigurationUseCase
        from manage_config import CreateConfigurationCommand, UpdateConfigurationCommand, DeleteConfigurationCommand
        
        # Step 1: Create configuration
        create_use_case = CreateConfigurationUseCase(mock_dynaconf_repository)
        create_command = CreateConfigurationCommand("IntegrationTest", sample_dynaconf_config_set.format)
        
        created_config = await create_use_case.execute(create_command, Path.cwd())
        assert created_config.project_name == "IntegrationTest"
        
        # Step 2: Update configuration
        update_use_case = UpdateConfigurationUseCase(mock_dynaconf_repository, Mock())
        update_command = UpdateConfigurationCommand(
            key_name="NEW_SETTING",
            new_value="new_value",
            description="New setting added via integration test"
        )
        
        update_result = await update_use_case.execute(update_command, sample_dynaconf_config_set)
        assert update_result is True
        assert "NEW_SETTING" in sample_dynaconf_config_set.items
        
        # Step 3: Delete configuration item
        delete_use_case = DeleteConfigurationUseCase(mock_dynaconf_repository)
        delete_command = DeleteConfigurationCommand(key_name="NEW_SETTING")
        
        delete_result = await delete_use_case.execute(delete_command, sample_dynaconf_config_set)
        assert delete_result is True
        assert "NEW_SETTING" not in sample_dynaconf_config_set.items
    
    @pytest.mark.asyncio
    async def test_dynaconf_validation_integration_workflow(self, sample_dynaconf_config_set):
        """Test validation integration workflow."""
        from manage_config import ConfigurationValidator, ConfigurationItem, ConfigurationKey, ConfigurationValue
        
        validator = ConfigurationValidator()
        
        # Step 1: Validate existing configuration items
        for key, item in sample_dynaconf_config_set.items.items():
            key_errors = validator.validate_key(item.key.name)
            value_errors = validator.validate_value(item.value.value, item.value.value_type)
            
            assert len(key_errors) == 0, f"Key validation failed for {key}: {key_errors}"
            assert len(value_errors) == 0, f"Value validation failed for {key}: {value_errors}"
        
        # Step 2: Test validation with invalid data
        invalid_item = ConfigurationItem(
            key=ConfigurationKey("INVALID KEY WITH SPACES"),
            value=ConfigurationValue(""),
            description="Invalid item for testing"
        )
        
        key_errors = validator.validate_key(invalid_item.key.name)
        value_errors = validator.validate_value(invalid_item.value.value, invalid_item.value.value_type)
        
        assert len(key_errors) > 0
        assert len(value_errors) > 0
    
    @pytest.mark.asyncio
    async def test_dynaconf_environment_filtering_workflow(self, sample_dynaconf_config_set):
        """Test environment-specific configuration filtering."""
        from manage_config import Environment
        
        # Step 1: Get development-specific items
        dev_items = sample_dynaconf_config_set.get_items_by_environment(Environment.DEVELOPMENT)
        assert len(dev_items) == 1
        assert dev_items[0].key.name == "DEBUG"
        
        # Step 2: Get production-specific items (should be empty for this test)
        prod_items = sample_dynaconf_config_set.get_items_by_environment(Environment.PRODUCTION)
        assert len(prod_items) == 0
        
        # Step 3: Add production-specific item
        from manage_config import ConfigurationItem, ConfigurationKey, ConfigurationValue
        
        prod_item = ConfigurationItem(
            key=ConfigurationKey("PRODUCTION_URL"),
            value=ConfigurationValue("https://prod.example.com"),
            description="Production URL",
            environment=Environment.PRODUCTION
        )
        sample_dynaconf_config_set.add_item(prod_item)
        
        # Step 4: Verify filtering works with new item
        prod_items = sample_dynaconf_config_set.get_items_by_environment(Environment.PRODUCTION)
        assert len(prod_items) == 1
        assert prod_items[0].key.name == "PRODUCTION_URL"


class TestCrossLayerIntegration:
    """Test integration across all architectural layers."""
    
    @pytest.fixture
    def integrated_system(self):
        """Create an integrated system with all layers."""
        config_repo = MockLoggerConfigurationRepository()
        logger_adapter = MockLoggerApplicationAdapter()
        
        return {
            'config_repo': config_repo,
            'logger_adapter': logger_adapter,
            'tui_app': LoguruConfigApp(config_repo, logger_adapter)
        }
    
    @pytest.mark.asyncio
    async def test_end_to_end_configuration_lifecycle(self, integrated_system, sample_logger_config):
        """Test complete configuration lifecycle across all layers."""
        tui_app = integrated_system['tui_app']
        
        # Step 1: Create and save configuration (Presentation -> Application -> Infrastructure)
        tui_app.current_config = sample_logger_config
        save_result = await tui_app.save_current_configuration()
        assert save_result is True
        
        # Step 2: Load configuration (Infrastructure -> Application -> Presentation)
        load_result = await tui_app.load_configuration(sample_logger_config.name)
        assert load_result is True
        
        # Step 3: Apply configuration (Presentation -> Application -> Infrastructure)
        apply_result = await tui_app.logger_port.apply_configuration(sample_logger_config)
        assert apply_result is True
        
        # Step 4: Test configuration (All layers involved)
        test_result = await tui_app.test_configuration(sample_logger_config)
        assert test_result["success"] is True
        
        # Step 5: Validate configuration (Domain -> Application -> Presentation)
        warnings = await tui_app.config_port.validate_configuration(sample_logger_config)
        assert isinstance(warnings, list)
        
        # Step 6: Export configuration (Infrastructure -> Application -> Presentation)
        export_result = await tui_app.config_port.export_configuration(sample_logger_config.name, "json")
        assert export_result is not None
    
    @pytest.mark.asyncio
    async def test_error_propagation_across_layers(self, integrated_system, sample_logger_config):
        """Test error propagation from infrastructure to presentation layer."""
        tui_app = integrated_system['tui_app']
        
        # Mock a failure in the infrastructure layer
        tui_app.config_port.save_configuration = AsyncMock(side_effect=Exception("Infrastructure failure"))
        
        # Attempt operation that should fail
        tui_app.current_config = sample_logger_config
        save_result = await tui_app.save_current_configuration()
        
        # Verify error is handled gracefully at presentation layer
        assert save_result is False
    
    @pytest.mark.asyncio
    async def test_concurrent_operations_handling(self, integrated_system, sample_logger_config):
        """Test handling of concurrent operations across layers."""
        tui_app = integrated_system['tui_app']
        
        # Set up configuration
        await tui_app.config_port.save_configuration(sample_logger_config)
        
        # Perform concurrent operations
        tasks = [
            tui_app.load_configuration(sample_logger_config.name),
            tui_app.test_configuration(sample_logger_config),
            tui_app.preview_log_output(sample_logger_config, ["Test message"]),
            tui_app.config_port.validate_configuration(sample_logger_config)
        ]
        
        # Execute concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify all operations completed successfully
        assert len(results) == 4
        assert results[0] is True  # load_configuration
        assert results[1]["success"] is True  # test_configuration
        assert len(results[2]) > 0  # preview_log_output
        assert isinstance(results[3], list)  # validate_configuration
    
    @pytest.mark.asyncio
    async def test_data_consistency_across_layers(self, integrated_system, sample_logger_config):
        """Test data consistency across architectural layers."""
        tui_app = integrated_system['tui_app']
        
        # Step 1: Save configuration
        await tui_app.config_port.save_configuration(sample_logger_config)
        
        # Step 2: Load configuration
        loaded_config = await tui_app.config_port.load_configuration(sample_logger_config.name)
        
        # Step 3: Verify data consistency
        assert loaded_config.name == sample_logger_config.name
        assert loaded_config.enabled == sample_logger_config.enabled
        assert loaded_config.global_level == sample_logger_config.global_level
        assert len(loaded_config.handlers) == len(sample_logger_config.handlers)
        
        # Step 4: Apply and retrieve from logger adapter
        await tui_app.logger_port.apply_configuration(loaded_config)
        current_config = await tui_app.logger_port.get_current_configuration()
        
        # Step 5: Verify consistency in logger adapter
        assert current_config == loaded_config


class TestPerformanceIntegration:
    """Test performance characteristics of integrated workflows."""
    
    @pytest.mark.asyncio
    async def test_configuration_loading_performance(self, integrated_system, sample_logger_config):
        """Test performance of configuration loading workflow."""
        tui_app = integrated_system['tui_app']
        
        # Save configuration first
        await tui_app.config_port.save_configuration(sample_logger_config)
        
        # Measure loading performance
        start_time = asyncio.get_event_loop().time()
        
        for _ in range(10):
            result = await tui_app.load_configuration(sample_logger_config.name)
            assert result is True
        
        end_time = asyncio.get_event_loop().time()
        total_time = end_time - start_time
        
        # Should complete 10 loads in under 1 second
        assert total_time < 1.0
        
        # Average time per load should be reasonable
        avg_time = total_time / 10
        assert avg_time < 0.1  # 100ms per load
    
    @pytest.mark.asyncio
    async def test_concurrent_workflow_performance(self, integrated_system, sample_logger_config):
        """Test performance under concurrent workflow execution."""
        tui_app = integrated_system['tui_app']
        
        # Save configuration
        await tui_app.config_port.save_configuration(sample_logger_config)
        
        # Create multiple concurrent workflows
        async def workflow():
            await tui_app.load_configuration(sample_logger_config.name)
            await tui_app.test_configuration(sample_logger_config)
            return True
        
        # Execute multiple workflows concurrently
        start_time = asyncio.get_event_loop().time()
        
        tasks = [workflow() for _ in range(5)]
        results = await asyncio.gather(*tasks)
        
        end_time = asyncio.get_event_loop().time()
        total_time = end_time - start_time
        
        # All workflows should complete successfully
        assert all(results)
        
        # Should complete in reasonable time even with concurrency
        assert total_time < 2.0  # 2 seconds for 5 concurrent workflows
    
    @pytest.mark.asyncio
    async def test_memory_usage_during_workflows(self, integrated_system, sample_logger_config):
        """Test memory usage characteristics during workflows."""
        tui_app = integrated_system['tui_app']
        
        # Perform memory-intensive operations
        configs = []
        
        for i in range(20):
            config = LoggerConfig(
                name=f"test_config_{i}",
                description=f"Test configuration {i}",
                enabled=True,
                global_level=LogLevel.DEBUG,
                handlers=[],
                activation=[],
                patcher=None,
                extra={}
            )
            configs.append(config)
            await tui_app.config_port.save_configuration(config)
        
        # Load all configurations
        loaded_configs = []
        for config in configs:
            loaded = await tui_app.config_port.load_configuration(config.name)
            loaded_configs.append(loaded)
        
        # Verify all configurations were loaded
        assert len(loaded_configs) == 20
        assert all(config is not None for config in loaded_configs)
        
        # Test that we can still perform operations efficiently
        test_results = []
        for config in loaded_configs[:5]:  # Test first 5 to avoid excessive test time
            result = await tui_app.test_configuration(config)
            test_results.append(result)
        
        assert len(test_results) == 5
        assert all(result["success"] for result in test_results)

