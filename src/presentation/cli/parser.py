"""Command line argument parser for Loguru configuration."""

import argparse
from typing import Dict, Any, Optional
from pathlib import Path

from src.domain.value_objects.log_level import LogLevelEnum
from src.domain.value_objects.log_format import LogFormatPreset
from src.domain.value_objects.rotation_policy import RotationType, SizeUnit, TimeUnit


class LoguruArgumentParser:
    """Comprehensive argument parser for Loguru configuration."""
    
    def __init__(self):
        """Initialize the argument parser."""
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the main argument parser with all options."""
        parser = argparse.ArgumentParser(
            prog="loguru-config",
            description="Configure Loguru logging with TUI or CLI interface",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=self._get_examples()
        )
        
        # Mode selection
        parser.add_argument(
            "--interactive", "-i",
            action="store_true",
            help="Launch interactive TUI mode (default if no config args provided)"
        )
        
        # Subcommands
        subparsers = parser.add_subparsers(dest="command", help="Available commands")
        
        # Configure command
        config_parser = subparsers.add_parser("configure", help="Configure logging settings")
        self._add_configuration_args(config_parser)
        
        # Test command
        test_parser = subparsers.add_parser("test", help="Test logging configuration")
        self._add_test_args(test_parser)
        
        # Show command
        show_parser = subparsers.add_parser("show", help="Show current configuration")
        self._add_show_args(show_parser)
        
        # Reset command
        reset_parser = subparsers.add_parser("reset", help="Reset to default configuration")
        self._add_reset_args(reset_parser)
        
        # Export/Import commands
        export_parser = subparsers.add_parser("export", help="Export configuration")
        self._add_export_args(export_parser)
        
        import_parser = subparsers.add_parser("import", help="Import configuration")
        self._add_import_args(import_parser)
        
        # Add configuration arguments to main parser for direct configuration
        self._add_configuration_args(parser)
        
        return parser
    
    def _add_configuration_args(self, parser: argparse.ArgumentParser) -> None:
        """Add configuration arguments to parser."""
        
        # Basic settings
        basic_group = parser.add_argument_group("Basic Settings")
        basic_group.add_argument(
            "--enable", "--on",
            action="store_true",
            help="Enable logging"
        )
        basic_group.add_argument(
            "--disable", "--off",
            action="store_true",
            help="Disable logging"
        )
        basic_group.add_argument(
            "--log-level", "--level",
            choices=[level.value for level in LogLevelEnum] + ["CUSTOM"],
            help="Set global log level"
        )
        basic_group.add_argument(
            "--custom-level",
            type=str,
            help="Custom log level name (use with --log-level CUSTOM)"
        )
        basic_group.add_argument(
            "--async-logging",
            action="store_true",
            help="Enable asynchronous logging"
        )
        
        # File configuration
        file_group = parser.add_argument_group("File Configuration")
        file_group.add_argument(
            "--file-path", "--file",
            type=str,
            help="Log file path"
        )
        file_group.add_argument(
            "--file-encoding",
            default="utf-8",
            help="File encoding (default: utf-8)"
        )
        file_group.add_argument(
            "--file-mode",
            choices=["a", "w", "x"],
            default="a",
            help="File open mode (default: a)"
        )
        file_group.add_argument(
            "--file-buffering",
            type=int,
            default=1,
            help="File buffering (default: 1)"
        )
        
        # Rotation settings
        rotation_group = parser.add_argument_group("Rotation & Retention")
        rotation_group.add_argument(
            "--rotation-type",
            choices=[t.value for t in RotationType],
            help="Type of log rotation"
        )
        rotation_group.add_argument(
            "--rotation-size",
            type=int,
            help="Size limit for rotation"
        )
        rotation_group.add_argument(
            "--rotation-size-unit",
            choices=[u.value for u in SizeUnit],
            default="MB",
            help="Unit for rotation size (default: MB)"
        )
        rotation_group.add_argument(
            "--rotation-time",
            type=str,
            help="Time for rotation (HH:MM format)"
        )
        rotation_group.add_argument(
            "--rotation-interval",
            type=int,
            help="Time interval for rotation"
        )
        rotation_group.add_argument(
            "--rotation-interval-unit",
            choices=[u.value for u in TimeUnit],
            default="day",
            help="Unit for rotation interval (default: day)"
        )
        rotation_group.add_argument(
            "--retention-count",
            type=int,
            help="Number of rotated files to keep"
        )
        rotation_group.add_argument(
            "--retention-time",
            type=str,
            help="Time to keep rotated files (e.g., '7 days')"
        )
        rotation_group.add_argument(
            "--compression",
            choices=["gz", "bz2", "xz", "lzma", "tar.gz", "tar.bz2", "tar.xz"],
            help="Compression format for rotated files"
        )
        
        # Formatting
        format_group = parser.add_argument_group("Formatting & Colors")
        format_group.add_argument(
            "--format-preset",
            choices=[p.value for p in LogFormatPreset],
            help="Predefined format preset"
        )
        format_group.add_argument(
            "--custom-format",
            type=str,
            help="Custom format string (use with --format-preset custom)"
        )
        format_group.add_argument(
            "--colorize", "--colors",
            action="store_true",
            help="Enable colorized output"
        )
        format_group.add_argument(
            "--no-colorize", "--no-colors",
            action="store_true",
            help="Disable colorized output"
        )
        format_group.add_argument(
            "--serialize", "--json",
            action="store_true",
            help="Serialize logs as JSON"
        )
        format_group.add_argument(
            "--backtrace",
            action="store_true",
            help="Enable backtrace in error logs"
        )
        format_group.add_argument(
            "--no-backtrace",
            action="store_true",
            help="Disable backtrace in error logs"
        )
        format_group.add_argument(
            "--diagnose",
            action="store_true",
            help="Enable variable values in backtrace"
        )
        format_group.add_argument(
            "--no-diagnose",
            action="store_true",
            help="Disable variable values in backtrace"
        )
        
        # Handlers
        handler_group = parser.add_argument_group("Handlers & Output")
        handler_group.add_argument(
            "--console-handler",
            action="store_true",
            help="Enable console handler"
        )
        handler_group.add_argument(
            "--no-console-handler",
            action="store_true",
            help="Disable console handler"
        )
        handler_group.add_argument(
            "--file-handler",
            action="store_true",
            help="Enable file handler"
        )
        handler_group.add_argument(
            "--no-file-handler",
            action="store_true",
            help="Disable file handler"
        )
        handler_group.add_argument(
            "--syslog-handler",
            action="store_true",
            help="Enable syslog handler"
        )
        handler_group.add_argument(
            "--systemd-journal",
            action="store_true",
            help="Enable systemd journal handler"
        )
        
        # Advanced options
        advanced_group = parser.add_argument_group("Advanced Options")
        advanced_group.add_argument(
            "--filter-expression",
            type=str,
            help="Filter expression for log messages"
        )
        advanced_group.add_argument(
            "--catch-exceptions",
            action="store_true",
            help="Catch exceptions in handlers"
        )
        advanced_group.add_argument(
            "--no-catch-exceptions",
            action="store_true",
            help="Don't catch exceptions in handlers"
        )
        advanced_group.add_argument(
            "--enqueue",
            action="store_true",
            help="Enable async logging queue"
        )
        
        # Configuration management
        config_group = parser.add_argument_group("Configuration Management")
        config_group.add_argument(
            "--config-name",
            type=str,
            default="default",
            help="Configuration name (default: default)"
        )
        config_group.add_argument(
            "--save-config",
            action="store_true",
            help="Save configuration after applying changes"
        )
        config_group.add_argument(
            "--load-config",
            type=str,
            help="Load named configuration"
        )
    
    def _add_test_args(self, parser: argparse.ArgumentParser) -> None:
        """Add test command arguments."""
        parser.add_argument(
            "--config-name",
            type=str,
            default="default",
            help="Configuration name to test (default: default)"
        )
        parser.add_argument(
            "--preview-only",
            action="store_true",
            help="Only preview output without actually logging"
        )
        parser.add_argument(
            "--test-messages",
            nargs="+",
            help="Custom test messages"
        )
        parser.add_argument(
            "--output-file",
            type=str,
            help="Save test output to file"
        )
    
    def _add_show_args(self, parser: argparse.ArgumentParser) -> None:
        """Add show command arguments."""
        parser.add_argument(
            "--config-name",
            type=str,
            help="Configuration name to show (default: current)"
        )
        parser.add_argument(
            "--format",
            choices=["table", "json", "yaml", "toml"],
            default="table",
            help="Output format (default: table)"
        )
        parser.add_argument(
            "--verbose", "-v",
            action="store_true",
            help="Show detailed configuration"
        )
    
    def _add_reset_args(self, parser: argparse.ArgumentParser) -> None:
        """Add reset command arguments."""
        parser.add_argument(
            "--confirm",
            action="store_true",
            help="Confirm reset without prompting"
        )
        parser.add_argument(
            "--config-name",
            type=str,
            help="Configuration name to reset (default: all)"
        )
    
    def _add_export_args(self, parser: argparse.ArgumentParser) -> None:
        """Add export command arguments."""
        parser.add_argument(
            "--config-name",
            type=str,
            default="default",
            help="Configuration name to export (default: default)"
        )
        parser.add_argument(
            "--format",
            choices=["toml", "json", "yaml"],
            default="toml",
            help="Export format (default: toml)"
        )
        parser.add_argument(
            "--output-file", "-o",
            type=str,
            help="Output file path (default: stdout)"
        )
    
    def _add_import_args(self, parser: argparse.ArgumentParser) -> None:
        """Add import command arguments."""
        parser.add_argument(
            "input_file",
            type=str,
            help="Input file path"
        )
        parser.add_argument(
            "--format",
            choices=["toml", "json", "yaml"],
            help="Import format (auto-detected if not specified)"
        )
        parser.add_argument(
            "--config-name",
            type=str,
            help="Name for imported configuration (default: from file)"
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Overwrite existing configuration"
        )
    
    def _get_examples(self) -> str:
        """Get usage examples."""
        return """
