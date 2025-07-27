#!/usr/bin/env python3
"""
Loguru Configuration Tool - TUI and CLI Interface

This is the main entry point for the Loguru configuration tool that provides
both a comprehensive TUI (Text User Interface) and CLI (Command Line Interface)
for configuring Loguru logging settings.

Usage:
    # Launch interactive TUI
    python loguru_config_tui.py --interactive
    
    # Quick CLI configuration
    python loguru_config_tui.py --enable --log-level DEBUG --file-path logs/app.log
    
    # Test configuration
    python loguru_config_tui.py test --config-name production --preview-only
    
    # Show current configuration
    python loguru_config_tui.py show --format json
"""

import asyncio
import sys
from pathlib import Path

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.presentation.cli.parser import LoguruArgumentParser
from src.presentation.cli.commands import CLICommandHandler


async def main() -> int:
    """
    Main entry point for the Loguru configuration tool.
    
    Returns:
        Exit code (0 for success, non-zero for error).
    """
    try:
        # Parse command line arguments
        parser = LoguruArgumentParser()
        args = parser.parse_args()
        
        # Validate arguments
        validation_errors = parser.validate_args(args)
        if validation_errors:
            print("Argument validation errors:", file=sys.stderr)
            for error in validation_errors:
                print(f"  - {error}", file=sys.stderr)
            return 1
        
        # Determine if we should launch TUI or handle CLI command
        if parser.should_launch_tui(args):
            return await launch_tui(args)
        else:
            return await handle_cli_command(args)
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        return 130  # Standard exit code for SIGINT
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


async def launch_tui(args) -> int:
    """
    Launch the interactive TUI interface.
    
    Args:
        args: Parsed command line arguments.
        
    Returns:
        Exit code from TUI application.
    """
    try:
        # Import TUI components (lazy import to avoid loading Textual if not needed)
        from src.presentation.tui.app import LoguruConfigApp
        from src.infrastructure.logger_dependencies import get_logger_config_dependencies
        
        print("🚀 Launching Loguru Configuration TUI...")
        
        # Get dependencies
        config_port, logger_port = await get_logger_config_dependencies()
        
        # Create and run TUI application
        app = LoguruConfigApp(config_port, logger_port)
        
        # Load initial configuration if specified
        if hasattr(args, 'load_config') and args.load_config:
            await app.load_configuration(args.load_config)
        
        # Run the TUI
        await app.run_async()
        
        return 0
        
    except ImportError as e:
        print(f"TUI dependencies not available: {e}", file=sys.stderr)
        print("Install with: pip install textual", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"TUI failed: {e}", file=sys.stderr)
        return 1


async def handle_cli_command(args) -> int:
    """
    Handle CLI command execution.
    
    Args:
        args: Parsed command line arguments.
        
    Returns:
        Exit code from CLI command.
    """
    try:
        # Import CLI dependencies
        from src.infrastructure.logger_dependencies import get_logger_config_dependencies
        
        # Get dependencies
        config_port, logger_port = await get_logger_config_dependencies()
        
        # Create CLI command handler
        cli_handler = CLICommandHandler(config_port, logger_port)
        
        # Execute command
        return await cli_handler.handle_command(args)
        
    except Exception as e:
        print(f"CLI command failed: {e}", file=sys.stderr)
        return 1


def print_banner():
    """Print application banner."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    Loguru Configuration Tool                 ║
║                                                              ║
║  🎯 Comprehensive TUI and CLI for Loguru logging setup      ║
║  ⚡ Real-time configuration testing and preview             ║
║  🏗️ Built with Hexagonal Architecture principles           ║
║                                                              ║
║  Use --help for detailed usage information                  ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_quick_help():
    """Print quick help information."""
    help_text = """
Quick Start:
  🖥️  Interactive TUI:     python loguru_config_tui.py --interactive
  ⚡ Quick CLI setup:     python loguru_config_tui.py --enable --log-level DEBUG --file logs/app.log
  🧪 Test configuration:  python loguru_config_tui.py test --preview-only
  📊 Show current config: python loguru_config_tui.py show --format table
  
For detailed help: python loguru_config_tui.py --help
    """
    print(help_text)


if __name__ == "__main__":
    # Print banner for interactive usage
    if len(sys.argv) == 1 or "--interactive" in sys.argv:
        print_banner()
    
    # Show quick help if no arguments provided
    if len(sys.argv) == 1:
        print_quick_help()
        sys.exit(0)
    
    # Run main application
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"💥 Fatal error: {e}", file=sys.stderr)
        sys.exit(1)
