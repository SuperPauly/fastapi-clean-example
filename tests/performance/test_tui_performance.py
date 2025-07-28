"""Performance tests for TUI components."""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock
from pathlib import Path

# Import test utilities
from tests.fixtures.tui_fixtures import sample_logger_config, async_test_timeout
from tests.fixtures.mock_repositories import MockLoggerConfigurationRepository, MockLoggerApplicationAdapter
from tests.utils.tui_test_helpers import AsyncTestHelper

# Import components under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.presentation.tui.app import LoguruConfigApp
from src.domain.entities.logger_config import LoggerConfig
from src.domain.value_objects.log_level import LogLevel


class TestLoguruTUIPerformance:
    """Test performance characteristics of Loguru TUI."""
    
    @pytest.fixture
    def performance_test_environment(self):
        """Set up environment for performance testing."""
        config_repo = MockLoggerConfigurationRepository()
        logger_adapter = MockLoggerApplicationAdapter()
        tui_app = LoguruConfigApp(config_repo, logger_adapter)
        
        return {
            'config_repo': config_repo,
            'logger_adapter': logger_adapter,
            'tui_app': tui_app
        }
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_configuration_loading_performance(self, performance_test_environment, sample_logger_config):
        """Test configuration loading performance under various conditions."""
        env = performance_test_environment
        tui_app = env['tui_app']
        
        # Save configuration first
        await tui_app.config_port.save_configuration(sample_logger_config)
        
        # Test single load performance
        start_time = time.perf_counter()
        result = await tui_app.load_configuration(sample_logger_config.name)
        single_load_time = time.perf_counter() - start_time
        
        assert result is True
        assert single_load_time < 0.1  # Should load in under 100ms
        
        # Test multiple sequential loads
        start_time = time.perf_counter()
        for _ in range(10):
            await tui_app.load_configuration(sample_logger_config.name)
        sequential_load_time = time.perf_counter() - start_time
        
        assert sequential_load_time < 1.0  # 10 loads in under 1 second
        
        # Test concurrent loads
        start_time = time.perf_counter()
        tasks = [tui_app.load_configuration(sample_logger_config.name) for _ in range(10)]
        await asyncio.gather(*tasks)
        concurrent_load_time = time.perf_counter() - start_time
        
        assert concurrent_load_time < 0.5  # Concurrent loads should be faster
        
        # Performance should improve with concurrency
        assert concurrent_load_time < sequential_load_time
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_configuration_saving_performance(self, performance_test_environment):
        """Test configuration saving performance."""
        env = performance_test_environment
        tui_app = env['tui_app']
        
        # Create multiple configurations for testing
        configs = []
        for i in range(20):
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
        
        # Test sequential saves
        start_time = time.perf_counter()
        for config in configs:
            await tui_app.config_port.save_configuration(config)
        sequential_save_time = time.perf_counter() - start_time
        
        assert sequential_save_time < 2.0  # 20 saves in under 2 seconds
        
        # Test concurrent saves (create new configs to avoid conflicts)
        concurrent_configs = []
        for i in range(20):
            config = LoggerConfig(
                name=f"concurrent_perf_test_config_{i}",
                description=f"Concurrent performance test configuration {i}",
                enabled=True,
                global_level=LogLevel.INFO,
                handlers=[],
                activation=[],
                patcher=None,
                extra={}
            )
            concurrent_configs.append(config)
        
        start_time = time.perf_counter()
        save_tasks = [tui_app.config_port.save_configuration(config) for config in concurrent_configs]
        await asyncio.gather(*save_tasks)
        concurrent_save_time = time.perf_counter() - start_time
        
        assert concurrent_save_time < 1.0  # Concurrent saves should be faster
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_configuration_testing_performance(self, performance_test_environment, sample_logger_config):
        """Test configuration testing performance."""
        env = performance_test_environment
        tui_app = env['tui_app']
        
        # Test single configuration test
        start_time = time.perf_counter()
        result = await tui_app.test_configuration(sample_logger_config)
        single_test_time = time.perf_counter() - start_time
        
        assert result["success"] is True
        assert single_test_time < 0.2  # Should test in under 200ms
        
        # Test multiple configuration tests
        start_time = time.perf_counter()
        for _ in range(5):
            await tui_app.test_configuration(sample_logger_config)
        multiple_test_time = time.perf_counter() - start_time
        
        assert multiple_test_time < 1.0  # 5 tests in under 1 second
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_preview_generation_performance(self, performance_test_environment, sample_logger_config):
        """Test log preview generation performance."""
        env = performance_test_environment
        tui_app = env['tui_app']
        
        # Test with small message set
        small_messages = [f"Test message {i}" for i in range(10)]
        start_time = time.perf_counter()
        result = await tui_app.preview_log_output(sample_logger_config, small_messages)
        small_preview_time = time.perf_counter() - start_time
        
        assert len(result) == len(small_messages)
        assert small_preview_time < 0.1  # Should generate quickly
        
        # Test with large message set
        large_messages = [f"Test message {i}" for i in range(1000)]
        start_time = time.perf_counter()
        result = await tui_app.preview_log_output(sample_logger_config, large_messages)
        large_preview_time = time.perf_counter() - start_time
        
        assert len(result) == len(large_messages)
        assert large_preview_time < 1.0  # Should handle large sets efficiently
        
        # Performance should scale reasonably
        assert large_preview_time < small_preview_time * 200  # Not more than 200x slower
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_memory_usage_performance(self, performance_test_environment):
        """Test memory usage characteristics."""
        env = performance_test_environment
        tui_app = env['tui_app']
        
        # Create many configurations to test memory usage
        configs = []
        for i in range(100):
            config = LoggerConfig(
                name=f"memory_test_config_{i}",
                description=f"Memory test configuration {i}",
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
        assert len(loaded_configs) == 100
        assert all(config is not None for config in loaded_configs)
        
        # Test that operations still work efficiently with many configs in memory
        start_time = time.perf_counter()
        test_results = []
        for config in loaded_configs[:10]:  # Test first 10 to avoid excessive test time
            result = await tui_app.test_configuration(config)
            test_results.append(result)
        operation_time = time.perf_counter() - start_time
        
        assert len(test_results) == 10
        assert all(result["success"] for result in test_results)
        assert operation_time < 2.0  # Should still operate efficiently


class TestDynaconfTUIPerformance:
    """Test performance characteristics of Dynaconf TUI."""
    
    @pytest.fixture
    def dynaconf_performance_environment(self):
        """Set up environment for Dynaconf performance testing."""
        mock_repo = Mock()
        mock_repo.save_configuration = AsyncMock(return_value=True)
        mock_repo.load_configuration = AsyncMock(return_value=None)
        mock_repo.backup_configuration = AsyncMock(return_value=True)
        
        return {'repository': mock_repo}
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_large_configuration_set_performance(self, dynaconf_performance_environment):
        """Test performance with large configuration sets."""
        env = dynaconf_performance_environment
        
        from manage_config import (
            ConfigurationSet, ConfigurationItem, ConfigurationKey, ConfigurationValue,
            ConfigurationFormat, UpdateConfigurationUseCase, UpdateConfigurationCommand
        )
        
        # Create large configuration set
        config_set = ConfigurationSet("LargePerformanceTest", ConfigurationFormat.TOML)
        update_use_case = UpdateConfigurationUseCase(env['repository'], Mock())
        
        # Add many configuration items
        start_time = time.perf_counter()
        for i in range(500):
            command = UpdateConfigurationCommand(
                key_name=f"CONFIG_ITEM_{i}",
                new_value=f"value_{i}",
                description=f"Configuration item {i}"
            )
            await update_use_case.execute(command, config_set)
        creation_time = time.perf_counter() - start_time
        
        assert len(config_set.items) >= 500
        assert creation_time < 5.0  # Should create 500 items in under 5 seconds
        
        # Test retrieval performance
        start_time = time.perf_counter()
        for i in range(100):  # Test retrieving 100 items
            item = config_set.get_item(f"CONFIG_ITEM_{i}")
            assert item is not None
        retrieval_time = time.perf_counter() - start_time
        
        assert retrieval_time < 0.1  # Should retrieve quickly
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_validation_performance(self, dynaconf_performance_environment):
        """Test validation performance with many configuration items."""
        from manage_config import (
            ConfigurationSet, ConfigurationItem, ConfigurationKey, ConfigurationValue,
            ConfigurationFormat, ConfigurationValidator
        )
        
        # Create configuration set with many items
        config_set = ConfigurationSet("ValidationPerformanceTest", ConfigurationFormat.JSON)
        
        for i in range(200):
            item = ConfigurationItem(
                key=ConfigurationKey(f"VALID_CONFIG_ITEM_{i}"),
                value=ConfigurationValue(f"valid_value_{i}"),
                description=f"Valid configuration item {i}"
            )
            config_set.add_item(item)
        
        # Test validation performance
        validator = ConfigurationValidator()
        start_time = time.perf_counter()
        
        total_errors = []
        for key, item in config_set.items.items():
            key_errors = validator.validate_key(item.key.name)
            value_errors = validator.validate_value(item.value.value, item.value.value_type)
            total_errors.extend(key_errors)
            total_errors.extend(value_errors)
        
        validation_time = time.perf_counter() - start_time
        
        assert len(total_errors) == 0  # All items should be valid
        assert validation_time < 1.0  # Should validate 200 items in under 1 second
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_environment_filtering_performance(self, dynaconf_performance_environment):
        """Test performance of environment-based filtering."""
        from manage_config import (
            ConfigurationSet, ConfigurationItem, ConfigurationKey, ConfigurationValue,
            ConfigurationFormat, Environment
        )
        
        # Create configuration set with items for different environments
        config_set = ConfigurationSet("FilteringPerformanceTest", ConfigurationFormat.YAML)
        
        environments = [Environment.DEVELOPMENT, Environment.PRODUCTION, Environment.TESTING, None]
        
        for i in range(400):  # 100 items per environment
            env = environments[i % len(environments)]
            item = ConfigurationItem(
                key=ConfigurationKey(f"CONFIG_ITEM_{i}"),
                value=ConfigurationValue(f"value_{i}"),
                description=f"Configuration item {i}",
                environment=env
            )
            config_set.add_item(item)
        
        # Test filtering performance
        start_time = time.perf_counter()
        
        dev_items = config_set.get_items_by_environment(Environment.DEVELOPMENT)
        prod_items = config_set.get_items_by_environment(Environment.PRODUCTION)
        test_items = config_set.get_items_by_environment(Environment.TESTING)
        
        filtering_time = time.perf_counter() - start_time
        
        # Verify filtering results
        assert len(dev_items) == 100
        assert len(prod_items) == 100
        assert len(test_items) == 100
        
        # Should filter quickly
        assert filtering_time < 0.1  # Should filter 400 items in under 100ms


class TestConcurrentPerformance:
    """Test performance under concurrent operations."""
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_concurrent_tui_operations(self, sample_logger_config):
        """Test performance of concurrent TUI operations."""
        # Create multiple TUI instances to simulate concurrent users
        tui_instances = []
        for i in range(5):
            config_repo = MockLoggerConfigurationRepository()
            logger_adapter = MockLoggerApplicationAdapter()
            tui_app = LoguruConfigApp(config_repo, logger_adapter)
            tui_instances.append(tui_app)
        
        # Define concurrent operations
        async def user_operations(tui_app, user_id):
            # Each user performs typical operations
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
            
            # Save configuration
            await tui_app.config_port.save_configuration(user_config)
            
            # Load configuration
            await tui_app.load_configuration(user_config.name)
            
            # Test configuration
            await tui_app.test_configuration(user_config)
            
            # Preview output
            await tui_app.preview_log_output(user_config, ["Test message"])
            
            return f"user_{user_id}_complete"
        
        # Execute concurrent operations
        start_time = time.perf_counter()
        
        tasks = [user_operations(tui_app, i) for i, tui_app in enumerate(tui_instances)]
        results = await asyncio.gather(*tasks)
        
        concurrent_time = time.perf_counter() - start_time
        
        # Verify all operations completed
        assert len(results) == 5
        assert all("complete" in result for result in results)
        
        # Should complete efficiently even with concurrency
        assert concurrent_time < 3.0  # 5 concurrent users in under 3 seconds
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_mixed_operation_performance(self):
        """Test performance of mixed read/write operations."""
        config_repo = MockLoggerConfigurationRepository()
        logger_adapter = MockLoggerApplicationAdapter()
        tui_app = LoguruConfigApp(config_repo, logger_adapter)
        
        # Create initial configurations
        configs = []
        for i in range(10):
            config = LoggerConfig(
                name=f"mixed_test_config_{i}",
                description=f"Mixed test configuration {i}",
                enabled=True,
                global_level=LogLevel.DEBUG,
                handlers=[],
                activation=[],
                patcher=None,
                extra={}
            )
            configs.append(config)
            await tui_app.config_port.save_configuration(config)
        
        # Define mixed operations
        async def mixed_operations():
            operations = []
            
            # Mix of read and write operations
            for i in range(20):
                if i % 3 == 0:
                    # Write operation
                    new_config = LoggerConfig(
                        name=f"mixed_new_config_{i}",
                        description=f"New configuration {i}",
                        enabled=True,
                        global_level=LogLevel.INFO,
                        handlers=[],
                        activation=[],
                        patcher=None,
                        extra={}
                    )
                    operations.append(tui_app.config_port.save_configuration(new_config))
                else:
                    # Read operation
                    config_name = f"mixed_test_config_{i % 10}"
                    operations.append(tui_app.load_configuration(config_name))
            
            return await asyncio.gather(*operations)
        
        # Execute mixed operations
        start_time = time.perf_counter()
        results = await mixed_operations()
        mixed_time = time.perf_counter() - start_time
        
        # Verify operations completed
        assert len(results) == 20
        
        # Should handle mixed operations efficiently
        assert mixed_time < 2.0  # 20 mixed operations in under 2 seconds


class TestScalabilityPerformance:
    """Test scalability characteristics."""
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_configuration_count_scalability(self):
        """Test how performance scales with number of configurations."""
        config_repo = MockLoggerConfigurationRepository()
        logger_adapter = MockLoggerApplicationAdapter()
        tui_app = LoguruConfigApp(config_repo, logger_adapter)
        
        # Test with different configuration counts
        config_counts = [10, 50, 100, 200]
        performance_results = {}
        
        for count in config_counts:
            # Create configurations
            configs = []
            for i in range(count):
                config = LoggerConfig(
                    name=f"scale_test_config_{count}_{i}",
                    description=f"Scale test configuration {i} for count {count}",
                    enabled=True,
                    global_level=LogLevel.DEBUG,
                    handlers=[],
                    activation=[],
                    patcher=None,
                    extra={}
                )
                configs.append(config)
                await tui_app.config_port.save_configuration(config)
            
            # Measure list operation performance
            start_time = time.perf_counter()
            config_list = await tui_app.config_port.list_configurations()
            list_time = time.perf_counter() - start_time
            
            # Measure load operation performance (sample of 10 configs)
            start_time = time.perf_counter()
            sample_size = min(10, count)
            for i in range(sample_size):
                await tui_app.load_configuration(f"scale_test_config_{count}_{i}")
            load_time = time.perf_counter() - start_time
            
            performance_results[count] = {
                'list_time': list_time,
                'load_time': load_time,
                'configs_created': len(config_list)
            }
        
        # Verify scalability characteristics
        for count in config_counts:
            result = performance_results[count]
            
            # List operation should remain fast
            assert result['list_time'] < 0.1, f"List operation too slow for {count} configs"
            
            # Load operations should remain reasonable
            assert result['load_time'] < 1.0, f"Load operations too slow for {count} configs"
            
            # Verify correct number of configurations
            assert result['configs_created'] >= count
        
        # Performance should not degrade dramatically
        small_list_time = performance_results[10]['list_time']
        large_list_time = performance_results[200]['list_time']
        
        # Large list should not be more than 10x slower than small list
        assert large_list_time < small_list_time * 10

