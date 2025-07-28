"""End-to-end tests for complete TUI workflows."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
import tempfile
import json
import asyncio
import os

# Import test utilities
from tests.fixtures.tui_fixtures import (
    sample_logger_config,
    temp_config_dir,
    async_test_timeout
)
from tests.fixtures.mock_repositories import MockLoggerConfigurationRepository, MockLoggerApplicationAdapter
from tests.utils.tui_test_helpers import (
    TUITestHelper,
    ConfigurationTestHelper,
    AsyncTestHelper,
    FileSystemTestHelper
)

# Import components under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.presentation.tui.app import LoguruConfigApp
from src.domain.entities.logger_config import LoggerConfig
from src.domain.value_objects.log_level import LogLevel


class TestCompleteLoguruTUIWorkflow:
    """Test complete end-to-end workflows for Loguru TUI."""
    
    @pytest.fixture
    def e2e_test_environment(self):
        """Set up complete test environment for e2e testing."""
        # Create temporary directory structure
        temp_dir = FileSystemTestHelper.create_temp_directory_structure({
            'configs': {
                'logging': {}
            },
            'logs': {},
            'backups': {}
        })
        
        # Create repositories with real file system interaction
        config_repo = MockLoggerConfigurationRepository()
        config_repo.storage_path = temp_dir / 'configs' / 'logging'
        
        logger_adapter = MockLoggerApplicationAdapter()
        
        # Create TUI app
        tui_app = LoguruConfigApp(config_repo, logger_adapter)
        
        return {
            'temp_dir': temp_dir,
            'config_repo': config_repo,
            'logger_adapter': logger_adapter,
            'tui_app': tui_app
        }
    
    @pytest.mark.asyncio
    async def test_complete_configuration_creation_and_usage_workflow(self, e2e_test_environment, sample_logger_config):
        """Test complete workflow from configuration creation to usage."""
        env = e2e_test_environment
        tui_app = env['tui_app']
        
        # Step 1: Create new configuration through TUI
        tui_app.current_config = sample_logger_config
        
        # Step 2: Save configuration
        save_result = await tui_app.save_current_configuration()
        assert save_result is True
        
        # Step 3: Verify configuration file was created
        config_file = env['config_repo'].storage_path / f"{sample_logger_config.name}.json"
        assert config_file.exists()
        
        # Step 4: Load configuration from file
        load_result = await tui_app.load_configuration(sample_logger_config.name)
        assert load_result is True
        
        # Step 5: Validate loaded configuration
        warnings = await tui_app.config_port.validate_configuration(sample_logger_config)
        assert isinstance(warnings, list)
        
        # Step 6: Test configuration with sample messages
        test_messages = ["Debug message", "Info message", "Warning message", "Error message"]
        test_result = await tui_app.test_configuration(sample_logger_config)
        assert test_result["success"] is True
        assert len(test_result["output"]) > 0
        
        # Step 7: Apply configuration to logger
        apply_result = await tui_app.logger_port.apply_configuration(sample_logger_config)
        assert apply_result is True
        
        # Step 8: Verify configuration is active
        current_config = await tui_app.logger_port.get_current_configuration()
        assert current_config == sample_logger_config
        
        # Step 9: Preview log output
        preview_result = await tui_app.preview_log_output(sample_logger_config, test_messages)
        assert len(preview_result) == len(test_messages)
        
        # Cleanup
        FileSystemTestHelper.cleanup_temp_directory(env['temp_dir'])
    
    @pytest.mark.asyncio
    async def test_configuration_import_export_workflow(self, e2e_test_environment, sample_logger_config):
        """Test complete import/export workflow."""
        env = e2e_test_environment
        tui_app = env['tui_app']
        
        # Step 1: Create and save original configuration
        await tui_app.config_port.save_configuration(sample_logger_config)
        
        # Step 2: Export configuration to JSON
        exported_json = await tui_app.config_port.export_configuration(sample_logger_config.name, "json")
        assert exported_json is not None
        
        # Step 3: Save exported data to file
        export_file = env['temp_dir'] / 'exported_config.json'
        export_file.write_text(exported_json)
        assert export_file.exists()
        
        # Step 4: Import configuration from file
        imported_data = export_file.read_text()
        imported_config = await tui_app.config_port.import_configuration(
            imported_data, "json", "imported_config"
        )
        assert imported_config is not None
        assert imported_config.name == "imported_config"
        
        # Step 5: Save imported configuration
        save_result = await tui_app.config_port.save_configuration(imported_config)
        assert save_result is True
        
        # Step 6: Verify both configurations exist
        config_list = await tui_app.config_port.list_configurations()
        assert sample_logger_config.name in config_list
        assert "imported_config" in config_list
        
        # Step 7: Test both configurations work
        original_test = await tui_app.test_configuration(sample_logger_config)
        imported_test = await tui_app.test_configuration(imported_config)
        
        assert original_test["success"] is True
        assert imported_test["success"] is True
        
        # Cleanup
        FileSystemTestHelper.cleanup_temp_directory(env['temp_dir'])
    
    @pytest.mark.asyncio
    async def test_configuration_backup_and_recovery_workflow(self, e2e_test_environment, sample_logger_config):
        """Test configuration backup and recovery workflow."""
        env = e2e_test_environment
        tui_app = env['tui_app']
        
        # Step 1: Create original configuration
        await tui_app.config_port.save_configuration(sample_logger_config)
        
        # Step 2: Create backup
        backup_dir = env['temp_dir'] / 'backups'
        backup_file = backup_dir / f"{sample_logger_config.name}_backup.json"
        
        # Export for backup
        backup_data = await tui_app.config_port.export_configuration(sample_logger_config.name, "json")
        backup_file.write_text(backup_data)
        
        # Step 3: Modify original configuration
        modified_config = LoggerConfig(
            name=sample_logger_config.name,
            description="Modified configuration",
            enabled=False,  # Changed from True
            global_level=LogLevel.ERROR,  # Changed from DEBUG
            handlers=[],
            activation=[],
            patcher=None,
            extra={}
        )
        
        await tui_app.config_port.save_configuration(modified_config)
        
        # Step 4: Verify modification
        loaded_modified = await tui_app.config_port.load_configuration(sample_logger_config.name)
        assert loaded_modified.enabled is False
        assert loaded_modified.global_level == LogLevel.ERROR
        
        # Step 5: Restore from backup
        backup_data = backup_file.read_text()
        restored_config = await tui_app.config_port.import_configuration(
            backup_data, "json", sample_logger_config.name
        )
        
        # Step 6: Save restored configuration
        await tui_app.config_port.save_configuration(restored_config)
        
        # Step 7: Verify restoration
        final_config = await tui_app.config_port.load_configuration(sample_logger_config.name)
        assert final_config.enabled == sample_logger_config.enabled
        assert final_config.global_level == sample_logger_config.global_level
        
        # Cleanup
        FileSystemTestHelper.cleanup_temp_directory(env['temp_dir'])
    
    @pytest.mark.asyncio
    async def test_multi_configuration_management_workflow(self, e2e_test_environment):
        """Test managing multiple configurations simultaneously."""
        env = e2e_test_environment
        tui_app = env['tui_app']
        
        # Step 1: Create multiple configurations
        configs = []
        for i in range(5):
            config = LoggerConfig(
                name=f"config_{i}",
                description=f"Configuration {i}",
                enabled=True,
                global_level=LogLevel.DEBUG if i % 2 == 0 else LogLevel.INFO,
                handlers=[],
                activation=[],
                patcher=None,
                extra={}
            )
            configs.append(config)
            await tui_app.config_port.save_configuration(config)
        
        # Step 2: Verify all configurations were saved
        config_list = await tui_app.config_port.list_configurations()
        assert len(config_list) == 5
        for config in configs:
            assert config.name in config_list
        
        # Step 3: Load and test each configuration
        test_results = []
        for config in configs:
            loaded = await tui_app.config_port.load_configuration(config.name)
            assert loaded is not None
            
            test_result = await tui_app.test_configuration(loaded)
            test_results.append(test_result)
        
        # Step 4: Verify all tests passed
        assert len(test_results) == 5
        assert all(result["success"] for result in test_results)
        
        # Step 5: Get summaries for all configurations
        summaries = []
        for config in configs:
            summary = await tui_app.config_port.get_configuration_summary(config.name)
            summaries.append(summary)
        
        assert len(summaries) == 5
        assert all(summary is not None for summary in summaries)
        
        # Step 6: Delete configurations one by one
        for config in configs:
            delete_result = await tui_app.config_port.delete_configuration(config.name)
            assert delete_result is True
        
        # Step 7: Verify all configurations were deleted
        final_list = await tui_app.config_port.list_configurations()
        assert len(final_list) == 0
        
        # Cleanup
        FileSystemTestHelper.cleanup_temp_directory(env['temp_dir'])


class TestCompleteDynaconfTUIWorkflow:
    """Test complete end-to-end workflows for Dynaconf TUI."""
    
    @pytest.fixture
    def dynaconf_e2e_environment(self):
        """Set up complete test environment for Dynaconf e2e testing."""
        # Create temporary directory structure
        temp_dir = FileSystemTestHelper.create_temp_directory_structure({
            'configs': {},
            'backups': {},
            'exports': {}
        })
        
        # Mock repository
        mock_repo = Mock()
        mock_repo.save_configuration = AsyncMock(return_value=True)
        mock_repo.load_configuration = AsyncMock(return_value=None)
        mock_repo.backup_configuration = AsyncMock(return_value=True)
        
        return {
            'temp_dir': temp_dir,
            'repository': mock_repo
        }
    
    @pytest.mark.asyncio
    async def test_complete_dynaconf_configuration_workflow(self, dynaconf_e2e_environment):
        """Test complete Dynaconf configuration workflow."""
        env = dynaconf_e2e_environment
        
        # Import Dynaconf components
        from manage_config import (
            ConfigurationSet, ConfigurationItem, ConfigurationKey, ConfigurationValue,
            ConfigurationFormat, Environment, CreateConfigurationUseCase,
            UpdateConfigurationUseCase, DeleteConfigurationUseCase,
            CreateConfigurationCommand, UpdateConfigurationCommand, DeleteConfigurationCommand
        )
        
        # Step 1: Create new configuration set
        create_use_case = CreateConfigurationUseCase(env['repository'])
        create_command = CreateConfigurationCommand("E2ETestProject", ConfigurationFormat.TOML)
        
        config_set = await create_use_case.execute(create_command, env['temp_dir'])
        assert config_set.project_name == "E2ETestProject"
        assert config_set.format == ConfigurationFormat.TOML
        
        # Step 2: Add configuration items
        update_use_case = UpdateConfigurationUseCase(env['repository'], Mock())
        
        items_to_add = [
            ("PROJECT_NAME", "E2ETestProject", "Project name"),
            ("DEBUG", True, "Debug mode"),
            ("DATABASE_URL", "postgresql://localhost/e2e_test", "Database URL"),
            ("SECRET_KEY", "super_secret_e2e_key", "Secret key"),
            ("API_TIMEOUT", 30, "API timeout in seconds")
        ]
        
        for key, value, description in items_to_add:
            update_command = UpdateConfigurationCommand(
                key_name=key,
                new_value=value,
                description=description
            )
            result = await update_use_case.execute(update_command, config_set)
            assert result is True
        
        # Step 3: Verify all items were added
        assert len(config_set.items) == len(items_to_add) + len(config_set.items)  # Including defaults
        
        for key, _, _ in items_to_add:
            assert key in config_set.items
        
        # Step 4: Test environment-specific configurations
        # Add development-specific item
        dev_command = UpdateConfigurationCommand(
            key_name="DEV_FEATURE_FLAG",
            new_value=True,
            description="Development feature flag",
            environment=Environment.DEVELOPMENT
        )
        await update_use_case.execute(dev_command, config_set)
        
        # Add production-specific item
        prod_command = UpdateConfigurationCommand(
            key_name="PROD_OPTIMIZATION",
            new_value=True,
            description="Production optimization",
            environment=Environment.PRODUCTION
        )
        await update_use_case.execute(prod_command, config_set)
        
        # Step 5: Test environment filtering
        dev_items = config_set.get_items_by_environment(Environment.DEVELOPMENT)
        prod_items = config_set.get_items_by_environment(Environment.PRODUCTION)
        
        assert len(dev_items) > 0
        assert len(prod_items) > 0
        assert any(item.key.name == "DEV_FEATURE_FLAG" for item in dev_items)
        assert any(item.key.name == "PROD_OPTIMIZATION" for item in prod_items)
        
        # Step 6: Test configuration validation
        from manage_config import ConfigurationValidator
        validator = ConfigurationValidator()
        
        validation_errors = []
        for key, item in config_set.items.items():
            key_errors = validator.validate_key(item.key.name)
            value_errors = validator.validate_value(item.value.value, item.value.value_type)
            validation_errors.extend(key_errors)
            validation_errors.extend(value_errors)
        
        # Should have no validation errors for properly created items
        assert len(validation_errors) == 0
        
        # Step 7: Test item deletion
        delete_use_case = DeleteConfigurationUseCase(env['repository'])
        delete_command = DeleteConfigurationCommand(key_name="DEV_FEATURE_FLAG")
        
        delete_result = await delete_use_case.execute(delete_command, config_set)
        assert delete_result is True
        assert "DEV_FEATURE_FLAG" not in config_set.items
        
        # Step 8: Test sensitive data handling
        secret_item = config_set.get_item("SECRET_KEY")
        assert secret_item is not None
        assert secret_item.is_sensitive() is True
        
        # Cleanup
        FileSystemTestHelper.cleanup_temp_directory(env['temp_dir'])
    
    @pytest.mark.asyncio
    async def test_dynaconf_configuration_persistence_workflow(self, dynaconf_e2e_environment):
        """Test configuration persistence workflow."""
        env = dynaconf_e2e_environment
        
        from manage_config import ConfigurationSet, ConfigurationFormat
        
        # Step 1: Create configuration
        config_set = ConfigurationSet("PersistenceTest", ConfigurationFormat.JSON)
        
        # Step 2: Save configuration
        save_result = await env['repository'].save_configuration(config_set)
        assert save_result is True
        
        # Step 3: Mock loading configuration
        env['repository'].load_configuration.return_value = config_set
        loaded_config = await env['repository'].load_configuration("PersistenceTest")
        
        assert loaded_config is not None
        assert loaded_config.project_name == "PersistenceTest"
        assert loaded_config.format == ConfigurationFormat.JSON
        
        # Step 4: Test backup functionality
        backup_result = await env['repository'].backup_configuration(config_set)
        assert backup_result is True
        
        # Cleanup
        FileSystemTestHelper.cleanup_temp_directory(env['temp_dir'])


class TestCrossSystemIntegration:
    """Test integration between Loguru and Dynaconf TUI systems."""
    
    @pytest.fixture
    def integrated_e2e_environment(self):
        """Set up environment for cross-system integration testing."""
        temp_dir = FileSystemTestHelper.create_temp_directory_structure({
            'configs': {
                'logging': {},
                'app': {}
            },
            'logs': {},
            'exports': {}
        })
        
        # Loguru components
        loguru_config_repo = MockLoggerConfigurationRepository()
        loguru_config_repo.storage_path = temp_dir / 'configs' / 'logging'
        loguru_logger_adapter = MockLoggerApplicationAdapter()
        loguru_tui = LoguruConfigApp(loguru_config_repo, loguru_logger_adapter)
        
        # Dynaconf components
        dynaconf_repo = Mock()
        dynaconf_repo.save_configuration = AsyncMock(return_value=True)
        dynaconf_repo.load_configuration = AsyncMock(return_value=None)
        
        return {
            'temp_dir': temp_dir,
            'loguru': {
                'config_repo': loguru_config_repo,
                'logger_adapter': loguru_logger_adapter,
                'tui': loguru_tui
            },
            'dynaconf': {
                'repository': dynaconf_repo
            }
        }
    
    @pytest.mark.asyncio
    async def test_configuration_sharing_between_systems(self, integrated_e2e_environment, sample_logger_config):
        """Test sharing configurations between Loguru and Dynaconf systems."""
        env = integrated_e2e_environment
        
        # Step 1: Create Loguru configuration
        loguru_tui = env['loguru']['tui']
        await loguru_tui.config_port.save_configuration(sample_logger_config)
        
        # Step 2: Export Loguru configuration
        exported_config = await loguru_tui.config_port.export_configuration(
            sample_logger_config.name, "json"
        )
        assert exported_config is not None
        
        # Step 3: Save exported configuration to shared location
        shared_config_file = env['temp_dir'] / 'exports' / 'shared_config.json'
        shared_config_file.write_text(exported_config)
        
        # Step 4: Create Dynaconf configuration that references Loguru settings
        from manage_config import ConfigurationSet, ConfigurationItem, ConfigurationKey, ConfigurationValue, ConfigurationFormat
        
        dynaconf_config = ConfigurationSet("SharedProject", ConfigurationFormat.JSON)
        
        # Add reference to Loguru configuration
        loguru_ref_item = ConfigurationItem(
            key=ConfigurationKey("LOGURU_CONFIG_FILE"),
            value=ConfigurationValue(str(shared_config_file)),
            description="Path to Loguru configuration file"
        )
        dynaconf_config.add_item(loguru_ref_item)
        
        # Step 5: Save Dynaconf configuration
        save_result = await env['dynaconf']['repository'].save_configuration(dynaconf_config)
        assert save_result is True
        
        # Step 6: Verify configurations can coexist
        loguru_configs = await loguru_tui.config_port.list_configurations()
        assert sample_logger_config.name in loguru_configs
        
        # Cleanup
        FileSystemTestHelper.cleanup_temp_directory(env['temp_dir'])
    
    @pytest.mark.asyncio
    async def test_concurrent_system_operations(self, integrated_e2e_environment, sample_logger_config):
        """Test concurrent operations across both systems."""
        env = integrated_e2e_environment
        
        # Define concurrent operations
        async def loguru_operations():
            loguru_tui = env['loguru']['tui']
            await loguru_tui.config_port.save_configuration(sample_logger_config)
            await loguru_tui.test_configuration(sample_logger_config)
            return "loguru_complete"
        
        async def dynaconf_operations():
            from manage_config import ConfigurationSet, ConfigurationFormat
            config_set = ConfigurationSet("ConcurrentTest", ConfigurationFormat.TOML)
            await env['dynaconf']['repository'].save_configuration(config_set)
            return "dynaconf_complete"
        
        # Execute operations concurrently
        results = await asyncio.gather(
            loguru_operations(),
            dynaconf_operations(),
            return_exceptions=True
        )
        
        # Verify both operations completed successfully
        assert len(results) == 2
        assert "loguru_complete" in results
        assert "dynaconf_complete" in results
        
        # Cleanup
        FileSystemTestHelper.cleanup_temp_directory(env['temp_dir'])


class TestErrorRecoveryWorkflows:
    """Test error recovery in complete workflows."""
    
    @pytest.mark.asyncio
    async def test_configuration_corruption_recovery(self, temp_config_dir, sample_logger_config):
        """Test recovery from configuration file corruption."""
        # Create repositories
        config_repo = MockLoggerConfigurationRepository()
        config_repo.storage_path = temp_config_dir
        logger_adapter = MockLoggerApplicationAdapter()
        tui_app = LoguruConfigApp(config_repo, logger_adapter)
        
        # Step 1: Save valid configuration
        await tui_app.config_port.save_configuration(sample_logger_config)
        
        # Step 2: Corrupt configuration file
        config_file = temp_config_dir / f"{sample_logger_config.name}.json"
        config_file.write_text("{ invalid json content")
        
        # Step 3: Attempt to load corrupted configuration
        # This should handle the error gracefully
        loaded_config = await tui_app.config_port.load_configuration(sample_logger_config.name)
        
        # The mock implementation should handle this gracefully
        # In a real implementation, this might return None or a default config
        assert loaded_config is None or isinstance(loaded_config, LoggerConfig)
    
    @pytest.mark.asyncio
    async def test_network_failure_simulation(self, sample_logger_config):
        """Test handling of network-like failures in operations."""
        # Create repositories that simulate network failures
        failing_config_repo = Mock()
        failing_config_repo.save_configuration = AsyncMock(side_effect=asyncio.TimeoutError("Network timeout"))
        failing_config_repo.load_configuration = AsyncMock(side_effect=ConnectionError("Connection failed"))
        
        logger_adapter = MockLoggerApplicationAdapter()
        tui_app = LoguruConfigApp(failing_config_repo, logger_adapter)
        
        # Step 1: Attempt save operation (should fail gracefully)
        tui_app.current_config = sample_logger_config
        save_result = await tui_app.save_current_configuration()
        assert save_result is False
        
        # Step 2: Attempt load operation (should fail gracefully)
        load_result = await tui_app.load_configuration("test_config")
        assert load_result is False
    
    @pytest.mark.asyncio
    async def test_partial_operation_recovery(self, sample_logger_config):
        """Test recovery from partial operation failures."""
        # Create a repository that fails intermittently
        intermittent_repo = Mock()
        call_count = 0
        
        async def intermittent_save(config):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("First attempt fails")
            return True
        
        intermittent_repo.save_configuration = AsyncMock(side_effect=intermittent_save)
        
        logger_adapter = MockLoggerApplicationAdapter()
        tui_app = LoguruConfigApp(intermittent_repo, logger_adapter)
        
        # Step 1: First save attempt (should fail)
        tui_app.current_config = sample_logger_config
        first_result = await tui_app.save_current_configuration()
        assert first_result is False
        
        # Step 2: Second save attempt (should succeed)
        second_result = await tui_app.save_current_configuration()
        assert second_result is True


class TestPerformanceE2E:
    """Test end-to-end performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_large_scale_configuration_management(self):
        """Test performance with large numbers of configurations."""
        # Create test environment
        temp_dir = FileSystemTestHelper.create_temp_directory_structure({
            'configs': {'logging': {}}
        })
        
        config_repo = MockLoggerConfigurationRepository()
        config_repo.storage_path = temp_dir / 'configs' / 'logging'
        logger_adapter = MockLoggerApplicationAdapter()
        tui_app = LoguruConfigApp(config_repo, logger_adapter)
        
        # Create many configurations
        configs = []
        for i in range(50):
            config = LoggerConfig(
                name=f"perf_test_config_{i}",
                description=f"Performance test configuration {i}",
                enabled=True,
                global_level=LogLevel.DEBUG,
                handlers=[],
                activation=[],
                patcher=None,
                extra={}
            )
            configs.append(config)
        
        # Measure save performance
        start_time = asyncio.get_event_loop().time()
        
        for config in configs:
            await tui_app.config_port.save_configuration(config)
        
        save_time = asyncio.get_event_loop().time() - start_time
        
        # Should complete in reasonable time
        assert save_time < 5.0  # 5 seconds for 50 configurations
        
        # Measure load performance
        start_time = asyncio.get_event_loop().time()
        
        loaded_configs = []
        for config in configs:
            loaded = await tui_app.config_port.load_configuration(config.name)
            loaded_configs.append(loaded)
        
        load_time = asyncio.get_event_loop().time() - start_time
        
        # Should complete in reasonable time
        assert load_time < 3.0  # 3 seconds for 50 loads
        
        # Verify all configurations were loaded
        assert len(loaded_configs) == 50
        assert all(config is not None for config in loaded_configs)
        
        # Cleanup
        FileSystemTestHelper.cleanup_temp_directory(temp_dir)
    
    @pytest.mark.asyncio
    async def test_concurrent_user_simulation(self, sample_logger_config):
        """Test performance under concurrent user operations."""
        # Create shared resources
        config_repo = MockLoggerConfigurationRepository()
        logger_adapter = MockLoggerApplicationAdapter()
        
        # Simulate multiple concurrent users
        async def user_workflow(user_id: int):
            tui_app = LoguruConfigApp(config_repo, logger_adapter)
            
            # Each user creates their own configuration
            user_config = LoggerConfig(
                name=f"user_{user_id}_config",
                description=f"Configuration for user {user_id}",
                enabled=True,
                global_level=LogLevel.INFO,
                handlers=[],
                activation=[],
                patcher=None,
                extra={}
            )
            
            # Perform typical user operations
            await tui_app.config_port.save_configuration(user_config)
            await tui_app.load_configuration(user_config.name)
            await tui_app.test_configuration(user_config)
            
            return f"user_{user_id}_complete"
        
        # Execute concurrent user workflows
        start_time = asyncio.get_event_loop().time()
        
        user_tasks = [user_workflow(i) for i in range(10)]
        results = await asyncio.gather(*user_tasks)
        
        total_time = asyncio.get_event_loop().time() - start_time
        
        # Verify all users completed successfully
        assert len(results) == 10
        assert all("complete" in result for result in results)
        
        # Should complete in reasonable time even with concurrency
        assert total_time < 10.0  # 10 seconds for 10 concurrent users
        
        # Verify all configurations were created
        config_list = await config_repo.list_configurations()
        assert len(config_list) == 10