Examples:
  # Launch interactive TUI
  loguru-config --interactive
  
  # Quick configuration via CLI
  loguru-config --enable --log-level DEBUG --file-path logs/app.log
  
  # Configure rotation
  loguru-config --rotation-type size --rotation-size 10 --rotation-size-unit MB
  
  # Test configuration
  loguru-config test --config-name production --preview-only
  
  # Show current configuration
  loguru-config show --format json --verbose
  
  # Export configuration
  loguru-config export --config-name production --format toml -o prod.toml
  
  # Import configuration
  loguru-config import config.toml --config-name imported
        """
    
    def parse_args(self, args: Optional[list] = None) -> argparse.Namespace:
        """Parse command line arguments."""
        return self.parser.parse_args(args)
    
    def should_launch_tui(self, args: argparse.Namespace) -> bool:
        """Determine if TUI should be launched based on arguments."""
        # Launch TUI if explicitly requested
        if args.interactive:
            return True
        
        # Launch TUI if no command and no configuration arguments provided
        if not args.command and not self._has_config_args(args):
            return True
        
        return False
    
    def _has_config_args(self, args: argparse.Namespace) -> bool:
        """Check if any configuration arguments were provided."""
        config_args = [
            'enable', 'disable', 'log_level', 'file_path', 'rotation_type',
            'format_preset', 'colorize', 'no_colorize', 'console_handler',
            'file_handler', 'syslog_handler', 'systemd_journal'
        ]
        
        return any(getattr(args, arg, None) for arg in config_args)
    
    def validate_args(self, args: argparse.Namespace) -> list[str]:
        """Validate argument combinations and return any errors."""
        errors = []
        
        # Check conflicting arguments
        if args.enable and args.disable:
            errors.append("Cannot specify both --enable and --disable")
        
        if args.colorize and args.no_colorize:
            errors.append("Cannot specify both --colorize and --no-colorize")
        
        if args.backtrace and args.no_backtrace:
            errors.append("Cannot specify both --backtrace and --no-backtrace")
        
        if args.diagnose and args.no_diagnose:
            errors.append("Cannot specify both --diagnose and --no-diagnose")
        
        # Check custom level requirements
        if hasattr(args, 'log_level') and args.log_level == "CUSTOM" and not args.custom_level:
            errors.append("--custom-level is required when --log-level is CUSTOM")
        
        # Check custom format requirements
        if hasattr(args, 'format_preset') and args.format_preset == "custom" and not args.custom_format:
            errors.append("--custom-format is required when --format-preset is custom")
        
        # Check file path for file handlers
        if hasattr(args, 'file_handler') and args.file_handler and not args.file_path:
            errors.append("--file-path is required when --file-handler is enabled")
        
        # Check rotation time format
        if hasattr(args, 'rotation_time') and args.rotation_time:
            import re
            if not re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', args.rotation_time):
                errors.append("--rotation-time must be in HH:MM format (24-hour)")
        
        return errors
