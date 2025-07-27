"""CLI command handlers for Loguru configuration."""

import asyncio
import json
import sys
from typing import Dict, Any, Optional
from pathlib import Path
import argparse

from src.domain.entities.logger_config import LoggerConfig, HandlerConfig
from src.domain.value_objects.log_level import LogLevel, LogLevelEnum
from src.domain.value_objects.log_format import LogFormat, LogFormatPreset
from src.domain.value_objects.rotation_policy import RotationPolicy, RotationType, SizeUnit, TimeUnit
from src.application.use_cases.load_logger_config import LoadLoggerConfigUseCase, LoadLoggerConfigRequest
from src.application.use_cases.save_logger_config import SaveLoggerConfigUseCase, SaveLoggerConfigRequest
from src.application.use_cases.test_logger_config import TestLoggerConfigUseCase, TestLoggerConfigRequest
from src.application.ports.logger_configuration import LoggerConfigurationPort, LoggerApplicationPort


class CLICommandHandler:
    """Handler for CLI commands."""
    
    def __init__(
        self,
        config_port: LoggerConfigurationPort,
        logger_port: LoggerApplicationPort
    ):
        """
        Initialize the CLI command handler.
        
        Args:
            config_port: Logger configuration port.
            logger_port: Logger application port.
        """
        self._config_port = config_port
        self._logger_port = logger_port
        
        # Initialize use cases
        self._load_use_case = LoadLoggerConfigUseCase(config_port)
        self._save_use_case = SaveLoggerConfigUseCase(config_port)
        self._test_use_case = TestLoggerConfigUseCase(logger_port)
    
    async def handle_command(self, args: argparse.Namespace) -> int:
        """
        Handle CLI command based on arguments.
        
        Args:
            args: Parsed command line arguments.
            
        Returns:
            Exit code (0 for success, non-zero for error).
        """
        try:
            if args.command == "configure" or self._has_config_args(args):
                return await self._handle_configure(args)
            elif args.command == "test":
                return await self._handle_test(args)
            elif args.command == "show":
                return await self._handle_show(args)
            elif args.command == "reset":
                return await self._handle_reset(args)
            elif args.command == "export":
                return await self._handle_export(args)
            elif args.command == "import":
                return await self._handle_import(args)
            else:
                print("No command specified. Use --help for usage information.", file=sys.stderr)
                return 1
                
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
    
    async def _handle_configure(self, args: argparse.Namespace) -> int:
        """Handle configuration command."""
        try:
            # Load existing configuration or create new one
            config_name = getattr(args, 'config_name', 'default')
            load_response = await self._load_use_case.execute(
                LoadLoggerConfigRequest(name=config_name)
            )
            
            if load_response.success:
                config = load_response.config
                print(f"Loaded existing configuration: {config.name}")
            else:
                # Create new configuration
                config = LoggerConfig(name=config_name)
                print(f"Created new configuration: {config.name}")
            
            # Apply CLI arguments to configuration
            updated_config = self._apply_args_to_config(config, args)
            
            # Save configuration if requested
            if getattr(args, 'save_config', False):
                save_response = await self._save_use_case.execute(
                    SaveLoggerConfigRequest(config=updated_config)
                )
                if save_response.success:
                    print(f"Configuration saved: {save_response.message}")
                    if save_response.warnings:
                        print("Warnings:")
                        for warning in save_response.warnings:
                            print(f"  - {warning}")
                else:
                    print(f"Failed to save configuration: {save_response.message}", file=sys.stderr)
                    return 1
            
            # Apply configuration to logger
            success = await self._logger_port.apply_configuration(updated_config)
            if success:
                print("Configuration applied successfully")
                
                # Test configuration if requested
                if hasattr(args, 'test') and args.test:
                    return await self._test_configuration(updated_config, preview_only=True)
            else:
                print("Failed to apply configuration", file=sys.stderr)
                return 1
            
            return 0
            
        except Exception as e:
            print(f"Configuration failed: {e}", file=sys.stderr)
            return 1
    
    async def _handle_test(self, args: argparse.Namespace) -> int:
        """Handle test command."""
        try:
            config_name = getattr(args, 'config_name', 'default')
            
            # Load configuration
            load_response = await self._load_use_case.execute(
                LoadLoggerConfigRequest(name=config_name)
            )
            
            if not load_response.success:
                print(f"Failed to load configuration: {load_response.message}", file=sys.stderr)
                return 1
            
            # Prepare test request
            test_request = TestLoggerConfigRequest(
                config=load_response.config,
                test_messages=getattr(args, 'test_messages', None),
                preview_only=getattr(args, 'preview_only', False)
            )
            
            # Execute test
            test_response = await self._test_use_case.execute(test_request)
            
            if test_response.success:
                print(f"Test result: {test_response.message}")
                
                # Display preview output
                if test_response.preview_output:
                    print("\nPreview output:")
                    for line in test_response.preview_output:
                        print(line)
                
                # Display warnings
                if test_response.warnings:
                    print("\nWarnings:")
                    for warning in test_response.warnings:
                        print(f"  - {warning}")
                
                # Save output to file if requested
                output_file = getattr(args, 'output_file', None)
                if output_file and test_response.preview_output:
                    with open(output_file, 'w') as f:
                        f.write('\n'.join(test_response.preview_output))
                    print(f"\nOutput saved to: {output_file}")
                
                return 0
            else:
                print(f"Test failed: {test_response.message}", file=sys.stderr)
                return 1
                
        except Exception as e:
            print(f"Test failed: {e}", file=sys.stderr)
            return 1
    
    async def _handle_show(self, args: argparse.Namespace) -> int:
        """Handle show command."""
        try:
            config_name = getattr(args, 'config_name', None)
            
            if config_name:
                # Show specific configuration
                load_response = await self._load_use_case.execute(
                    LoadLoggerConfigRequest(name=config_name)
                )
                
                if not load_response.success:
                    print(f"Configuration not found: {load_response.message}", file=sys.stderr)
                    return 1
                
                config = load_response.config
            else:
                # Show current configuration
                config = await self._logger_port.get_current_configuration()
                if not config:
                    print("No current configuration available", file=sys.stderr)
                    return 1
            
            # Format and display configuration
            output_format = getattr(args, 'format', 'table')
            verbose = getattr(args, 'verbose', False)
            
            if output_format == 'json':
                self._display_json(config, verbose)
            elif output_format == 'yaml':
                self._display_yaml(config, verbose)
            elif output_format == 'toml':
                self._display_toml(config, verbose)
            else:  # table
                self._display_table(config, verbose)
            
            return 0
            
        except Exception as e:
            print(f"Show failed: {e}", file=sys.stderr)
            return 1
    
    async def _handle_reset(self, args: argparse.Namespace) -> int:
        """Handle reset command."""
        try:
            config_name = getattr(args, 'config_name', None)
            confirm = getattr(args, 'confirm', False)
            
            if not confirm:
                if config_name:
                    response = input(f"Reset configuration '{config_name}'? (y/N): ")
                else:
                    response = input("Reset all configurations? (y/N): ")
                
                if response.lower() not in ['y', 'yes']:
                    print("Reset cancelled")
                    return 0
            
            if config_name:
                # Reset specific configuration
                success = await self._config_port.delete_configuration(config_name)
                if success:
                    print(f"Configuration '{config_name}' reset successfully")
                else:
                    print(f"Failed to reset configuration '{config_name}'", file=sys.stderr)
                    return 1
            else:
                # Reset logger to default state
                success = await self._logger_port.reset_logger()
                if success:
                    print("Logger reset to default state")
                else:
                    print("Failed to reset logger", file=sys.stderr)
                    return 1
            
            return 0
            
        except Exception as e:
            print(f"Reset failed: {e}", file=sys.stderr)
            return 1
    
    async def _handle_export(self, args: argparse.Namespace) -> int:
        """Handle export command."""
        try:
            config_name = args.config_name
            export_format = args.format
            output_file = getattr(args, 'output_file', None)
            
            # Export configuration
            exported_data = await self._config_port.export_configuration(
                config_name, 
                export_format
            )
            
            if exported_data is None:
                print(f"Failed to export configuration '{config_name}'", file=sys.stderr)
                return 1
            
            # Output to file or stdout
            if output_file:
                with open(output_file, 'w') as f:
                    f.write(exported_data)
                print(f"Configuration exported to: {output_file}")
            else:
                print(exported_data)
            
            return 0
            
        except Exception as e:
            print(f"Export failed: {e}", file=sys.stderr)
            return 1
    
    async def _handle_import(self, args: argparse.Namespace) -> int:
        """Handle import command."""
        try:
            input_file = args.input_file
            import_format = getattr(args, 'format', None)
            config_name = getattr(args, 'config_name', None)
            overwrite = getattr(args, 'overwrite', False)
            
            # Read input file
            if not Path(input_file).exists():
                print(f"Input file not found: {input_file}", file=sys.stderr)
                return 1
            
            with open(input_file, 'r') as f:
                config_data = f.read()
            
            # Auto-detect format if not specified
            if not import_format:
                if input_file.endswith('.json'):
                    import_format = 'json'
                elif input_file.endswith('.yaml') or input_file.endswith('.yml'):
                    import_format = 'yaml'
                else:
                    import_format = 'toml'
            
            # Import configuration
            imported_config = await self._config_port.import_configuration(
                config_data,
                import_format,
                config_name
            )
            
            if imported_config is None:
                print(f"Failed to import configuration from: {input_file}", file=sys.stderr)
                return 1
            
            # Check if configuration already exists
            if not overwrite:
                existing = await self._config_port.load_configuration(imported_config.name)
                if existing:
                    response = input(f"Configuration '{imported_config.name}' already exists. Overwrite? (y/N): ")
                    if response.lower() not in ['y', 'yes']:
                        print("Import cancelled")
                        return 0
            
            # Save imported configuration
            save_response = await self._save_use_case.execute(
                SaveLoggerConfigRequest(config=imported_config)
            )
            
            if save_response.success:
                print(f"Configuration imported successfully: {imported_config.name}")
                if save_response.warnings:
                    print("Warnings:")
                    for warning in save_response.warnings:
                        print(f"  - {warning}")
            else:
                print(f"Failed to save imported configuration: {save_response.message}", file=sys.stderr)
                return 1
            
            return 0
            
        except Exception as e:
            print(f"Import failed: {e}", file=sys.stderr)
            return 1
    
    def _apply_args_to_config(self, config: LoggerConfig, args: argparse.Namespace) -> LoggerConfig:
        """Apply CLI arguments to configuration."""
        # Create a mutable copy of the configuration
        config_dict = config.model_dump()
        
        # Apply basic settings
        if hasattr(args, 'enable') and args.enable:
            config_dict['enabled'] = True
        elif hasattr(args, 'disable') and args.disable:
            config_dict['enabled'] = False
        
        if hasattr(args, 'log_level') and args.log_level:
            if args.log_level == "CUSTOM" and hasattr(args, 'custom_level') and args.custom_level:
                config_dict['global_level'] = {'value': args.custom_level}
            else:
                config_dict['global_level'] = {'value': args.log_level}
        
        # Apply handler configurations
        handlers = config_dict.get('handlers', [])
        
        # Update or create console handler
        if hasattr(args, 'console_handler') and (args.console_handler or getattr(args, 'no_console_handler', False)):
            console_handler = self._find_or_create_handler(handlers, 'console', 'console')
            console_handler['enabled'] = args.console_handler
        
        # Update or create file handler
        if hasattr(args, 'file_handler') and (args.file_handler or getattr(args, 'file_path', None)):
            file_handler = self._find_or_create_handler(handlers, 'file', 'file')
            if args.file_handler:
                file_handler['enabled'] = True
            if hasattr(args, 'file_path') and args.file_path:
                file_handler['sink'] = args.file_path
                file_handler['enabled'] = True
            
            # Apply file-specific settings
            if hasattr(args, 'file_encoding'):
                file_handler['encoding'] = args.file_encoding
            if hasattr(args, 'file_mode'):
                file_handler['mode'] = args.file_mode
            if hasattr(args, 'file_buffering'):
                file_handler['buffering'] = args.file_buffering
        
        # Apply format settings to all handlers
        for handler in handlers:
            if hasattr(args, 'format_preset') and args.format_preset:
                handler['format_config']['preset'] = args.format_preset
                if args.format_preset == 'custom' and hasattr(args, 'custom_format') and args.custom_format:
                    handler['format_config']['custom_format'] = args.custom_format
            
            if hasattr(args, 'colorize') and args.colorize:
                handler['format_config']['colorize'] = True
            elif hasattr(args, 'no_colorize') and args.no_colorize:
                handler['format_config']['colorize'] = False
            
            if hasattr(args, 'serialize') and args.serialize:
                handler['format_config']['serialize'] = True
            
            if hasattr(args, 'backtrace') and args.backtrace:
                handler['format_config']['backtrace'] = True
            elif hasattr(args, 'no_backtrace') and args.no_backtrace:
                handler['format_config']['backtrace'] = False
            
            if hasattr(args, 'diagnose') and args.diagnose:
                handler['format_config']['diagnose'] = True
            elif hasattr(args, 'no_diagnose') and args.no_diagnose:
                handler['format_config']['diagnose'] = False
            
            # Apply rotation settings
            if hasattr(args, 'rotation_type') and args.rotation_type:
                handler['rotation']['rotation_type'] = args.rotation_type
            
            if hasattr(args, 'rotation_size') and args.rotation_size:
                handler['rotation']['size_limit'] = args.rotation_size
                if hasattr(args, 'rotation_size_unit'):
                    handler['rotation']['size_unit'] = args.rotation_size_unit
            
            if hasattr(args, 'rotation_time') and args.rotation_time:
                handler['rotation']['rotation_time'] = args.rotation_time
            
            if hasattr(args, 'rotation_interval') and args.rotation_interval:
                handler['rotation']['time_interval'] = args.rotation_interval
                if hasattr(args, 'rotation_interval_unit'):
                    handler['rotation']['time_unit'] = args.rotation_interval_unit
            
            if hasattr(args, 'retention_count') and args.retention_count:
                handler['rotation']['retention_count'] = args.retention_count
            
            if hasattr(args, 'retention_time') and args.retention_time:
                handler['rotation']['retention_time'] = args.retention_time
            
            if hasattr(args, 'compression') and args.compression:
                handler['rotation']['compression'] = args.compression
            
            # Apply advanced settings
            if hasattr(args, 'enqueue') and args.enqueue:
                handler['enqueue'] = True
            
            if hasattr(args, 'catch_exceptions') and args.catch_exceptions:
                handler['catch'] = True
            elif hasattr(args, 'no_catch_exceptions') and args.no_catch_exceptions:
                handler['catch'] = False
            
            if hasattr(args, 'filter_expression') and args.filter_expression:
                handler['filter_expression'] = args.filter_expression
        
        config_dict['handlers'] = handlers
        
        # Create new configuration from updated dict
        return LoggerConfig(**config_dict)
    
    def _find_or_create_handler(self, handlers: list, name: str, handler_type: str) -> dict:
        """Find existing handler or create new one."""
        for handler in handlers:
            if handler.get('name') == name:
                return handler
        
        # Create new handler
        new_handler = {
            'name': name,
            'handler_type': handler_type,
            'enabled': True,
            'level': {'value': 'INFO'},
            'format_config': {
                'preset': 'simple',
                'colorize': True,
                'serialize': False,
                'backtrace': True,
                'diagnose': True
            },
            'rotation': {
                'rotation_type': 'none'
            },
            'enqueue': False,
            'catch': True,
            'encoding': 'utf-8',
            'mode': 'a',
            'buffering': 1
        }
        handlers.append(new_handler)
        return new_handler
    
    def _has_config_args(self, args: argparse.Namespace) -> bool:
        """Check if any configuration arguments were provided."""
        config_args = [
            'enable', 'disable', 'log_level', 'file_path', 'rotation_type',
            'format_preset', 'colorize', 'no_colorize', 'console_handler',
            'file_handler', 'syslog_handler', 'systemd_journal'
        ]
        
        return any(getattr(args, arg, None) for arg in config_args)
    
    def _display_json(self, config: LoggerConfig, verbose: bool) -> None:
        """Display configuration as JSON."""
        if verbose:
            data = config.model_dump()
        else:
            data = config.get_summary()
        
        print(json.dumps(data, indent=2, default=str))
    
    def _display_yaml(self, config: LoggerConfig, verbose: bool) -> None:
        """Display configuration as YAML."""
        try:
            import yaml
            if verbose:
                data = config.model_dump()
            else:
                data = config.get_summary()
            
            print(yaml.dump(data, default_flow_style=False))
        except ImportError:
            print("PyYAML not installed. Install with: pip install pyyaml", file=sys.stderr)
    
    def _display_toml(self, config: LoggerConfig, verbose: bool) -> None:
        """Display configuration as TOML."""
        try:
            import tomli_w
            if verbose:
                data = config.model_dump()
            else:
                data = config.get_summary()
            
            print(tomli_w.dumps(data))
        except ImportError:
            print("tomli-w not installed. Install with: pip install tomli-w", file=sys.stderr)
    
    def _display_table(self, config: LoggerConfig, verbose: bool) -> None:
        """Display configuration as formatted table."""
        print(f"Configuration: {config.name}")
        print(f"Status: {'Enabled' if config.enabled else 'Disabled'}")
        print(f"Global Level: {config.global_level}")
        print(f"Handlers: {len(config.handlers)} total, {len(config.enabled_handlers)} enabled")
        
        if verbose:
            print("\nHandlers:")
            for handler in config.handlers:
                status = "✓" if handler.enabled else "✗"
                print(f"  {status} {handler.display_name}")
                print(f"    Level: {handler.level}")
                print(f"    Format: {handler.format_config}")
                if handler.handler_type == 'file' and handler.sink:
                    print(f"    File: {handler.sink}")
                if handler.rotation.rotation_type != RotationType.NONE:
                    print(f"    Rotation: {handler.rotation}")
        
        warnings = config.validate_configuration()
        if warnings:
            print("\nWarnings:")
            for warning in warnings:
                print(f"  ⚠ {warning}")
    
    async def _test_configuration(self, config: LoggerConfig, preview_only: bool = False) -> int:
        """Test a configuration and return exit code."""
        test_request = TestLoggerConfigRequest(
            config=config,
            preview_only=preview_only
        )
        
        test_response = await self._test_use_case.execute(test_request)
        
        if test_response.success:
            print(f"\nTest: {test_response.message}")
            if test_response.preview_output:
                print("Sample output:")
                for line in test_response.preview_output[:3]:  # Show first 3 lines
                    print(f"  {line}")
            return 0
        else:
            print(f"\nTest failed: {test_response.message}", file=sys.stderr)
            return 1
